"""
services/material_service.py

Camada de dados do card "materiais mais solicitados" da página de
Reposições. Responde duas perguntas diferentes, que a planilha guarda em
lugares diferentes:

  • LINHA DE MATÉRIA-PRIMA (Jeans, Malha, Pólo, Tear, Básico, Elaborado) —
    não é coluna: vem embutida no texto de "Nome da tarefa" e é extraída
    por core/materia_prima_normalize.py.
  • PARTE DA PEÇA (Traseiro, Viés de reforço, Etiqueta de preço, Linha…) —
    já vem rotulada em Notas e é extraída pelo
    reposicao_parser_service.

As duas viram o MESMO formato de saída (lista de ItemRanking), para o card
da UI não precisar saber de onde o número veio.

Este módulo devolve dados JÁ POSICIONADOS e JÁ COM PERCENTUAL: quem
desenha não faz conta, seguindo a divisão do resto do app.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.config import COL_MATERIA_PRIMA, COL_NOME_TAREFA, COL_PARTE_PECA
from core.materia_prima_normalize import (
    MATERIA_PRIMA_NAO_INFORMADA,
    extrair_materia_prima,
)

# Valor de "não preenchido" usado pelo parser de Reposições. Linhas com
# esse rótulo ficam fora do ranking: um pódio liderado por "Não informado"
# não responde à pergunta "qual material as oficinas mais pedem".
_ROTULOS_IGNORADOS = {MATERIA_PRIMA_NAO_INFORMADA, "Não informado", "—", ""}

TOP_N_MATERIAIS = 3


@dataclass(frozen=True)
class ItemRanking:
    """Uma posição do pódio, pronta para exibição."""

    posicao: int
    rotulo: str
    quantidade: int
    percentual: float


def enrich_com_materia_prima(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona a coluna "Linha de Matéria-Prima" ao DataFrame de Reposições.

    Precisa rodar sobre o DataFrame JÁ ENRIQUECIDO pelo
    reposicao_parser_service, porque a extração usa "Parte da peça" para
    saber onde termina o nome da oficina (ver
    core.materia_prima_normalize.extrair_materia_prima).

    Se "Nome da tarefa" não existir, a coluna é criada preenchida com
    "Não informado" em vez de estourar KeyError: o card fica vazio e o
    resto do dashboard continua funcionando — e o motivo aparece na tela
    como "sem dados", não como stack trace.
    """
    out = df.copy()

    if COL_NOME_TAREFA not in out.columns:
        out[COL_MATERIA_PRIMA] = MATERIA_PRIMA_NAO_INFORMADA
        return out

    partes = (
        out[COL_PARTE_PECA]
        if COL_PARTE_PECA in out.columns
        else pd.Series([None] * len(out), index=out.index)
    )

    out[COL_MATERIA_PRIMA] = [
        extrair_materia_prima(nome, parte)
        for nome, parte in zip(out[COL_NOME_TAREFA], partes)
    ]
    return out


def _ranking(df: pd.DataFrame, coluna: str, top_n: int) -> list[ItemRanking]:
    """
    Conta as ocorrências de `coluna` e devolve as `top_n` maiores como
    pódio, com o percentual sobre o total CONSIDERADO (ou seja, sobre as
    linhas que têm o dado preenchido).

    O percentual usa esse total, e não o total de reposições do recorte,
    porque a leitura do card é "entre as reposições em que sabemos o
    material, tanto % foi deste" — dividir pelo total geral misturaria as
    linhas sem informação e reduziria todos os percentuais sem explicação
    visível.
    """
    if not isinstance(df, pd.DataFrame) or coluna not in df.columns or df.empty:
        return []

    serie = df[coluna].dropna().astype(str).str.strip()
    serie = serie[~serie.isin(_ROTULOS_IGNORADOS)]
    if serie.empty:
        return []

    contagem = serie.value_counts()
    total = int(contagem.sum())

    return [
        ItemRanking(
            posicao=i,
            rotulo=str(rotulo),
            quantidade=int(qtd),
            percentual=round(float(qtd) / total * 100, 1) if total else 0.0,
        )
        for i, (rotulo, qtd) in enumerate(contagem.head(max(1, int(top_n))).items(), start=1)
    ]


def top_materias_primas(df: pd.DataFrame, top_n: int = TOP_N_MATERIAIS) -> list[ItemRanking]:
    """Pódio das linhas de matéria-prima mais solicitadas em reposição.
    Exige que enrich_com_materia_prima já tenha rodado."""
    return _ranking(df, COL_MATERIA_PRIMA, top_n)


def top_partes_peca(df: pd.DataFrame, top_n: int = TOP_N_MATERIAIS) -> list[ItemRanking]:
    """Pódio das partes da peça mais solicitadas em reposição."""
    return _ranking(df, COL_PARTE_PECA, top_n)
