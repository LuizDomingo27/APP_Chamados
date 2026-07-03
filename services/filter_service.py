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


def _week_label(year: int, week: int) -> str:
    """Rótulo amigável de uma semana ISO, ex.: 'Semana 27/2026 (29/06 a 05/07)'."""
    monday = pd.Timestamp.fromisocalendar(int(year), int(week), 1)
    sunday = monday + pd.Timedelta(days=6)
    return f"Semana {int(week):02d}/{int(year)} ({monday.strftime('%d/%m')} a {sunday.strftime('%d/%m')})"


def _week_label_column(df: pd.DataFrame) -> pd.Series:
    """Rótulo de semana ISO por linha, a partir de COL_CRIADO_EM (NaT vira None)."""
    iso = df[COL_CRIADO_EM].dt.isocalendar()
    return pd.Series(
        [
            _week_label(year, week) if pd.notna(year) else None
            for year, week in zip(iso["year"], iso["week"])
        ],
        index=df.index,
    )


def get_available_weeks(df: pd.DataFrame) -> list[str]:
    """Extrai as semanas (ISO) presentes em COL_CRIADO_EM, ordenadas cronologicamente."""
    datas = df[COL_CRIADO_EM].dropna()
    if datas.empty:
        return []
    iso = datas.dt.isocalendar()
    combos = sorted(set(zip(iso["year"].tolist(), iso["week"].tolist())))
    return [_week_label(year, week) for year, week in combos]


def filter_by_semanas(df: pd.DataFrame, semanas: list[str]) -> pd.DataFrame:
    """Filtra pelas semanas (rótulo ISO) selecionadas. Lista vazia = nenhum resultado."""
    if not semanas:
        return df.iloc[0:0]
    return df[_week_label_column(df).isin(semanas)]


def apply_all_filters(
    df: pd.DataFrame,
    start: date | None,
    end: date | None,
    numero_chamado: str,
    oficinas: list[str],
    semanas: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica todos os filtros em sequência."""
    out = filter_by_date_range(df, start, end)
    out = filter_by_numero_chamado(out, numero_chamado)
    out = filter_by_oficinas(out, oficinas)
    if semanas is not None:
        out = filter_by_semanas(out, semanas)
    return out
