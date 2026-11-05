"""
ui/exportacao.py

Botão único "Exportar para Excel", o mesmo nas duas páginas. Cada página guarda
a própria planilha, então o botão busca as duas fontes: primeiro na sessão,
depois no cache em disco.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import streamlit as st

from core.config import (
    ESTADO_BYTES_CHAMADOS,
    ESTADO_BYTES_REPOSICOES,
    ESTADO_NOME_CHAMADOS,
    ESTADO_NOME_REPOSICOES,
    SLOT_CHAMADOS,
    SLOT_REPOSICOES,
)
from core.utils import agora_local
from services.export_service import MIME_XLSX, AbaRelatorio, gerar_relatorio_excel
from services.planilhas import carregar_chamados, carregar_reposicoes
from services.upload_cache import load_upload

_FONTES: list[tuple[str, str, str, str, Callable[[bytes], pd.DataFrame]]] = [
    ("Chamados", ESTADO_BYTES_CHAMADOS, ESTADO_NOME_CHAMADOS, SLOT_CHAMADOS, carregar_chamados),
    ("Reposição", ESTADO_BYTES_REPOSICOES, ESTADO_NOME_REPOSICOES, SLOT_REPOSICOES, carregar_reposicoes),
]


def _localizar_arquivos() -> dict[str, tuple[bytes, str] | None]:
    arquivos: dict[str, tuple[bytes, str] | None] = {}
    for aba, chave_bytes, chave_nome, slot, _ in _FONTES:
        conteudo = st.session_state.get(chave_bytes)
        if conteudo is not None:
            arquivos[aba] = (conteudo, st.session_state.get(chave_nome) or "—")
        else:
            arquivos[aba] = load_upload(slot)
    return arquivos


def _montar_abas(arquivos: dict[str, tuple[bytes, str] | None]) -> list[AbaRelatorio]:
    abas = []
    for aba, _, _, _, carregar in _FONTES:
        arquivo = arquivos[aba]
        if arquivo is None:
            abas.append(AbaRelatorio(aba, aviso=f"A planilha de {aba} não foi carregada no app."))
            continue
        try:
            abas.append(AbaRelatorio(aba, df=carregar(arquivo[0]), arquivo=arquivo[1]))
        except Exception as exc:  # noqa: BLE001 - uma planilha ruim não derruba a outra aba
            abas.append(AbaRelatorio(aba, aviso=f"Não foi possível processar a planilha de {aba}: {exc}"))
    return abas


def render_botao_exportacao() -> None:
    arquivos = _localizar_arquivos()
    # O arquivo só é gerado no clique: ler as duas planilhas a cada interação
    # deixaria as páginas lentas sem ninguém ter pedido a exportação.
    st.download_button(
        "Exportar para Excel",
        data=lambda: gerar_relatorio_excel(_montar_abas(arquivos), agora_local()),
        file_name=f"Relatorio_Chamados_Reposicao_{agora_local():%d-%m-%Y}.xlsx",
        mime=MIME_XLSX,
        width="stretch",
        on_click="ignore",
        help="Gera um único Excel com as abas Chamados e Reposição, sobre a base completa de cada planilha",
    )
    faltando = [aba for aba, arquivo in arquivos.items() if arquivo is None]
    if faltando:
        st.caption(f"Planilha de {' e '.join(faltando)} não carregada: essa aba sairá sem dados.")
