"""
core/item_secundario.py

Classifica a reposição como de ITEM SECUNDÁRIO — material de apoio da
oficina (filme plástico, lacre, papelão para gabarito, pistola, sacos,
capas e artoks vazios), que não é parte da peça costurada.

ONDE O ITEM ESTÁ: dentro de "Notas", no campo rotulado "Parte da peça:"
(presente em 99,9% das linhas da planilha). O resto das Notas (Motivo,
Observações) fala do problema, não do item — buscar nelas trazia falso
positivo, como "Agulha" cujo motivo cita "agulha DA PISTOLA". Por isso a
classificação olha só a Parte da peça; Observações só entram quando a
Parte não veio preenchida com texto.

POR QUE NÃO UM "CONTÉM": o texto é digitado à mão, com erro de grafia
("PISTOA", "FIME PLASTICO", "ARTOC"), ordem invertida ("PLASTICO FILME"),
plural, palavras coladas e complementos ("LACRES PARA AS OPS"). O
algoritmo:

  1. normaliza (sem acento, maiúscula, sem pontuação) e separa palavras;
  2. reduz cada palavra a um "esqueleto" fonético (K/Q→C, Y→I, plural e
     letras dobradas fora), para "ARTOKS"/"ARTOC"/"ARTOQUE" virarem o mesmo;
  3. compara palavra a palavra com as palavras-chave tolerando um erro a
     cada 5 letras (distância de edição) — "PISTOA" casa com PISTOLA, mas
     "PAPEL" não vira PAPELAO e "LACO" (laço) não vira LACRE;
  4. olha a PRIMEIRA palavra relevante (o núcleo do pedido): se for um
     acessório como Agulha, Pino ou Etiqueta ("AGULHA DE PISTOLA"), o
     pedido é desse acessório, não do item secundário;
  5. aplica as regras na ordem, da mais específica para a mais genérica.

Função pura (sem pandas/streamlit), para poder ser testada isoladamente.
"""

from __future__ import annotations

import re

from core.text_normalize import normalize_text_key

# Rótulos canônicos exibidos no card.
FILME_PLASTICO = "Filme Plástico"
PAPEL_FILME = "Papel Filme"
LACRE = "Lacre"
PAPELAO_GABARITO = "Papelão para Gabarito"
PISTOLA = "Pistola"
SACOS_ARTOK = "Sacos para Artok"
ARTOK_VAZIO = "Artok Vazio"
CAPAS_ARTOK = "Capas de Artok"

ITENS_SECUNDARIOS = (
    FILME_PLASTICO,
    PAPEL_FILME,
    LACRE,
    PAPELAO_GABARITO,
    PISTOLA,
    SACOS_ARTOK,
    ARTOK_VAZIO,
    CAPAS_ARTOK,
)

# Palavras que não carregam significado para a classificação.
_PALAVRAS_VAZIAS = {
    "DE", "DA", "DO", "DAS", "DOS", "PARA", "PRA", "PRO", "P", "E", "A", "O",
    "AS", "OS", "COM", "EM", "NA", "NO", "UM", "UMA", "REPOSICAO", "SOLICITO",
    "SOLICITACAO", "MAIS",
}

# Núcleos que indicam que o pedido é de OUTRO item, mesmo que o texto cite
# um secundário como complemento ("AGULHA DE PISTOLA", "PINO DA PISTOLA").
_NUCLEOS_EXCLUIDOS = {"AGULHA", "PINO", "PENTE", "ETIQUETA", "ETQ", "TAG", "MOLA"}


def _esqueleto(palavra: str) -> str:
    """Forma reduzida da palavra para comparar grafias diferentes."""
    p = palavra.upper()
    p = p.replace("QU", "C").replace("Q", "C").replace("K", "C")
    p = p.replace("Y", "I").replace("W", "V").replace("PH", "F")
    p = re.sub(r"(.)\1+", r"\1", p)  # letras dobradas: "LACRRE" -> "LACRE"
    if len(p) > 3 and p.endswith("S"):  # plural: "LACRES" -> "LACRE"
        p = p[:-1]
    # "ARTOQUE" -> "ARTOCE" -> "ARTOC": o E final de grafia aportuguesada.
    if len(p) > 4 and p.endswith("CE"):
        p = p[:-1]
    return p


def _distancia(a: str, b: str) -> int:
    """Distância de edição (Levenshtein) com transposição simples."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 2:
        return 99
    anterior2: list[int] | None = None
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            custo = 0 if ca == cb else 1
            atual[j] = min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + custo)
            if (
                anterior2 is not None and i > 1 and j > 1
                and ca == b[j - 2] and a[i - 2] == cb
            ):
                atual[j] = min(atual[j], anterior2[j - 2] + 1)
        anterior2, anterior = anterior, atual
    return anterior[-1]


# Itens reais da planilha a uma letra de distância de uma palavra-chave:
# "ELASTICO" ~ PLASTICO, "LACO" (laço) ~ LACRE. Nunca são erro de grafia.
_PALAVRAS_PROTEGIDAS = {"ELASTICO", "LACO", "FITA", "FILETE", "PASTA", "PAPEL"}


def _parecida(palavra: str, chave: str) -> bool:
    """Mesma palavra, admitindo 1 erro a cada 5 letras da palavra-chave.

    O erro tolerado nunca é na primeira letra (quem digita erra no meio ou
    no fim da palavra; trocar a inicial costuma dar OUTRA palavra, como
    ELASTICO/PLASTICO) e palavras protegidas nunca casam por aproximação.
    """
    a, b = _esqueleto(palavra), _esqueleto(chave)
    if a == b:
        return True
    if a in _PALAVRAS_PROTEGIDAS or not a or a[0] != b[0]:
        return False
    tolerancia = len(b) // 5
    return tolerancia > 0 and _distancia(a, b) <= tolerancia


# Palavras-chave que, coladas a outras ("FILMEPLASTICO"), ainda devem ser
# reconhecidas. Só entram as longas e inconfundíveis.
_CHAVES_COLADAS = ("FILME", "PLASTICO", "PAPELAO", "GABARITO", "PISTOLA", "ARTOC", "LACRE")


class _Texto:
    """Palavras do texto já normalizadas, com consultas aproximadas."""

    def __init__(self, texto: str) -> None:
        chave = normalize_text_key(texto)
        chave = re.sub(r"[^A-Z0-9 ]+", " ", chave)
        self.palavras = [p for p in chave.split() if p not in _PALAVRAS_VAZIAS and not p.isdigit()]
        self._colado = _esqueleto("".join(self.palavras)) if self.palavras else ""

    @property
    def nucleo(self) -> str:
        return self.palavras[0] if self.palavras else ""

    def tem(self, chave: str) -> bool:
        if any(_parecida(p, chave) for p in self.palavras):
            return True
        esq = _esqueleto(chave)
        return chave in _CHAVES_COLADAS and esq in self._colado

    def nucleo_e(self, chave: str) -> bool:
        return bool(self.nucleo) and _parecida(self.nucleo, chave)


def _classificar(t: _Texto) -> str | None:
    if not t.palavras:
        return None
    if any(_parecida(t.nucleo, n) for n in _NUCLEOS_EXCLUIDOS):
        return None

    artok = t.tem("ARTOK")
    # Artok: o que diferencia é a palavra que acompanha.
    if artok and (t.tem("SACO") or t.tem("SACOLA")):
        return SACOS_ARTOK
    if artok and (t.tem("CAPA") or t.tem("PANO") or t.tem("CAPINHA")):
        return CAPAS_ARTOK
    if artok:
        return ARTOK_VAZIO
    # Sacos sem citar artok ("SACOS PARA EMBALAR ORDENS") são o mesmo
    # material de embalagem — mas só quando o saco é o núcleo do pedido.
    if t.nucleo_e("SACO") or t.nucleo_e("SACOLA"):
        return SACOS_ARTOK

    if t.tem("LACRE"):
        return LACRE
    if t.tem("PAPELAO") or t.tem("GABARITO"):
        return PAPELAO_GABARITO

    filme = t.tem("FILME")
    if filme and t.tem("PAPEL"):
        return PAPEL_FILME
    # "PLASTICO" sozinho só conta como núcleo ("PLASTICO PARA FUSIONAR
    # PASSANTE"): no meio do texto pode ser só o material de outra peça.
    if filme or t.nucleo_e("PLASTICO"):
        return FILME_PLASTICO

    if t.nucleo_e("PISTOLA"):
        return PISTOLA
    return None


def _tem_letras(texto: str | None) -> bool:
    return bool(texto) and bool(re.search(r"[A-Za-zÀ-ÿ]{3,}", str(texto)))


def classificar_item_secundario(parte_peca: str | None, observacoes: str | None = None) -> str | None:
    """
    Devolve o rótulo canônico do item secundário pedido, ou None quando a
    reposição não é de item secundário.

    `parte_peca` é o valor do campo "Parte da peça" das Notas. As
    `observacoes` só são consultadas quando a parte não traz texto (vazia,
    "0000", "10"...).
    """
    if _tem_letras(parte_peca):
        return _classificar(_Texto(str(parte_peca)))
    if _tem_letras(observacoes):
        return _classificar(_Texto(str(observacoes)))
    return None
