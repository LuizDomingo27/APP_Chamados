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

_TOOLTIP_BASE = {
    "backgroundColor": "rgba(16, 36, 31, 0.92)",
    "borderColor": PALETTE["neon_soft"],
    "borderWidth": 1,
    "borderRadius": 10,
    "padding": [10, 14],
    "textStyle": {"color": "#FFFFFF", "fontFamily": "Inter, sans-serif", "fontSize": 13},
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
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": "Inter"},
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": "Inter"},
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
                        "color": "#FFFFFF",
                        "backgroundColor": PALETTE["warning"],
                        "padding": [4, 8],
                        "borderRadius": 6,
                        "fontFamily": "Inter",
                        "fontSize": 11,
                        "fontWeight": 600,
                    },
                    "lineStyle": {"color": PALETTE["warning"], "type": "dashed", "width": 1.5},
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
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": "Inter"},
        },
        "yAxis": {
            "type": "category",
            "data": nomes,
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"color": PALETTE["text"], "fontFamily": "Inter", "fontSize": 12},
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
                    "fontFamily": "Inter",
                    "fontWeight": 600,
                },
            }
        ],
    }


def build_categoria_bar_option(categoria_df: pd.DataFrame) -> dict:
    """Barra vertical simples com total de chamados por categoria."""
    nomes = categoria_df.iloc[:, 0].astype(str).tolist()
    valores = categoria_df["Total de Chamados"].tolist()

    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 40, "right": 20, "top": 20, "bottom": 70, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": nomes,
            "axisLabel": {
                "color": PALETTE["text_muted"],
                "fontFamily": "Inter",
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
            "axisLabel": {"color": PALETTE["text_muted"], "fontFamily": "Inter"},
        },
        "series": [
            {
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
        ],
    }
