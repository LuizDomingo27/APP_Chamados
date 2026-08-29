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

from core.config import PALETTE, SERIES_COLORS
from core.utils import rgba

_ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"

# Fonte dos rótulos dos gráficos: o componente roda num iframe isolado que
# não carrega a fonte "Inter" (importada só no documento principal via
# Google Fonts), então "fontFamily: Inter" sem fallback caía no serif
# padrão do navegador — daí o visual "ofuscado". Usamos a stack de fonte
# nativa do sistema, sempre disponível, sem depender de rede.
_CHART_FONT = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Nome da coluna de valor que todos os builders deste módulo esperam. Os
# services de KPI produzem esse nome; as páginas só renomeiam para exibição
# DEPOIS de montar o gráfico.
_COL_VALOR = "Total de Chamados"

_TOOLTIP_BASE = {
    "backgroundColor": rgba(PALETTE["surface"], 0.98),
    "borderColor": rgba(PALETTE["neon"], 0.45),
    "borderWidth": 1,
    "borderRadius": 12,
    "padding": [10, 14],
    "textStyle": {"color": PALETTE["text"], "fontFamily": _CHART_FONT, "fontSize": 13},
    "extraCssText": "box-shadow: 0 8px 28px rgba(15, 23, 42, 0.14);",
}


def _extrair_serie(df: pd.DataFrame, valor_col: str = _COL_VALOR) -> tuple[list[str], list]:
    """
    Extrai (rótulos, valores) no formato que os builders deste módulo usam:
    primeira coluna = rótulo, `valor_col` = valor.

    Levanta ValueError com a coluna que faltou em vez de deixar estourar um
    KeyError cru: se um service mudar o nome da coluna, a mensagem já diz
    onde arrumar — e as páginas transformam isso numa mensagem de erro na
    tela (ver o try/except em torno do carregamento).
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Esperado um DataFrame para o gráfico, recebido {type(df).__name__}.")
    if valor_col not in df.columns:
        raise ValueError(
            f"A coluna '{valor_col}' não existe nos dados do gráfico. "
            f"Colunas disponíveis: {', '.join(map(str, df.columns)) or '(nenhuma)'}"
        )
    if df.empty:
        return [], []
    return df.iloc[:, 0].astype(str).tolist(), df[valor_col].tolist()


def render_echarts(option: dict, height: int = 380) -> None:
    """Renderiza um dicionário de opções ECharts dentro de um componente HTML."""
    div_id = f"echarts_{uuid.uuid4().hex}"
    try:
        option_json = json.dumps(option, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        # Um valor não serializável (Timestamp, numpy type solto) viraria uma
        # exceção crua no meio da página. Mostramos o erro no lugar do
        # gráfico e o resto do dashboard continua utilizável.
        st.error(f"Não foi possível montar este gráfico: {exc}")
        return

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


def build_trend_bar_option(trend_df: pd.DataFrame) -> dict:
    """Barras verticais da tendência diária, sem linha de média."""
    faltando = [
        col for col in ("Data", "Chamados", "Média do Período")
        if col not in getattr(trend_df, "columns", [])
    ]
    if faltando:
        raise ValueError(
            "Dados de tendência sem as colunas esperadas: " + ", ".join(faltando)
        )

    datas = trend_df["Data"].dt.strftime("%d/%m").tolist()
    valores = trend_df["Chamados"].tolist()
    return {
        "tooltip": {**_TOOLTIP_BASE, "trigger": "axis", "axisPointer": {"type": "shadow"}},
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
                "type": "bar",
                "data": valores,
                "barMaxWidth": 34,
                "itemStyle": {
                    "color": PALETTE["neon"],
                    "borderRadius": [6, 6, 0, 0],
                },
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
            }
        ],
    }


# Compatibilidade para qualquer consumidor externo que ainda importe o nome
# anterior. A página usa o nome novo, mas a assinatura e os dados não mudam.
build_trend_line_option = build_trend_bar_option


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
    nomes, valores = _extrair_serie(dados_df)
    total = int(sum(valores))

    # Uma cor por fatia na sequência canônica da paleta (teal → lime →
    # amber → slate, ver core.config.SERIES_COLORS): é a mesma ordem da
    # rosca da referência e mantém a leitura cronológica — mês mais antigo
    # no teal, mais recente no fim da série.
    data = [
        {
            "name": nome,
            "value": valor,
            "itemStyle": {"color": SERIES_COLORS[i % len(SERIES_COLORS)]},
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
                    # A borda das fatias é da cor da SUPERFÍCIE do card (e
                    # não do fundo da página): a rosca vive dentro de um
                    # painel, e usar o fundo deixava um vinco escuro visível
                    # entre as fatias.
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
                    "fontSize": 15,
                    "fontWeight": 700,
                    "lineHeight": 19,
                },
                "labelLine": {
                    "length": 12,
                    "length2": 10,
                    "lineStyle": {
                        "color": PALETTE["border_strong"],
                        "width": 1.25,
                    },
                },
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
                    "font": f"800 28px {_CHART_FONT}",
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
                    "font": f"600 13px {_CHART_FONT}",
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
    pela ordenação por valor. Todas as visões usam somente barras: a linha
    de variação foi removida para manter a leitura uniforme entre dia,
    semana e mês.

    ``show_trend`` é mantido apenas por compatibilidade com consumidores
    anteriores e não adiciona mais uma série de linha.
    """
    if _COL_VALOR not in getattr(categoria_df, "columns", []):
        raise ValueError(f"A coluna '{_COL_VALOR}' não existe nos dados do gráfico de barras.")
    df_sorted = (
        categoria_df.sort_values(_COL_VALOR, ascending=True)
        if sort_ascending
        else categoria_df
    )
    nomes, valores = _extrair_serie(df_sorted)

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
                "color": PALETTE["neon"],
            },
        }
    ]

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
        "yAxis": {
            "type": "value",
            "splitLine": {"show": False},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {"show": False},
        },
        "series": series,
    }
