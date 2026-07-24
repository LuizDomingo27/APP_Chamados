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
    COL_CRIADO_EM,
    COL_OFICINA,
    COL_SOLICITACAO,
    OFICINA_ALIASES_RAW,
    OFICINA_INVALID_NAMES_RAW,
    OFICINA_SUFIXOS_MATERIA_PRIMA,
    OFICINAS_OFICIAIS_RAW,
    PALETTE,
    TOP_N_SOLICITACOES,
)
from core.utils import format_decimal, format_int, safe_unique_sorted
from services.data_loader import load_dados_consolidados, validate_workbook
from services.filter_service import apply_all_filters, semana_options
from services.kpi_service import (
    agregado_por_coluna,
    calcular_analise,
    calcular_destaques,
    contagem_por_status,
    tendencia_diaria,
    tendencia_mensal,
    tendencia_semanal,
    total_chamados,
)
from services.parser_service import (
    canonicalizacao_fingerprint,
    enrich_with_parsed_fields,
)
from services.upload_cache import clear_upload, load_upload, save_upload
from ui.charts import (
    build_categoria_bar_option,
    build_donut_option,
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
# O CSS custom é injetado uma única vez em app.py, antes da navbar.

# Chave onde os BYTES do arquivo ficam persistidos, desacoplada da key do
# widget st.file_uploader. Isso é proposital: se o widget e o estado
# persistido compartilhassem a mesma key, o Streamlit limpa o estado de
# um widget que deixa de ser renderizado em um rerun (qualquer interação
# que troque a tela renderizada) — o que fazia o app "voltar"
# para a tela de upload sozinho. Guardando os bytes numa chave própria,
# o estado sobrevive a qualquer rerun, independente do que é renderizado.
_FILE_STATE_KEY = "ppc_file_bytes"
_FILE_NAME_KEY = "ppc_file_name"

# Identificador desta página no cache em disco de uploads: o session_state
# morre com a sessão do navegador (F5 = tela de upload de novo), então os
# bytes também vão para services/upload_cache.py e voltam sozinhos.
_CACHE_SLOT = "chamados"


# Assinatura das regras de padronização de oficinas. Entra como argumento
# da função cacheada para que editar o cadastro/aliases em core.config
# invalide o cache — sem isso o dashboard segue mostrando os nomes
# calculados pela versão anterior das regras.
_REGRAS_OFICINA = canonicalizacao_fingerprint(
    OFICINAS_OFICIAIS_RAW,
    OFICINA_ALIASES_RAW,
    OFICINA_INVALID_NAMES_RAW,
    OFICINA_SUFIXOS_MATERIA_PRIMA,
)


@st.cache_data(show_spinner=False)
def _load_and_enrich(file_bytes: bytes, regras_oficina: str):
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
        save_upload(_CACHE_SLOT, uploaded.name, uploaded.getvalue())
        st.rerun()


@st.dialog("📊 Visão Analítica", width="large")
def _dialog_analise(resumo) -> None:
    """Pop-up da área analítica. Só exibe — todos os números já vêm
    calculados de kpi_service.calcular_analise()."""
    st.caption(
        "Indicadores do recorte atual — refletem os filtros aplicados na "
        "barra de filtros."
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


def _render_filtros(df):
    """Barra de filtros do topo. Substitui a antiga sidebar — a navegação
    virou navbar (st.navigation position="top"), então não há mais barra
    lateral onde ancorar os filtros. Devolve também se o botão da Visão
    Analítica foi clicado, porque o pop-up depende do recorte filtrado e
    só pode ser aberto depois que os filtros forem aplicados."""
    min_date = df[COL_CRIADO_EM].min()
    max_date = df[COL_CRIADO_EM].max()

    with st.expander("🔍 Filtros", expanded=True):
        # Campos e botões na MESMA linha; vertical_alignment="bottom" alinha
        # os botões (sem rótulo) pela base dos campos (que têm rótulo acima).
        c_periodo, c_numero, c_semana, c_oficina, c_analise, c_reset = st.columns(
            [2, 1.4, 1.5, 2.2, 1.3, 1.6], vertical_alignment="bottom"
        )
        with c_periodo:
            date_range = st.date_input(
                "Período (Criado em)",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
                format="DD/MM/YYYY",
                key="ppc_date_range",
            )
        with c_numero:
            numero_chamado = st.text_input(
                "Número do chamado", placeholder="Ex: 25128", key="ppc_numero"
            )
        with c_semana:
            semanas_selecionadas = render_dropdown_all(
                "🗓️ Semana(s)", semana_options(df), "_select_all_semanas_filter"
            )
        with c_oficina:
            oficinas_selecionadas = render_dropdown_all(
                "🏭 Oficina(s)", safe_unique_sorted(df[COL_OFICINA]), "_select_all_oficinas_filter"
            )

        with c_analise:
            abrir_analise = st.button(
                "📊 Visão Analítica",
                width="stretch",
                key="ppc_analytics_btn",
                help="Abre o resumo analítico do período filtrado",
            )
        with c_reset:
            if st.button("🔄 Carregar outro arquivo", width="stretch", key="ppc_reset"):
                st.session_state.pop(_FILE_STATE_KEY, None)
                st.session_state.pop(_FILE_NAME_KEY, None)
                clear_upload(_CACHE_SLOT)
                st.cache_data.clear()
                st.rerun()

        nome_arquivo = st.session_state.get(_FILE_NAME_KEY)
        if nome_arquivo:
            st.caption(f"📄 Arquivo carregado: **{nome_arquivo}**")

    start, end = (date_range if isinstance(date_range, tuple) and len(date_range) == 2
                  else (min_date.date(), max_date.date()))

    return start, end, numero_chamado, oficinas_selecionadas, semanas_selecionadas, abrir_analise


def _render_dashboard(df) -> None:
    # O cabeçalho mostra a contagem do recorte, que só existe depois dos
    # filtros — reservamos o espaço dele antes e preenchemos no fim, para
    # que continue aparecendo ACIMA da barra de filtros.
    slot_header = st.container()

    start, end, numero_chamado, oficinas, semanas, abrir_analise = _render_filtros(df)
    filtrado = apply_all_filters(df, start, end, numero_chamado, oficinas, semanas)

    with slot_header:
        render_header(
            title="Central de Acompanhamento de Chamados",
            subtitle=f"{total_chamados(filtrado)} chamado(s) no filtro atual",
            icon="🎫",
        )

    if filtrado.empty:
        st.warning("Nenhum chamado encontrado para os filtros selecionados.")
        return

    if abrir_analise:
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

    # ---------------- Fechamento: total por mês ----------------
    # Mesmo fechamento da página de Reposições: a tabela traz a série
    # completa do recorte e a rosca ao lado isola os 3 meses mais recentes,
    # que é o horizonte usado na conversa do dia a dia.
    agregado_mes = tendencia_mensal(filtrado)
    if not agregado_mes.empty:
        render_section_title("Chamados por Mês")
        # A rosca fica com 70% da linha: a tabela tem só 2 colunas estreitas
        # e não precisa de mais que o restante, enquanto o gráfico ganha o
        # espaço necessário para os rótulos externos das fatias respirarem.
        col_tabela, col_rosca = st.columns([3, 7], gap="medium")
        with col_tabela:
            render_styled_dataframe(agregado_mes, height=460, fit_content=True)
        with col_rosca:
            ultimos_meses = agregado_mes.tail(3)
            st.caption(f"Últimos {len(ultimos_meses)} meses")
            # O diâmetro da rosca é limitado pela MENOR dimensão do
            # container — alargar a coluna sozinha não aumentaria o círculo,
            # por isso a altura sobe junto com a largura.
            render_echarts(
                build_donut_option(
                    ultimos_meses,
                    titulo_centro="chamados",
                    unidade="chamado(s)",
                ),
                height=460,
            )


def main() -> None:
    file_bytes = st.session_state.get(_FILE_STATE_KEY)

    # Sessão nova (primeiro acesso do dia, F5, outra aba): recupera do disco
    # o último arquivo usado, em vez de exigir um novo upload.
    if file_bytes is None:
        em_cache = load_upload(_CACHE_SLOT)
        if em_cache is not None:
            file_bytes, nome = em_cache
            st.session_state[_FILE_STATE_KEY] = file_bytes
            st.session_state[_FILE_NAME_KEY] = nome

    if file_bytes is None:
        _render_upload_screen()
        return

    ok, error_msg = validate_workbook(io.BytesIO(file_bytes))
    if not ok:
        st.error(error_msg)
        return

    df = _load_and_enrich(file_bytes, _REGRAS_OFICINA)
    _render_dashboard(df)


main()
