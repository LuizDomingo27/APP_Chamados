"""
services/planilhas.py

Transforma os bytes de cada planilha na base usada pelo app. As páginas e a
exportação passam por aqui, para o Excel exportado nunca divergir da tela
(mesmas oficinas descartadas, mesmas grafias padronizadas).
"""

from __future__ import annotations

import io

import pandas as pd

from services.data_format_service import normalize_reposicao_formats
from services.data_loader import load_dados_consolidados
from services.material_service import enrich_com_materia_prima
from services.parser_service import enrich_with_parsed_fields
from services.reposicao_parser_service import enrich_with_parsed_fields_reposicao


def carregar_chamados(file_bytes: bytes) -> pd.DataFrame:
    return enrich_with_parsed_fields(load_dados_consolidados(io.BytesIO(file_bytes)))


def carregar_reposicoes(file_bytes: bytes) -> pd.DataFrame:
    df = load_dados_consolidados(io.BytesIO(file_bytes))
    df = enrich_with_parsed_fields_reposicao(df)
    # A linha de matéria-prima depende de "Parte da peça" já extraída pelo
    # parser, então entra por último no pipeline.
    return normalize_reposicao_formats(enrich_com_materia_prima(df))
