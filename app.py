"""
app.py

Ponto de entrada do app. Define a navegação entre as páginas
(Chamados e Reposições) via st.navigation — cada página mora em
pages/ e é totalmente independente (upload, filtros e estado próprios),
compartilhando apenas as camadas core/, services/ e ui/.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="PP Chamados | Central de Ajuda",
    page_icon="🎫",
    layout="wide",
)

pagina_chamados = st.Page("pages/chamados.py", title="Chamados", icon="🎫", default=True)
pagina_reposicoes = st.Page("pages/reposicoes.py", title="Reposições", icon="🧵")

pg = st.navigation([pagina_chamados, pagina_reposicoes])
pg.run()
