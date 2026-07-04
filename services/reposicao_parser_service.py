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
)
from services.parser_service import canonicalize_oficinas, remove_invalid_oficinas

_VAZIO = "Não informado"

_RE_NUMERO = re.compile(r"^(\d+)-")

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
_RE_SUFIXO_EMPRESARIAL = re.compile(r"\b(?:LTDA|EIRELI|EPP|MEI|S/A|S\.A\.?|ME)\b", re.IGNORECASE)


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
        oficina = re.sub(re.escape(parte) + r"\s*$", "", oficina, flags=re.IGNORECASE)
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
        COL_MOTIVO: motivo or _VAZIO,
        COL_QUANTIDADE_REPOSICAO: quantidade or _VAZIO,
    }


def enrich_with_parsed_fields_reposicao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica parse_reposicao_row em todo o DataFrame, adiciona as colunas
    derivadas (Número da Reposição, Oficina, Ordem de Produção, Parte da
    Peça, Motivo, Quantidade Solicitada), remove reposições com oficina
    inválida e padroniza grafias divergentes do nome da oficina —
    reaproveitando a mesma lógica de canonicalização usada nos Chamados
    (services.parser_service), já que são as mesmas oficinas parceiras.
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
    out = remove_invalid_oficinas(out)
    out = canonicalize_oficinas(out)

    # A planilha de origem tem espaços em branco soltos na Categoria
    # (ex.: "    TRIAGEM", "AVIAMENTO ") — não são grafias divergentes,
    # só ruído de digitação, então um strip simples já resolve.
    if COL_CATEGORIA in out.columns:
        out[COL_CATEGORIA] = out[COL_CATEGORIA].astype(str).str.strip()

    return out
