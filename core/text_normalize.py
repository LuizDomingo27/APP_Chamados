"""
core/text_normalize.py

Helper puro (sem dependência de pandas/streamlit) para normalizar texto
para fins de COMPARAÇÃO/AGRUPAMENTO — nunca para exibição. Usado para
detectar que duas grafias diferentes ("ACAUÃ CONFECÇÕES" e
"ACAUA CONFECCOES") se referem ao mesmo registro.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_text_key(text: str) -> str:
    """
    Remove acentos, converte para maiúsculas e colapsa espaços extras.
    Ex.: "  Açaí  Confecções " -> "ACAI CONFECCOES".
    """
    text = str(text or "").strip()
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sem_acento.upper()).strip()


def build_normalized_alias_map(raw_aliases: dict[str, str]) -> dict[str, str]:
    """
    Converte um dicionário {grafia_qualquer: nome_canônico} num dicionário
    cuja chave é a versão normalizada (normalize_text_key) da grafia —
    para permitir lookup independente de acento/maiúscula na hora de
    aplicar o alias.
    """
    return {normalize_text_key(k): v for k, v in raw_aliases.items()}


def build_normalized_key_set(raw_values: list[str]) -> set[str]:
    """Converte uma lista de valores numa chave normalizada para lookup O(1)."""
    return {normalize_text_key(v) for v in raw_values}
