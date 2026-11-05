"""
services/kpi_service.py

Toda a lógica de cálculo de indicadores (KPIs) mora aqui. Cada função
resolve UMA necessidade específica do dashboard e devolve estruturas
simples (dict, DataFrame, namedtuple-like) prontas para a camada de UI
consumir — a UI não faz nenhuma conta, só renderiza o que esta camada
devolve.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.config import (
    COL_CRIADO_EM,
    COL_OFICINA,
    COL_SOLICITACAO,
    COL_STATUS,
    STATUS_CONCLUIDA,
    STATUS_EM_ABERTO,
    STATUS_NAO_INICIADO,
    STATUS_ORDER,
)


# ---------------------------------------------------------------------------
# Estruturas de retorno
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ResumoAnalitico:
    """Números da área analítica (pop-up "Visão Analítica").

    Os TOTAIS são do período mais recente presente no recorte filtrado
    (último mês / última semana / último dia com chamados) — por isso cada
    um vem acompanhado do seu rótulo, para a tela deixar explícito de qual
    mês/semana/dia o número está falando.

    As MÉDIAS usam o calendário cheio do recorte (todos os meses/semanas/
    dias entre o primeiro e o último chamado, inclusive os que ficaram sem
    chamado nenhum) — mesma base da linha de média em tendencia_diaria.
    Dividir só pelos períodos que tiveram chamado seria outro indicador e
    inflaria o valor.
    """

    total_geral: int

    total_mes: int
    total_semana: int
    total_dia: int
    label_mes: str
    label_semana: str
    label_dia: str

    media_mes: float
    media_semana: float
    media_dia: float
    qtd_meses: int
    qtd_semanas: int
    qtd_dias: int

    oficina_top_nome: str
    oficina_top_qtd: int
    tipo_top_nome: str
    tipo_top_qtd: int


@dataclass(frozen=True)
class ResumoAtendimento:
    """Totais do relatório exportado. Percentuais em fração (0,125 = 12,5%)."""

    total: int
    atendidos: int
    em_aberto: int
    pct_atendimento: float
    pct_em_aberto: float
    primeiro_dia: pd.Timestamp | None
    ultimo_dia: pd.Timestamp | None


@dataclass(frozen=True)
class Destaques:
    dia_top_data: str
    dia_top_qtd: int
    oficina_top_nome: str
    oficina_top_qtd: int
    solicitacao_top_nome: str
    solicitacao_top_qtd: int


# ---------------------------------------------------------------------------
# Totais gerais
# ---------------------------------------------------------------------------
def total_chamados(df: pd.DataFrame) -> int:
    return int(len(df))


def contagem_por_status(df: pd.DataFrame) -> dict[str, int]:
    """Devolve contagem por status, sempre incluindo as 3 chaves padrão."""
    counts = df[COL_STATUS].value_counts().to_dict()
    return {status: int(counts.get(status, 0)) for status in STATUS_ORDER}


def nao_iniciados_do_dia(df: pd.DataFrame, dia: pd.Timestamp) -> tuple[int, int]:
    """Devolve (não iniciados criados no dia, total de criados no dia) — a
    base do card "Não iniciado" quando nenhum período foi escolhido."""
    criados = df[df[COL_CRIADO_EM].dt.normalize() == pd.Timestamp(dia).normalize()]
    return int((criados[COL_STATUS] == STATUS_NAO_INICIADO).sum()), int(len(criados))


def card_nao_iniciado_do_dia(df: pd.DataFrame, dia: pd.Timestamp) -> dict[str, dict]:
    """Conteúdo do card "Não iniciado" restrito ao dia, no formato de
    `substituicoes` de ui.components.render_status_kpis."""
    qtd, criados = nao_iniciados_do_dia(df, dia)
    pct = qtd / criados * 100 if criados else 0.0
    return {
        STATUS_NAO_INICIADO: {
            "value": qtd,
            "subtitle": f"criados hoje ({dia:%d/%m/%Y})",
            "chip": f"{pct:.0f}% dos criados hoje",
            "progress": pct,
        }
    }


def abertos_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Itens ainda em aberto (Não iniciado + Em andamento) agrupados pelo dia
    de criação, do mais recente para o mais antigo.

    Dias sem nenhum item em aberto simplesmente não aparecem. O status da
    planilha é o de hoje, então a contagem diz quantos itens criados naquele
    dia CONTINUAM em aberto, e não quantos estavam abertos na data."""
    abertos = df[df[COL_STATUS].isin(STATUS_EM_ABERTO)]
    dias = abertos[COL_CRIADO_EM].dropna().dt.normalize()
    out = dias.value_counts().sort_index(ascending=False).reset_index()
    out.columns = ["Data", "Em Aberto"]
    return out


# ---------------------------------------------------------------------------
# Relatório de atendimento (exportação)
# ---------------------------------------------------------------------------
def _marcar_atendimento(df: pd.DataFrame) -> pd.DataFrame:
    """Itens datados, com o dia de criação e a situação atual de cada um."""
    base = df.dropna(subset=[COL_CRIADO_EM])
    return pd.DataFrame(
        {
            "dia": base[COL_CRIADO_EM].dt.normalize(),
            "atendido": base[COL_STATUS] == STATUS_CONCLUIDA,
            "aberto": base[COL_STATUS].isin(STATUS_EM_ABERTO),
        }
    )


def _somar_por_periodo(marcados: pd.DataFrame, chave: pd.Series) -> pd.DataFrame:
    return marcados.groupby(chave).agg(
        total=("dia", "size"), atendidos=("atendido", "sum"), abertos=("aberto", "sum")
    )


def _com_percentuais(out: pd.DataFrame, total: str, atendidos: str, abertos: str) -> pd.DataFrame:
    out["% Atendimento"] = out[atendidos] / out[total]
    out["% Em aberto"] = out[abertos] / out[total]
    return out


def indicadores_diarios(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por dia de criação, em ordem cronológica.

    Todo item pertence ao dia em que foi aberto: "Acumulado em aberto" conta os
    criados naquele dia que continuam abertos hoje, mesma regra de
    abertos_por_dia. Um chamado de 20/09 ainda aberto em 05/10 segue contando
    em 20/09, e não em cada dia que passou.
    """
    colunas = ["Data", "Total do dia", "Atendidos", "Acumulado em aberto", "% Atendimento", "% Em aberto"]
    marcados = _marcar_atendimento(df)
    if marcados.empty:
        return pd.DataFrame(columns=colunas)

    por_dia = _somar_por_periodo(marcados, marcados["dia"])
    out = pd.DataFrame(
        {
            "Data": por_dia.index,
            "Total do dia": por_dia["total"].to_numpy(),
            "Atendidos": por_dia["atendidos"].to_numpy(),
            "Acumulado em aberto": por_dia["abertos"].to_numpy(),
        }
    )
    return _com_percentuais(out, "Total do dia", "Atendidos", "Acumulado em aberto")[colunas]


def indicadores_mensais(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por mês de criação; "Mês" é o primeiro dia do mês, como data."""
    colunas = ["Mês", "Total do mês", "Atendidos", "Em aberto", "% Atendimento", "% Em aberto"]
    marcados = _marcar_atendimento(df)
    if marcados.empty:
        return pd.DataFrame(columns=colunas)

    por_mes = _somar_por_periodo(marcados, marcados["dia"].dt.to_period("M").dt.start_time)
    out = pd.DataFrame(
        {
            "Mês": por_mes.index,
            "Total do mês": por_mes["total"].to_numpy(),
            "Atendidos": por_mes["atendidos"].to_numpy(),
            "Em aberto": por_mes["abertos"].to_numpy(),
        }
    )
    return _com_percentuais(out, "Total do mês", "Atendidos", "Em aberto")[colunas]


def resumo_atendimento(df: pd.DataFrame) -> ResumoAtendimento:
    """Totais gerais: o % em aberto é o peso dos abertos sobre todos os itens."""
    marcados = _marcar_atendimento(df)
    total = len(marcados)
    if not total:
        return ResumoAtendimento(0, 0, 0, 0.0, 0.0, None, None)
    atendidos = int(marcados["atendido"].sum())
    em_aberto = int(marcados["aberto"].sum())
    return ResumoAtendimento(
        total=total,
        atendidos=atendidos,
        em_aberto=em_aberto,
        pct_atendimento=atendidos / total,
        pct_em_aberto=em_aberto / total,
        primeiro_dia=marcados["dia"].min(),
        ultimo_dia=marcados["dia"].max(),
    )


# ---------------------------------------------------------------------------
# Agregações
# ---------------------------------------------------------------------------
def agregado_por_coluna(df: pd.DataFrame, coluna: str, top_n: int | None = None) -> pd.DataFrame:
    """Total de chamados agrupado por uma coluna categórica genérica,
    ordenado decrescente — usado no gráfico de top tipos de solicitação
    (Tipo de Solicitação em Chamados, Motivo em Reposições)."""
    out = (
        df.groupby(coluna, dropna=False)
        .size()
        .reset_index(name="Total de Chamados")
        .sort_values("Total de Chamados", ascending=False)
        .reset_index(drop=True)
    )
    return out.head(top_n) if top_n is not None else out


# ---------------------------------------------------------------------------
# Tendência (série temporal)
# ---------------------------------------------------------------------------
def tendencia_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """
    Série diária de chamados criados, com todos os dias do período
    preenchidos (mesmo com 0 chamados) para o gráfico de linha não ter
    "buracos", e uma coluna com a média do período repetida em todas as
    linhas (linha de referência no gráfico).
    """
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return pd.DataFrame(columns=["Data", "Chamados", "Média do Período"])

    diario = serie.dt.floor("D").value_counts().sort_index()
    full_range = pd.date_range(diario.index.min(), diario.index.max(), freq="D")
    diario = diario.reindex(full_range, fill_value=0)

    media = diario.mean()

    out = diario.reset_index()
    out.columns = ["Data", "Chamados"]
    out["Média do Período"] = round(media, 2)
    return out


def tendencia_semanal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total de itens criados por semana (semana fechando no domingo).
    Formato de saída (['Semana', 'Total de Chamados']) é proposital:
    reaproveita build_categoria_bar_option (ui/charts.py) sem precisar de
    código de gráfico novo. O rótulo é o número ISO da semana (ex.:
    "Sem. 24"), que é como o usuário se refere à semana.
    """
    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return pd.DataFrame(columns=["Semana", "Total de Chamados"])

    inicio_semana = serie.dt.to_period("W-SUN").dt.start_time
    contagem = inicio_semana.value_counts().sort_index()
    out = contagem.reset_index()
    out.columns = ["_inicio_semana", "Total de Chamados"]
    out["Semana"] = "Sem. " + out["_inicio_semana"].dt.isocalendar().week.astype(str)
    return out[["Semana", "Total de Chamados"]]


def tendencia_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Total de itens criados por mês (rótulo 'MM/AAAA')."""
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
# Cards de destaque
# ---------------------------------------------------------------------------
def _valor_mais_frequente(df: pd.DataFrame, coluna: str) -> tuple[str, int]:
    """Devolve (valor mais frequente, quantidade) de uma coluna categórica.
    Coluna ausente ou só com nulos devolve o placeholder ('—', 0)."""
    if coluna not in df.columns:
        return "—", 0
    contagem = df[coluna].value_counts()
    if contagem.empty:
        return "—", 0
    return str(contagem.idxmax()), int(contagem.max())


def calcular_destaques(df: pd.DataFrame) -> Destaques:
    """Calcula os 3 destaques: dia com mais pedidos, oficina e tipo de
    solicitação mais frequentes."""
    if df.empty:
        return Destaques("—", 0, "—", 0, "—", 0)

    # Dia com mais pedidos
    por_dia = df[COL_CRIADO_EM].dropna().dt.floor("D").value_counts()
    if not por_dia.empty:
        dia_top = por_dia.idxmax()
        dia_top_data = dia_top.strftime("%d/%m/%Y")
        dia_top_qtd = int(por_dia.max())
    else:
        dia_top_data, dia_top_qtd = "—", 0

    oficina_top_nome, oficina_top_qtd = _valor_mais_frequente(df, COL_OFICINA)
    solicitacao_top_nome, solicitacao_top_qtd = _valor_mais_frequente(df, COL_SOLICITACAO)

    return Destaques(
        dia_top_data=dia_top_data,
        dia_top_qtd=dia_top_qtd,
        oficina_top_nome=oficina_top_nome,
        oficina_top_qtd=oficina_top_qtd,
        solicitacao_top_nome=solicitacao_top_nome,
        solicitacao_top_qtd=solicitacao_top_qtd,
    )


# ---------------------------------------------------------------------------
# Área analítica (pop-up)
# ---------------------------------------------------------------------------
_RESUMO_VAZIO = ResumoAnalitico(
    total_geral=0,
    total_mes=0,
    total_semana=0,
    total_dia=0,
    label_mes="—",
    label_semana="—",
    label_dia="—",
    media_mes=0.0,
    media_semana=0.0,
    media_dia=0.0,
    qtd_meses=0,
    qtd_semanas=0,
    qtd_dias=0,
    oficina_top_nome="—",
    oficina_top_qtd=0,
    tipo_top_nome="—",
    tipo_top_qtd=0,
)


def calcular_analise(
    df: pd.DataFrame, coluna_tipo: str = COL_SOLICITACAO
) -> ResumoAnalitico:
    """Consolida os números da área analítica a partir do recorte já
    filtrado. Ver ResumoAnalitico para a definição de cada bloco.

    `coluna_tipo` é a coluna que responde "qual o tipo mais frequente":
    "Tipo de Solicitação" em Chamados e "Categoria" em Reposições — mesma
    troca que calcular_destaques_reposicao já faz."""
    if df.empty or COL_CRIADO_EM not in df.columns:
        return _RESUMO_VAZIO

    serie = df[COL_CRIADO_EM].dropna()
    if serie.empty:
        return _RESUMO_VAZIO

    # A base das médias são os chamados datados: um chamado sem "Criado em"
    # não pertence a nenhum mês/semana/dia e distorceria a divisão.
    total_geral = int(len(serie))
    ultimo = serie.max()

    # ---- Totais do período mais recente do recorte ----
    dias = serie.dt.floor("D")
    dia_ref = ultimo.floor("D")
    total_dia = int((dias == dia_ref).sum())

    meses = serie.dt.to_period("M")
    mes_ref = ultimo.to_period("M")
    total_mes = int((meses == mes_ref).sum())

    # Semana fechando no domingo — mesma convenção de tendencia_semanal.
    semanas = serie.dt.to_period("W-SUN")
    semana_ref = ultimo.to_period("W-SUN")
    total_semana = int((semanas == semana_ref).sum())

    # ---- Quantidade de períodos do recorte (calendário cheio) ----
    qtd_dias = int((dia_ref - dias.min()).days) + 1
    qtd_meses = len(pd.period_range(meses.min(), mes_ref, freq="M"))
    qtd_semanas = len(pd.period_range(semanas.min(), semana_ref, freq="W-SUN"))

    oficina_top_nome, oficina_top_qtd = _valor_mais_frequente(df, COL_OFICINA)
    tipo_top_nome, tipo_top_qtd = _valor_mais_frequente(df, coluna_tipo)

    return ResumoAnalitico(
        total_geral=total_geral,
        total_mes=total_mes,
        total_semana=total_semana,
        total_dia=total_dia,
        label_mes=mes_ref.start_time.strftime("%m/%Y"),
        label_semana=f"Sem. {semana_ref.start_time.isocalendar().week}",
        label_dia=dia_ref.strftime("%d/%m/%Y"),
        media_mes=total_geral / qtd_meses,
        media_semana=total_geral / qtd_semanas,
        media_dia=total_geral / qtd_dias,
        qtd_meses=qtd_meses,
        qtd_semanas=qtd_semanas,
        qtd_dias=qtd_dias,
        oficina_top_nome=oficina_top_nome,
        oficina_top_qtd=oficina_top_qtd,
        tipo_top_nome=tipo_top_nome,
        tipo_top_qtd=tipo_top_qtd,
    )


# ---------------------------------------------------------------------------
# Atalho: pendentes (não iniciado + em andamento) — útil para alertas
# ---------------------------------------------------------------------------
def total_pendentes(df: pd.DataFrame) -> int:
    return int(df[COL_STATUS].isin(STATUS_EM_ABERTO).sum())
