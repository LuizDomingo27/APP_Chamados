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
    """Filtra pelas oficinas selecionadas. Lista vazia = sem filtro (traz tudo)."""
    if not oficinas:
        return df
    return df[df[COL_OFICINA].isin(oficinas)]


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
    Lista vazia = sem filtro (traz tudo)."""
    if not semanas:
        return df
    rotulos = _semana_inicio(df[COL_CRIADO_EM]).map(
        lambda d: _semana_label(d) if pd.notna(d) else None
    )
    return df[rotulos.isin(semanas)]


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
