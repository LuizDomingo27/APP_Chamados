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

from core.config import COL_OFICINA, PALETTE, STATUS_COLORS
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


def render_chart_caption(text: str) -> None:
    """Legenda centralizada acima de um gráfico. Existe para a rosca:
    st.caption alinha à esquerda, o que destoa de um gráfico radial."""
    st.markdown(f'<p class="chart-caption">{text}</p>', unsafe_allow_html=True)


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


def render_dropdown_all(label: str, options: list[str], state_key: str) -> list[str]:
    """Filtro dropdown (st.selectbox) com opção "Todas" no topo da lista,
    equivalente a nenhum filtro aplicado.

    Renderiza no container ATUAL (e não em st.sidebar): as páginas o
    posicionam dentro das colunas da barra de filtros do topo, já que a
    navegação passou a ser uma navbar e não existe mais barra lateral.

    Seleção única — retorna lista vazia quando "Todas" está selecionada, e
    uma lista de 1 item com o valor escolhido caso contrário. Mantém o
    mesmo contrato de retorno do filtro multiselect anterior (lista vazia =
    sem filtro, ver services/filter_service.py), então os services de
    filtro não precisam mudar.
    """
    widget_key = f"{state_key}_dropdown"
    todas = "Todas"
    escolhas = [todas, *options]

    # Reseta para "Todas" se a seleção atual não existe mais entre as
    # opções (ex.: novo arquivo carregado) — evita erro de validação do
    # selectbox contra a nova lista.
    if widget_key not in st.session_state or st.session_state[widget_key] not in escolhas:
        st.session_state[widget_key] = todas

    st.selectbox(label=label, options=escolhas, key=widget_key)

    selecionado = st.session_state[widget_key]
    return [] if selecionado == todas else [selecionado]



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


def render_analytics_group(titulo: str, cards: list[dict], accent: str | None = None) -> None:
    """
    Renderiza um bloco da área analítica: rótulo do grupo + grade de cards.

    O grupo inteiro sai num único bloco de HTML (grid CSS) em vez de um
    st.columns por card — assim a altura dos cards se iguala sozinha e o
    espaçamento fica idêntico em todos os grupos, sem depender das calhas
    do Streamlit.

    Cada item de `cards` aceita:
      label — rótulo curto do card (ex.: "Mês")
      value — número ou texto JÁ formatado para exibição
      meta  — linha de apoio abaixo do valor (opcional)
      texto — True quando o valor é um nome, e não um número: reduz a
              fonte e libera a quebra de linha
    """
    accent = accent or PALETTE["neon"]

    cards_html = []
    for card in cards:
        meta = card.get("meta", "")
        meta_html = f'<p class="an-card__meta">{escape(str(meta))}</p>' if meta else ""
        modifier = " an-card--texto" if card.get("texto") else ""
        cards_html.append(
            f'<div class="an-card{modifier}">'
            f'<p class="an-card__label">{escape(str(card["label"]))}</p>'
            f'<p class="an-card__value">{escape(str(card["value"]))}</p>'
            f"{meta_html}"
            "</div>"
        )

    # O HTML sai numa linha só, sem indentação: o st.markdown passa a
    # string pelo parser de Markdown ANTES de injetar o HTML, e linhas
    # indentadas com 4+ espaços viram bloco de código — o que fazia só o
    # primeiro card de cada grupo aparecer.
    html = (
        f'<div class="an-group" style="--accent:{accent}">'
        f'<p class="an-group__title"><span class="an-group__bar"></span>{escape(titulo)}</p>'
        f'<div class="an-grid">{"".join(cards_html)}</div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_styled_dataframe(
    df: pd.DataFrame,
    date_columns: list[str] | None = None,
    height: int = 420,
    fit_content: bool = False,
) -> None:
    """
    Renderiza a tabela como HTML próprio (cabeçalho em gradiente verde-ciano,
    linhas com zebra suavizada, cabeçalho centralizado e valores alinhados
    por tipo de coluna). Optamos por HTML/CSS em vez de st.dataframe porque
    o widget nativo é renderizado em canvas (glide-data-grid) e não aceita
    estilização de linha/cabeçalho via CSS.

    A largura de cada coluna segue o conteúdo (table-layout: auto do
    navegador) — sem larguras fixas artificiais estourando ou espremendo
    colunas.

    `fit_content=True` faz a tabela ocupar só a largura do conteúdo e ficar
    centralizada — usado nas tabelas de poucas colunas, que esticadas até a
    borda ficariam com um vazio enorme no meio.
    """
    date_columns = date_columns or []
    display_df = df.copy()

    for col in date_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_date_br)

    # Todas as colunas ficam centralizadas — só "Oficina" (nome da empresa,
    # texto mais longo e o principal ponto de leitura da tabela) fica à
    # esquerda.
    def _align_for(col: str) -> str:
        if col == COL_OFICINA:
            return "ppc-align-left"
        return "ppc-align-center"

    alignments = {col: _align_for(col) for col in display_df.columns}

    # Colunas numéricas com mais de um valor distinto ganham um destaque em
    # "pílula" nas linhas acima da mediana da própria coluna — mesmo efeito
    # visual do exemplo de referência (valores que se destacam ficam com um
    # selo verde), só que calculado por coluna em vez de um limiar fixo, já
    # que cada tabela do app tem colunas numéricas com unidades diferentes
    # (dias, contagens, %).
    badge_cols = {
        col
        for col in display_df.columns
        if col not in date_columns
        and pd.api.types.is_numeric_dtype(df[col])
        and df[col].nunique(dropna=True) > 1
    }
    medians = {col: df[col].median() for col in badge_cols}

    header_html = "".join(
        f'<th><span class="ppc-th-icon">◆</span>{escape(str(col))}</th>'
        for col in display_df.columns
    )

    rows_html = []
    for _, row in display_df.iterrows():
        cells = []
        for col in display_df.columns:
            raw = row[col]
            text = escape(str(raw)) if pd.notna(raw) else "—"
            cell_content = text
            if col in badge_cols and pd.notna(raw) and raw > medians[col]:
                cell_content = f'<span class="ppc-pill">{text}</span>'
            cells.append(
                f'<td class="{alignments[col]}" title="{text}">{cell_content}</td>'
            )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    wrapper_class = "styled-table-wrapper"
    if fit_content:
        wrapper_class += " styled-table-wrapper--fit"

    table_html = f"""
    <div class="{wrapper_class}">
        <div class="ppc-table-scroll" style="max-height:{height}px;">
            <table class="ppc-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
