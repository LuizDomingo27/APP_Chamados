"""
core/utils.py

Funções utilitárias reaproveitáveis em todo o app. Sem regra de negócio
específica de chamados aqui — apenas helpers genéricos de formatação
(número, data) e de cor. Não importa streamlit: quem desenha é ui/.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from core.config import DATE_FORMAT_BR


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


# ---------------------------------------------------------------------------
# Cor
# ---------------------------------------------------------------------------
_FALLBACK_HEX = "#2AE5C8"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """
    Converte "#RRGGBB" (ou "#RGB") na tripla RGB.

    Cor malformada NÃO levanta exceção: cai no teal primário. As cores
    entram na UI por interpolação de string (CSS e opções de gráfico), onde
    um ValueError derrubaria a tela inteira por causa de um token com erro
    de digitação — desproporcional para um detalhe estético, que aliás fica
    visível na tela quando o fallback entra.
    """
    texto = str(color or "").strip().lstrip("#")
    if len(texto) == 3:
        texto = "".join(ch * 2 for ch in texto)
    if len(texto) != 6:
        texto = _FALLBACK_HEX.lstrip("#")
    try:
        return int(texto[0:2], 16), int(texto[2:4], 16), int(texto[4:6], 16)
    except ValueError:
        base = _FALLBACK_HEX.lstrip("#")
        return int(base[0:2], 16), int(base[2:4], 16), int(base[4:6], 16)


def rgba(color: str, alpha: float) -> str:
    """Monta "rgba(r,g,b,a)" a partir de um hex da paleta. `alpha` fora da
    faixa 0-1 é limitado, em vez de gerar um CSS inválido."""
    r, g, b = hex_to_rgb(color)
    try:
        a = float(alpha)
    except (TypeError, ValueError):
        a = 1.0
    a = max(0.0, min(1.0, a))
    return f"rgba({r}, {g}, {b}, {a:g})"
