"""
ui/styles.py

CSS do tema dark moderno. Cards com borda/glow verde-ciano neon sobre
fundo navy profundo, tipografia Sora (headings/KPI) + Inter (corpo),
cantos arredondados suaves. Centraliza toda a estética para não espalhar
CSS inline pelas telas.
"""

from __future__ import annotations

from core.config import PALETTE


def get_custom_css() -> str:
    p = PALETTE
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background: {p['bg']};
}}

h1, h2, h3, h4, .kpi-value {{
    font-family: 'Sora', sans-serif !important;
}}

/* ---------- Navbar (app.py) ---------- */
/* A navegação nativa está desligada; a navbar é uma linha de st.page_link
   dentro do container com key="navbar". Aqui ela vira uma barra de pílulas
   centralizada, e a página ativa ganha o preenchimento neon. */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

.st-key-navbar {{
    gap: 10px;
    margin-bottom: 18px;
    padding: 8px;
    background: linear-gradient(120deg, {p['surface']} 0%, {p['surface_alt']} 100%);
    border: 1px solid {p['border']};
    border-radius: 999px;
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
}}

.st-key-navbar button {{
    background: transparent !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 8px 26px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: {p['text_muted']} !important;
    transition: background .2s ease, color .2s ease, box-shadow .2s ease;
}}

.st-key-navbar button:hover {{
    background: {p['surface_alt']} !important;
    color: {p['text']} !important;
}}

/* A página ativa é renderizada como botão primary (ver app.py). */
.st-key-navbar [data-testid="stBaseButton-primary"] {{
    background: linear-gradient(120deg, {p['neon']} 0%, {p['purple']} 100%) !important;
    color: {p['bg']} !important;
    box-shadow: 0 6px 18px {p['neon']}44;
}}

.st-key-navbar [data-testid="stBaseButton-primary"] * {{
    color: {p['bg']} !important;
}}

/* ---------- Cabeçalho ---------- */
.app-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 22px 28px;
    background: linear-gradient(120deg, {p['surface']} 0%, {p['surface_alt']} 100%);
    border: 1px solid {p['border']};
    border-radius: 18px;
    box-shadow: 0 2px 18px {p['neon_glow']};
    margin-bottom: 22px;
}}
.app-header__icon {{
    font-size: 30px;
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: {p['neon']};
    box-shadow: 0 0 22px {p['neon_glow']};
}}
.app-header__title {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 22px;
    color: {p['text']};
    margin: 0;
}}
.app-header__subtitle {{
    font-size: 13px;
    color: {p['text_muted']};
    margin: 2px 0 0 0;
}}

/* ---------- KPI cards ---------- */
.kpi-card {{
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, {p['surface']} 70%, {p['surface_alt']} 100%);
    border: 1px solid {p['neon_soft']}55;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 2px 14px rgba(0, 0, 0, 0.35);
    transition: box-shadow .2s ease, transform .2s ease;
    height: 100%;
}}
.kpi-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 18px;
    right: 18px;
    height: 3px;
    border-radius: 0 0 4px 4px;
    background: linear-gradient(90deg, var(--accent, {p['neon']}), {p['neon_soft']});
}}
.kpi-card::after {{
    content: "";
    position: absolute;
    top: -22px;
    right: -22px;
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: radial-gradient(circle, {p['neon_soft']}66 0%, {p['neon_soft']}00 72%);
    filter: blur(2px);
    pointer-events: none;
}}
.kpi-card:hover {{
    box-shadow: 0 4px 22px {p['neon_glow']};
    transform: translateY(-2px);
}}
.kpi-card__label {{
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: .04em;
    color: {p['text']};
    text-transform: uppercase;
    margin: 2px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.kpi-card__label-icon {{
    color: var(--accent, {p['neon']});
    font-size: 13px;
}}
.kpi-card__value {{
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 25px;
    color: {p['text']};
    margin: 0 0 4px 0;
    line-height: 1.15;
}}
.kpi-card__subtitle {{
    font-size: 12.5px;
    font-weight: 500;
    color: {p['text_muted']};
    margin: 0;
}}

/* ---------- Destaque cards ---------- */
.destaque-card {{
    background: linear-gradient(135deg, {p['surface']} 60%, {p['surface_alt']} 100%);
    border: 1px solid {p['neon_soft']};
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 2px 16px {p['neon_glow']};
    height: 100%;
}}
.destaque-card__tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: {p['neon']};
    background: {p['surface_alt']};
    border: 1px solid {p['neon_soft']};
    border-radius: 999px;
    padding: 3px 10px;
    margin-bottom: 10px;
}}
.destaque-card__value {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 19px;
    color: {p['text']};
    margin: 0 0 2px 0;
    line-height: 1.3;
}}
.destaque-card__subvalue {{
    font-size: 13px;
    color: {p['text_muted']};
    margin: 0;
}}

/* ---------- Tabela estilizada (HTML custom) ---------- */
.styled-table-wrapper {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 16px;
    padding: 4px;
    box-shadow: 0 2px 14px rgba(0, 0, 0, 0.35);
}}

/* Variante "ajustada ao conteúdo": tabelas de poucas colunas (ex.: mês +
   total) ficam com a largura do próprio conteúdo e centralizadas, em vez
   de esticadas de ponta a ponta com um vazio enorme entre as colunas. */
.styled-table-wrapper--fit {{
    width: fit-content;
    max-width: 100%;
    margin-left: auto;
    margin-right: auto;
}}

.styled-table-wrapper--fit table.ppc-table {{
    min-width: 0;
}}

.ppc-table-scroll {{
    overflow: auto;
    border-radius: 12px;
}}

table.ppc-table {{
    width: auto;
    min-width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Inter', sans-serif;
    font-size: 12.5px;
    table-layout: auto;
}}

table.ppc-table thead th {{
    position: sticky;
    top: 0;
    z-index: 1;
    background: linear-gradient(135deg, {p['table_header_start']} 0%, {p['table_header_end']} 100%);
    color: #FFFFFF;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 11.5px;
    letter-spacing: .03em;
    text-transform: uppercase;
    text-align: center;
    padding: 9px 14px;
    white-space: nowrap;
}}
table.ppc-table thead th:first-child {{ border-top-left-radius: 12px; }}
table.ppc-table thead th:last-child {{ border-top-right-radius: 12px; }}

.ppc-th-icon {{
    color: rgba(255, 255, 255, 0.75);
    font-size: 8px;
    margin-right: 6px;
    vertical-align: middle;
}}

/* ---------- Badge de valor em destaque ---------- */
.ppc-pill {{
    display: inline-block;
    background: {p['table_badge_bg']};
    color: {p['table_badge_text']};
    font-weight: 700;
    padding: 2px 11px;
    border-radius: 999px;
}}

table.ppc-table tbody td {{
    padding: 7px 14px;
    color: {p['text']};
    border-bottom: 1px solid {p['border']};
    white-space: nowrap;
}}

table.ppc-table tbody tr:nth-child(even) {{
    background: {p['surface_alt']};
}}
table.ppc-table tbody tr:nth-child(odd) {{
    background: {p['surface']};
}}
table.ppc-table tbody tr:hover {{
    background: {p['neon_soft']}26;
}}
table.ppc-table tbody tr:last-child td {{
    border-bottom: none;
}}

td.ppc-align-left {{ text-align: left; }}
td.ppc-align-right {{ text-align: right; }}
td.ppc-align-center {{ text-align: center; }}

/* ---------- Dropdown de filtros (multiselect) ---------- */
div[data-testid="stMultiSelect"] > div > div {{
    border-radius: 12px !important;
    border: 1px solid {p['border']} !important;
    background: {p['surface']} !important;
}}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
    background: {p['neon']} !important;
    border-radius: 999px !important;
}}

/* ---------- Área analítica (pop-up) ---------- */
/* Reaproveita a linguagem visual dos kpi-card (mesma superfície, mesmo
   glow, mesma família de raio) num formato mais compacto: aqui são 8
   cards juntos dentro de um diálogo, não 3-4 espalhados na página. */
.an-group {{
    margin-bottom: 22px;
}}
.an-group__title {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: {p['text_muted']};
    margin: 0 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.an-group__bar {{
    width: 4px;
    height: 14px;
    border-radius: 4px;
    background: var(--accent, {p['neon']});
    display: inline-block;
}}

/* auto-fit + minmax: 3 colunas na largura cheia do diálogo, quebrando
   sozinho para 2/1 em telas estreitas — sem media query. */
.an-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}}

.an-card {{
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, {p['surface']} 70%, {p['surface_alt']} 100%);
    border: 1px solid {p['border']};
    border-left: 3px solid var(--accent, {p['neon']});
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.32);
    transition: box-shadow .2s ease, transform .2s ease;
}}
.an-card:hover {{
    box-shadow: 0 4px 20px {p['neon_glow']};
    transform: translateY(-2px);
}}
.an-card__label {{
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
    color: {p['text_muted']};
    margin: 0 0 8px 0;
}}
.an-card__value {{
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 26px;
    line-height: 1.1;
    color: {p['text']};
    margin: 0;
}}
.an-card__meta {{
    font-size: 11.5px;
    color: {p['text_muted']};
    margin: 6px 0 0 0;
}}

/* Destaques: o valor é um nome (oficina / tipo de solicitação), não um
   número — fonte menor e quebra liberada, senão nome longo de oficina
   estoura o card. */
.an-card--texto .an-card__value {{
    font-size: 16px;
    line-height: 1.35;
    white-space: normal;
    overflow-wrap: anywhere;
}}

/* ---------- Diálogo (pop-up) ---------- */
div[data-testid="stDialog"] div[role="dialog"] {{
    background: {p['bg']};
    border: 1px solid {p['border']};
    border-radius: 20px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.55);
}}

/* ---------- Botão da área analítica ---------- */
/* Escopo pela classe st-key-<key> que o Streamlit aplica no container do
   widget — evita vazar estilo para os demais botões do app. */
/* Uma key por página (ppc_ = Chamados, rep_ = Reposições), já que a mesma
   key não pode ser reusada entre widgets. O botão fica na barra de filtros
   do topo, ao lado do "Carregar outro arquivo" — sem margem extra, para
   não desalinhar da base dos campos da mesma linha. */
.st-key-ppc_analytics_btn button,
.st-key-rep_analytics_btn button {{
    background: linear-gradient(120deg, {p['surface']} 0%, {p['surface_alt']} 100%) !important;
    border: 1px solid {p['neon_soft']}66 !important;
    border-radius: 999px !important;
    color: {p['text']} !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 6px 18px !important;
    transition: box-shadow .2s ease, transform .2s ease, border-color .2s ease !important;
}}
.st-key-ppc_analytics_btn button:hover,
.st-key-rep_analytics_btn button:hover {{
    border-color: {p['neon']} !important;
    box-shadow: 0 4px 18px {p['neon_glow']} !important;
    transform: translateY(-1px);
}}

/* ---------- Seção títulos ---------- */
.section-title {{
    font-family: 'Sora', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: {p['text']};
    margin: 26px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-title__bar {{
    width: 5px;
    height: 18px;
    border-radius: 4px;
    background: {p['neon']};
    display: inline-block;
}}
</style>
"""
