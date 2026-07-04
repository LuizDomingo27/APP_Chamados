"""
services/reposicao_filter_service.py

Aplica os filtros do módulo de Reposições sobre o DataFrame já
enriquecido. Reaproveita filter_by_date_range e filter_by_oficinas de
services.filter_service — são genéricas, dependem só de COL_CRIADO_EM /
COL_OFICINA. Só o filtro por número é próprio deste módulo, porque a
coluna derivada de número tem outro nome (COL_NUM_REPOSICAO).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core.config import COL_NUM_REPOSICAO
from services.filter_service import filter_by_date_range, filter_by_oficinas


def filter_by_numero_reposicao(df: pd.DataFrame, termo: str) -> pd.DataFrame:
    """Filtra por número da reposição (busca parcial, case-insensitive)."""
    if not termo:
        return df
    termo = termo.strip()
    if not termo:
        return df
    return df[df[COL_NUM_REPOSICAO].astype(str).str.contains(termo, case=False, na=False)]


def apply_all_filters_reposicao(
    df: pd.DataFrame,
    start: date | None,
    end: date | None,
    numero_reposicao: str,
    oficinas: list[str],
) -> pd.DataFrame:
    """Aplica todos os filtros de Reposições em sequência."""
    out = filter_by_date_range(df, start, end)
    out = filter_by_numero_reposicao(out, numero_reposicao)
    out = filter_by_oficinas(out, oficinas)
    return out
