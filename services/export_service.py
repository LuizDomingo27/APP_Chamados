"""
services/export_service.py

Monta o relatório executivo em Excel: uma aba por módulo, com resumo, tabela
por dia e tabela por mês. Datas, números e percentuais são gravados como
valores nativos do Excel com formato pt-BR, para continuarem somáveis e
filtráveis por quem receber o arquivo. Não conhece Streamlit.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

from core.config import PALETTE
from services.kpi_service import (
    ResumoAtendimento,
    indicadores_diarios,
    indicadores_mensais,
    resumo_atendimento,
)

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# O código de localidade [$-416] mantém a data em português mesmo em um Excel
# configurado em outro idioma. Os separadores de número e de percentual vêm do
# Windows de quem abre o arquivo: em pt-BR, 1.030 e 12,5%.
_FORMATO_DATA = "[$-416]dd/mm/yyyy"
_FORMATO_MES = "[$-416]mmmm/yyyy"
_FORMATO_INTEIRO = "#,##0"
_FORMATO_PERCENTUAL = "0.0%"

_FONTE = "Calibri"
_PRIMARIA = "0F766E"
_TEXTO = PALETTE["text"].lstrip("#")
_APOIO = PALETTE["text_muted"].lstrip("#")
_BORDA = PALETTE["border"].lstrip("#")
_ZEBRA = PALETTE["surface_alt"].lstrip("#")
_FUNDO_TOTAL = "E6F4F1"

_LINHA = Side(style="thin", color=_BORDA)
_CAIXA = Border(left=_LINHA, right=_LINHA, top=_LINHA, bottom=_LINHA)

# (primeira coluna, última coluna) de cada bloco, com a coluna A de margem e a
# coluna H separando as duas tabelas.
_COL_DIA = 2
_COL_MES = 9
_ULTIMA_COL = 14

_LINHA_TITULO = 2
_LINHA_SUBTITULO = 3
_LINHA_CARD_ROTULO = 5
_LINHA_CARD_VALOR = 6
_LINHA_SECAO = 8
_LINHA_CABECALHO = 9

_LARGURAS = {
    "A": 2, "B": 13, "C": 11, "D": 11, "E": 13, "F": 13, "G": 11,
    "H": 3, "I": 17, "J": 10, "K": 11, "L": 11, "M": 13, "N": 11,
}


@dataclass(frozen=True)
class AbaRelatorio:
    """Conteúdo de uma aba: a base já tratada, ou o motivo de não haver base."""

    nome: str
    df: pd.DataFrame | None = None
    arquivo: str = ""
    aviso: str = ""


def _estilizar(
    celula: Cell,
    *,
    negrito: bool = False,
    cor: str = _TEXTO,
    tamanho: int = 10,
    fundo: str | None = None,
    alinhar: str = "center",
    formato: str | None = None,
    borda: bool = False,
) -> None:
    celula.font = Font(name=_FONTE, bold=negrito, color=cor, size=tamanho)
    celula.alignment = Alignment(horizontal=alinhar, vertical="center", wrap_text=True)
    if fundo:
        celula.fill = PatternFill("solid", start_color=fundo, end_color=fundo)
    if formato:
        celula.number_format = formato
    if borda:
        celula.border = _CAIXA


def _mesclar(ws: Worksheet, linha: int, col_ini: int, col_fim: int) -> Cell:
    ws.merge_cells(start_row=linha, start_column=col_ini, end_row=linha, end_column=col_fim)
    return ws.cell(linha, col_ini)


def _preparar_pagina(ws: Worksheet) -> None:
    ws.sheet_view.showGridLines = False
    for coluna, largura in _LARGURAS.items():
        ws.column_dimensions[coluna].width = largura
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.oddFooter.center.text = "Página &P de &N"


def _escrever_titulo(ws: Worksheet, titulo: str, subtitulo: str) -> None:
    ws.row_dimensions[_LINHA_TITULO].height = 34
    for coluna in range(_COL_DIA, _ULTIMA_COL + 1):
        ws.cell(_LINHA_TITULO, coluna).fill = PatternFill(
            "solid", start_color=_PRIMARIA, end_color=_PRIMARIA
        )
    celula = _mesclar(ws, _LINHA_TITULO, _COL_DIA, _ULTIMA_COL)
    celula.value = titulo
    _estilizar(celula, negrito=True, cor="FFFFFF", tamanho=16, alinhar="left", fundo=_PRIMARIA)

    ws.row_dimensions[_LINHA_SUBTITULO].height = 20
    celula = _mesclar(ws, _LINHA_SUBTITULO, _COL_DIA, _ULTIMA_COL)
    celula.value = subtitulo
    _estilizar(celula, cor=_APOIO, alinhar="left")


def _escrever_cards(ws: Worksheet, resumo: ResumoAtendimento) -> None:
    cards = [
        (2, 3, "TOTAL", resumo.total, _FORMATO_INTEIRO),
        (4, 5, "ATENDIDOS", resumo.atendidos, _FORMATO_INTEIRO),
        (6, 7, "EM ABERTO", resumo.em_aberto, _FORMATO_INTEIRO),
        (9, 11, "% ATENDIMENTO (SOBRE O TOTAL)", resumo.pct_atendimento, _FORMATO_PERCENTUAL),
        (12, 14, "% EM ABERTO (SOBRE O TOTAL)", resumo.pct_em_aberto, _FORMATO_PERCENTUAL),
    ]
    ws.row_dimensions[_LINHA_CARD_ROTULO].height = 20
    ws.row_dimensions[_LINHA_CARD_VALOR].height = 32
    for col_ini, col_fim, rotulo, valor, formato in cards:
        for linha in (_LINHA_CARD_ROTULO, _LINHA_CARD_VALOR):
            for coluna in range(col_ini, col_fim + 1):
                ws.cell(linha, coluna).border = _CAIXA
        celula = _mesclar(ws, _LINHA_CARD_ROTULO, col_ini, col_fim)
        celula.value = rotulo
        _estilizar(celula, negrito=True, cor=_APOIO, tamanho=9, fundo=_ZEBRA)
        celula = _mesclar(ws, _LINHA_CARD_VALOR, col_ini, col_fim)
        celula.value = valor
        _estilizar(celula, negrito=True, cor=_PRIMARIA, tamanho=18, formato=formato)


def _valor_excel(valor: object) -> object:
    """Converte para o tipo que o openpyxl grava; sem valor vira célula vazia."""
    if pd.isna(valor):  # type: ignore[call-overload]
        return None
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    return valor.item() if hasattr(valor, "item") else valor


def _escrever_tabela(
    ws: Worksheet,
    col_ini: int,
    titulo: str,
    dados: pd.DataFrame,
    formatos: list[str],
    total: list[object],
) -> None:
    col_fim = col_ini + len(dados.columns) - 1
    celula = _mesclar(ws, _LINHA_SECAO, col_ini, col_fim)
    celula.value = titulo
    _estilizar(celula, negrito=True, cor=_PRIMARIA, tamanho=12, alinhar="left")

    ws.row_dimensions[_LINHA_CABECALHO].height = 32
    for i, nome in enumerate(dados.columns):
        celula = ws.cell(_LINHA_CABECALHO, col_ini + i, nome)
        _estilizar(celula, negrito=True, cor="FFFFFF", fundo=_PRIMARIA, borda=True)

    for n, linha in enumerate(dados.itertuples(index=False)):
        numero_linha = _LINHA_CABECALHO + 1 + n
        fundo = _ZEBRA if n % 2 else None
        for i, valor in enumerate(linha):
            celula = ws.cell(numero_linha, col_ini + i, _valor_excel(valor))
            _estilizar(celula, formato=formatos[i], fundo=fundo, borda=True)

    numero_linha = _LINHA_CABECALHO + 1 + len(dados)
    for i, valor in enumerate(total):
        celula = ws.cell(numero_linha, col_ini + i, valor)
        _estilizar(celula, negrito=True, formato=formatos[i], fundo=_FUNDO_TOTAL, borda=True)


def _escrever_aba(ws: Worksheet, aba: AbaRelatorio, gerado_em: pd.Timestamp) -> None:
    _preparar_pagina(ws)
    titulo = f"Relatório Executivo — {aba.nome}"
    if aba.df is None:
        _escrever_titulo(ws, titulo, aba.aviso)
        return

    resumo = resumo_atendimento(aba.df)
    periodo = (
        f"Período: {resumo.primeiro_dia:%d/%m/%Y} a {resumo.ultimo_dia:%d/%m/%Y}"
        if resumo.total
        else "Sem registros datados"
    )
    _escrever_titulo(
        ws,
        titulo,
        f"{periodo}  ·  Arquivo: {aba.arquivo}  ·  "
        f"Gerado em {gerado_em:%d/%m/%Y às %H:%M}  ·  Base completa, sem filtros de tela",
    )
    _escrever_cards(ws, resumo)

    int_, pct = _FORMATO_INTEIRO, _FORMATO_PERCENTUAL
    _escrever_tabela(
        ws,
        _COL_DIA,
        "Total e acumulado por dia",
        indicadores_diarios(aba.df),
        [_FORMATO_DATA, int_, int_, int_, pct, pct],
        ["Total", resumo.total, resumo.atendidos, resumo.em_aberto,
         resumo.pct_atendimento, resumo.pct_em_aberto],
    )
    _escrever_tabela(
        ws,
        _COL_MES,
        "Total por mês",
        indicadores_mensais(aba.df),
        [_FORMATO_MES, int_, int_, int_, pct, pct],
        ["Total", resumo.total, resumo.atendidos, resumo.em_aberto,
         resumo.pct_atendimento, resumo.pct_em_aberto],
    )

    ws.freeze_panes = ws.cell(_LINHA_CABECALHO + 1, 1)
    ws.print_title_rows = f"{_LINHA_CABECALHO}:{_LINHA_CABECALHO}"


def gerar_relatorio_excel(abas: list[AbaRelatorio], gerado_em: pd.Timestamp) -> bytes:
    """Devolve os bytes do .xlsx, com uma aba para cada item de `abas`."""
    workbook = Workbook()
    workbook.remove(workbook.active)
    for aba in abas:
        _escrever_aba(workbook.create_sheet(aba.nome), aba, gerado_em)
    saida = io.BytesIO()
    workbook.save(saida)
    return saida.getvalue()
