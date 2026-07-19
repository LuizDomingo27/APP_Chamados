"""
core/utils.py

Funções utilitárias reaproveitáveis em todo o app. Sem regra de negócio
específica de chamados aqui — apenas helpers genéricos de UI/formatação,
seguindo o mesmo padrão usado nos outros apps (select_all_popover etc).
"""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
import streamlit as st

from core.config import DATE_FORMAT_BR


def select_all_popover(
    label: str,
    options: Sequence[str],
    key: str,
    icon: str = "🔎",
) -> list[str]:
    """
    Renderiza um popover com multiselect + atalhos "Selecionar todos" /
    "Limpar". Mantém o estado em st.session_state para persistir a escolha
    entre reruns, evitando o "poluído" visual do multiselect padrão.

    Retorna a lista de valores selecionados.
    """
    state_key = f"_select_all_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = list(options)

    # Remove da seleção qualquer valor que não exista mais nas opções atuais
    st.session_state[state_key] = [
        v for v in st.session_state[state_key] if v in options
    ]

    selected = st.session_state[state_key]
    total = len(options)
    qtd = len(selected)

    button_label = (
        f"{icon} {label}: Todas ({total})"
        if qtd == total
        else f"{icon} {label}: {qtd}/{total}"
    )

    with st.popover(button_label, use_container_width=True):
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Selecionar todos", key=f"{key}_all", width="stretch"):
                st.session_state[state_key] = list(options)
                st.rerun()
        with col_b:
            if st.button("Limpar", key=f"{key}_clear", width="stretch"):
                st.session_state[state_key] = []
                st.rerun()

        chosen = st.multiselect(
            "Buscar / refinar",
            options=options,
            default=st.session_state[state_key],
            key=f"{key}_multiselect",
            label_visibility="collapsed",
        )
        st.session_state[state_key] = chosen

    return st.session_state[state_key]


def format_date_br(value) -> str:
    """Formata um valor de data (Timestamp/NaT/str) para DD/MM/AAAA."""
    if pd.isna(value):
        return "—"
    return pd.Timestamp(value).strftime(DATE_FORMAT_BR)


def format_int(value) -> str:
    """Formata inteiro com separador de milhar no padrão BR (ponto)."""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def format_decimal(value, casas: int = 1) -> str:
    """Formata número com separador BR (milhar com ponto, decimal com
    vírgula) — usado nas médias, que raramente são inteiras."""
    try:
        texto = f"{float(value):,.{casas}f}"
    except (TypeError, ValueError):
        return "0,0"
    # Troca em duas etapas para os separadores não colidirem entre si.
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def safe_unique_sorted(values: Iterable) -> list[str]:
    """Retorna valores únicos, não nulos, ordenados — para popular filtros."""
    series = pd.Series(list(values)).dropna()
    return sorted(series.astype(str).unique().tolist())
