"""
services/reposicao_kpi_service.py

KPIs específicos do módulo de Reposições. As contas que já são
genéricas o suficiente (dependem só dos nomes de coluna de core.config,
sem nada "de chamado" embutido) são reaproveitadas direto de
services.kpi_service: total_chamados, contagem_por_status,
agregado_por_oficina, agregado_por_categoria, ranking_oficinas,
tendencia_diaria, tabela_ordenada_por_prioridade e total_pendentes.

Este módulo cobre o que é específico de Reposições:
- tendência semanal/mensal (o pedido cobre dia/semana/mês, o serviço
  original só tinha tendência diária);
- tempo de atendimento (Concluído em - Criado em);
- ranking de quem mais solicita reposições;
- oficinas com reposição em aberto e há quantos dias esperam;
- destaques (reaproveita o dataclass Destaques, só troca a 3ª métrica
  de "Tipo de Solicitação" para "Categoria", que é o campo equivalente
  na planilha de Reposições).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.config import (
    COL_CATEGORIA,
    COL_CONCLUIDO_EM,
    COL_CRIADO_EM,
    COL_CRIADO_POR,
    COL_DIAS_ABERTO,
    COL_OFICINA,
    COL_STATUS,
    COL_TEMPO_ATENDIMENTO_DIAS,
    STATUS_CONCLUIDA,
    STATUS_EM_ANDAMENTO,
    STATUS_NAO_INICIADO,
)
from services.kpi_service import Destaques


# ---------------------------------------------------------------------------
# Destaques (reaproveita o dataclass Destaques do módulo de Chamados)
# ---------------------------------------------------------------------------
def calcular_destaques_reposicao(df: pd.DataFrame) -> Destaques:
    """Calcula os 3 destaques do período: dia com mais solicitações,
    oficina com mais solicitações e categoria mais comum."""
    if df.empty:
        return Destaques("—", 0, "—", 0, "—", 0)

    por_dia = df[COL_CRIADO_EM].dropna().dt.floor("D").value_counts()
    if not por_dia.empty:
        dia_top = por_dia.idxmax()
        dia_top_data = dia_top.strftime("%d/%m/%Y")
        dia_top_qtd = int(por_dia.max())
    else:
        dia_top_data, dia_top_qtd = "—", 0

    por_oficina = df[COL_OFICINA].value_counts()
    if not por_oficina.empty:
        oficina_top_nome = str(por_oficina.idxmax())
        oficina_top_qtd = int(por_oficina.max())
    else:
        oficina_top_nome, oficina_top_qtd = "—", 0

    por_categoria = df[COL_CATEGORIA].value_counts()
    if not por_categoria.empty:
        categoria_top_nome = str(por_categoria.idxmax())
        categoria_top_qtd = int(por_categoria.max())
    else:
        categoria_top_nome, categoria_top_qtd = "—", 0

    return Destaques(
        dia_top_data=dia_top_data,
        dia_top_qtd=dia_top_qtd,
        oficina_top_nome=oficina_top_nome,
        oficina_top_qtd=oficina_top_qtd,
        solicitacao_top_nome=categoria_top_nome,
        solicitacao_top_qtd=categoria_top_qtd,
    )


# ---------------------------------------------------------------------------
# Tendências semanal / mensal
# ---------------------------------------------------------------------------
def tendencia_semanal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total de reposições solicitadas por semana (semana fechando no
    domingo). Formato de saída (['Semana', 'Total de Chamados']) é
    proposital: reaproveita build_categoria_bar_option (ui/charts.py)
    sem precisar de nenhum código de gráfico novo.
    """
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return pd.DataFrame(columns=["Semana", "Total de Chamados"])

    inicio_semana = serie.dt.to_period("W-SUN").dt.start_time
    contagem = inicio_semana.value_counts().sort_index()
    out = contagem.reset_index()
    out.columns = ["_inicio_semana", "Total de Chamados"]
    # Rótulo = número ISO da semana (ex.: "Sem. 24"), não a data de início —
    # é o identificador que o usuário usa para se referir à semana.
    out["Semana"] = "Sem. " + out["_inicio_semana"].dt.isocalendar().week.astype(str)
    return out[["Semana", "Total de Chamados"]]


def tendencia_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Total de reposições solicitadas por mês."""
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return pd.DataFrame(columns=["Mês", "Total de Chamados"])

    inicio_mes = serie.dt.to_period("M").dt.start_time
    contagem = inicio_mes.value_counts().sort_index()
    out = contagem.reset_index()
    out.columns = ["_inicio_mes", "Total de Chamados"]
    out["Mês"] = out["_inicio_mes"].dt.strftime("%m/%Y")
    return out[["Mês", "Total de Chamados"]]


# ---------------------------------------------------------------------------
# Quem mais solicita
# ---------------------------------------------------------------------------
def ranking_solicitantes(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Ranking de quem mais solicita reposições (coluna 'Criado por')."""
    out = (
        df.groupby(COL_CRIADO_POR, dropna=False)
        .size()
        .reset_index(name="Total de Chamados")
        .sort_values("Total de Chamados", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return out


# ---------------------------------------------------------------------------
# Tempo de atendimento
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TempoAtendimento:
    media_dias: float
    mediana_dias: float
    min_dias: float
    max_dias: float
    qtd_amostras: int


def tempo_atendimento_stats(df: pd.DataFrame) -> TempoAtendimento:
    """
    Estatísticas de tempo de atendimento (Concluído em - Criado em), em
    dias, considerando só reposições já concluídas com as duas datas
    preenchidas.
    """
    concluidas = df[df[COL_STATUS] == STATUS_CONCLUIDA].copy()
    concluidas = concluidas.dropna(subset=[COL_CRIADO_EM, COL_CONCLUIDO_EM])
    if concluidas.empty:
        return TempoAtendimento(0.0, 0.0, 0.0, 0.0, 0)

    dias = (concluidas[COL_CONCLUIDO_EM] - concluidas[COL_CRIADO_EM]).dt.total_seconds() / 86400
    dias = dias.clip(lower=0)

    return TempoAtendimento(
        media_dias=round(float(dias.mean()), 1),
        mediana_dias=round(float(dias.median()), 1),
        min_dias=round(float(dias.min()), 1),
        max_dias=round(float(dias.max()), 1),
        qtd_amostras=int(len(dias)),
    )


def enrich_com_indicadores_temporais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona duas colunas de apoio para a tabela detalhada — cada linha
    preenche só uma delas, conforme seu status:
    - 'Dias em Aberto': para reposições pendentes (Não iniciado / Em
      andamento), quantos dias se passaram desde a solicitação até hoje.
    - 'Tempo de Atendimento (dias)': para reposições concluídas, quantos
      dias entre a solicitação (Criado em) e a conclusão (Concluído em).
    """
    out = df.copy()
    agora = pd.Timestamp.now().normalize()

    pendente_mask = out[COL_STATUS].isin([STATUS_NAO_INICIADO, STATUS_EM_ANDAMENTO])
    concluida_mask = out[COL_STATUS] == STATUS_CONCLUIDA

    dias_aberto = (agora - out[COL_CRIADO_EM]).dt.days
    out[COL_DIAS_ABERTO] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[pendente_mask, COL_DIAS_ABERTO] = dias_aberto[pendente_mask].astype("Int64")

    tempo_atendimento = (out[COL_CONCLUIDO_EM] - out[COL_CRIADO_EM]).dt.total_seconds() / 86400
    out[COL_TEMPO_ATENDIMENTO_DIAS] = pd.NA
    out.loc[concluida_mask, COL_TEMPO_ATENDIMENTO_DIAS] = tempo_atendimento[concluida_mask].round(1)

    return out


# ---------------------------------------------------------------------------
# Oficinas com reposição em aberto
# ---------------------------------------------------------------------------
def oficinas_com_reposicao_pendente(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada oficina com reposições pendentes (Não iniciado / Em
    andamento), calcula a quantidade pendente, a data da solicitação
    mais antiga e há quantos dias ela está em aberto — para priorizar o
    atendimento de quem espera há mais tempo.
    """
    colunas_saida = [COL_OFICINA, "Qtd. Pendente", "Solicitação Mais Antiga", "Dias em Aberto"]
    pendentes = df[df[COL_STATUS].isin([STATUS_NAO_INICIADO, STATUS_EM_ANDAMENTO])].copy()
    if pendentes.empty:
        return pd.DataFrame(columns=colunas_saida)

    agora = pd.Timestamp.now().normalize()
    agrupado = (
        pendentes.groupby(COL_OFICINA, dropna=False)[COL_CRIADO_EM]
        .agg(["count", "min"])
        .reset_index()
    )
    agrupado.columns = [COL_OFICINA, "Qtd. Pendente", "Solicitação Mais Antiga"]
    agrupado["Dias em Aberto"] = (agora - agrupado["Solicitação Mais Antiga"]).dt.days
    agrupado = agrupado.sort_values("Dias em Aberto", ascending=False).reset_index(drop=True)
    return agrupado[colunas_saida]
