"""
app.py

Ponto de entrada do app. Define a navegação entre as páginas
(Chamados e Reposições) — cada página mora em pages/ e é totalmente
independente (upload, filtros e estado próprios), compartilhando apenas
as camadas core/, services/ e ui/.

A navegação é um RAIL LATERAL (sidebar) com o bloco de marca no topo e um
item por página, desenhado aqui com st.button. A navegação nativa fica
desligada (position="hidden") em vez de position="top" porque a versão
nativa ancora os links à esquerda do header e, com o tema custom, colapsa
os itens num menu "1 more" mesmo sobrando espaço.
"""

from __future__ import annotations

import streamlit as st

from ui.icons import icon
from ui.styles import get_custom_css

st.set_page_config(
    page_title="PP Chamados | Central de Ajuda",
    layout="wide",
    # A sidebar deixou de ser espaço morto: ela É a navegação (rail).
    # Nenhuma página escreve nela — os filtros continuam no topo do
    # conteúdo, como antes.
    initial_sidebar_state="expanded",
)

# O CSS é injetado AQUI (e não em cada página) porque o rail abaixo já
# precisa da folha de estilo, e ele é desenhado antes do conteúdo da página.
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Sem `icon=` nas páginas: o ícone de cada item do rail é desenhado pelo
# CSS (máscara SVG no ::before, ver ui/styles.py), e não por emoji no
# rótulo do botão — emoji muda de desenho e de cor a cada sistema.
pagina_chamados = st.Page("pages/chamados.py", title="Chamados", default=True)
pagina_reposicoes = st.Page("pages/reposicoes.py", title="Reposições")

paginas = [pagina_chamados, pagina_reposicoes]

# Slug de cada item do rail, explícito. É ele que forma a key do botão e,
# por consequência, a classe "st-key-nav_<slug>" que o CSS usa para pintar o
# ícone. Derivar do url_path não serve: a página default fica com url_path
# vazio, e o slug mudaria junto com a ordem das páginas.
_RAIL_SLUGS = {pagina_chamados: "chamados", pagina_reposicoes: "reposicoes"}

# A MARCA é escrita na sidebar ANTES de st.navigation, e os itens depois.
#
# A ordem não é estética, é o que faz o rail aparecer no primeiro
# carregamento: com position="hidden" o front-end não desenha a sidebar se
# ela não tiver nenhum ELEMENTO no momento em que a mensagem de navegação
# chega — e um container vazio não conta. Sem este bloco de marca antes, o
# rail só surgia a partir do segundo run (depois de qualquer clique).
#
# Os itens continuam vindo depois porque dependem de pg.url_path para saber
# qual página marcar como ativa; eles são preenchidos no container reservado
# aqui, que já nasce dentro de uma sidebar não vazia.
with st.sidebar:
    st.markdown(
        f"""
        <div class="rail-brand">
            <div class="rail-brand__icon">{icon("chart")}</div>
            <p class="rail-brand__title">CHAMADOS &amp;<br/>REPOSIÇÕES</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _nav_slot = st.container(key="nav_rail")

pg = st.navigation(paginas, position="hidden")

# Botões (e não st.page_link) porque só assim dá para marcar visualmente a
# página ativa: o st.page_link não expõe nenhum atributo estável de "página
# atual" no HTML, enquanto o botão aceita type="primary".
with _nav_slot:
    for pagina in paginas:
        ativa = pagina.url_path == pg.url_path
        if st.button(
            pagina.title,
            key=f"nav_{_RAIL_SLUGS[pagina]}",
            type="primary" if ativa else "secondary",
            width="stretch",
        ):
            st.switch_page(pagina)

pg.run()
