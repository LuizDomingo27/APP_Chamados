"""
services/reposicao_parser_service.py

Na planilha de Reposições, o campo "Nome da tarefa" também concentra em
texto livre número da reposição / ordem de produção / oficina / parte da
peça — mas, ao contrário dos Chamados, a ORDEM desses pedaços não é
100% consistente (poucas linhas têm oficina e ordem de produção
trocadas de posição, ex.: "173-FACCAO ELLO LTDA- 300270501-Viés de
reforço"). Um regex rígido de posição erraria esses casos.

Por isso a extração usa como âncora os campos já rotulados dentro de
"Notas" — "Ordem de Produção Mestre", "Parte da peça", "Motivo" e
"Quantidade" — que estão presentes em 100% das linhas testadas. A
oficina é obtida por eliminação: pega-se o texto de "Nome da tarefa" sem
o prefixo do número, remove-se dele a ordem de produção e a parte da
peça (já conhecidas via Notas) e o que sobra é o nome da oficina,
independente da ordem em que apareciam originalmente.

Formato observado:
    26-300260622-CONFECCOES FRANOELDA M. M. ARAUJO EIRELI-Traseiro

    Notas:
    Ordem de Produção Mestre: 300260622
    Email da oficina: falconconfeccoes@hotmail.com
    Parte da peça: Traseiro
    Motivo: Quantidade insuficiente para terminar a ordem
    Quantidade: 7
    Observações:
"""

from __future__ import annotations

import re

import pandas as pd

from core.config import (
    COL_CATEGORIA,
    COL_MOTIVO,
    COL_NOME_TAREFA,
    COL_NOTAS,
    COL_NUM_REPOSICAO,
    COL_OFICINA,
    COL_ORDEM_PRODUCAO,
    COL_PARTE_PECA,
    COL_QUANTIDADE_REPOSICAO,
    OFICINA_INVALID_NAMES_RAW,
    OFICINA_INVALID_NAMES_REPOSICAO_RAW,
    OFICINAS_OFICIAIS_RAW,
)
from core.motivo_normalize import canonicalize_motivo
from services.parser_service import canonicalize_oficinas, remove_invalid_oficinas

_VAZIO = "Não informado"

# O "Nome da tarefa" aparece em dois formatos na planilha:
#   26-300260622-CONFECCOES ... -Traseiro
#   MALHA- 1000-300277277-F & L AZEVEDO CONFECCAO LTDA FILIAL  - Etiqueta ...
# O segundo traz na frente a linha de matéria-prima (JEANS/MALHA/POLO/TEAR)
# e responde por ~20% das linhas. Sem o prefixo opcional aqui, o número não
# era reconhecido e todo o trecho "MALHA- 1000-" acabava colado no nome da
# oficina — como o número muda a cada reposição, cada linha virava uma
# "oficina" diferente e os totais por oficina saíam fragmentados.
_RE_NUMERO = re.compile(r"^\s*(?:[A-Za-zÀ-ÿ]+-\s*)?(\d+)-")

# Sufixos de razão social que marcam o fim do nome real da oficina. Usados
# como rede de segurança: em algumas linhas o texto de "Parte da peça" no
# "Nome da tarefa" não bate 100% com o valor rotulado em Notas (ex.: uma
# descrição mais longa em vez do nome curto da peça), então a eliminação
# abaixo não consegue remover esse pedaço e ele fica grudado na oficina
# (ex.: "DANTAS E PAULINO CONFECCOES LTDA-Linha aguardando retorno do
# código da"). Cortando tudo depois da ÚLTIMA ocorrência de um sufixo
# empresarial reconhecido, recuperamos só o nome da empresa nesses casos
# sem arriscar truncar nomes legítimos como "ASA CONFECCOES LTDA - ME"
# (o "ME" final também é reconhecido, então nada é cortado ali). Oficinas
# sem nenhum desses sufixos (ex.: "INDUSTRIALIZACAO EXTERNA") não são
# afetadas.
# O sufixo empresarial pode vir seguido do sufixo de unidade/linha
# (MATRIZ, FILIAL, PÓLO, TEAR, BÁSICO, ELABORADO), que faz parte do nome
# cadastrado — "F & L AZEVEDO CONFECCAO LTDA FILIAL". Cortar no LTDA
# descartaria o "FILIAL" e somaria matriz e filial no mesmo total, então o
# corte só acontece depois desses sufixos.
_RE_SUFIXO_EMPRESARIAL = re.compile(
    r"\b(?:LTDA|EIRELI|EPP|MEI|S/A|S\.A\.?|ME|LIMITADA)\b\.?"
    r"(?:\s*-?\s*(?:ME|MATRIZ|FILIAL|P[OÓ]LO|TEAR|B[AÁ]SICO|ELABORADO))*",
    re.IGNORECASE,
)


def _truncar_apos_sufixo_empresarial(oficina: str) -> str:
    matches = list(_RE_SUFIXO_EMPRESARIAL.finditer(oficina))
    if not matches:
        return oficina
    return oficina[: matches[-1].end()].strip()


def _extract_label(text: str, label: str) -> str | None:
    """Extrai o valor de um campo rotulado dentro de Notas (ex.: 'Motivo:
    valor'). Cada campo ocupa uma linha, então o valor vai até a próxima
    quebra de linha ou o fim do texto."""
    match = re.search(rf"{re.escape(label)}:\s*(.*?)(?:\n|$)", text, re.DOTALL)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def parse_reposicao_row(nome_tarefa: str, notas: str) -> dict[str, str | None]:
    """Extrai número da reposição, oficina, ordem de produção, parte da
    peça e motivo de uma linha da planilha de Reposições."""
    nome = str(nome_tarefa or "")
    notas_txt = str(notas or "")

    numero_match = _RE_NUMERO.match(nome)
    numero = numero_match.group(1) if numero_match else None
    remainder = nome[numero_match.end():] if numero_match else nome

    ordem = _extract_label(notas_txt, "Ordem de Produção Mestre")
    parte = _extract_label(notas_txt, "Parte da peça")
    motivo = _extract_label(notas_txt, "Motivo")
    quantidade = _extract_label(notas_txt, "Quantidade")

    # Elimina do texto restante a ordem de produção e a parte da peça já
    # conhecidas (via Notas) — o que sobra é o nome da oficina, não
    # importa em que posição elas apareciam no "Nome da tarefa".
    oficina = remainder
    if ordem:
        oficina = oficina.replace(ordem, "")
    if parte:
        # A "Parte da peça" marca o início do trecho descritivo do "Nome da
        # tarefa" — remove-se ela E tudo que vier depois (até o fim do
        # texto). Antes o corte era ancorado só no FIM (\s*$), então quando
        # o nome trazia uma descrição livre mais longa que apenas COMEÇA com
        # o rótulo curto de Notas (ex.: parte "Etiqueta de preço" vs. texto
        # "Etiqueta de preço aguardando a impressão da etiqueta de preço"),
        # o parte não batia no fim e a descrição ficava grudada em oficinas
        # sem sufixo empresarial (ex.: "F DA SILVA JUNIOR-Etiqueta de preço
        # aguardando..."). Cortando da parte até o fim, sobra só a oficina.
        oficina = re.sub(re.escape(parte) + r".*$", "", oficina, flags=re.IGNORECASE | re.DOTALL)
    oficina = oficina.strip(" -\t\n")
    oficina = _truncar_apos_sufixo_empresarial(oficina)

    # Guarda-chuva para os ~0,1% de linhas onde a eliminação não deixa um
    # nome de oficina plausível (texto vazio ou só dígitos residuais).
    if not oficina or len(oficina) < 3 or oficina.replace(" ", "").isdigit():
        oficina = _VAZIO

    return {
        COL_NUM_REPOSICAO: numero or _VAZIO,
        COL_OFICINA: oficina,
        COL_ORDEM_PRODUCAO: ordem or _VAZIO,
        COL_PARTE_PECA: parte or _VAZIO,
        # O motivo é digitado à mão pela oficina — a mesma causa aparece em
        # dezenas de grafias ("VEIO FALTANDO" / "faltou" / "insuficiente para
        # finalizar a ordem"). Sem reduzir ao rótulo canônico, o ranking de
        # motivos se fragmenta e nenhuma fatia reflete o volume real.
        COL_MOTIVO: canonicalize_motivo(motivo) if motivo else _VAZIO,
        COL_QUANTIDADE_REPOSICAO: quantidade or _VAZIO,
    }


def enrich_with_parsed_fields_reposicao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica parse_reposicao_row em todo o DataFrame, adiciona as colunas
    derivadas (Número da Reposição, Oficina, Ordem de Produção, Parte da
    Peça, Motivo, Quantidade Solicitada), remove reposições com oficina
    inválida e padroniza grafias divergentes do nome da oficina.

    A canonicalização reaproveita services.parser_service, mas aqui é
    ancorada no cadastro oficial (OFICINAS_OFICIAIS_RAW): o nome que vai
    para os KPIs é sempre o cadastrado, não a grafia mais frequente da
    planilha.
    """
    parsed = df.apply(
        lambda row: parse_reposicao_row(row[COL_NOME_TAREFA], row[COL_NOTAS]),
        axis=1,
    ).apply(pd.Series)

    out = df.copy()
    cols = [
        COL_NUM_REPOSICAO,
        COL_OFICINA,
        COL_ORDEM_PRODUCAO,
        COL_PARTE_PECA,
        COL_MOTIVO,
        COL_QUANTIDADE_REPOSICAO,
    ]
    out[cols] = parsed[cols]
    out = remove_invalid_oficinas(
        out, OFICINA_INVALID_NAMES_RAW + OFICINA_INVALID_NAMES_REPOSICAO_RAW
    )
    out = canonicalize_oficinas(out, oficinas_oficiais=OFICINAS_OFICIAIS_RAW)

    # A planilha de origem tem espaços em branco soltos na Categoria
    # (ex.: "    TRIAGEM", "AVIAMENTO ") — não são grafias divergentes,
    # só ruído de digitação, então um strip simples já resolve.
    if COL_CATEGORIA in out.columns:
        out[COL_CATEGORIA] = out[COL_CATEGORIA].astype(str).str.strip()

    return out
