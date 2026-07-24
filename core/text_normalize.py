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


# Termos de tipo societário e pontuação são a maior fonte de divergência
# entre a grafia digitada na planilha e a razão social oficial ("FACCAO ELLO
# LTDA" vs "FACCAO ELLO LTDA - ME", "CONFECCOES J. S. LTDA" vs "CONFECCOES
# J.S. LTDA"). Removê-los da chave permite reconhecer a mesma empresa sem
# precisar de um alias manual para cada variação.
_RE_TIPO_SOCIETARIO = re.compile(r"\b(?:LTDA|LIMITADA|EIRELI|EPP|MEI|ME|SA|S/A)\b\.?")


def normalize_company_key(text: str) -> str:
    """
    Chave de comparação mais tolerante que normalize_text_key: além de
    remover acento/maiúscula, descarta o tipo societário e toda a
    pontuação, e trata "&" como "E".

    Ex.: "B & N SILVA CONFECCOES LTDA" e "B&N SILVA CONFECCOES LTDA"
    viram ambos "B E N SILVA CONFECCOES".

    Só deve ser usada para casar contra uma lista fechada de nomes
    oficiais — nunca para agrupar nomes livres entre si, já que empresas
    diferentes podem colidir (o chamador é responsável por verificar
    colisões dentro da sua lista).
    """
    key = normalize_text_key(text).replace("&", " E ")
    key = _RE_TIPO_SOCIETARIO.sub(" ", key)
    key = re.sub(r"[^A-Z0-9 ]+", " ", key)
    return re.sub(r"\s+", " ", key).strip()


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
