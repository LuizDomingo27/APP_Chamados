"""
ui/styles.py

CSS do tema light moderno. Cards com borda/glow verde-ciano neon sobre
fundo claro, tipografia Sora (headings/KPI) + Inter (corpo), cantos
arredondados suaves. Centraliza toda a estética para não espalhar CSS
inline pelas telas.
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
    box-shadow: 0 1px 10px rgba(16, 36, 31, 0.05);
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
    box-shadow: 0 1px 10px rgba(16, 36, 31, 0.05);
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
    background: linear-gradient(135deg, {p['neon']} 0%, {p['neon_soft']} 100%);
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

/* ---------- Popover de filtros ---------- */
div[data-testid="stPopover"] button {{
    border-radius: 12px !important;
    border: 1px solid {p['border']} !important;
    background: {p['surface']} !important;
    font-weight: 500;
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
