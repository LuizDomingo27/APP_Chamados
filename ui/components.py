"""
ui/components.py

Componentes visuais reutilizáveis (cards, cabeçalho, tabela estilizada).
Recebem dados já prontos da camada de service — não calculam nada aqui,
só renderizam.
"""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from core.config import PALETTE, STATUS_COLORS, PRIORIDADE_COLORS
from core.utils import format_date_br, format_int


def render_header(title: str, subtitle: str, icon: str = "🎫") -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header__icon">{icon}</div>
            <div>
                <p class="app-header__title">{title}</p>
                <p class="app-header__subtitle">{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">
            <span class="section-title__bar"></span>{title}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str,
    value: int | str,
    subtitle: str = "",
    accent: str | None = None,
) -> None:
    accent = accent or PALETTE["neon"]
    value_fmt = format_int(value) if isinstance(value, (int, float)) else value
    subtitle_html = f'<p class="kpi-card__subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="kpi-card" style="--accent:{accent}">
            <p class="kpi-card__label"><span class="kpi-card__label-icon">✦</span>{label}</p>
            <p class="kpi-card__value">{value_fmt}</p>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_kpis(status_counts: dict[str, int]) -> None:
    subtitles = {"Concluída": "chamados finalizados", "Não iniciado": "aguardando início", "Em andamento": "em execução"}
    cols = st.columns(len(status_counts))
    for col, (status, qtd) in zip(cols, status_counts.items()):
        with col:
            render_kpi_card(
                label=status,
                value=qtd,
                subtitle=subtitles.get(status, ""),
                accent=STATUS_COLORS.get(status),
            )


def render_priority_kpis(priority_counts: dict[str, int]) -> None:
    subtitles = {"Urgente": "alta severidade", "Importante": "atenção necessária", "Média": "fluxo normal"}
    cols = st.columns(len(priority_counts))
    for col, (prioridade, qtd) in zip(cols, priority_counts.items()):
        with col:
            render_kpi_card(
                label=f"Prioridade {prioridade}",
                value=qtd,
                subtitle=subtitles.get(prioridade, ""),
                accent=PRIORIDADE_COLORS.get(prioridade),
            )


def render_destaque_card(tag: str, value: str, subvalue: str) -> None:
    st.markdown(
        f"""
        <div class="destaque-card">
            <span class="destaque-card__tag">{tag}</span>
            <p class="destaque-card__value">{value}</p>
            <p class="destaque-card__subvalue">{subvalue}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_styled_dataframe(df: pd.DataFrame, date_columns: list[str] | None = None, height: int = 420) -> None:
    """
    Renderiza a tabela como HTML próprio (cabeçalho em gradiente verde-ciano,
    linhas com zebra suavizada, cabeçalho centralizado e valores alinhados
    por tipo de coluna). Optamos por HTML/CSS em vez de st.dataframe porque
    o widget nativo é renderizado em canvas (glide-data-grid) e não aceita
    estilização de linha/cabeçalho via CSS.

    A largura de cada coluna segue o conteúdo (table-layout: auto do
    navegador) — sem larguras fixas artificiais estourando ou espremendo
    colunas.
    """
    date_columns = date_columns or []
    display_df = df.copy()

    for col in date_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_date_br)

    # Colunas curtas/categóricas ficam centralizadas; texto fica à esquerda;
    # números ficam à direita.
    centered_cols = {"Status", "Prioridade"}

    def _align_for(col: str) -> str:
        if col in centered_cols:
            return "ppc-align-center"
        if pd.api.types.is_numeric_dtype(df[col]):
            return "ppc-align-right"
        return "ppc-align-left"

    alignments = {col: _align_for(col) for col in display_df.columns}

    header_html = "".join(f"<th>{escape(str(col))}</th>" for col in display_df.columns)

    rows_html = []
    for _, row in display_df.iterrows():
        cells = []
        for col in display_df.columns:
            raw = row[col]
            text = escape(str(raw)) if pd.notna(raw) else "—"
            cells.append(
                f'<td class="{alignments[col]}" title="{text}">{text}</td>'
            )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f"""
    <div class="styled-table-wrapper">
        <div class="ppc-table-scroll" style="max-height:{height}px;">
            <table class="ppc-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
