"""
services/reposicao_filter_service.py

Aplica os filtros do módulo de Reposições sobre o DataFrame já
enriquecido. Reaproveita filter_by_date_range, filter_by_oficinas,
semana_options e filter_by_semanas de services.filter_service — são
genéricas, dependem só de COL_CRIADO_EM / COL_OFICINA, e são as mesmas
usadas pela página de Chamados.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from services.filter_service import (
    filter_by_date_range,
    filter_by_oficinas,
    filter_by_semanas,
    semana_options,
)

__all__ = ["apply_all_filters_reposicao", "semana_options"]


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
