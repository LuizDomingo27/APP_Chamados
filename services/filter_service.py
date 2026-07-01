"""
services/filter_service.py

Aplica os filtros escolhidos pelo usuário (período, número do chamado,
oficina) sobre o DataFrame já enriquecido. Função pura — recebe DataFrame
+ critérios, devolve DataFrame filtrado. Não conhece Streamlit.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core.config import COL_CRIADO_EM, COL_NUM_CHAMADO, COL_OFICINA


def filter_by_date_range(
    df: pd.DataFrame, start: date | None, end: date | None
) -> pd.DataFrame:
    """Filtra pela coluna 'Criado em' dentro do intervalo [start, end]."""
    if start is None and end is None:
        return df

    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= df[COL_CRIADO_EM] >= pd.Timestamp(start)
    if end is not None:
        # inclui o dia final inteiro
        mask &= df[COL_CRIADO_EM] < (pd.Timestamp(end) + pd.Timedelta(days=1))

    return df[mask]


def filter_by_numero_chamado(df: pd.DataFrame, termo: str) -> pd.DataFrame:
    """Filtra por número do chamado (busca parcial, case-insensitive)."""
    if not termo:
        return df
    termo = termo.strip()
    if not termo:
        return df
    return df[df[COL_NUM_CHAMADO].astype(str).str.contains(termo, case=False, na=False)]


def filter_by_oficinas(df: pd.DataFrame, oficinas: list[str]) -> pd.DataFrame:
    """Filtra pelas oficinas selecionadas. Lista vazia = nenhum resultado."""
    if not oficinas:
        return df.iloc[0:0]
    return df[df[COL_OFICINA].isin(oficinas)]


def apply_all_filters(
    df: pd.DataFrame,
    start: date | None,
    end: date | None,
    numero_chamado: str,
    oficinas: list[str],
) -> pd.DataFrame:
    """Aplica todos os filtros em sequência."""
    out = filter_by_date_range(df, start, end)
    out = filter_by_numero_chamado(out, numero_chamado)
    out = filter_by_oficinas(out, oficinas)
    return out
