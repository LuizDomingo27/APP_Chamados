"""
services/filter_service.py

Aplica os filtros escolhidos pelo usuário (período, número do chamado,
oficina) sobre o DataFrame já enriquecido. Função pura — recebe DataFrame
+ critérios, devolve DataFrame filtrado. Não conhece Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    return df[df[COL_NUM_CHAMADO].astype(str).str.contains(termo, case=False, na=False, regex=False)]


def filter_by_oficinas(df: pd.DataFrame, oficinas: list[str]) -> pd.DataFrame:
    """Filtra pelas oficinas selecionadas. Lista vazia = sem filtro (traz tudo)."""
    if not oficinas:
        return df
    return df[df[COL_OFICINA].isin(oficinas)]


def _semana_inicio(serie: pd.Series) -> pd.Series:
    """Data de início de cada semana (semana fechando no domingo)."""
    return serie.dt.to_period("W-SUN").dt.start_time.dt.normalize()


def _semana_label(inicio: pd.Timestamp) -> str:
    # Rótulo pelo número da semana ISO (com o ano, para semanas de anos
    # diferentes não colidirem, ex.: semana 25 de 2024 vs. de 2025). O ano
    # ISO é usado em vez do calendário para evitar divergência na virada do
    # ano (a semana ISO pode pertencer ao ano seguinte/anterior).
    iso_year, iso_week, _ = inicio.isocalendar()
    return f"Semana {iso_week:02d}/{iso_year}"


def semana_options(df: pd.DataFrame) -> list[str]:
    """Lista as semanas disponíveis (rótulo 'Semana NN/aaaa'), da mais
    recente para a mais antiga — usada para popular o filtro de semana."""
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return []
    inicios = sorted(_semana_inicio(serie).unique(), reverse=True)
    return [_semana_label(pd.Timestamp(inicio)) for inicio in inicios]


def filter_by_semanas(df: pd.DataFrame, semanas: list[str]) -> pd.DataFrame:
    """Filtra pelas semanas selecionadas (rótulo 'Semana NN/aaaa').
    Lista vazia = sem filtro (traz tudo)."""
    if not semanas:
        return df
    rotulos = _semana_inicio(df[COL_CRIADO_EM]).map(
        lambda d: _semana_label(d) if pd.notna(d) else None
    )
    return df[rotulos.isin(semanas)]


_MESES_PT_BR = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)


def _mes_label(periodo: pd.Period) -> str:
    """Rótulo legível e estável para um mês de calendário."""
    return f"{_MESES_PT_BR[periodo.month - 1]}/{periodo.year}"


def mes_options(df: pd.DataFrame) -> list[str]:
    """Lista os meses disponíveis, do mais recente para o mais antigo."""
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return []
    meses = sorted(serie.dt.to_period("M").unique(), reverse=True)
    return [_mes_label(mes) for mes in meses]


def filter_by_meses(df: pd.DataFrame, meses: list[str]) -> pd.DataFrame:
    """Filtra pelos meses selecionados. Lista vazia = sem filtro."""
    if not meses:
        return df
    rotulos = df[COL_CRIADO_EM].dt.to_period("M").map(
        lambda mes: _mes_label(mes) if pd.notna(mes) else None
    )
    return df[rotulos.isin(meses)]


def ha_filtro_de_periodo(
    df: pd.DataFrame,
    start: date,
    end: date,
    semanas: list[str] | None = None,
    meses: list[str] | None = None,
) -> bool:
    """True quando o usuário escolheu um período: datas diferentes do intervalo
    completo da planilha, ou algum mês/semana."""
    intervalo_completo = (df[COL_CRIADO_EM].min().date(), df[COL_CRIADO_EM].max().date())
    return (start, end) != intervalo_completo or bool(semanas) or bool(meses)


@dataclass(frozen=True)
class RecorteTendencia:
    """O que os gráficos de tendência por dia/semana devem exibir.

    `legenda` explica o recorte para o usuário (vazia quando quem manda é o
    filtro de período) e `aviso_vazio` é a mensagem para um recorte sem dados.
    """

    df: pd.DataFrame
    legenda: str
    aviso_vazio: str


def recorte_tendencia(
    df: pd.DataFrame, periodo_filtrado: bool, hoje: pd.Timestamp
) -> RecorteTendencia:
    """Sem período escolhido, a tendência mostra só o mês vigente; com período
    (datas, mês ou semana), mostra exatamente o que o filtro já recortou.

    O mês vigente é o do calendário, sem cair para o último mês da planilha:
    mostrar outro mês sob esse nome faria um arquivo antigo parecer atual."""
    if periodo_filtrado:
        return RecorteTendencia(df, "", "Nenhum registro datado no filtro atual.")

    mes = pd.Timestamp(hoje).to_period("M")
    rotulo = _mes_label(mes)
    ultimo = df[COL_CRIADO_EM].max()
    ultimo_txt = (
        f" Último registro no filtro atual: {ultimo:%d/%m/%Y}."
        if pd.notna(ultimo)
        else ""
    )
    return RecorteTendencia(
        df[df[COL_CRIADO_EM].dt.to_period("M") == mes],
        f"Por Dia e Por Semana: mês vigente ({rotulo}). "
        "Para ver outros meses, use o filtro de data.",
        f"Nenhum registro em {rotulo}.{ultimo_txt} "
        "Para ver outros meses, use o filtro de data.",
    )


def apply_all_filters(
    df: pd.DataFrame,
    start: date | None,
    end: date | None,
    numero_chamado: str,
    oficinas: list[str],
    semanas: list[str] | None = None,
    meses: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica todos os filtros em sequência."""
    out = filter_by_date_range(df, start, end)
    out = filter_by_numero_chamado(out, numero_chamado)
    out = filter_by_oficinas(out, oficinas)
    if semanas is not None:
        out = filter_by_semanas(out, semanas)
    if meses is not None:
        out = filter_by_meses(out, meses)
    return out
