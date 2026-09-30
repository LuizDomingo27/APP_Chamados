"""Padronização de partes e quantidades, preservando os textos originais."""
import re

import pandas as pd

from core.config import COL_PARTE_PECA, COL_QUANTIDADE_REPOSICAO
from core.text_normalize import clean_text, normalize_text_key

_PARTES = {
    "LINHA": "Linhas", "LINHAS": "Linhas",
    "FIO": "Fios", "FIOS": "Fios",
    "ETIQUETA COMPOSICAO": "Etiqueta de Composição",
    "ETIQUETA DE COMPOSICAO": "Etiqueta de Composição",
    "ETIQUETA DE PRECO": "Etiqueta de Preço",
    "ETIQUETA DE COS": "Etiqueta de Cós",
}
_UNIDADES = {
    "CONE": "cones", "CONES": "cones", "ROLO": "rolos", "ROLOS": "rolos",
    "PAR": "pares", "PARES": "pares", "PECA": "peças", "PECAS": "peças",
    "UN": "unidades", "UNIDADE": "unidades", "UNIDADES": "unidades",
    "METRO": "metros", "METROS": "metros", "M": "metros",
    "KG": "kg", "QUILO": "kg", "QUILOS": "kg",
}


def parse_quantidade(value: object) -> tuple[float | None, str | None]:
    """Converte só um valor simples; distribuições e unidades mistas ficam no original."""
    text = clean_text(value)
    match = re.fullmatch(r"(\d+(?:[.,]\d+)*)(?:\s+([A-Za-zÀ-ÿ]+))?", text)
    if not match:
        return None, None
    number, unit = match.groups()
    unidade = _UNIDADES.get(normalize_text_key(unit or "")) if unit else "Não informada"
    if unidade is None:
        return None, None
    # Formato brasileiro: 1.000 ou 1.000,5. Ponto único fora do agrupamento
    # de milhares é aceito como separador decimal.
    if "," in number:
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+),\d+", number):
            return None, None
        number = number.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", number):
        number = number.replace(".", "")
    elif number.count(".") > 1:
        return None, None
    return float(number), unidade


def normalize_reposicao_formats(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Parte da Peça Original"] = out[COL_PARTE_PECA]
    parts = out[COL_PARTE_PECA].map(clean_text)
    keys = parts.map(normalize_text_key)
    # Grafia mais frequente para variações apenas de caixa/acento/espaços.
    canonical = parts.groupby(keys).agg(lambda s: s.value_counts().index[0]).to_dict()
    out[COL_PARTE_PECA] = keys.map(lambda k: _PARTES.get(k, canonical.get(k) or "Não informado"))
    parsed = out[COL_QUANTIDADE_REPOSICAO].map(parse_quantidade)
    out["Quantidade Numérica"] = pd.array([v[0] for v in parsed], dtype="Float64")
    out["Unidade da Quantidade"] = pd.array([v[1] for v in parsed], dtype="string")
    return out
