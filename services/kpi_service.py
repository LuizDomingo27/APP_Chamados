"""
services/kpi_service.py

Toda a lógica de cálculo de indicadores (KPIs) mora aqui. Cada função
resolve UMA necessidade específica do dashboard e devolve estruturas
simples (dict, DataFrame, namedtuple-like) prontas para a camada de UI
consumir — a UI não faz nenhuma conta, só renderiza o que esta camada
devolve.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.config import (
    COL_CATEGORIA,
    COL_CRIADO_EM,
    COL_NUM_CHAMADO,
    COL_OFICINA,
    COL_PRIORIDADE,
    COL_SOLICITACAO,
    COL_STATUS,
    PRIORIDADE_ORDER,
    PRIORIDADE_RANK,
    STATUS_EM_ANDAMENTO,
    STATUS_NAO_INICIADO,
    STATUS_ORDER,
    TOP_N_OFICINAS,
)


# ---------------------------------------------------------------------------
# Estruturas de retorno
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Destaques:
    dia_top_data: str
    dia_top_qtd: int
    oficina_top_nome: str
    oficina_top_qtd: int
    solicitacao_top_nome: str
    solicitacao_top_qtd: int


# ---------------------------------------------------------------------------
# Totais gerais
# ---------------------------------------------------------------------------
def total_chamados(df: pd.DataFrame) -> int:
    return int(len(df))


def contagem_por_status(df: pd.DataFrame) -> dict[str, int]:
    """Devolve contagem por status, sempre incluindo as 3 chaves padrão."""
    counts = df[COL_STATUS].value_counts().to_dict()
    return {status: int(counts.get(status, 0)) for status in STATUS_ORDER}


def contagem_por_prioridade(df: pd.DataFrame) -> dict[str, int]:
    """Devolve contagem por prioridade, sempre incluindo as 3 chaves padrão."""
    counts = df[COL_PRIORIDADE].value_counts().to_dict()
    return {p: int(counts.get(p, 0)) for p in PRIORIDADE_ORDER}


# ---------------------------------------------------------------------------
# Agregações (oficina / categoria)
# ---------------------------------------------------------------------------
def agregado_por_oficina(df: pd.DataFrame) -> pd.DataFrame:
    """Total de chamados por oficina, ordenado decrescente."""
    out = (
        df.groupby(COL_OFICINA, dropna=False)
        .size()
        .reset_index(name="Total de Chamados")
        .sort_values("Total de Chamados", ascending=False)
        .reset_index(drop=True)
    )
    return out


def agregado_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Total de chamados por categoria (setor), ordenado decrescente."""
    out = (
        df.groupby(COL_CATEGORIA, dropna=False)
        .size()
        .reset_index(name="Total de Chamados")
        .sort_values("Total de Chamados", ascending=False)
        .reset_index(drop=True)
    )
    return out


def ranking_oficinas(df: pd.DataFrame, top_n: int = TOP_N_OFICINAS) -> pd.DataFrame:
    """Top N oficinas com mais chamados — usado no gráfico de ranking."""
    return agregado_por_oficina(df).head(top_n)


# ---------------------------------------------------------------------------
# Tabela ordenada por prioridade (fila de triagem)
# ---------------------------------------------------------------------------
def tabela_ordenada_por_prioridade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devolve o DataFrame ordenado pela severidade da prioridade
    (Urgente -> Importante -> Média) e, dentro de cada prioridade, pelos
    chamados mais antigos primeiro — simula uma fila de atendimento.
    """
    out = df.copy()
    out["_rank_prioridade"] = out[COL_PRIORIDADE].map(PRIORIDADE_RANK).fillna(99)
    out = out.sort_values(["_rank_prioridade", COL_CRIADO_EM], ascending=[True, True])
    return out.drop(columns="_rank_prioridade")


# ---------------------------------------------------------------------------
# Tendência (série temporal)
# ---------------------------------------------------------------------------
def tendencia_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """
    Série diária de chamados criados, com todos os dias do período
    preenchidos (mesmo com 0 chamados) para o gráfico de linha não ter
    "buracos", e uma coluna com a média do período repetida em todas as
    linhas (linha de referência no gráfico).
    """
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return pd.DataFrame(columns=["Data", "Chamados", "Média do Período"])

    diario = serie.dt.floor("D").value_counts().sort_index()
    full_range = pd.date_range(diario.index.min(), diario.index.max(), freq="D")
    diario = diario.reindex(full_range, fill_value=0)

    media = diario.mean()

    out = diario.reset_index()
    out.columns = ["Data", "Chamados"]
    out["Média do Período"] = round(media, 2)
    return out


# ---------------------------------------------------------------------------
# Cards de destaque
# ---------------------------------------------------------------------------
def calcular_destaques(df: pd.DataFrame) -> Destaques:
    """Calcula os 3 destaques: dia com mais pedidos, oficina e tipo de
    solicitação mais frequentes."""
    if df.empty:
        return Destaques("—", 0, "—", 0, "—", 0)

    # Dia com mais pedidos
    por_dia = df[COL_CRIADO_EM].dropna().dt.floor("D").value_counts()
    if not por_dia.empty:
        dia_top = por_dia.idxmax()
        dia_top_data = dia_top.strftime("%d/%m/%Y")
        dia_top_qtd = int(por_dia.max())
    else:
        dia_top_data, dia_top_qtd = "—", 0

    # Oficina com mais pedidos
    por_oficina = df[COL_OFICINA].value_counts()
    if not por_oficina.empty:
        oficina_top_nome = str(por_oficina.idxmax())
        oficina_top_qtd = int(por_oficina.max())
    else:
        oficina_top_nome, oficina_top_qtd = "—", 0

    # Tipo de solicitação mais comum
    por_solicitacao = df[COL_SOLICITACAO].value_counts()
    if not por_solicitacao.empty:
        solicitacao_top_nome = str(por_solicitacao.idxmax())
        solicitacao_top_qtd = int(por_solicitacao.max())
    else:
        solicitacao_top_nome, solicitacao_top_qtd = "—", 0

    return Destaques(
        dia_top_data=dia_top_data,
        dia_top_qtd=dia_top_qtd,
        oficina_top_nome=oficina_top_nome,
        oficina_top_qtd=oficina_top_qtd,
        solicitacao_top_nome=solicitacao_top_nome,
        solicitacao_top_qtd=solicitacao_top_qtd,
    )


# ---------------------------------------------------------------------------
# Atalho: pendentes (não iniciado + em andamento) — útil para alertas
# ---------------------------------------------------------------------------
def total_pendentes(df: pd.DataFrame) -> int:
    return int(df[COL_STATUS].isin([STATUS_NAO_INICIADO, STATUS_EM_ANDAMENTO]).sum())
