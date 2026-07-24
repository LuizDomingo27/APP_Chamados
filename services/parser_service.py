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

import hashlib
import json
import re

import pandas as pd

from core.config import (
    COL_NOME_TAREFA,
    COL_NUM_CHAMADO,
    COL_OFICINA,
    COL_SOLICITACAO,
    OFICINA_ALIASES_RAW,
    OFICINA_INVALID_NAMES_RAW,
    OFICINA_SUFIXOS_MATERIA_PRIMA,
    OFICINAS_OFICIAIS_RAW,
)
from core.text_normalize import (
    build_normalized_alias_map,
    build_normalized_key_set,
    normalize_company_key,
    normalize_text_key,
)

_OFICINA_INVALID_KEYS = build_normalized_key_set(OFICINA_INVALID_NAMES_RAW)

_RE_SUFIXO_MP = re.compile(
    r"\s*\b(?:" + "|".join(OFICINA_SUFIXOS_MATERIA_PRIMA) + r")\s*$",
    re.IGNORECASE,
)

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


def canonicalizacao_fingerprint(*regras: object) -> str:
    """
    Assinatura curta das regras de padronização de oficinas (cadastro
    oficial, aliases, lista de inválidos).

    Existe por causa do @st.cache_data das páginas: o cache é chaveado
    pelos bytes do arquivo enviado e pelo código da própria função
    decorada — mudanças aqui, em core.config ou neste módulo passam
    despercebidas, e o dashboard continua exibindo o resultado antigo
    mesmo depois do deploy. Passando esta assinatura como argumento da
    função cacheada, editar as regras invalida o cache automaticamente.
    """
    dados = json.dumps(regras, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(dados.encode("utf-8")).hexdigest()[:16]


def remove_invalid_oficinas(
    df: pd.DataFrame, nomes_invalidos: list[str] | None = None
) -> pd.DataFrame:
    """
    Remove chamados cuja oficina é um valor inválido/lixo (ex.: "aaaaaa",
    entrada de teste). Sem argumento usa core.config.OFICINA_INVALID_NAMES_RAW;
    módulos com lixo próprio (ex.: Reposições) passam a lista completa.
    """
    invalid_keys = (
        _OFICINA_INVALID_KEYS
        if nomes_invalidos is None
        else build_normalized_key_set(nomes_invalidos)
    )
    mask_invalida = df[COL_OFICINA].apply(normalize_text_key).isin(invalid_keys)
    return df[~mask_invalida].copy()


def remover_sufixo_materia_prima(nome: str) -> str:
    """
    Tira do fim do nome o sufixo de linha de matéria-prima (BÁSICO,
    ELABORADO, PÓLO, TEAR) — "IDEAL CONFECCOES LTDA POLO" vira "IDEAL
    CONFECCOES LTDA". Sufixos de unidade (MATRIZ/FILIAL) são preservados.
    """
    return _RE_SUFIXO_MP.sub("", str(nome or "")).strip()


def build_canonical_maps(
    oficinas_oficiais: list[str],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    A partir do cadastro oficial, monta os dois índices de lookup usados na
    canonicalização: um por chave exata (normalize_text_key) e outro por
    chave tolerante a tipo societário/pontuação (normalize_company_key).

    Nomes oficiais distintos podem, em tese, colidir na chave tolerante
    (que é mais frouxa). Quando isso acontece a chave é descartada do
    segundo índice, para nunca fundir duas empresas diferentes por engano —
    esses casos caem no lookup exato ou nos aliases manuais.
    """
    canonicos: list[str] = []
    for nome in oficinas_oficiais:
        base = remover_sufixo_materia_prima(nome)
        if base and base not in canonicos:
            canonicos.append(base)

    por_chave_exata = {normalize_text_key(n): n for n in canonicos}

    agrupado: dict[str, set[str]] = {}
    for nome in canonicos:
        agrupado.setdefault(normalize_company_key(nome), set()).add(nome)
    por_chave_tolerante = {
        chave: next(iter(nomes)) for chave, nomes in agrupado.items() if len(nomes) == 1
    }

    return por_chave_exata, por_chave_tolerante


def _canonicalizar_por_frequencia(out: pd.DataFrame) -> dict[str, str]:
    """Elege, para cada chave normalizada, a grafia mais frequente como nome
    oficial — resolve casos como "GENESIS" vs "genesis" quando não há um
    cadastro oficial para consultar."""
    contagem = out.groupby(["_oficina_key", COL_OFICINA]).size().reset_index(name="qtd")
    contagem = contagem.sort_values(
        ["_oficina_key", "qtd", COL_OFICINA],
        ascending=[True, False, False],
        key=lambda s: s.str.len() if s.name == COL_OFICINA else s,
    )
    return contagem.groupby("_oficina_key")[COL_OFICINA].first().to_dict()


def canonicalize_oficinas(
    df: pd.DataFrame,
    oficinas_oficiais: list[str] | None = None,
) -> pd.DataFrame:
    """
    Padroniza grafias divergentes da mesma oficina para um único nome
    canônico. A ordem das etapas é da decisão mais explícita para a mais
    automática — a primeira que casar vence:

    1) Alias manual, chave exata (core.config.OFICINA_ALIASES_RAW):
       apelidos, abreviações e erros de digitação que nenhuma regra
       automática reconhece ("GENESIS" -> "CONFECCOES GENESIS LTDA ME").
    2) Cadastro oficial, chave exata: adota a grafia de `oficinas_oficiais`
       (resolve acento/maiúscula).
    3) Alias manual, chave tolerante a tipo societário/pontuação.
    4) Cadastro oficial, chave tolerante: cobre o grosso das divergências
       sem alias manual ("FACCAO ELLO LTDA" -> "FACCAO ELLO LTDA - ME").
    5) Frequência: para nomes fora do cadastro, mantém a grafia mais
       frequente daquela chave normalizada.

    Sem `oficinas_oficiais`, só as etapas de alias e de frequência se
    aplicam.
    """
    raw_aliases = OFICINA_ALIASES_RAW
    aliases = build_normalized_alias_map(raw_aliases)
    # A mesma tolerância a tipo societário vale para os aliases: assim
    # "IVANILDO JOSE DE SOUZA" cobre também "IVANILDO JOSE DE SOUZA - ME"
    # sem precisar de uma linha por variação. Chaves ambíguas (duas grafias
    # de origem que apontam para destinos diferentes) são descartadas.
    agrupado_aliases: dict[str, set[str]] = {}
    for grafia, canonico in raw_aliases.items():
        agrupado_aliases.setdefault(normalize_company_key(grafia), set()).add(canonico)
    aliases_tolerantes = {
        chave: next(iter(destinos))
        for chave, destinos in agrupado_aliases.items()
        if len(destinos) == 1
    }

    exatas, tolerantes = (
        build_canonical_maps(oficinas_oficiais) if oficinas_oficiais else ({}, {})
    )

    out = df.copy()
    # O sufixo de matéria-prima sai antes de qualquer comparação, para que
    # "POTENGI TEXTIL LTDA PÓLO" e "POTENGI TEXTIL LTDA" caiam na mesma chave.
    out[COL_OFICINA] = out[COL_OFICINA].apply(remover_sufixo_materia_prima)
    out["_oficina_key"] = out[COL_OFICINA].apply(normalize_text_key)
    out["_oficina_key_tolerante"] = out[COL_OFICINA].apply(normalize_company_key)

    por_frequencia = _canonicalizar_por_frequencia(out)

    def resolver(row: pd.Series) -> str:
        chave, chave_tol = row["_oficina_key"], row["_oficina_key_tolerante"]
        if chave in aliases:
            return remover_sufixo_materia_prima(aliases[chave])
        if chave in exatas:
            return exatas[chave]
        if chave_tol in aliases_tolerantes:
            return remover_sufixo_materia_prima(aliases_tolerantes[chave_tol])
        if chave_tol in tolerantes:
            return tolerantes[chave_tol]
        return por_frequencia.get(chave, row[COL_OFICINA])

    out[COL_OFICINA] = out.apply(resolver, axis=1)

    return out.drop(columns=["_oficina_key", "_oficina_key_tolerante"])


def enrich_with_parsed_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica parse_nome_tarefa em todo o DataFrame, adiciona as colunas
    derivadas (Número do Chamado, Oficina, Tipo de Solicitação), remove
    chamados com oficina inválida e padroniza grafias divergentes do
    nome da oficina.

    Assim como em Reposições, a canonicalização é ancorada no cadastro
    oficial (OFICINAS_OFICIAIS_RAW): o nome exibido é sempre o cadastrado,
    não a grafia mais frequente digitada na planilha — sem isso a mesma
    oficina aparecia com nomes diferentes em cada uma das duas páginas.
    """
    parsed = df[COL_NOME_TAREFA].apply(parse_nome_tarefa).apply(pd.Series)
    out = df.copy()
    out[[COL_NUM_CHAMADO, COL_OFICINA, COL_SOLICITACAO]] = parsed[
        [COL_NUM_CHAMADO, COL_OFICINA, COL_SOLICITACAO]
    ]
    out = remove_invalid_oficinas(out)
    out = canonicalize_oficinas(out, oficinas_oficiais=OFICINAS_OFICIAIS_RAW)
    return out
