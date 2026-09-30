"""
ui/components.py

Componentes visuais reutilizáveis (painéis, cards, cabeçalho, tabela
estilizada). Recebem dados já prontos da camada de service — não calculam
nada aqui, só renderizam.

Convenções desta camada:

  • TODO texto vindo de dado (nome de oficina, tipo de solicitação, rótulo)
    passa por html.escape antes de entrar no markup. Os componentes montam
    HTML com unsafe_allow_html=True, então um "&" ou "<" no nome de uma
    oficina quebraria a marcação — e nome de oficina vem de planilha
    preenchida à mão.
  • Entradas são validadas/coeridas no lugar de assumir tipo: a planilha é
    dado externo, e um None inesperado não pode derrubar a página inteira.
    Onde há degradação, ela é VISÍVEL ("—", 0, cor primária) — nada de
    except silencioso.
"""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from typing import Iterator

import pandas as pd
import streamlit as st

from core.config import COL_OFICINA, PALETTE, SERIES_COLORS, STATUS_COLORS
from core.utils import format_date_br, format_int, hex_to_rgb, rgba
from ui.icons import icon as svg_icon
from ui.styles import get_custom_css

# Acento padrão usado quando o chamador não informa cor (ou informa uma
# inválida) — a cor primária do tema.
_DEFAULT_ACCENT = PALETTE["neon"]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
def _accent_style(accent: str | None) -> str:
    """
    Monta o atributo style com as custom properties do acento consumidas
    por ui/styles.py (--accent e suas variações translúcidas).

    As variações saem daqui, em rgba() calculado, em vez de color-mix() no
    CSS: color-mix não tem suporte uniforme, e uma declaração descartada
    pelo navegador apagaria o preenchimento/anel do medalhão em vez de só
    mudar de tom.
    """
    bruto = accent if isinstance(accent, str) and accent.strip() else _DEFAULT_ACCENT
    # Re-emitir a cor a partir do RGB já validado garante que --accent seja
    # SEMPRE um hex legítimo: interpolar a string crua deixaria passar algo
    # como "vermelho", e um custom property inválido invalida a declaração
    # que o consome (sem cair no fallback do var()).
    r, g, b = hex_to_rgb(bruto)
    cor = f"#{r:02X}{g:02X}{b:02X}"
    return (
        f"--accent:{cor};"
        f"--accent-soft:{rgba(cor, 0.10)};"
        f"--accent-ring:{rgba(cor, 0.26)};"
        f"--accent-glow:{rgba(cor, 0.10)};"
        f"--accent-halo:{rgba(cor, 0.08)};"
    )


def _texto(value: object, vazio: str = "—") -> str:
    """Texto pronto para markup: nulos viram travessão e o resto é escapado."""
    if value is None:
        return vazio
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return vazio
    except (TypeError, ValueError):
        # pd.isna não aceita listas/objetos arbitrários — segue como texto.
        pass
    texto = str(value).strip()
    return escape(texto) if texto else vazio


def _percentual(value: object) -> float | None:
    """
    Converte a proporção da barra para 0-100, ou None quando não há barra.

    Fora da faixa o valor é limitado (e não descartado): uma barra em 100%
    comunica "no teto" melhor do que barra nenhuma.
    """
    if value is None:
        return None
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return None
    if pct != pct:  # NaN
        return None
    return max(0.0, min(100.0, pct))


# ---------------------------------------------------------------------------
# Estrutura de página
# ---------------------------------------------------------------------------
def render_header(title: str, subtitle: str, icon: str = "clipboard") -> None:
    """Cabeçalho e estilos, inclusive quando a página é aberta diretamente."""
    st.markdown(
        get_custom_css() + f"""
        <div class="app-header">
            <div class="app-header__icon">{svg_icon(icon)}</div>
            <div>
                <p class="app-header__title">{_texto(title, vazio="")}</p>
                <p class="app-header__subtitle">{_texto(subtitle, vazio="")}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_title_html(title: str, extra_class: str = "") -> str:
    classes = f"section-title {extra_class}".strip()
    return (
        f'<div class="{classes}">'
        f'<span class="section-title__bar"></span>{_texto(title, vazio="")}'
        "</div>"
    )


def render_section_title(title: str) -> None:
    """Rótulo de seção solto na página (fora de painel)."""
    st.markdown(_section_title_html(title), unsafe_allow_html=True)


@contextmanager
def panel(title: str, key: str) -> Iterator[None]:
    """
    Abre um painel de seção: caixa com hairline e o rótulo em teal no topo,
    conforme a referência (cada bloco do dashboard é uma caixa).

    O `key` é OBRIGATÓRIO e explícito porque é ele que gera a classe
    "st-key-ppcpanel-<key>" usada pelo CSS (ver ui/styles.py). Derivar a key
    do título automaticamente traria colisão silenciosa entre dois painéis
    homônimos — melhor o chamador nomear.

    Uso:
        with panel("Visão Geral", key="visao-geral"):
            ...conteúdo...
    """
    slug = str(key or "").strip() or "sem-nome"
    with st.container(key=f"ppcpanel-{slug}"):
        # Variante sem margem no topo: dentro do painel o rótulo já é o
        # primeiro elemento e o padding da caixa faz o espaçamento.
        st.markdown(
            _section_title_html(title, "section-title--panel"),
            unsafe_allow_html=True,
        )
        yield


def render_chart_caption(text: str) -> None:
    """Legenda centralizada acima de um gráfico. Existe para a rosca:
    st.caption alinha à esquerda, o que destoa de um gráfico radial."""
    st.markdown(
        f'<p class="chart-caption">{_texto(text, vazio="")}</p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
def render_kpi_card(
    label: str,
    value: int | str,
    subtitle: str = "",
    accent: str | None = None,
    icon: str = "dot",
    chip: str = "",
    progress: float | None = None,
) -> None:
    """
    Card de indicador no formato da referência: medalhão circular do ícone,
    rótulo em caixa alta, valor pesado e, opcionalmente, um chip com a
    proporção ("25% do total") e/ou uma barra da mesma proporção.

    `icon` é o NOME de um ícone de ui/icons.py (não um emoji: ver o
    cabeçalho daquele módulo). `progress` é a porcentagem (0-100) da barra;
    None esconde a barra.
    """
    value_fmt = format_int(value) if isinstance(value, (int, float)) else _texto(value)
    subtitle_html = (
        f'<p class="kpi-card__subtitle">{_texto(subtitle)}</p>' if subtitle else ""
    )
    chip_html = f'<span class="kpi-card__chip">{_texto(chip)}</span>' if chip else ""

    pct = _percentual(progress)
    progress_html = (
        f'<div class="kpi-card__track"><div class="kpi-card__fill" '
        f'style="width:{pct:.1f}%"></div></div>'
        if pct is not None
        else ""
    )
    card_modifier = " kpi-card--compact" if not chip_html and not progress_html else ""

    st.markdown(
        f"""
        <div class="kpi-card{card_modifier}" style="{_accent_style(accent)}">
            <div class="kpi-card__head">
                <div class="kpi-card__medallion">{svg_icon(icon)}</div>
                <p class="kpi-card__label">{_texto(label, vazio="")}</p>
            </div>
            <div class="kpi-card__content">
                <p class="kpi-card__value">{value_fmt}</p>
                {subtitle_html}
            </div>
            {progress_html}
            {chip_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Ícone por status — o medalhão da referência troca de glifo junto com a
# cor, então status e ícone andam juntos, definidos num só lugar.
_STATUS_ICONS = {
    "Concluída": "check",
    "Não iniciado": "hourglass",
    "Em andamento": "refresh",
}


def render_status_kpis(status_counts: dict[str, int]) -> None:
    """Linha de cards com a contagem por status. Cada card usa a cor e o
    ícone fixos daquele status (ver core.config.STATUS_COLORS)."""
    if not status_counts:
        # st.columns(0) levanta StreamlitAPIException — sem status para
        # mostrar, a linha simplesmente não existe.
        st.caption("Sem status para exibir no filtro atual.")
        return

    subtitles = {
        "Concluída": "chamados finalizados",
        "Não iniciado": "aguardando início",
        "Em andamento": "em execução",
    }
    total = sum(v for v in status_counts.values() if isinstance(v, (int, float)))

    cols = st.columns(len(status_counts))
    for col, (status, qtd) in zip(cols, status_counts.items()):
        # A barra mostra o peso do status no total do recorte — a mesma
        # leitura de proporção que a referência faz nos cards de causa.
        pct = (float(qtd) / total * 100) if total else None
        with col:
            render_kpi_card(
                label=status,
                value=qtd,
                subtitle=subtitles.get(status, ""),
                accent=STATUS_COLORS.get(status),
                icon=_STATUS_ICONS.get(status, "dot"),
                chip=f"{pct:.0f}% do total" if pct is not None else "",
                progress=pct,
            )


def render_destaque_card(
    tag: str,
    value: str,
    subvalue: str,
    icon: str = "dot",
    accent: str | None = None,
) -> None:
    """Card de destaque: medalhão + rótulo em caixa alta + valor (um nome ou
    data) + linha de apoio na cor do acento. `icon` é o NOME de um ícone de
    ui/icons.py."""
    st.markdown(
        f"""
        <div class="destaque-card" style="{_accent_style(accent)}">
            <div class="destaque-card__medallion">{svg_icon(icon)}</div>
            <div class="destaque-card__body">
                <span class="destaque-card__tag">{_texto(tag, vazio="")}</span>
                <p class="destaque-card__value">{_texto(value)}</p>
                <p class="destaque-card__subvalue">{_texto(subvalue, vazio="")}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Cor de cada posição do pódio, na sequência canônica da paleta: 1º teal,
# 2º lime, 3º amber e, do 4º em diante, o neutro. Segue o bloco "TOP 3
# PROBLEMAS" da referência, onde a posição é lida pela cor antes do número.
_CORES_PODIO = SERIES_COLORS


def render_rank_list(items, vazio: str = "Sem dados para o filtro atual.") -> None:
    """
    Pódio numerado: um item por linha, com o número em círculo colorido,
    o rótulo e a contagem/percentual à direita.

    `items` é a lista de ItemRanking de services/material_service.py — já
    posicionada e com percentual calculado; aqui não se faz conta nenhuma.

    Lista vazia não desenha uma caixa oca: mostra a mensagem `vazio`, que
    é a informação útil quando o filtro não deixou nenhum registro.
    """
    linhas = []
    for i, item in enumerate(items or []):
        # Aceita tanto ItemRanking quanto um objeto/dicionário equivalente:
        # o componente só precisa dos quatro campos, e falhar por causa do
        # tipo exato deixaria a página sem o card por um detalhe de forma.
        posicao = getattr(item, "posicao", None) or i + 1
        rotulo = getattr(item, "rotulo", "")
        quantidade = getattr(item, "quantidade", 0)
        percentual = getattr(item, "percentual", None)

        cor = _CORES_PODIO[min(int(posicao) - 1, len(_CORES_PODIO) - 1)]
        meta = format_int(quantidade)
        if isinstance(percentual, (int, float)):
            meta = f"{meta} · {percentual:.1f}%".replace(".", ",")

        linhas.append(
            f'<li class="rank-row" style="{_accent_style(cor)}">'
            f'<span class="rank-row__badge">{int(posicao)}</span>'
            f'<span class="rank-row__label">{_texto(rotulo)}</span>'
            f'<span class="rank-row__meta">{meta}</span>'
            "</li>"
        )

    if not linhas:
        st.markdown(
            f'<p class="rank-empty">{_texto(vazio, vazio="")}</p>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(f'<ol class="rank-list">{"".join(linhas)}</ol>', unsafe_allow_html=True)


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

    Itens sem "label" nem "value" são ignorados em vez de estourar
    KeyError: o pop-up junta números de várias origens e um campo ausente
    não deve fechar a análise inteira.
    """
    cards_html = []
    for card in cards or []:
        if not isinstance(card, dict):
            continue
        label = card.get("label")
        value = card.get("value")
        if label is None and value is None:
            continue
        meta = card.get("meta", "")
        meta_html = f'<p class="an-card__meta">{_texto(meta)}</p>' if meta else ""
        modifier = " an-card--texto" if card.get("texto") else ""
        cards_html.append(
            f'<div class="an-card{modifier}">'
            f'<p class="an-card__label">{_texto(label, vazio="")}</p>'
            f'<p class="an-card__value">{_texto(value)}</p>'
            f"{meta_html}"
            "</div>"
        )

    if not cards_html:
        return

    # O HTML sai numa linha só, sem indentação: o st.markdown passa a
    # string pelo parser de Markdown ANTES de injetar o HTML, e linhas
    # indentadas com 4+ espaços viram bloco de código — o que fazia só o
    # primeiro card de cada grupo aparecer.
    html = (
        f'<div class="an-group" style="{_accent_style(accent)}">'
        f'<p class="an-group__title"><span class="an-group__bar"></span>'
        f'{_texto(titulo, vazio="")}</p>'
        f'<div class="an-grid">{"".join(cards_html)}</div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
def render_dropdown_all(label: str, options: list[str], state_key: str) -> list[str]:
    """
    Filtro dropdown (st.selectbox) com opção "Todas" no topo da lista,
    equivalente a nenhum filtro aplicado.

    Renderiza no container ATUAL (e não em st.sidebar): as páginas o
    posicionam dentro das colunas da barra de filtros do topo — a sidebar
    é o rail de navegação e não recebe conteúdo de página.

    Seleção única — retorna lista vazia quando "Todas" está selecionada, e
    uma lista de 1 item com o valor escolhido caso contrário. Mantém o
    mesmo contrato de retorno do filtro multiselect anterior (lista vazia =
    sem filtro, ver services/filter_service.py), então os services de
    filtro não precisam mudar.
    """
    widget_key = f"{state_key}_dropdown"
    todas = "Todos"
    escolhas = [todas, *(options or [])]

    # Reseta para "Todas" se a seleção atual não existe mais entre as
    # opções (ex.: novo arquivo carregado) — evita erro de validação do
    # selectbox contra a nova lista.
    if widget_key not in st.session_state or st.session_state[widget_key] not in escolhas:
        st.session_state[widget_key] = todas

    st.selectbox(label=label, options=escolhas, key=widget_key)

    selecionado = st.session_state[widget_key]
    return [] if selecionado == todas else [selecionado]


# ---------------------------------------------------------------------------
# Tabela
# ---------------------------------------------------------------------------
def render_recurrence_table(df: pd.DataFrame) -> None:
    """Ranking com cabeçalho em duas linhas, posição discreta e total em destaque."""
    week_columns = list(df.columns[2:6])
    headers = []
    for column in week_columns:
        week, dates = str(column).split(" (", 1)
        headers.append(
            f'<th scope="col">{_texto(week)}<span class="recurrence-dates">{_texto(dates.rstrip(")"))}</span></th>'
        )
    rows = []
    for _, row in df.iterrows():
        weeks = ''.join(f'<td class="recurrence-number">{format_int(row[c])}</td>' for c in week_columns)
        rows.append(
            '<tr>'
            f'<td class="recurrence-position">{format_int(row["Posição"])}</td>'
            f'<th scope="row" class="recurrence-workshop">{_texto(row[COL_OFICINA])}</th>'
            f'{weeks}<td class="recurrence-total">{format_int(row["Total"])}</td>'
            '</tr>'
        )
    html = (
        '<div class="recurrence-summary">'
        f'<span><strong>{format_int(len(df))}</strong> oficinas recorrentes</span>'
        f'<span><strong>{format_int(df["Total"].sum())}</strong> solicitações nas 4 semanas</span>'
        '</div><div class="recurrence-scroll" role="region" aria-label="Ranking de oficinas recorrentes" tabindex="0">'
        '<table class="recurrence-table"><caption class="recurrence-sr">Oficinas com solicitações em todas as quatro semanas, ordenadas por total</caption>'
        '<colgroup><col style="width:4%"><col style="width:44%">'
        '<col style="width:11%"><col style="width:11%"><col style="width:11%"><col style="width:11%"><col style="width:8%"></colgroup>'
        '<thead><tr><th scope="col" class="recurrence-position">#</th>'
        '<th scope="col" class="recurrence-workshop">Oficina</th>'
        f'{"".join(headers)}<th scope="col" class="recurrence-total">Total</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_styled_dataframe(
    df: pd.DataFrame,
    date_columns: list[str] | None = None,
    height: int = 420,
    fit_content: bool = False,
) -> None:
    """
    Renderiza a tabela como HTML próprio (cabeçalho em gradiente teal,
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
    if not isinstance(df, pd.DataFrame) or df.empty:
        # Chamadores já checam .empty antes; a checagem aqui é a rede de
        # segurança para não emitir uma tabela sem nenhuma linha (que
        # renderiza como um retângulo vazio sem explicação).
        st.caption("Nenhum dado para exibir nesta tabela.")
        return

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
    # selo teal), só que calculado por coluna em vez de um limiar fixo, já
    # que cada tabela do app tem colunas numéricas com unidades diferentes
    # (dias, contagens, %).
    badge_cols = {
        col
        for col in display_df.columns
        if col not in date_columns
        and pd.api.types.is_numeric_dtype(df[col])
        and df[col].nunique(dropna=True) > 1
    }
    # Coluna inteira nula tem mediana NaN, e comparar valor > NaN é sempre
    # False — a mediana fica fora do dicionário e a coluna não recebe selo.
    medians = {
        col: df[col].median()
        for col in badge_cols
        if pd.notna(df[col].median())
    }

    header_html = "".join(
        f"<th>{escape(str(col))}</th>" for col in display_df.columns
    )

    rows_html = []
    for _, row in display_df.iterrows():
        cells = []
        for col in display_df.columns:
            raw = row[col]
            text = _texto(raw)
            cell_content = text
            if col in medians and pd.notna(raw) and raw > medians[col]:
                cell_content = f'<span class="ppc-pill">{text}</span>'
            cells.append(
                f'<td class="{alignments[col]}" title="{text}">{cell_content}</td>'
            )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    wrapper_class = "styled-table-wrapper"
    if fit_content:
        wrapper_class += " styled-table-wrapper--fit"

    # Altura fora de faixa cairia num max-height absurdo (ou negativo) no
    # CSS; 120px é o mínimo para caber cabeçalho + uma linha.
    altura = max(120, int(height)) if isinstance(height, (int, float)) else 420

    # HTML sem indentação: o parser Markdown interpreta linhas com quatro
    # espaços como bloco de código e, dependendo da versão do Streamlit,
    # isso fazia a tabela perder as classes e parecer sem estilização.
    table_html = (
        f'<div class="{wrapper_class}">'
        f'<div class="ppc-table-scroll" style="max-height:{altura}px;">'
        '<table class="ppc-table">'
        f'<thead><tr>{header_html}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table></div></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)
