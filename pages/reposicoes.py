"""
pages/reposicoes.py

Página "Reposições" — dashboard de acompanhamento das reposições
solicitadas pelas oficinas de costura. Segue exatamente o mesmo padrão
de camadas da página de Chamados (upload → services → UI), reaproveita
os mesmos componentes visuais (cards, tabela estilizada, gráficos) e só
acrescenta os serviços que são específicos de Reposições (parsing do
"Nome da tarefa" nesse formato, tendência semanal/mensal, tempo de
atendimento, ranking de solicitantes e oficinas com reposição em
aberto).
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.config import (
    COL_CATEGORIA,
    COL_CONCLUIDO_EM,
    COL_CRIADO_EM,
    COL_DIAS_ABERTO,
    COL_MOTIVO,
    COL_OFICINA,
    COL_PARTE_PECA,
    COL_TEMPO_ATENDIMENTO_DIAS,
    PALETTE,
    TOP_N_OFICINAS,
    TOP_N_SOLICITACOES,
)
from core.utils import format_decimal, format_int, safe_unique_sorted
from services.data_loader import load_dados_consolidados, validate_workbook
from services.export_service import build_excel_report_reposicao
from services.kpi_service import (
    agregado_por_categoria,
    agregado_por_coluna,
    agregado_por_oficina,
    contagem_por_status,
    ranking_oficinas,
    tabela_ordenada_por_prioridade,
    tendencia_diaria,
    total_chamados,
    total_pendentes,
)
from services.reposicao_filter_service import apply_all_filters_reposicao, semana_options
from services.reposicao_kpi_service import (
    calcular_analise_reposicao,
    calcular_destaques_reposicao,
    enrich_com_indicadores_temporais,
    oficinas_com_reposicao_pendente,
    tempo_atendimento_stats,
    tendencia_mensal,
    tendencia_semanal,
)
from services.reposicao_parser_service import enrich_with_parsed_fields_reposicao
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

# Chaves de estado próprias desta página (prefixo "rep_"), independentes
# das usadas em Chamados ("ppc_") — os dois arquivos podem ficar
# carregados ao mesmo tempo, cada um na sua página.
_FILE_STATE_KEY = "rep_file_bytes"
_FILE_NAME_KEY = "rep_file_name"


@st.cache_data(show_spinner=False)
def _load_and_enrich(file_bytes: bytes):
    df = load_dados_consolidados(io.BytesIO(file_bytes))
    df = enrich_with_parsed_fields_reposicao(df)
    return enrich_com_indicadores_temporais(df)


def _render_upload_screen() -> None:
    render_header(
        title="Central de Acompanhamento de Reposições",
        subtitle="Faça upload da exportação de Reposições (.xlsx) para começar",
        icon="🧵",
    )
    st.info(
        "📤 Envie o arquivo Excel exportado (aba **Dados Consolidados**) para "
        "gerar o dashboard de reposições das oficinas de costura.",
    )
    uploaded = st.file_uploader(
        "Arquivo Excel de Reposições",
        type=["xlsx"],
        key="rep_file_uploader",
    )
    if uploaded is not None:
        st.session_state[_FILE_STATE_KEY] = uploaded.getvalue()
        st.session_state[_FILE_NAME_KEY] = uploaded.name
        st.rerun()


@st.dialog("📊 Visão Analítica", width="large")
def _dialog_analise(resumo) -> None:
    """Pop-up da área analítica. Só exibe — todos os números já vêm
    calculados de reposicao_kpi_service.calcular_analise_reposicao()."""
    st.caption(
        "Indicadores do recorte atual — refletem os filtros aplicados na "
        "barra lateral."
    )

    render_analytics_group(
        "Total de Reposições",
        [
            {"label": "Mês", "value": format_int(resumo.total_mes), "meta": resumo.label_mes},
            {"label": "Semana", "value": format_int(resumo.total_semana), "meta": resumo.label_semana},
            {"label": "Dia", "value": format_int(resumo.total_dia), "meta": resumo.label_dia},
        ],
        accent=PALETTE["neon"],
    )

    render_analytics_group(
        "Média de Reposições",
        [
            {"label": "Por Mês", "value": format_decimal(resumo.media_mes),
             "meta": f"em {resumo.qtd_meses} mês(es)"},
            {"label": "Por Semana", "value": format_decimal(resumo.media_semana),
             "meta": f"em {resumo.qtd_semanas} semana(s)"},
            {"label": "Por Dia", "value": format_decimal(resumo.media_dia),
             "meta": f"em {resumo.qtd_dias} dia(s)"},
        ],
        accent=PALETTE["purple"],
    )

    render_analytics_group(
        "Destaques",
        [
            {"label": "🏭 Oficina com mais solicitações", "value": resumo.oficina_top_nome,
             "meta": f"{format_int(resumo.oficina_top_qtd)} reposição(ões)", "texto": True},
            {"label": "🏷️ Categoria mais frequente", "value": resumo.tipo_top_nome,
             "meta": f"{format_int(resumo.tipo_top_qtd)} reposição(ões)", "texto": True},
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
        key="rep_date_range",
    )
    start, end = (date_range if isinstance(date_range, tuple) and len(date_range) == 2
                  else (min_date.date(), max_date.date()))

    semanas_disponiveis = semana_options(df)
    semanas_selecionadas = render_dropdown_all(
        "🗓️ Semana(s)", semanas_disponiveis, "_select_all_semanas_filter_rep"
    )

    oficinas_disponiveis = safe_unique_sorted(df[COL_OFICINA])
    oficinas_selecionadas = render_dropdown_all(
        "🏭 Oficina(s)", oficinas_disponiveis, "_select_all_oficinas_filter_rep"
    )

    st.sidebar.divider()
    if st.sidebar.button("🔄 Carregar outro arquivo", width="stretch", key="rep_reset"):
        st.session_state.pop(_FILE_STATE_KEY, None)
        st.session_state.pop(_FILE_NAME_KEY, None)
        st.cache_data.clear()
        st.rerun()

    return start, end, semanas_selecionadas, oficinas_selecionadas


def _render_dashboard(df) -> None:
    start, end, semanas, oficinas = _render_sidebar_filters(df)
    filtrado = apply_all_filters_reposicao(df, start, end, semanas, oficinas)

    render_header(
        title="Central de Acompanhamento de Reposições",
        subtitle=f"{total_chamados(filtrado)} reposição(ões) no filtro atual",
        icon="🧵",
    )

    if filtrado.empty:
        st.warning("Nenhuma reposição encontrada para os filtros selecionados.")
        return

    # ---------------- Totais gerais ----------------
    # Botão do pop-up analítico na sidebar. Fica aqui (e não dentro de
    # _render_sidebar_filters) porque depende do recorte já filtrado — a
    # sidebar respeita a ordem das chamadas, então ele aparece logo
    # abaixo do "Carregar outro arquivo".
    if st.sidebar.button(
        "📊 Visão Analítica",
        width="stretch",
        key="rep_analytics_btn",
        help="Abre o resumo analítico do período filtrado",
    ):
        _dialog_analise(calcular_analise_reposicao(filtrado))

    render_section_title("Visão Geral")
    col1, col2 = st.columns([1, 3])
    with col1:
        render_kpi_card("Total de Reposições", total_chamados(filtrado), subtitle="no período filtrado")
    with col2:
        status_counts = contagem_por_status(filtrado)
        render_status_kpis(status_counts)

    # ---------------- Pendências ----------------
    render_section_title("Pendências")
    qtd_pendentes = total_pendentes(filtrado)
    oficinas_pendentes_df = oficinas_com_reposicao_pendente(filtrado)
    p1, p2 = st.columns([1, 3])
    with p1:
        render_kpi_card(
            "Reposições Pendentes",
            qtd_pendentes,
            subtitle="aguardando ou em andamento",
            accent="#FF6B6B",
        )
    with p2:
        if not oficinas_pendentes_df.empty:
            dias_max = int(oficinas_pendentes_df["Dias em Aberto"].max())
            oficina_mais_antiga = str(oficinas_pendentes_df.iloc[0][COL_OFICINA])
            qtd_oficinas_pendentes = int(oficinas_pendentes_df[COL_OFICINA].nunique())
            sub1, sub2 = st.columns(2)
            with sub1:
                render_kpi_card(
                    "Oficinas com Pendência",
                    qtd_oficinas_pendentes,
                    subtitle="aguardando reposição",
                    accent="#FFB020",
                )
            with sub2:
                render_kpi_card(
                    "Espera Mais Longa",
                    f"{dias_max} dia(s)",
                    subtitle=f"{oficina_mais_antiga}",
                    accent="#FFB020",
                )
        else:
            st.success("Nenhuma reposição pendente no filtro atual. ✅")

    if not oficinas_pendentes_df.empty:
        render_section_title("Oficinas com Reposição em Aberto")
        render_styled_dataframe(
            oficinas_pendentes_df,
            date_columns=["Solicitação Mais Antiga"],
            height=320,
        )

    # ---------------- Destaques ----------------
    render_section_title("Destaques do Período")
    destaques = calcular_destaques_reposicao(filtrado)
    d1, d2, d3 = st.columns(3)
    with d1:
        render_destaque_card(
            "📅 Dia com mais solicitações",
            destaques.dia_top_data,
            f"{destaques.dia_top_qtd} reposição(ões)",
        )
    with d2:
        render_destaque_card(
            "🏭 Oficina que mais solicita",
            destaques.oficina_top_nome,
            f"{destaques.oficina_top_qtd} reposição(ões)",
        )
    with d3:
        render_destaque_card(
            "🏷️ Categoria mais comum",
            destaques.solicitacao_top_nome,
            f"{destaques.solicitacao_top_qtd} reposição(ões)",
        )

    # ---------------- Tempo de atendimento ----------------
    render_section_title("Tempo de Atendimento")
    tempo = tempo_atendimento_stats(filtrado)
    if tempo.qtd_amostras > 0:
        t1, t2 = st.columns(2)
        with t1:
            render_kpi_card("Média", f"{tempo.media_dias} dia(s)", subtitle="tempo médio de atendimento")
        with t2:
            render_kpi_card("Mais demorado", f"{tempo.max_dias} dia(s)", subtitle="maior tempo registrado")
        st.caption(f"Calculado sobre {tempo.qtd_amostras} reposição(ões) já concluída(s) no filtro atual.")
    else:
        st.info("Ainda não há reposições concluídas no filtro atual para calcular o tempo de atendimento.")

    # ---------------- Tendência (dia / semana / mês) ----------------
    render_section_title("Tendência de Reposições")
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

    # ---------------- Ranking de Oficinas ----------------
    render_section_title(f"Ranking de Oficinas (Top {TOP_N_OFICINAS})")
    rank_df = ranking_oficinas(filtrado, TOP_N_OFICINAS)
    if not rank_df.empty:
        render_echarts(build_oficina_ranking_option(rank_df), height=380)

    # ---------------- Top Motivos de Reposição ----------------
    render_section_title(f"Top {TOP_N_SOLICITACOES} Motivos de Reposição")
    motivo_df = agregado_por_coluna(filtrado, COL_MOTIVO, TOP_N_SOLICITACOES)
    if not motivo_df.empty:
        render_echarts(build_categoria_bar_option(motivo_df, sort_ascending=True), height=380)

    # ---------------- Agregados em tabela ----------------
    render_section_title("Totais Agregados")
    tab_oficina, tab_categoria = st.tabs(["Por Oficina", "Por Categoria"])
    with tab_oficina:
        render_styled_dataframe(agregado_por_oficina(filtrado), height=320)
    with tab_categoria:
        render_styled_dataframe(agregado_por_categoria(filtrado), height=320)
        cat_df = agregado_por_categoria(filtrado)
        if not cat_df.empty:
            render_echarts(build_categoria_bar_option(cat_df), height=380)

    # ---------------- Tabela detalhada (ordenada por prioridade) ----------------
    render_section_title("Reposições — Fila por Prioridade")
    detalhe_cols = [
        COL_CATEGORIA,
        COL_OFICINA,
        COL_PARTE_PECA,
        COL_MOTIVO,
        "Status",
        "Prioridade",
        COL_CRIADO_EM,
        COL_CONCLUIDO_EM,
        COL_DIAS_ABERTO,
        COL_TEMPO_ATENDIMENTO_DIAS,
    ]
    detalhe_cols = [c for c in detalhe_cols if c in filtrado.columns]
    tabela_fila = tabela_ordenada_por_prioridade(filtrado)[detalhe_cols]

    # Filtro local por dias em aberto — afeta SOMENTE esta tabela (não os
    # KPIs, gráficos ou demais tabelas). A métrica cobre todas as linhas:
    # pendentes usam "Dias em Aberto" (espera até hoje) e concluídas usam
    # "Tempo de Atendimento" (dias que ficaram abertas). Slider de faixa
    # com mínimo de 1 dia: reposições abertas há menos de 1 dia ficam fora.
    dias_efetivo = tabela_fila[COL_DIAS_ABERTO].astype("Float64")
    if COL_TEMPO_ATENDIMENTO_DIAS in tabela_fila.columns:
        dias_efetivo = dias_efetivo.fillna(
            tabela_fila[COL_TEMPO_ATENDIMENTO_DIAS].astype("Float64")
        )

    dias_validos = dias_efetivo.dropna()
    max_dias = math.ceil(float(dias_validos.max())) if not dias_validos.empty else 1
    if max_dias > 1:
        low_dias, high_dias = st.slider(
            "🕒 Filtrar por dias em aberto",
            min_value=1,
            max_value=max_dias,
            value=(1, max_dias),
            key="rep_fila_dias_aberto",
            help="Mostra na fila apenas reposições cujo tempo em aberto está "
            "dentro do intervalo. Afeta somente esta tabela.",
        )
    else:
        low_dias, high_dias = 1, max_dias

    tabela_prioridade = tabela_fila[
        dias_efetivo.notna() & dias_efetivo.between(low_dias, high_dias)
    ]
    render_styled_dataframe(
        tabela_prioridade,
        date_columns=[COL_CRIADO_EM, COL_CONCLUIDO_EM],
        height=420,
    )

    # ---------------- Exportação ----------------
    # A exportação leva a fila completa (sem o filtro visual de dias em
    # aberto), respeitando apenas os filtros da barra lateral.
    st.divider()
    excel_bytes = build_excel_report_reposicao(
        tabela_reposicoes=tabela_fila,
        agregado_oficina=agregado_por_oficina(filtrado),
        oficinas_pendentes=oficinas_pendentes_df,
        date_columns=[COL_CRIADO_EM, COL_CONCLUIDO_EM],
    )

    st.download_button(
        "⬇️ Exportar dados filtrados (Excel)",
        data=excel_bytes,
        file_name="reposicoes_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="rep_download",
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
