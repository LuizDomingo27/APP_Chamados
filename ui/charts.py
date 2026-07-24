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
                "label": {
                    "show": True,
                    "position": "top",
                    "color": PALETTE["text"],
                    "fontFamily": _CHART_FONT,
                    "fontSize": 10.5,
                    "fontWeight": 600,
                },
                # A série diária pode ter dezenas de pontos e os rótulos
                # encostariam uns nos outros. hideOverlap deixa o ECharts
                # omitir os que colidem, mantendo os demais legíveis — sem
                # isso o gráfico vira um borrão de números em períodos longos.
                "labelLayout": {"hideOverlap": True},
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


def build_donut_option(
    dados_df: pd.DataFrame,
    titulo_centro: str = "Total",
    unidade: str = "chamado(s)",
) -> dict:
    """
    Rosca (donut) com a distribuição de um punhado de categorias — usada
    para comparar o peso dos últimos meses entre si.

    Espera o mesmo formato das demais funções deste módulo (primeira
    coluna = rótulo, "Total de Chamados" = valor), para poder receber
    direto a saída de tendencia_mensal sem transformação intermediária.
    O buraco do meio exibe o total somado das fatias, que é a leitura
    que se perde quando o gráfico só mostra percentuais.

    ``unidade`` é o substantivo usado no tooltip ("chamado(s)",
    "reposição(ões)") — o mesmo gráfico atende as duas páginas.
    """
    nomes = dados_df.iloc[:, 0].astype(str).tolist()
    valores = dados_df["Total de Chamados"].tolist()
    total = int(sum(valores))

    # Uma cor por fatia, do acento primário ao secundário — poucas fatias
    # (3 por padrão), então uma lista fixa basta e mantém a ordem
    # cronológica legível: mês mais antigo no tom mais claro.
    cores = [PALETTE["purple_soft"], PALETTE["neon_soft"], PALETTE["neon"]]
    data = [
        {
            "name": nome,
            "value": valor,
            "itemStyle": {"color": cores[i % len(cores)]},
        }
        for i, (nome, valor) in enumerate(zip(nomes, valores))
    ]

    return {
        "tooltip": {
            **_TOOLTIP_BASE,
            "trigger": "item",
            "formatter": f"{{b}}<br/><b>{{c}}</b> {unidade} ({{d}}%)",
        },
        "legend": {
            "bottom": 0,
            "icon": "circle",
            "itemWidth": 9,
            "itemHeight": 9,
            "textStyle": {
                "color": PALETTE["text_muted"],
                "fontFamily": _CHART_FONT,
                "fontSize": 11,
            },
        },
        "series": [
            {
                "type": "pie",
                "radius": ["52%", "76%"],
                "center": ["50%", "44%"],
                "avoidLabelOverlap": True,
                # Sem isso o ECharts imprime "21.55%" — duas casas num
                # rótulo curto só poluem a leitura da fatia.
                "percentPrecision": 1,
                "data": data,
                "itemStyle": {
                    "borderColor": PALETTE["surface"],
                    "borderWidth": 3,
                    "borderRadius": 6,
                },
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{c}\n{d}%",
                    "color": PALETTE["text"],
                    "fontFamily": _CHART_FONT,
                    "fontSize": 11,
                    "fontWeight": 600,
                    "lineHeight": 14,
                },
                "labelLine": {"length": 8, "length2": 8, "lineStyle": {"color": PALETTE["border"]}},
                "emphasis": {"scaleSize": 6},
            }
        ],
        # O total vai como "graphic" (e não como label da série) porque um
        # label central de pie só aparece no hover da fatia; aqui ele
        # precisa ficar visível o tempo todo, dentro do furo da rosca.
        "graphic": [
            {
                "type": "text",
                "left": "center",
                "top": "38%",
                "style": {
                    "text": str(total),
                    "fill": PALETTE["text"],
                    "font": f"700 22px {_CHART_FONT}",
                    "textAlign": "center",
                },
            },
            {
                "type": "text",
                "left": "center",
                "top": "48%",
                "style": {
                    "text": titulo_centro,
                    "fill": PALETTE["text_muted"],
                    "font": f"500 11px {_CHART_FONT}",
                    "textAlign": "center",
                },
            },
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

    # Rótulo com o total de cada coluna, acima da barra. É o único rótulo
    # desenhado no gráfico — a variação percentual fica só no tooltip, pois
    # impressa sobre as colunas ela cobria justamente estes valores.
    label_barra: dict = {
        "show": True,
        "position": "top",
        "color": PALETTE["text"],
        "fontFamily": _CHART_FONT,
        "fontSize": 11,
        "fontWeight": 600,
    }

    series: list[dict] = [
        {
            "name": "Total",
            "type": "bar",
            "data": valores,
            "barWidth": "55%",
            "label": label_barra,
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

    y_axis: list[dict] = [
        {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"show": False},
        }
    ]

    if show_trend:
        # A linha não repete o valor absoluto da coluna (isso só duplicava o
        # rótulo do total) — em vez disso plota a variação percentual em
        # relação ao período anterior, num eixo secundário próprio, já que a
        # escala de "%" não tem relação com a escala de contagem das barras.
        # O número da variação aparece apenas no tooltip: impresso sobre o
        # gráfico ele cobria os rótulos de total das colunas.
        pct_points: list[dict] = []
        for i, valor in enumerate(valores):
            anterior = valores[i - 1] if i > 0 else None
            if not anterior:
                pct_points.append({"value": None})
                continue
            variacao = round((valor - anterior) / anterior * 100, 1)
            # Cor do ponto mantém o sinal de leitura rápida mesmo sem rótulo:
            # verde para alta, vermelho para queda.
            cor = PALETTE["table_header_start"] if variacao >= 0 else PALETTE["danger"]
            pct_points.append({"value": variacao, "itemStyle": {"color": cor}})

        series.append(
            {
                "name": "Variação vs. período anterior (%)",
                "type": "line",
                "yAxisIndex": 1,
                "data": pct_points,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 7,
                "z": 3,
                "connectNulls": True,
                "lineStyle": {"color": PALETTE["text_muted"], "width": 2, "type": "dashed"},
                "itemStyle": {"borderColor": "#FFFFFF", "borderWidth": 1.5},
            }
        )
        y_axis.append(
            {
                "type": "value",
                "splitLine": {"show": False},
                "axisLine": {"show": False},
                "axisTick": {"show": False},
                "axisLabel": {"show": False},
            }
        )

    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 20, "right": 20, "top": 36, "bottom": 70, "containLabel": True},
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
        "yAxis": y_axis,
        "series": series,
    }
