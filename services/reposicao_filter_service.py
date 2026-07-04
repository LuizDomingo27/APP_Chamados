"""
services/reposicao_filter_service.py

Aplica os filtros do módulo de Reposições sobre o DataFrame já
enriquecido. Reaproveita filter_by_date_range e filter_by_oficinas de
services.filter_service — são genéricas, dependem só de COL_CRIADO_EM /
COL_OFICINA. O filtro por semana é próprio deste módulo (a página de
Chamados já tem seu próprio filtro por semana).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core.config import COL_CRIADO_EM
from services.filter_service import filter_by_date_range, filter_by_oficinas


def _semana_inicio(serie: pd.Series) -> pd.Series:
    """Data de início de cada semana (semana fechando no domingo)."""
    return serie.dt.to_period("W-SUN").dt.start_time.dt.normalize()


def _semana_label(inicio: pd.Timestamp) -> str:
    fim = inicio + pd.Timedelta(days=6)
    return f"{inicio.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}"


def semana_options(df: pd.DataFrame) -> list[str]:
    """Lista as semanas disponíveis (rótulo 'dd/mm a dd/mm/aaaa'), da mais
    recente para a mais antiga — usada para popular o filtro de semana."""
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return []
    inicios = sorted(_semana_inicio(serie).unique(), reverse=True)
    return [_semana_label(pd.Timestamp(inicio)) for inicio in inicios]


def filter_by_semanas(df: pd.DataFrame, semanas: list[str]) -> pd.DataFrame:
    """Filtra pelas semanas selecionadas (rótulo 'dd/mm a dd/mm/aaaa').
    Lista vazia = nenhum resultado."""
    if not semanas:
        return df.iloc[0:0]
    rotulos = _semana_inicio(df[COL_CRIADO_EM]).map(
        lambda d: _semana_label(d) if pd.notna(d) else None
    )
    return df[rotulos.isin(semanas)]


def apply_all_filters_reposicao(
    df: pd.DataFrame,
    start: date | None,
    end: date | None,
    semanas: list[str],
    oficinas: list[str],
) -> pd.DataFrame:
    """Aplica todos os filtros de Reposições em sequência."""
    out = filter_by_date_range(df, start, end)
    out = filter_by_semanas(out, semanas)
    out = filter_by_oficinas(out, oficinas)
    return out
