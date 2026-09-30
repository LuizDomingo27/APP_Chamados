"""
ui/styles.py

Folha de estilo única do app — tema "Clean Light".

Linguagem visual (espelha o dashboard de referência aprovado):
  • fundo cinza muito claro e superfícies brancas;
  • cartões com hairline, sombra curta e cantos generosos;
  • rótulos azul-acinzentados e valores em azul-marinho;
  • acentos semânticos: teal, verde, âmbar, rosa e slate;
  • ícones em pequenos quadrados tonalizados, sem brilho ou degradê.

Centraliza toda a estética para não espalhar CSS inline pelas telas: as
páginas só chamam os componentes de ui/components.py, que consomem as
classes definidas aqui.
"""

from __future__ import annotations

from core.config import PALETTE
from core.utils import rgba
from ui.icons import icon_data_uri

# A largura do rail acompanha o viewport: mantém 212 px em telas largas e
# encolhe até 176 px quando o espaço horizontal aperta. O mesmo valor é
# aplicado ao contêiner e ao conteúdo para evitar desalinhamento.
_RAIL_WIDTH = "clamp(176px, 15vw, 212px)"


def _icon_uri(name: str) -> str:
    """Ícone como data URI para mask-image. A cor vem do background-color da
    regra (a máscara só usa a forma), então o stroke aqui é irrelevante —
    fixamos em branco para o SVG ser válido. O escape de "#" é feito pelo
    quote() dentro de icon_data_uri — passar já escapado aqui geraria
    escape duplo (%2523) e um data URI inválido."""
    return icon_data_uri(name, color="#ffffff")


def get_custom_css() -> str:
    """Devolve a tag <style> completa do tema, pronta para st.markdown."""
    p = PALETTE
    # Tons translúcidos usados nos alertas. Ficam em variáveis porque uma
    # chamada de função com argumentos não cabe dentro de uma f-string que
    # já usa chaves duplicadas para o CSS.
    rgba_neon_08 = rgba(p["neon"], 0.08)
    rgba_neon_28 = rgba(p["neon"], 0.28)
    rgba_amber_08 = rgba(p["amber"], 0.08)
    rgba_amber_28 = rgba(p["amber"], 0.28)
    rgba_pink_08 = rgba(p["pink"], 0.08)
    rgba_pink_28 = rgba(p["pink"], 0.28)
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Tokens expostos como custom properties: os componentes de
   ui/components.py referenciam var(--accent) para trocar de cor sem que
   cada card precise de uma regra própria. */
:root {{
    --ppc-bg: {p['bg']};
    --ppc-surface: {p['surface']};
    --ppc-surface-alt: {p['surface_alt']};
    --ppc-surface-inset: {p['surface_inset']};
    --ppc-border: {p['border']};
    --ppc-border-strong: {p['border_strong']};
    --ppc-text: {p['text']};
    --ppc-text-muted: {p['text_muted']};
    --ppc-text-dim: {p['text_dim']};
    --ppc-neon: {p['neon']};
    --ppc-radius: 16px;
    --ppc-radius-sm: 12px;
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {p['text']};
}}

h1, h2, h3, h4, .kpi-card__value {{
    font-family: 'Inter', sans-serif !important;
}}

/* ---------- Fundo da aplicação ---------- */
/* O halo teal é um pseudo-elemento fixo, e não background-image no .stApp:
   como gradiente do próprio .stApp ele "andava" com o scroll da página e
   ficava visível no meio do conteúdo. */
.stApp {{
    background: {p['bg']};
    color: {p['text']};
}}

.stApp::before {{
    display: none;
}}

/* O header nativo do Streamlit (menu/deploy) fica transparente para não
   desenhar uma faixa mais clara em cima do fundo. */
header[data-testid="stHeader"] {{
    background: transparent !important;
}}

/* ---------- Rail de navegação (sidebar, ver app.py) ---------- */
[data-testid="stSidebar"] {{
    width: {_RAIL_WIDTH} !important;
    min-width: 0 !important;
    max-width: 212px !important;
    background: {p['surface']} !important;
    border-right: 1px solid {p['border']};
}}

[data-testid="stSidebar"] > div:first-child {{
    width: 100% !important;
    min-width: 0 !important;
}}

/* O Streamlit marca o rail recolhido com aria-expanded="false". A antiga
   largura mínima fixa mantinha os 212 px reservados mesmo nesse estado. */
[data-testid="stSidebar"][aria-expanded="false"] {{
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    border-right-width: 0;
    overflow: hidden;
}}

[data-testid="stSidebarUserContent"] {{
    padding: 18px 14px 24px 14px !important;
}}

/* Linhas decorativas no pé do rail — mesmo detalhe gráfico da referência,
   feito com dois gradientes cônicos suaves em vez de imagem. */
[data-testid="stSidebar"]::after {{
    display: none;
}}

/* Bloco de marca (topo do rail) */
.rail-brand {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 4px 0 20px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid {p['border']};
}}
.rail-brand__icon {{
    width: 46px;
    height: 46px;
    color: {p['neon']};
    filter: none;
}}
.rail-brand__icon svg {{
    width: 100%;
    height: 100%;
    display: block;
}}
.rail-brand__title {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 11.5px !important;
    line-height: 1.35 !important;
    letter-spacing: .09em !important;
    text-align: center;
    text-transform: uppercase;
    color: {p['text']};
    margin: 0;
}}

/* Itens de navegação: botões full-width alinhados à esquerda. */
.st-key-nav_rail {{
    gap: 6px;
}}

.st-key-nav_rail button {{
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: var(--ppc-radius-sm) !important;
    padding: 10px 14px !important;
    justify-content: flex-start !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    color: {p['text_muted']} !important;
    transition: background .18s ease, color .18s ease, border-color .18s ease;
}}

.st-key-nav_rail button p {{
    text-align: left !important;
}}

/* Ícone do item: o rótulo de st.button é texto puro e não aceita markup,
   então o SVG entra como máscara no ::before, pintada por background-color
   (assim herda a cor do estado — cinza, branco no hover, teal no ativo).
   A key do botão vira a classe st-key-nav_<url_path> (ver app.py). */
.st-key-nav_rail button::before {{
    content: "";
    width: 17px;
    height: 17px;
    flex: 0 0 17px;
    margin-right: 10px;
    background-color: currentColor;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-position: center;
    mask-position: center;
    -webkit-mask-size: contain;
    mask-size: contain;
}}
.st-key-nav_chamados button::before {{
    -webkit-mask-image: {_icon_uri('clipboard')};
    mask-image: {_icon_uri('clipboard')};
}}
.st-key-nav_reposicoes button::before {{
    -webkit-mask-image: {_icon_uri('spool')};
    mask-image: {_icon_uri('spool')};
}}

.st-key-nav_rail button:hover {{
    background: {p['surface_inset']} !important;
    color: {p['text']} !important;
}}

/* A página ativa é renderizada como botão primary (ver app.py): pílula
   teal translúcida com texto teal — o preenchimento sólido usado antes
   brigava com o rótulo de seção, que agora também é teal. */
.st-key-nav_rail [data-testid="stBaseButton-primary"] {{
    background: rgba(15, 159, 143, 0.09) !important;
    border-color: rgba(15, 159, 143, 0.18) !important;
    color: {p['neon']} !important;
    box-shadow: none;
}}

.st-key-nav_rail [data-testid="stBaseButton-primary"] * {{
    color: {p['neon']} !important;
}}

/* ---------- Cabeçalho da página ---------- */
.app-header {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 26px;
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: var(--ppc-radius);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}}
/* Fio teal na borda superior — assina o card sem recorrer a degradê no
   preenchimento, que é o que "amassava" o visual plano da referência. */
.app-header::before {{
    display: none;
}}
.app-header__icon {{
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    padding: 10px;
    box-sizing: border-box;
    color: {p['neon']};
    border-radius: 12px;
    background: rgba(15, 159, 143, 0.09);
    border: 1px solid rgba(15, 159, 143, 0.14);
    box-shadow: none;
}}
.app-header__icon svg {{
    display: block;
    width: 100%;
    height: 100%;
}}
.app-header__title {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 21px;
    letter-spacing: -.01em;
    color: {p['text']};
    margin: 0;
}}
.app-header__subtitle {{
    font-size: 12.5px;
    color: {p['text_muted']};
    margin: 3px 0 0 0;
}}

/* ---------- Painéis de seção ---------- */
/* Toda seção do dashboard vive dentro de um painel, como na referência:
   uma grade de caixas com hairline, rótulo em teal e conteúdo respirando
   por dentro.

   O gancho é a classe "st-key-<key>" que o Streamlit imprime no container
   quando ele recebe key (ver ui.components.panel) — todas as keys de painel
   começam com "ppcpanel-", então um seletor por prefixo pega todas sem
   precisar de uma regra por seção. Preferimos isso a estilizar o wrapper
   de st.container(border=True), cujo data-testid não é contrato estável. */
div[class*="st-key-ppcpanel-"] {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: var(--ppc-radius);
    padding: 18px 20px 20px 20px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}}

/* Os cards de Destaques terminam imediatamente antes deste painel. O
   Streamlit não injeta gap entre os dois blocos, então reservamos aqui o
   mesmo respiro vertical usado entre as demais seções do dashboard. */
.st-key-ppcpanel-ppc-tendencia {{
    margin-top: 24px;
}}

/* ---------- Rótulo de seção ---------- */
/* Teal, caixa alta e espaçado — é o marcador visual mais característico da
   referência ("OFICINAS COM MAIOR QUANTIDADE DE AJUSTES"). */
.section-title {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: .10em;
    text-transform: uppercase;
    color: {p['text_muted']};
    margin: 26px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 9px;
}}
.section-title__bar {{
    width: 4px;
    height: 15px;
    border-radius: 4px;
    background: {p['neon']};
    box-shadow: none;
    display: inline-block;
    flex: 0 0 4px;
}}
/* Dentro de um painel o rótulo já é o primeiro elemento e o padding da
   caixa faz o espaçamento — sem margem no topo (ver ui.components.panel). */
.section-title--panel {{
    margin: 0 0 14px 0;
}}

/* ---------- KPI cards ---------- */
.kpi-card {{
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: {p['surface']};
    border: 1px solid var(--accent-ring, {p['border']});
    border-radius: var(--ppc-radius);
    padding: 18px 20px;
    height: 100%;
    min-height: 200px;
    box-shadow: 0 4px 15px var(--accent-glow, rgba(15, 159, 143, 0.10));
    transition: border-color .18s ease, box-shadow .18s ease;
}}
.kpi-card:hover {{
    border-color: var(--accent, {p['neon']});
    box-shadow: 0 7px 22px var(--accent-glow, rgba(15, 159, 143, 0.12));
}}
/* Halo do acento no canto — único "brilho" que sobrou, bem discreto. */
.kpi-card::after {{
    display: none;
}}

.kpi-card__head {{
    display: block;
    height: 36px;
    min-height: 36px;
    flex: 0 0 36px;
    box-sizing: border-box;
    padding-right: 48px;
    margin-bottom: 12px;
}}

/* Medalhão circular do ícone: anel na cor do acento sobre preenchimento
   translúcido da mesma cor — o "selo" dos cards da referência. */
.kpi-card__medallion {{
    position: absolute;
    top: 18px;
    right: 20px;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    padding: 9px;
    box-sizing: border-box;
    color: var(--accent, {p['neon']});
    border-radius: 11px;
    background: var(--accent-soft, rgba(15, 159, 143, 0.10));
    border: none;
    box-shadow: none;
}}
.kpi-card__medallion svg,
.destaque-card__medallion svg {{
    display: block;
    width: 100%;
    height: 100%;
}}

.kpi-card__label {{
    flex: 1 1 auto;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .09em;
    color: {p['text_muted']};
    text-transform: uppercase;
    margin: 0 !important;
    line-height: 1.35 !important;
}}
.kpi-card__value {{
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 32px;
    letter-spacing: -.02em;
    color: {p['text']};
    margin: 0 0 2px 0 !important;
    line-height: 1.1 !important;
}}
.kpi-card__content {{
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}}
.kpi-card__subtitle {{
    font-size: 12px;
    font-weight: 500;
    color: {p['text_muted']};
    margin: 0 !important;
    line-height: 1.4 !important;
}}

/* Cards sem pílula ou barra mantêm a mesma altura dos demais. O bloco de
   valor + texto informativo desce inteiro para o rodapé, preservando o
   cabeçalho no topo e evitando conteúdo solto no meio do card. */
.kpi-card--compact {{
    min-height: 200px;
}}
.kpi-card--compact .kpi-card__content {{
    margin-top: auto;
}}

/* Chip "25% do total" — mesma pílula translúcida da referência. */
.kpi-card__chip {{
    align-self: flex-start;
    margin-top: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .02em;
    color: var(--accent, {p['neon']});
    background: var(--accent-soft, rgba(15, 159, 143, 0.10));
    border: 1px solid var(--accent-ring, rgba(15, 159, 143, 0.28));
    border-radius: 999px;
    padding: 3px 11px;
}}

/* Barra de proporção sob o valor */
.kpi-card__track {{
    margin-top: 14px;
    height: 5px;
    border-radius: 999px;
    background: {p['surface_inset']};
    overflow: hidden;
}}
.kpi-card__fill {{
    height: 100%;
    border-radius: 999px;
    background: var(--accent, {p['neon']});
    box-shadow: none;
}}

/* ---------- Destaque cards ---------- */
.destaque-card {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: {p['surface']};
    border: 1px solid var(--accent-ring, {p['border']});
    border-radius: var(--ppc-radius);
    padding: 18px 20px;
    height: 100%;
    min-height: 144px;
    box-sizing: border-box;
    box-shadow: 0 4px 15px var(--accent-glow, rgba(15, 159, 143, 0.10));
    transition: border-color .18s ease, box-shadow .18s ease;
}}
.destaque-card:hover {{
    border-color: var(--accent, {p['neon']});
    box-shadow: 0 7px 22px var(--accent-glow, rgba(15, 159, 143, 0.12));
}}
.destaque-card__medallion {{
    width: 38px;
    height: 38px;
    flex: 0 0 38px;
    padding: 9px;
    box-sizing: border-box;
    color: var(--accent, {p['neon']});
    border-radius: 11px;
    background: var(--accent-soft, rgba(15, 159, 143, 0.10));
    border: none;
}}
.destaque-card__body {{
    min-width: 0;
    align-self: flex-start;
}}
.destaque-card__tag {{
    display: block;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: {p['text_muted']};
    margin: 0 0 7px 0;
}}
.destaque-card__value {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 17px;
    color: {p['text']};
    margin: 0 0 3px 0;
    line-height: 1.3;
    overflow-wrap: anywhere;
}}
.destaque-card__subvalue {{
    font-size: 12.5px;
    font-weight: 600;
    color: var(--accent, {p['neon']});
    margin: 0;
}}

/* ---------- Pódio numerado (ui.components.render_rank_list) ---------- */
.rank-list {{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}
.rank-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: {p['surface_alt']};
    border: 1px solid var(--accent-ring, {p['border']});
    border-radius: var(--ppc-radius-sm);
    transition: border-color .18s ease, box-shadow .18s ease;
}}
.rank-row:hover {{
    border-color: var(--accent, {p['neon']});
    box-shadow: 0 4px 14px var(--accent-glow, rgba(15, 159, 143, 0.10));
}}
/* O número é o marcador de posição — círculo cheio na cor da colocação,
   com texto escuro por cima, como no bloco "Top 3" da referência. */
.rank-row__badge {{
    width: 22px;
    height: 22px;
    flex: 0 0 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: var(--accent, {p['neon']});
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 11.5px;
    line-height: 1;
}}
.rank-row__label {{
    flex: 1 1 auto;
    min-width: 0;
    font-size: 13px;
    font-weight: 600;
    color: {p['text']};
    overflow-wrap: anywhere;
}}
.rank-row__meta {{
    flex: 0 0 auto;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: var(--accent, {p['neon']});
    white-space: nowrap;
}}
.rank-empty {{
    font-size: 12.5px;
    color: {p['text_muted']};
    margin: 4px 0 0 0;
}}

/* ---------- Tabela estilizada (HTML custom) ---------- */
.recurrence-summary {{
    display: flex; flex-wrap: wrap; gap: 8px 28px;
    color: {p['text_muted']}; font-size: 13px; margin: 8px 0 16px;
}}
.recurrence-summary strong {{ color: {p['text']}; font-weight: 700; }}
.recurrence-scroll {{
    max-height: 520px; overflow: auto; border: 1px solid {p['border']};
    border-radius: 12px; scrollbar-color: {p['border_strong']} transparent;
}}
.recurrence-scroll:focus-visible {{ outline: 2px solid {p['neon']}; outline-offset: 3px; }}
table.recurrence-table {{
    width: 100%; min-width: 760px; border-collapse: separate; border-spacing: 0;
    font-size: 13px; font-variant-numeric: tabular-nums; table-layout: fixed;
}}
table.recurrence-table thead th {{
    position: sticky; top: 0; z-index: 1; background: {p['surface_inset']};
    color: {p['text_muted']}; font-size: 12px; font-weight: 600;
    padding: 14px 16px; border: 0; border-bottom: 1px solid {p['border']};
    text-align: center; white-space: nowrap;
}}
.recurrence-dates {{ display: block; font-size: 11px; font-weight: 400; margin-top: 4px; }}
table.recurrence-table tbody td, table.recurrence-table tbody th {{
    padding: 15px 16px; border: 0; border-bottom: 1px solid {p['border']};
    color: {p['text']}; background: {p['surface']}; line-height: 1.4;
}}
table.recurrence-table .recurrence-position {{
    width: 48px; text-align: center; color: {p['text_muted']}; font-weight: 400;
}}
table.recurrence-table .recurrence-workshop {{
    text-align: left; font-weight: 500; overflow-wrap: anywhere;
}}
.recurrence-number {{ text-align: center; }}
table.recurrence-table .recurrence-total {{
    text-align: center; color: {p['table_badge_text']}; font-weight: 700;
    background: {rgba(p['neon'], 0.06)};
}}
table.recurrence-table tbody tr:hover td, table.recurrence-table tbody tr:hover th {{
    background: {p['surface_alt']};
}}
table.recurrence-table tbody tr:last-child td, table.recurrence-table tbody tr:last-child th {{ border-bottom: 0; }}
.recurrence-sr {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }}

.styled-table-wrapper {{
    background: {p['surface']};
    border: 1px solid {rgba(p['neon'], 0.28)};
    border-radius: var(--ppc-radius);
    padding: 6px;
    box-shadow: 0 5px 18px {rgba(p['neon'], 0.09)};
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
    border-radius: var(--ppc-radius-sm);
    scrollbar-color: {rgba(p['neon'], 0.38)} {p['surface_inset']};
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
    background: {rgba(p['neon'], 0.10)};
    color: {p['table_badge_text']};
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: .07em;
    text-transform: uppercase;
    text-align: center;
    padding: 12px 16px;
    white-space: nowrap;
    border-bottom: 1px solid {rgba(p['neon'], 0.22)};
    box-shadow: 0 1px 0 {rgba(p['neon'], 0.07)};
}}
table.ppc-table thead th:first-child {{ border-top-left-radius: var(--ppc-radius-sm); }}
table.ppc-table thead th:last-child {{ border-top-right-radius: var(--ppc-radius-sm); }}

/* ---------- Badge de valor em destaque ---------- */
.ppc-pill {{
    display: inline-block;
    background: {p['table_badge_bg']};
    color: {p['table_badge_text']};
    font-weight: 700;
    padding: 3px 11px;
    border-radius: 999px;
    border: 1px solid {rgba(p['neon'], 0.18)};
    box-shadow: 0 2px 8px {rgba(p['neon'], 0.08)};
}}

table.ppc-table tbody td {{
    padding: 11px 16px;
    color: {p['text']};
    border-bottom: 1px solid {p['border']};
    white-space: nowrap;
    transition: background-color .15s ease, color .15s ease;
}}
table.ppc-table tbody td + td {{
    border-left: 1px solid {rgba(p['border'], 0.72)};
}}

table.ppc-table tbody tr:nth-child(even) {{
    background: {p['surface_alt']};
}}
table.ppc-table tbody tr:nth-child(odd) {{
    background: {p['surface']};
}}
table.ppc-table tbody tr:hover {{
    background: {rgba(p['neon'], 0.075)};
}}
table.ppc-table tbody tr:last-child td {{
    border-bottom: none;
}}

td.ppc-align-left {{ text-align: left; }}
td.ppc-align-right {{ text-align: right; }}
td.ppc-align-center {{ text-align: center; }}

/* ---------- Barra de filtros (st.expander) ---------- */
/* Vira o card de contexto do topo, equivalente ao "Período analisado" da
   referência: superfície plana, hairline e rótulo discreto. */
[data-testid="stExpander"] details {{
    background: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: var(--ppc-radius) !important;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}}
[data-testid="stExpander"] summary {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    letter-spacing: .04em;
    color: {p['text']} !important;
    padding: 12px 18px !important;
}}
[data-testid="stExpander"] summary:hover {{
    color: {p['neon']} !important;
}}

/* ---------- Campos de formulário ---------- */
div[data-testid="stMultiSelect"] > div > div,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] > div > div,
div[data-testid="stDateInput"] > div > div {{
    border-radius: var(--ppc-radius-sm) !important;
    border: 1px solid {p['border']} !important;
    background: {p['surface']} !important;
    transition: border-color .18s ease;
}}
div[data-testid="stMultiSelect"] > div > div:focus-within,
div[data-testid="stSelectbox"] > div > div:focus-within,
div[data-testid="stTextInput"] > div > div:focus-within,
div[data-testid="stDateInput"] > div > div:focus-within {{
    border-color: {p['neon']} !important;
}}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
    background: {p['neon']} !important;
    border-radius: 999px !important;
}}
[data-testid="stWidgetLabel"] p {{
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: .05em;
    text-transform: uppercase;
    color: {p['text_muted']} !important;
}}

/* ---------- Abas (tendência por dia/semana/mês) ---------- */
[data-baseweb="tab-list"] {{
    gap: 4px;
    background: {p['surface_inset']};
    border-radius: 999px;
    padding: 4px;
    width: fit-content;
}}
[data-baseweb="tab-list"] [data-baseweb="tab"] {{
    border-radius: 999px !important;
    padding: 6px 18px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    color: {p['text_muted']} !important;
}}
[data-baseweb="tab-list"] [aria-selected="true"] {{
    background: rgba(15, 159, 143, 0.10) !important;
    color: {p['neon']} !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* ---------- Mensagens (info / warning / success / error) ---------- */
/* O azul padrão do st.info é a única cor do app fora da paleta. Aqui cada
   tipo de alerta é retintado com o acento correspondente.

   O tipo só é identificável pelo data-testid do FILHO (stAlertContentInfo
   etc.), enquanto o fundo mora no container — daí o :has(). Se o navegador
   não suportar :has(), as regras específicas são ignoradas e o alerta fica
   com as cores nativas do Streamlit, que continuam legíveis: degradação,
   não quebra. */
[data-testid="stAlertContainer"] {{
    border-radius: var(--ppc-radius-sm) !important;
    border: 1px solid {p['border']} !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{
    background: {rgba_neon_08} !important;
    border-color: {rgba_neon_28} !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{
    background: {rgba_neon_08} !important;
    border-color: {rgba_neon_28} !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{
    background: {rgba_amber_08} !important;
    border-color: {rgba_amber_28} !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{
    background: {rgba_pink_08} !important;
    border-color: {rgba_pink_28} !important;
}}

/* ---------- Uploader ---------- */
[data-testid="stFileUploaderDropzone"] {{
    background: {p['surface']} !important;
    border: 1px dashed {p['border_strong']} !important;
    border-radius: var(--ppc-radius) !important;
    transition: border-color .18s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {p['neon']} !important;
}}

/* ---------- Área analítica (pop-up) ---------- */
/* Reaproveita a linguagem visual dos kpi-card (mesma superfície, mesmo
   hairline, mesma família de raio) num formato mais compacto: aqui são 8
   cards juntos dentro de um diálogo, não 3-4 espalhados na página. */
.an-group {{
    margin-bottom: 22px;
}}
.an-group__title {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 11.5px;
    letter-spacing: .10em;
    text-transform: uppercase;
    color: var(--accent, {p['neon']});
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
    flex: 0 0 4px;
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
    background: {p['surface']};
    border: 1px solid var(--accent-ring, {p['border']});
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 4px 14px var(--accent-glow, rgba(15, 159, 143, 0.09));
    transition: border-color .18s ease, box-shadow .18s ease;
}}
.an-card:hover {{
    border-color: var(--accent, {p['neon']});
    box-shadow: 0 7px 20px var(--accent-glow, rgba(15, 159, 143, 0.12));
}}
.an-card__label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: {p['text_muted']};
    margin: 0 0 8px 0;
}}
.an-card__value {{
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 26px;
    line-height: 1.1;
    letter-spacing: -.02em;
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
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 20px;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.20);
}}

/* ---------- Botões de ação da barra de filtros ---------- */
/* Escopo pela classe st-key-<key> que o Streamlit aplica no container do
   widget — evita vazar estilo para os demais botões do app.
   Uma key por página (ppc_ = Chamados, rep_ = Reposições), já que a mesma
   key não pode ser reusada entre widgets. */
.st-key-ppc_analytics_btn button,
.st-key-rep_analytics_btn button,
.st-key-ppc_reset button,
.st-key-rep_reset button {{
    background: {p['surface']} !important;
    border: 1px solid {p['border_strong']} !important;
    border-radius: 12px !important;
    color: {p['text']} !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    padding: 7px 18px !important;
    transition: border-color .18s ease, color .18s ease, transform .18s ease !important;
}}
.st-key-ppc_analytics_btn button:hover,
.st-key-rep_analytics_btn button:hover,
.st-key-ppc_reset button:hover,
.st-key-rep_reset button:hover {{
    border-color: {p['neon']} !important;
    color: {p['neon']} !important;
    transform: translateY(-1px);
}}

/* Legenda de gráfico centralizada — usada sobre a rosca, cujo conteúdo
   é radial e fica desalinhado com um texto encostado à esquerda. */
.chart-caption {{
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: {p['text_muted']};
    text-align: center;
    margin: 0 0 6px 0;
}}

/* ---------- Ajustes responsivos ---------- */
@media (max-width: 1180px) {{
    [data-testid="stSidebarUserContent"] {{
        padding-left: 10px !important;
        padding-right: 10px !important;
    }}

    .rail-brand__title {{
        font-size: 10.5px !important;
        letter-spacing: .06em !important;
    }}

    .st-key-nav_rail button {{
        padding-left: 10px !important;
        padding-right: 10px !important;
        font-size: 13px !important;
    }}

    .st-key-nav_rail button::before {{
        margin-right: 8px;
    }}

    .app-header {{
        padding: 16px 18px;
    }}

    .kpi-card {{
        padding: 15px 14px;
    }}

    .kpi-card__head {{
        height: 36px;
        min-height: 36px;
        flex-basis: 36px;
        padding-right: 38px;
    }}

    .kpi-card__medallion {{
        top: 14px;
        right: 14px;
        width: 32px;
        height: 32px;
        flex-basis: 32px;
        padding: 8px;
    }}

    .kpi-card__label {{
        font-size: 9.5px;
        letter-spacing: .045em;
    }}

    .kpi-card__value {{
        font-size: 29px;
    }}

    .kpi-card__chip {{
        font-size: 10px;
        padding: 2px 8px;
    }}

    [data-testid="stWidgetLabel"] p {{
        font-size: 9.5px !important;
        letter-spacing: .03em;
    }}

    .st-key-ppc_analytics_btn button,
    .st-key-rep_analytics_btn button,
    .st-key-ppc_reset button,
    .st-key-rep_reset button {{
        min-height: 40px;
        padding: 6px 8px !important;
        font-size: 10.5px !important;
        line-height: 1.2 !important;
    }}
}}

@media (max-width: 640px) {{
    [data-testid="stSidebar"] {{
        width: clamp(156px, 44vw, 176px) !important;
    }}
}}
</style>
"""
