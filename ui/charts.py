"""
ui/charts.py

Wrapper para renderizar gráficos ECharts dentro do Streamlit via
components.v1.html (a lib streamlit-echarts está com incompatibilidade
de versão no ambiente atual, então carregamos o echarts.min.js direto
via CDN dentro de um componente HTML — mesmo resultado, zero dependência
extra). Cada "build_*_option" monta o dicionário de opções do ECharts;
"render_echarts" cuida só de desenhar.
"""

from __future__ import annotations

import json
import uuid

import pandas as pd
import streamlit as st

from core.config import PALETTE

_ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"

# Fonte dos rótulos dos gráficos: o componente roda num iframe isolado que
# não carrega a fonte "Inter" (importada só no documento principal via
# Google Fonts), então "fontFamily: Inter" sem fallback caía no serif
# padrão do navegador — daí o visual "ofuscado". Usamos a stack de fonte
# nativa do sistema, sempre disponível, sem depender de rede.
_CHART_FONT = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

_TOOLTIP_BASE = {
    "backgroundColor": "rgba(16, 36, 31, 0.92)",
    "borderColor": PALETTE["neon_soft"],
    "borderWidth": 1,
    "borderRadius": 10,
    "padding": [10, 14],
    "textStyle": {"color": "#FFFFFF", "fontFamily": _CHART_FONT, "fontSize": 13},
    "extraCssText": "box-shadow: 0 6px 24px rgba(15,191,159,0.25);",
}


def render_echarts(option: dict, height: int = 380) -> None:
    """Renderiza um dicionário de opções ECharts dentro de um componente HTML."""
    div_id = f"echarts_{uuid.uuid4().hex}"
    option_json = json.dumps(option, ensure_ascii=False)

    html = f"""
    <html>
    <head>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: transparent;
        }}
        #{div_id} {{
            width: 100%;
            height: {height}px;
            overflow: hidden;
        }}
    </style>
    </head>
    <body>
        <div id="{div_id}"></div>
        <script src="{_ECHARTS_CDN}"></script>
        <script>
            (function() {{
                function renderChart() {{
                    var el = document.getElementById('{div_id}');
                    if (!el || typeof echarts === 'undefined') {{
                        setTimeout(renderChart, 80);
                        return;
                    }}
                    var chart = echarts.init(el, null, {{renderer: 'svg'}});
                    chart.setOption({option_json});
                    window.addEventListener('resize', function() {{ chart.resize(); }});
                }}
                renderChart();
            }})();
        </script>
    </body>
    </html>
    """
    st.iframe(html, height=height, width="stretch")


def build_trend_line_option(trend_df: pd.DataFrame) -> dict:
    """Linha de tendência diária de chamados + linha de referência (média)."""
    datas = trend_df["Data"].dt.strftime("%d/%m").tolist()
    valores = trend_df["Chamados"].tolist()
    media = float(trend_df["Média do Período"].iloc[0]) if not trend_df.empty else 0

    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis"},
        "grid": {"left": 40, "right": 70, "top": 30, "bottom": 36},
        "xAxis": {
            "type": "category",
            "data": datas,
            "axisLine": {"lineStyle": {"color": PALETTE["border"]}},
            "axisTick": {"show": False},
            "splitLine": {"show": False},
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": _CHART_FONT},
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"show": False},
        },
        "series": [
            {
                "name": "Chamados",
                "type": "line",
                "data": valores,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {"color": PALETTE["neon"], "width": 3},
                "itemStyle": {"color": PALETTE["neon"]},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(15,191,159,0.35)"},
                            {"offset": 1, "color": "rgba(15,191,159,0.02)"},
                        ],
                    }
                },
                "markLine": {
                    "symbol": "none",
                    "label": {
                        "show": True,
                        "position": "end",
                        "formatter": f"Média: {media:.1f}",
                        "color": PALETTE["table_badge_text"],
                        "backgroundColor": PALETTE["table_badge_bg"],
                        "padding": [4, 8],
                        "borderRadius": 6,
                        "fontFamily": _CHART_FONT,
                        "fontSize": 11,
                        "fontWeight": 600,
                    },
                    "lineStyle": {"color": PALETTE["table_badge_text"], "type": "dashed", "width": 1.5},
                    "data": [{"yAxis": media}],
                },
            }
        ],
    }


def build_oficina_ranking_option(ranking_df: pd.DataFrame) -> dict:
    """Barra horizontal com o ranking das oficinas com mais chamados."""
    df_sorted = ranking_df.sort_values("Total de Chamados", ascending=True)
    nomes = df_sorted.iloc[:, 0].astype(str).tolist()
    valores = df_sorted["Total de Chamados"].tolist()

    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 10, "right": 30, "top": 10, "bottom": 10, "containLabel": True},
        "xAxis": {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": _CHART_FONT},
        },
        "yAxis": {
            "type": "category",
            "data": nomes,
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"color": PALETTE["text"], "fontFamily": _CHART_FONT, "fontSize": 12},
        },
        "series": [
            {
                "type": "bar",
                "data": valores,
                "barWidth": "55%",
                "itemStyle": {
                    "borderRadius": [0, 8, 8, 0],
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 1, "y2": 0,
                        "colorStops": [
                            {"offset": 0, "color": PALETTE["neon_soft"]},
                            {"offset": 1, "color": PALETTE["neon"]},
                        ],
                    },
                },
                "label": {
                    "show": True,
                    "position": "right",
                    "color": PALETTE["text"],
                    "fontFamily": _CHART_FONT,
                    "fontWeight": 600,
                },
            }
        ],
    }


def build_categoria_bar_option(
    categoria_df: pd.DataFrame,
    sort_ascending: bool = True,
    show_trend: bool = False,
) -> dict:
    """
    Barra vertical simples com total de chamados por categoria.

    Esta função também é reaproveitada pelas tendências semanal/mensal
    (mesmo formato de colunas) — nesses casos ``sort_ascending`` deve vir
    False, pois a ordem cronológica das barras não pode ser embaralhada
    pela ordenação por valor, e ``show_trend=True`` sobrepõe uma linha
    acompanhando os mesmos valores das colunas, deixando a variação entre
    os períodos mais fácil de enxergar.
    """
    df_sorted = (
        categoria_df.sort_values("Total de Chamados", ascending=True)
        if sort_ascending
        else categoria_df
    )
    nomes = df_sorted.iloc[:, 0].astype(str).tolist()
    valores = df_sorted["Total de Chamados"].tolist()

    series: list[dict] = [
        {
            "name": "Total",
            "type": "bar",
            "data": valores,
            "barWidth": "55%",
            "itemStyle": {
                "borderRadius": [8, 8, 0, 0],
                "color": {
                    "type": "linear",
                    "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": PALETTE["neon"]},
                        {"offset": 1, "color": PALETTE["neon_soft"]},
                    ],
                },
            },
        }
    ]

    if show_trend:
        series.append(
            {
                "name": "Variação",
                "type": "line",
                "data": valores,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 7,
                "z": 3,
                "lineStyle": {"color": PALETTE["warning"], "width": 2.5},
                "itemStyle": {"color": PALETTE["warning"], "borderColor": "#FFFFFF", "borderWidth": 1.5},
            }
        )

    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 20, "right": 20, "top": 20, "bottom": 70, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": nomes,
            "axisLabel": {
                "color": PALETTE["text_muted"],
                "fontFamily": _CHART_FONT,
                "rotate": 28,
                "fontSize": 11,
            },
            "axisLine": {"lineStyle": {"color": PALETTE["border"]}},
            "axisTick": {"show": False},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"show": False},
        },
        "series": series,
    }
