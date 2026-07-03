"""
app.py

Ponto de entrada do APP_PPCHAMADO — dashboard de acompanhamento de
chamados (Central de Ajuda). Esta camada só ORQUESTRA: lê o upload,
chama os services para parsear/filtrar/calcular KPIs e chama os
componentes de UI para desenhar a tela. Nenhuma regra de negócio mora
aqui.
"""

from __future__ import annotations

import io

import streamlit as st

from core.config import (
    COL_CONCLUIDO_EM,
    COL_CRIADO_EM,
    COL_DATA_CONCLUSAO,
    COL_DATA_INICIO,
    COL_OFICINA,
    TOP_N_OFICINAS,
)
from core.utils import safe_unique_sorted, select_all_popover
from services.data_loader import load_dados_consolidados, validate_workbook
from services.export_service import build_excel_report
from services.filter_service import apply_all_filters, get_available_weeks
from services.kpi_service import (
    agregado_por_categoria,
    agregado_por_oficina,
    calcular_destaques,
    contagem_por_prioridade,
    contagem_por_status,
    ranking_oficinas,
    tabela_ordenada_por_prioridade,
    tendencia_diaria,
    total_chamados,
)
from services.parser_service import enrich_with_parsed_fields
from ui.charts import (
    build_categoria_bar_option,
    build_oficina_ranking_option,
    build_trend_line_option,
    render_echarts,
)
from ui.components import (
    render_destaque_card,
    render_header,
    render_kpi_card,
    render_priority_kpis,
    render_section_title,
    render_status_kpis,
    render_styled_dataframe,
)
from ui.styles import get_custom_css

st.set_page_config(
    page_title="PP Chamados | Central de Ajuda",
    page_icon="🎫",
    layout="wide",
)
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Chave onde os BYTES do arquivo ficam persistidos, desacoplada da key do
# widget st.file_uploader. Isso é proposital: se o widget e o estado
# persistido compartilhassem a mesma key, o Streamlit limpa o estado de
# um widget que deixa de ser renderizado em um rerun (ex.: ao clicar em
# "Exportar", que sempre dispara um rerun) — o que fazia o app "voltar"
# para a tela de upload sozinho. Guardando os bytes numa chave própria,
# o estado sobrevive a qualquer rerun, independente do que é renderizado.
_FILE_STATE_KEY = "ppc_file_bytes"
_FILE_NAME_KEY = "ppc_file_name"


@st.cache_data(show_spinner=False)
def _load_and_enrich(file_bytes: bytes):
    df = load_dados_consolidados(io.BytesIO(file_bytes))
    return enrich_with_parsed_fields(df)


def _render_upload_screen() -> None:
    render_header(
        title="Central de Acompanhamento de Chamados",
        subtitle="Faça upload da exportação (Central de Ajuda.xlsx) para começar",
        icon="🎫",
    )
    st.info(
        "📤 Envie o arquivo Excel exportado (aba **Dados Consolidados**) para "
        "gerar o dashboard.",
    )
    uploaded = st.file_uploader(
        "Arquivo Excel da Central de Ajuda",
        type=["xlsx"],
        key="ppc_file_uploader",
    )
    if uploaded is not None:
        # Persiste os bytes numa chave própria (ver _FILE_STATE_KEY acima)
        # e força um rerun para entrar imediatamente no dashboard.
        st.session_state[_FILE_STATE_KEY] = uploaded.getvalue()
        st.session_state[_FILE_NAME_KEY] = uploaded.name
        st.rerun()


def _render_sidebar_filters(df):
    st.sidebar.markdown("### 🔍 Filtros")

    min_date = df[COL_CRIADO_EM].min()
    max_date = df[COL_CRIADO_EM].max()

    date_range = st.sidebar.date_input(
        "Período (Criado em)",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )
    start, end = (date_range if isinstance(date_range, tuple) and len(date_range) == 2
                  else (min_date.date(), max_date.date()))

    semanas_disponiveis = get_available_weeks(df)
    with st.sidebar:
        semanas_selecionadas = select_all_popover(
            "Semana(s)", semanas_disponiveis, key="semanas_filter", icon="📆"
        )

    numero_chamado = st.sidebar.text_input("Número do chamado", placeholder="Ex: 25128")

    oficinas_disponiveis = safe_unique_sorted(df[COL_OFICINA])
    state_key = "_select_all_oficinas_filter"
    if state_key not in st.session_state:
        st.session_state[state_key] = oficinas_disponiveis

    with st.sidebar.popover(
        f"🏭 Oficina(s): "
        f"{'Todas' if len(st.session_state[state_key]) == len(oficinas_disponiveis) else len(st.session_state[state_key])}"
        f" ({len(oficinas_disponiveis)})",
        use_container_width=True,
    ):
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Selecionar todas", key="oficinas_all", width="stretch"):
                st.session_state[state_key] = oficinas_disponiveis
                st.rerun()
        with col_b:
            if st.button("Limpar", key="oficinas_clear", width="stretch"):
                st.session_state[state_key] = []
                st.rerun()
        chosen = st.multiselect(
            "Buscar oficina",
            options=oficinas_disponiveis,
            default=st.session_state[state_key],
            key="oficinas_multiselect",
            label_visibility="collapsed",
        )
        st.session_state[state_key] = chosen

    oficinas_selecionadas = st.session_state[state_key]

    st.sidebar.divider()
    if st.sidebar.button("🔄 Carregar outro arquivo", width="stretch"):
        st.session_state.pop(_FILE_STATE_KEY, None)
        st.session_state.pop(_FILE_NAME_KEY, None)
        st.cache_data.clear()
        st.rerun()

    return start, end, numero_chamado, oficinas_selecionadas, semanas_selecionadas


def _render_dashboard(df) -> None:
    start, end, numero_chamado, oficinas, semanas = _render_sidebar_filters(df)
    filtrado = apply_all_filters(df, start, end, numero_chamado, oficinas, semanas)

    render_header(
        title="Central de Acompanhamento de Chamados",
        subtitle=f"{total_chamados(filtrado)} chamado(s) no filtro atual",
        icon="🎫",
    )

    if filtrado.empty:
        st.warning("Nenhum chamado encontrado para os filtros selecionados.")
        return

    # ---------------- Totais gerais ----------------
    render_section_title("Visão Geral")
    col1, col2 = st.columns([1, 3])
    with col1:
        render_kpi_card("Total de Chamados", total_chamados(filtrado), subtitle="no período filtrado")
    with col2:
        status_counts = contagem_por_status(filtrado)
        render_status_kpis(status_counts)

    # ---------------- Prioridade ----------------
    render_section_title("Por Prioridade")
    priority_counts = contagem_por_prioridade(filtrado)
    render_priority_kpis(priority_counts)

    # ---------------- Destaques ----------------
    render_section_title("Destaques do Período")
    destaques = calcular_destaques(filtrado)
    d1, d2, d3 = st.columns(3)
    with d1:
        render_destaque_card(
            "📅 Dia com mais pedidos",
            destaques.dia_top_data,
            f"{destaques.dia_top_qtd} chamado(s)",
        )
    with d2:
        render_destaque_card(
            "🏭 Oficina com mais pedidos",
            destaques.oficina_top_nome,
            f"{destaques.oficina_top_qtd} chamado(s)",
        )
    with d3:
        render_destaque_card(
            "🏷️ Tipo de solicitação mais comum",
            destaques.solicitacao_top_nome,
            f"{destaques.solicitacao_top_qtd} chamado(s)",
        )

    # ---------------- Gráficos ----------------
    render_section_title("Tendência de Chamados (com média do período)")
    trend_df = tendencia_diaria(filtrado)
    if not trend_df.empty:
        render_echarts(build_trend_line_option(trend_df), height=360)

    col_rank, col_cat = st.columns([1.2, 1])
    with col_rank:
        render_section_title(f"Ranking de Oficinas (Top {TOP_N_OFICINAS})")
        rank_df = ranking_oficinas(filtrado, TOP_N_OFICINAS)
        if not rank_df.empty:
            render_echarts(build_oficina_ranking_option(rank_df), height=380)

    with col_cat:
        render_section_title("Chamados por Categoria")
        cat_df = agregado_por_categoria(filtrado)
        if not cat_df.empty:
            render_echarts(build_categoria_bar_option(cat_df), height=380)

    # ---------------- Agregados em tabela ----------------
    render_section_title("Totais Agregados")
    tab_oficina, tab_categoria = st.tabs(["Por Oficina", "Por Categoria"])
    with tab_oficina:
        render_styled_dataframe(agregado_por_oficina(filtrado), height=320)
    with tab_categoria:
        render_styled_dataframe(agregado_por_categoria(filtrado), height=320)

    # ---------------- Tabela detalhada (ordenada por prioridade) ----------------
    render_section_title("Chamados — Fila por Prioridade")
    detalhe_cols = [
        "Categoria",
        COL_OFICINA,
        "Status",
        "Prioridade",
        COL_CRIADO_EM,
        COL_DATA_CONCLUSAO,
    ]
    detalhe_cols = [c for c in detalhe_cols if c in filtrado.columns]
    tabela_prioridade = tabela_ordenada_por_prioridade(filtrado)[detalhe_cols]
    render_styled_dataframe(
        tabela_prioridade,
        date_columns=[COL_CRIADO_EM, COL_DATA_CONCLUSAO],
        height=420,
    )

    # ---------------- Exportação ----------------
    st.divider()
    excel_bytes = build_excel_report(
        tabela_chamados=tabela_prioridade,
        agregado_oficina=agregado_por_oficina(filtrado),
        agregado_categoria=agregado_por_categoria(filtrado),
        date_columns=[COL_CRIADO_EM, COL_DATA_CONCLUSAO],
    )

    st.download_button(
        "⬇️ Exportar dados filtrados (Excel)",
        data=excel_bytes,
        file_name="chamados_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def main() -> None:
    file_bytes = st.session_state.get(_FILE_STATE_KEY)

    if file_bytes is None:
        _render_upload_screen()
        return

    ok, error_msg = validate_workbook(io.BytesIO(file_bytes))
    if not ok:
        st.error(error_msg)
        return

    df = _load_and_enrich(file_bytes)
    _render_dashboard(df)


if __name__ == "__main__":
    main()
