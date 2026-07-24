"""
app.py

Ponto de entrada do app. Define a navegação entre as páginas
(Chamados e Reposições) — cada página mora em pages/ e é totalmente
independente (upload, filtros e estado próprios), compartilhando apenas
as camadas core/, services/ e ui/.

A navegação é uma NAVBAR centralizada no topo do conteúdo, desenhada
aqui com st.page_link. A navegação nativa fica desligada
(position="hidden") em vez de position="top" porque a versão nativa
ancora os links à esquerda do header e, com o tema custom, colapsa os
itens num menu "1 more" mesmo sobrando espaço.
"""

from __future__ import annotations

import streamlit as st

from ui.styles import get_custom_css

st.set_page_config(
    page_title="PP Chamados | Central de Ajuda",
    page_icon="🎫",
    layout="wide",
    # Nenhuma página escreve em st.sidebar — os filtros migraram para o
    # topo do conteúdo. O "collapsed" só garante que nem o botão de abrir
    # a barra apareça enquanto ela estiver vazia.
    initial_sidebar_state="collapsed",
)

# O CSS é injetado AQUI (e não em cada página) porque a navbar abaixo já
# precisa da folha de estilo, e ela é desenhada antes do conteúdo da página.
st.markdown(get_custom_css(), unsafe_allow_html=True)

pagina_chamados = st.Page("pages/chamados.py", title="Chamados", icon="🎫", default=True)
pagina_reposicoes = st.Page("pages/reposicoes.py", title="Reposições", icon="🧵")

paginas = [pagina_chamados, pagina_reposicoes]
pg = st.navigation(paginas, position="hidden")

# Botões (e não st.page_link) porque só assim dá para marcar visualmente a
# página ativa: o st.page_link não expõe nenhum atributo estável de
# "página atual" no HTML, enquanto o botão aceita type="primary".
with st.container(key="navbar", horizontal=True, horizontal_alignment="center"):
    for pagina in paginas:
        ativa = pagina.url_path == pg.url_path
        if st.button(
            f"{pagina.icon}  {pagina.title}",
            key=f"nav_{pagina.url_path or 'home'}",
            type="primary" if ativa else "secondary",
        ):
            st.switch_page(pagina)

pg.run()
