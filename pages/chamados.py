"""
pages/chamados.py

Página "Chamados" — dashboard de acompanhamento de chamados (Central de
Ajuda). Esta camada só ORQUESTRA: lê o upload, chama os services para
parsear/filtrar/calcular KPIs e chama os componentes de UI para
desenhar a tela. Nenhuma regra de negócio mora aqui.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import streamlit as st

# Garante que a raiz do projeto (onde ficam core/, services/, ui/) esteja
# no sys.path, independente de como o Streamlit resolve o diretório de
# execução desta página dentro de st.navigation.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.config import (
    COL_CONCLUIDO_EM,
    COL_CRIADO_EM,
    COL_DATA_CONCLUSAO,
    COL_DATA_INICIO,
    COL_DIAS_ABERTO,
    COL_OFICINA,
    COL_SOLICITACAO,
    PALETTE,
    TOP_N_OFICINAS,
    TOP_N_SOLICITACOES,
)
from core.utils import format_decimal, format_int, safe_unique_sorted
from services.data_loader import load_dados_consolidados, validate_workbook
from services.export_service import build_excel_report
from services.filter_service import apply_all_filters, semana_options
from services.kpi_service import (
    agregado_por_categoria,
    agregado_por_coluna,
    agregado_por_oficina,
    calcular_analise,
    calcular_destaques,
    contagem_por_status,
    enrich_com_dias_aberto,
    ranking_oficinas,
    tabela_ordenada_por_prioridade,
    tendencia_diaria,
    tendencia_mensal,
    tendencia_semanal,
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
    render_analytics_group,
    render_destaque_card,
    render_dropdown_all,
    render_header,
    render_kpi_card,
    render_section_title,
    render_status_kpis,
    render_styled_dataframe,
)
from ui.styles import get_custom_css

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
        st.session_state[_FILE_STATE_KEY] = uploaded.getvalue()
        st.session_state[_FILE_NAME_KEY] = uploaded.name
        st.rerun()


@st.dialog("📊 Visão Analítica", width="large")
def _dialog_analise(resumo) -> None:
    """Pop-up da área analítica. Só exibe — todos os números já vêm
    calculados de kpi_service.calcular_analise()."""
    st.caption(
        "Indicadores do recorte atual — refletem os filtros aplicados na "
        "barra lateral."
    )

    render_analytics_group(
        "Total de Chamados",
        [
            {"label": "Mês", "value": format_int(resumo.total_mes), "meta": resumo.label_mes},
            {"label": "Semana", "value": format_int(resumo.total_semana), "meta": resumo.label_semana},
            {"label": "Dia", "value": format_int(resumo.total_dia), "meta": resumo.label_dia},
        ],
        accent=PALETTE["neon"],
    )

    render_analytics_group(
        "Média de Chamados",
        [
            {
                "label": "Por Mês",
                "value": format_decimal(resumo.media_mes),
                "meta": f"em {resumo.qtd_meses} mês(es)",
            },
            {
                "label": "Por Semana",
                "value": format_decimal(resumo.media_semana),
                "meta": f"em {resumo.qtd_semanas} semana(s)",
            },
            {
                "label": "Por Dia",
                "value": format_decimal(resumo.media_dia),
                "meta": f"em {resumo.qtd_dias} dia(s)",
            },
        ],
        accent=PALETTE["purple"],
    )

    render_analytics_group(
        "Destaques",
        [
            {
                "label": "🏭 Oficina com mais solicitações",
                "value": resumo.oficina_top_nome,
                "meta": f"{format_int(resumo.oficina_top_qtd)} chamado(s)",
                "texto": True,
            },
            {
                "label": "🏷️ Tipo de chamado mais frequente",
                "value": resumo.tipo_top_nome,
                "meta": f"{format_int(resumo.tipo_top_qtd)} chamado(s)",
                "texto": True,
            },
        ],
        accent=PALETTE["warning"],
    )


def _render_sidebar_filters(df):
    st.sidebar.markdown("### 🔍 Filtros")

    min_date = df[COL_CRIADO_EM].min()
    max_date = df[COL_CRIADO_EM].max()

    date_range = st.sidebar.date_input(
        "Período (Criado em)",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
        format="DD/MM/YYYY",
        key="ppc_date_range",
    )
    start, end = (date_range if isinstance(date_range, tuple) and len(date_range) == 2
                  else (min_date.date(), max_date.date()))

    numero_chamado = st.sidebar.text_input("Número do chamado", placeholder="Ex: 25128", key="ppc_numero")

    semanas_disponiveis = semana_options(df)
    semanas_selecionadas = render_dropdown_all(
        "🗓️ Semana(s)", semanas_disponiveis, "_select_all_semanas_filter"
    )

    oficinas_disponiveis = safe_unique_sorted(df[COL_OFICINA])
    oficinas_selecionadas = render_dropdown_all(
        "🏭 Oficina(s)", oficinas_disponiveis, "_select_all_oficinas_filter"
    )

    st.sidebar.divider()
    if st.sidebar.button("🔄 Carregar outro arquivo", width="stretch", key="ppc_reset"):
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

    # Botão do pop-up analítico na sidebar. Fica aqui (e não dentro de
    # _render_sidebar_filters) porque depende do recorte já filtrado — a
    # sidebar respeita a ordem das chamadas, então ele aparece logo
    # abaixo do "Carregar outro arquivo".
    if st.sidebar.button(
        "📊 Visão Analítica",
        width="stretch",
        key="ppc_analytics_btn",
        help="Abre o resumo analítico do período filtrado",
    ):
        _dialog_analise(calcular_analise(filtrado))

    # ---------------- Totais gerais ----------------
    render_section_title("Visão Geral")
    col1, col2 = st.columns([1, 3])
    with col1:
        render_kpi_card("Total de Chamados", total_chamados(filtrado), subtitle="no período filtrado")
    with col2:
        status_counts = contagem_por_status(filtrado)
        render_status_kpis(status_counts)

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

    # ---------------- Tendência (dia / semana / mês) ----------------
    render_section_title("Tendência de Chamados")
    tab_dia, tab_semana, tab_mes = st.tabs(["Por Dia", "Por Semana", "Por Mês"])
    with tab_dia:
        trend_df = tendencia_diaria(filtrado)
        if not trend_df.empty:
            render_echarts(build_trend_line_option(trend_df), height=360)
    with tab_semana:
        semana_df = tendencia_semanal(filtrado)
        if not semana_df.empty:
            render_echarts(build_categoria_bar_option(semana_df, sort_ascending=False, show_trend=True), height=360)
    with tab_mes:
        mes_df = tendencia_mensal(filtrado)
        if not mes_df.empty:
            render_echarts(build_categoria_bar_option(mes_df, sort_ascending=False, show_trend=True), height=360)

    # ---------------- Top Tipos de Solicitação ----------------
    render_section_title(f"Top {TOP_N_SOLICITACOES} Tipos de Solicitação")
    solicitacao_df = agregado_por_coluna(filtrado, COL_SOLICITACAO, TOP_N_SOLICITACOES)
    if not solicitacao_df.empty:
        render_echarts(build_categoria_bar_option(solicitacao_df, sort_ascending=True), height=380)

    # ---------------- Chamados por Categoria ----------------
    # Mesma linha de variação (%) das tendências temporais: aqui ela mostra
    # o quanto cada categoria varia em relação à anterior (ordenadas por
    # volume, crescente), em taxa percentual.
    render_section_title("Chamados por Categoria")
    categoria_df = agregado_por_categoria(filtrado)
    if not categoria_df.empty:
        render_echarts(
            build_categoria_bar_option(categoria_df, sort_ascending=True, show_trend=True),
            height=380,
        )

    # ---------------- Ranking de Oficinas ----------------
    render_section_title(f"Ranking de Oficinas (Top {TOP_N_OFICINAS})")
    rank_df = ranking_oficinas(filtrado, TOP_N_OFICINAS)
    if not rank_df.empty:
        render_echarts(build_oficina_ranking_option(rank_df), height=380)

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
        COL_DIAS_ABERTO,
        COL_CRIADO_EM,
        COL_DATA_CONCLUSAO,
    ]
    tabela_fila = enrich_com_dias_aberto(tabela_ordenada_por_prioridade(filtrado))
    detalhe_cols = [c for c in detalhe_cols if c in tabela_fila.columns]
    tabela_fila = tabela_fila[detalhe_cols]

    # Filtro local por dias em aberto — afeta SOMENTE esta tabela (não os
    # KPIs, gráficos ou demais tabelas acima). Slider de faixa com mínimo
    # de 1 dia: chamados abertos há menos de 1 dia ficam de fora.
    dias_validos = tabela_fila[COL_DIAS_ABERTO].dropna()
    max_dias = int(dias_validos.max()) if not dias_validos.empty else 1
    if max_dias > 1:
        faixa_dias = st.slider(
            "🕒 Filtrar por dias em aberto",
            min_value=1,
            max_value=max_dias,
            value=(1, max_dias),
            key="ppc_fila_dias_aberto",
            help="Mostra na fila apenas chamados cujo tempo em aberto está "
            "dentro do intervalo. Afeta somente esta tabela.",
        )
        low_dias, high_dias = faixa_dias
    else:
        low_dias, high_dias = 1, max_dias

    dias_col = tabela_fila[COL_DIAS_ABERTO]
    tabela_prioridade = tabela_fila[dias_col.notna() & dias_col.between(low_dias, high_dias)]

    render_styled_dataframe(
        tabela_prioridade,
        date_columns=[COL_CRIADO_EM, COL_DATA_CONCLUSAO],
        height=420,
    )

    # ---------------- Exportação ----------------
    # O relatório exporta a fila completa (sem o filtro de dias em aberto,
    # que é só visual desta tabela), já respeitando os filtros da barra
    # lateral aplicados em 'filtrado'.
    st.divider()
    excel_bytes = build_excel_report(
        tabela_chamados=tabela_fila,
        agregado_oficina=agregado_por_oficina(filtrado),
        agregado_categoria=agregado_por_categoria(filtrado),
        date_columns=[COL_CRIADO_EM, COL_DATA_CONCLUSAO],
    )

    st.download_button(
        "⬇️ Exportar dados filtrados (Excel)",
        data=excel_bytes,
        file_name="chamados_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="ppc_download",
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


main()
