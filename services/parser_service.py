"""
services/parser_service.py

O campo "Nome da tarefa" concentra, em texto livre, várias informações
estruturadas (nº do chamado, oficina, tipo de solicitação). Esta camada
isola toda a lógica de regex/parsing — se o padrão de texto mudar no
futuro, só este arquivo precisa ser ajustado.

Formato observado:
    CHAMADO Nº-25128- REF.-15733084-OFICINA-ACAUÃ CONFECÇÕES LTDA
    -SOLICITAÇÃO- Solicitação de Nota fiscal
"""

from __future__ import annotations

import re

import pandas as pd

from core.config import (
    COL_NOME_TAREFA,
    COL_NUM_CHAMADO,
    COL_OFICINA,
    COL_SOLICITACAO,
    OFICINA_ALIASES_RAW,
    OFICINA_INVALID_NAMES_RAW,
)
from core.text_normalize import (
    build_normalized_alias_map,
    build_normalized_key_set,
    normalize_text_key,
)

_OFICINA_ALIASES = build_normalized_alias_map(OFICINA_ALIASES_RAW)
_OFICINA_INVALID_KEYS = build_normalized_key_set(OFICINA_INVALID_NAMES_RAW)

_RE_NUMERO = re.compile(r"CHAMADO\s*Nº-(\d+)")
_RE_OFICINA = re.compile(r"OFICINA-(.*?)\n", re.DOTALL)
_RE_SOLICITACAO = re.compile(r"SOLICITAÇÃO-\s*(.*)$", re.DOTALL)

_VAZIO = "Não informado"


def _extract_one(pattern: re.Pattern, text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def parse_nome_tarefa(nome_tarefa: str) -> dict[str, str | None]:
    """Extrai número do chamado, oficina e tipo de solicitação de um texto."""
    text = str(nome_tarefa or "")
    return {
        COL_NUM_CHAMADO: _extract_one(_RE_NUMERO, text),
        COL_OFICINA: _extract_one(_RE_OFICINA, text) or _VAZIO,
        COL_SOLICITACAO: _extract_one(_RE_SOLICITACAO, text) or _VAZIO,
    }


def remove_invalid_oficinas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove chamados cuja oficina é um valor inválido/lixo (ex.: "aaaaaa",
    entrada de teste). A lista de nomes inválidos vem de
    core.config.OFICINA_INVALID_NAMES_RAW.
    """
    mask_invalida = df[COL_OFICINA].apply(normalize_text_key).isin(_OFICINA_INVALID_KEYS)
    return df[~mask_invalida].copy()


def canonicalize_oficinas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza grafias divergentes da mesma oficina para um único nome
    canônico, em duas etapas:

    1) Automática: agrupa por chave normalizada (sem acento/maiúscula) e
       elege a grafia mais frequente como nome oficial — resolve casos
       como "GENESIS" vs "genesis".
    2) Manual: aplica os aliases definidos em core.config.OFICINA_ALIASES_RAW
       por cima do resultado da etapa 1 — resolve casos que a normalização
       automática não cobre, como razão social divergente ou nome
       incompleto (ex.: "SOLY BRASIL" -> "SOLY BRASIL LTDA").
    """
    out = df.copy()
    out["_oficina_key"] = out[COL_OFICINA].apply(normalize_text_key)

    contagem = (
        out.groupby(["_oficina_key", COL_OFICINA]).size().reset_index(name="qtd")
    )
    contagem = contagem.sort_values(
        ["_oficina_key", "qtd", COL_OFICINA],
        ascending=[True, False, False],
        key=lambda s: s.str.len() if s.name == COL_OFICINA else s,
    )
    canonico_por_key = (
        contagem.groupby("_oficina_key")[COL_OFICINA].first().to_dict()
    )

    out[COL_OFICINA] = out["_oficina_key"].map(canonico_por_key)

    # Etapa 2: aliases manuais — aplicados sobre a chave normalizada
    # original, para cobrir grafias que a etapa automática (agrupada por
    # chave) não uniu por serem chaves distintas entre si.
    out[COL_OFICINA] = out.apply(
        lambda row: _OFICINA_ALIASES.get(row["_oficina_key"], row[COL_OFICINA]),
        axis=1,
    )

    return out.drop(columns="_oficina_key")


def enrich_with_parsed_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica parse_nome_tarefa em todo o DataFrame, adiciona as colunas
    derivadas (Número do Chamado, Oficina, Tipo de Solicitação), remove
    chamados com oficina inválida e padroniza grafias divergentes do
    nome da oficina.
    """
    parsed = df[COL_NOME_TAREFA].apply(parse_nome_tarefa).apply(pd.Series)
    out = df.copy()
    out[[COL_NUM_CHAMADO, COL_OFICINA, COL_SOLICITACAO]] = parsed[
        [COL_NUM_CHAMADO, COL_OFICINA, COL_SOLICITACAO]
    ]
    out = remove_invalid_oficinas(out)
    out = canonicalize_oficinas(out)
    return out
