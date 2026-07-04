"""
core/config.py

Configurações e constantes globais do app APP_PPCHAMADO.
Centraliza nomes de colunas/abas da planilha, paleta de cores do tema
e parâmetros que podem precisar de ajuste futuro — evita "números/strings
mágicos" espalhados pelas camadas de serviço e UI.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Planilha de origem
# ---------------------------------------------------------------------------
SHEET_DADOS = "Dados Consolidados"
SHEET_BUCKETS = "Buckets"
SHEET_USUARIOS = "Usuários"

COL_ID = "Identificação da tarefa"
COL_NOME_TAREFA = "Nome da tarefa"
COL_CATEGORIA = "Categoria"
COL_STATUS = "Status"
COL_PRIORIDADE = "Prioridade"
COL_ATRIBUIDO_A = "Atribuído a"
COL_CRIADO_POR = "Criado por"
COL_CRIADO_EM = "Criado em"
COL_DATA_CONCLUSAO = "Data de conclusão"
COL_DATA_INICIO = "Data de início"
COL_ATRASADOS = "Atrasados"
COL_CONCLUIDO_EM = "Concluído em"
COL_CONCLUIDA_POR = "Concluída por"
COL_ROTULOS = "Rótulos"
COL_NOTAS = "Notas"

# Colunas derivadas (criadas pelo parser_service)
COL_NUM_CHAMADO = "Número do Chamado"
COL_OFICINA = "Oficina"
COL_SOLICITACAO = "Tipo de Solicitação"

# Colunas derivadas específicas do módulo de Reposições (criadas pelo
# reposicao_parser_service e reposicao_kpi_service)
COL_NUM_REPOSICAO = "Número da Reposição"
COL_ORDEM_PRODUCAO = "Ordem de Produção"
COL_PARTE_PECA = "Parte da Peça"
COL_MOTIVO = "Motivo"
COL_QUANTIDADE_REPOSICAO = "Quantidade Solicitada"
COL_DIAS_ABERTO = "Dias em Aberto"
COL_TEMPO_ATENDIMENTO_DIAS = "Tempo de Atendimento (dias)"

# ---------------------------------------------------------------------------
# Domínio / regras de negócio
# ---------------------------------------------------------------------------
STATUS_CONCLUIDA = "Concluída"
STATUS_NAO_INICIADO = "Não iniciado"
STATUS_EM_ANDAMENTO = "Em andamento"

STATUS_ORDER = [STATUS_NAO_INICIADO, STATUS_EM_ANDAMENTO, STATUS_CONCLUIDA]

# Ordem de severidade da prioridade (1 = mais urgente)
PRIORIDADE_RANK = {
    "Urgente": 1,
    "Importante": 2,
    "Média": 3,
}
DATE_FORMAT_BR = "%d/%m/%Y"

# ---------------------------------------------------------------------------
# Paleta — tema dark moderno (fundo navy profundo, acentos teal + roxo),
# inspirado no dashboard de referência: superfícies escuras, verde-ciano
# neon como cor primária e roxo como acento secundário.
# ---------------------------------------------------------------------------
PALETTE = {
    "bg": "#0E1420",
    "surface": "#171F30",
    "surface_alt": "#1E2740",
    "text": "#EAF0F7",
    "text_muted": "#8A97AD",
    "border": "#2A3450",
    "neon": "#2DD4BF",
    "neon_soft": "#5EEAD4",
    "neon_glow": "rgba(45, 212, 191, 0.30)",
    "purple": "#8B5CF6",
    "purple_soft": "#A78BFA",
    "danger": "#FF6B6B",
    "warning": "#FBBF24",
    "info": "#3B82F6",
    "success": "#2DD4BF",
    "table_header_start": "#0F8A73",
    "table_header_end": "#149E86",
    "table_badge_bg": "#123A34",
    "table_badge_text": "#5EEAD4",
}

# Cores fixas por status/prioridade — usadas nos cards e gráficos para
# manter consistência visual em todo o app.
STATUS_COLORS = {
    STATUS_CONCLUIDA: PALETTE["success"],
    STATUS_NAO_INICIADO: PALETTE["danger"],
    STATUS_EM_ANDAMENTO: PALETTE["warning"],
}

# Quantidade padrão de itens no ranking de oficinas
TOP_N_OFICINAS = 10

# ---------------------------------------------------------------------------
# Padronização manual de oficinas
# ---------------------------------------------------------------------------
# Casos que a normalização automática (acento/maiúscula) não resolve —
# abreviações, nomes incompletos ou razão social divergente da mesma
# empresa. Chave = qualquer grafia encontrada na planilha; valor = nome
# canônico final. As chaves são comparadas via normalize_text_key
# (sem acento, maiúsculo), então não é necessário cobrir variações de
# capitalização/acentuação aqui — só grafias realmente diferentes.
OFICINA_ALIASES_RAW: dict[str, str] = {
    "SOLY BRASIL": "SOLY BRASIL LTDA",
    "SOLY BRASIL LTDA": "SOLY BRASIL LTDA",
    "POEST INDUSTRIA E COM. DO VESTUARIO LTDA": "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "POEST INDUSTRIA COMERCIO VESTUARIO LTDA": "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "SERRANA": "SERRANA TEXTIL LTDA",
    "SERRANA TEXTIL": "SERRANA TEXTIL LTDA",
    "SERRANA TEXTIL LTDA": "SERRANA TEXTIL LTDA",
    "G4 CONFECÇÃO": "G4 CONFECÇÕES",
    "G4 CONFECÇÕES": "G4 CONFECÇÕES",
}

# Nomes de oficina inválidos (dado de teste/lixo) — chamados com esses
# valores são descartados do dashboard.
OFICINA_INVALID_NAMES_RAW: list[str] = [
    "aaaaaa",
]
