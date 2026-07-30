"""
core/materia_prima_normalize.py

A LINHA DE MATÉRIA-PRIMA de uma reposição (Jeans, Malha, Pólo, Tear,
Básico, Elaborado) não é uma coluna da planilha: ela aparece embutida no
texto de "Nome da tarefa", em duas posições diferentes, e hoje as duas são
descartadas no parsing.

  1) como PREFIXO, antes do número da reposição — presente em ~20% das
     linhas:
        "MALHA- 1000-300277277-F & L AZEVEDO CONFECCAO LTDA FILIAL - Etiqueta"
     services/reposicao_parser_service.py reconhece esse prefixo só para
     não colá-lo no nome da oficina, e o joga fora.

  2) como SUFIXO do nome da oficina:
        "1-300260622-IDEAL CONFECCOES LTDA POLO-Traseiro"
     services/parser_service.remover_sufixo_materia_prima remove esse
     sufixo antes de agregar (matriz/filial de uma mesma empresa precisam
     somar junto), e com isso a informação de linha também se perde.

Este módulo é a camada PURA dessa extração: recebe texto, devolve o rótulo
canônico. Sem pandas e sem streamlit — quem trabalha com DataFrame é
services/material_service.py.

Precisão da detecção (o ponto delicado do módulo):

  • Os tokens de linha BASICO / ELABORADO / POLO / TEAR só aparecem no
    cadastro oficial de oficinas como sufixo final do nome — nunca no meio
    de uma razão social. Por isso são reconhecidos por posição (fim do
    trecho da oficina), o que evita casar com descrições de peça como
    "Gola polo".
  • JEANS e MALHA, ao contrário, só são aceitos no PREFIXO: "JEANS"
    aparece no meio de um nome de oficina real ("LAJEDO JEANS CONFECÇÕES
    LTDA"), e uma busca livre classificaria toda reposição dessa oficina
    como linha Jeans.
"""

from __future__ import annotations

import re

from core.text_normalize import normalize_text_key

MATERIA_PRIMA_NAO_INFORMADA = "Não informado"

# Rótulos canônicos — todo texto extraído é reduzido a um destes.
MP_JEANS = "Jeans"
MP_MALHA = "Malha"
MP_POLO = "Pólo"
MP_TEAR = "Tear"
MP_BASICO = "Básico"
MP_ELABORADO = "Elaborado"

# Token normalizado (sem acento, maiúsculo) -> rótulo de exibição.
_CANONICO_POR_TOKEN: dict[str, str] = {
    "JEANS": MP_JEANS,
    "MALHA": MP_MALHA,
    "POLO": MP_POLO,
    "TEAR": MP_TEAR,
    "BASICO": MP_BASICO,
    "ELABORADO": MP_ELABORADO,
}

# Prefixo da linha, antes do número da reposição. Mesmo formato que o
# _RE_NUMERO de reposicao_parser_service reconhece e descarta — aqui é
# justamente o pedaço que interessa.
_RE_PREFIXO = re.compile(r"^([A-Z]+)\s*-")

# Tokens aceitos na posição de SUFIXO do nome da oficina. Deliberadamente
# sem JEANS/MALHA (ver o cabeçalho do módulo).
_RE_SUFIXO_LINHA = re.compile(r"\b(BASICO|ELABORADO|POLO|TEAR)$")


def canonicalize_materia_prima(texto: str) -> str:
    """
    Reduz um token de linha de matéria-prima ao rótulo canônico.

    Texto que não corresponde a nenhuma linha conhecida devolve
    "Não informado" em vez de levantar exceção: a planilha é preenchida à
    mão e um prefixo novo (uma linha de produção criada depois desta
    tabela) não pode derrubar o dashboard — ele apenas não entra no
    ranking, e a ausência fica visível na tela.
    """
    return _CANONICO_POR_TOKEN.get(normalize_text_key(texto), MATERIA_PRIMA_NAO_INFORMADA)


def extrair_materia_prima(nome_tarefa: str, parte_peca: str | None = None) -> str:
    """
    Extrai a linha de matéria-prima do "Nome da tarefa".

    `parte_peca` é o valor já rotulado em Notas ("Parte da peça"). Quando
    informado, ele e tudo que vem depois são removidos antes da busca pelo
    sufixo — é o mesmo recorte que reposicao_parser_service usa para
    isolar o nome da oficina, e é o que impede que uma descrição de peça
    ("Gola polo", "Linha para tear") seja lida como linha de produção.

    Devolve "Não informado" quando nenhuma das duas posições traz uma
    linha reconhecida — o que é o caso normal na maioria das linhas, não
    um erro.
    """
    chave = normalize_text_key(nome_tarefa)
    if not chave:
        return MATERIA_PRIMA_NAO_INFORMADA

    # 1) Prefixo: posição inequívoca, aceita qualquer linha conhecida.
    prefixo = _RE_PREFIXO.match(chave)
    if prefixo:
        canonico = _CANONICO_POR_TOKEN.get(prefixo.group(1))
        if canonico:
            return canonico

    # 2) Sufixo do trecho da oficina: corta a descrição da peça e testa o
    #    fim do que sobrou.
    trecho = chave
    if parte_peca:
        chave_parte = normalize_text_key(parte_peca)
        if chave_parte:
            trecho = re.sub(re.escape(chave_parte) + r".*$", "", trecho)
    trecho = trecho.strip(" -\t")

    sufixo = _RE_SUFIXO_LINHA.search(trecho)
    if sufixo:
        return _CANONICO_POR_TOKEN[sufixo.group(1)]

    return MATERIA_PRIMA_NAO_INFORMADA
