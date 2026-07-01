"""
services/data_loader.py

Responsável apenas por ABRIR o arquivo Excel exportado e devolver os
DataFrames brutos já com os tipos de data corretos. Nenhuma regra de
negócio (KPI, filtro, parsing de texto) entra aqui — só leitura e
normalização básica de tipos.
"""

from __future__ import annotations

import io

import pandas as pd

from core.config import (
    COL_CONCLUIDO_EM,
    COL_CRIADO_EM,
    COL_DATA_CONCLUSAO,
    COL_DATA_INICIO,
    SHEET_DADOS,
)

DATE_COLUMNS = [COL_CRIADO_EM, COL_DATA_CONCLUSAO, COL_DATA_INICIO, COL_CONCLUIDO_EM]


def load_dados_consolidados(file: io.BytesIO | str) -> pd.DataFrame:
    """
    Lê a aba "Dados Consolidados" do arquivo "Central de Ajuda.xlsx" e
    devolve um DataFrame com as colunas de data já convertidas para
    datetime nativo (mantém o tipo datetime através do pipeline, conforme
    convenção do projeto — a formatação DD/MM/AAAA só acontece na camada
    de exibição/exportação).
    """
    df = pd.read_excel(file, sheet_name=SHEET_DADOS)

    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def validate_workbook(file: io.BytesIO | str) -> tuple[bool, str]:
    """
    Validação leve antes de processar: confere se a aba esperada existe.
    Retorna (ok, mensagem_de_erro).
    """
    try:
        xls = pd.ExcelFile(file)
    except Exception as exc:  # noqa: BLE001 - queremos a mensagem real pro usuário
        return False, f"Não foi possível abrir o arquivo: {exc}"

    if SHEET_DADOS not in xls.sheet_names:
        return False, (
            f"A aba '{SHEET_DADOS}' não foi encontrada no arquivo. "
            f"Abas disponíveis: {', '.join(xls.sheet_names)}"
        )

    return True, ""
