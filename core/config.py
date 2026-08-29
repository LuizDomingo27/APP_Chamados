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

# Dicionário de dados da aba "Dados Consolidados": UMA constante por coluna
# da planilha, inclusive as que nenhuma tela usa hoje. Não é código morto —
# é o contrato com o arquivo de origem, e o que impede que a próxima coluna
# consumida entre no código como string mágica.
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
# Linha de matéria-prima da ordem (Jeans, Malha, Pólo, Tear, Básico,
# Elaborado). Derivada por services/material_service.py a partir do texto
# de "Nome da tarefa" — ver core/materia_prima_normalize.py.
COL_MATERIA_PRIMA = "Linha de Matéria-Prima"

# ---------------------------------------------------------------------------
# Domínio / regras de negócio
# ---------------------------------------------------------------------------
STATUS_CONCLUIDA = "Concluída"
STATUS_NAO_INICIADO = "Não iniciado"
STATUS_EM_ANDAMENTO = "Em andamento"

STATUS_ORDER = [STATUS_NAO_INICIADO, STATUS_EM_ANDAMENTO, STATUS_CONCLUIDA]

DATE_FORMAT_BR = "%d/%m/%Y"

# ---------------------------------------------------------------------------
# Paleta — tema "Clean Light": fundo cinza muito claro, superfícies brancas,
# texto azul-marinho e acentos semânticos discretos. A hierarquia visual vem
# de espaço, tipografia, hairlines e pequenas áreas de cor — nunca de fundos
# escuros, neon ou degradês decorativos.
# ---------------------------------------------------------------------------
PALETTE = {
    # Superfícies
    "bg": "#F5F7FA",
    "bg_deep": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "surface_inset": "#F1F5F9",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    # Texto
    "text": "#071A36",
    "text_muted": "#5F7694",
    "text_dim": "#94A3B8",
    # Acentos
    "neon": "#0F9F8F",
    "neon_glow": "rgba(15, 159, 143, 0.16)",
    "lime": "#10B981",
    "amber": "#F59E0B",
    "pink": "#FF3B5C",
    "slate": "#334155",
    # Aliases semânticos (o que a UI consome por significado, não por cor)
    "danger": "#FF3B5C",
    "warning": "#F59E0B",
    "success": "#10B981",
    # Tabela
    "table_header_start": "#F1F5F9",
    "table_header_end": "#F1F5F9",
    "table_badge_bg": "rgba(15, 159, 143, 0.10)",
    "table_badge_text": "#0F766E",
}

# Cores fixas por status/prioridade — usadas nos cards e gráficos para
# manter consistência visual em todo o app.
STATUS_COLORS = {
    STATUS_CONCLUIDA: PALETTE["success"],
    STATUS_NAO_INICIADO: PALETTE["danger"],
    STATUS_EM_ANDAMENTO: PALETTE["warning"],
}

# Ordem de cores para séries categóricas (fatias de rosca, grupos de
# cards). Segue a referência: teal → lime → amber → slate, com o slate
# fechando a série como "outros/neutro".
SERIES_COLORS = [
    PALETTE["neon"],
    PALETTE["lime"],
    PALETTE["amber"],
    PALETTE["slate"],
]

# Quantidade padrão de itens no gráfico de top tipos de solicitação
TOP_N_SOLICITACOES = 7

# ---------------------------------------------------------------------------
# Padronização manual de oficinas
# ---------------------------------------------------------------------------
# Casos que a normalização automática (acento/maiúscula) não resolve —
# abreviações, nomes incompletos ou razão social divergente da mesma
# empresa. Chave = qualquer grafia encontrada na planilha; valor = nome
# canônico final. As chaves são comparadas via normalize_text_key
# (sem acento, maiúsculo), então não é necessário cobrir variações de
# capitalização/acentuação aqui — só grafias realmente diferentes.
#
# A tabela é COMPARTILHADA por Chamados e Reposições: as duas planilhas são
# preenchidas pelas mesmas pessoas e repetem as mesmas abreviações, então
# separar os apelidos por módulo só fazia a mesma oficina aparecer com um
# nome em cada dashboard.
OFICINA_ALIASES_RAW: dict[str, str] = {
    "SOLY BRASIL": "SOLY BRASIL LTDA",
    "SOLY BRASIL LTDA": "SOLY BRASIL LTDA",
    "POEST INDUSTRIA E COM. DO VESTUARIO LTDA": "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "POEST INDUSTRIA COMERCIO VESTUARIO LTDA": "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "POEST INDUSTRIA E COMERCIO DE VESTUARIO LTDA": "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "SERRANA": "SERRANA TEXTIL LTDA",
    "SERRANA TEXTIL": "SERRANA TEXTIL LTDA",
    "SERRANA TEXTIL LTDA": "SERRANA TEXTIL LTDA",
    "G4 CONFECÇÃO": "G4 CONFECÇÕES",
    "G4 CONFECÇÕES": "G4 CONFECÇÕES",
    # Razão social divergente da cadastrada
    "CONFECCAO G. B. DA SILVA JUNIOR & CIA LTDA": "CONFECCAO G. B. DA S. JUNIOR & CIA LTDA",
    "CONFECÇÃO GB DA SILVA": "CONFECCAO G. B. DA S. JUNIOR & CIA LTDA",
    "CONFECÇÕES GB DA SILVA": "CONFECCAO G. B. DA S. JUNIOR & CIA LTDA",
    "FLAVIA GEORGIA BRAGA SILVA CONFECCOES LTDA": "FLAVIA GEORGIA B SILVA CONFECCOES EIRELI",
    "FLAVIA GEORGIA BRAGA SILVA - ME": "FLAVIA GEORGIA B SILVA CONFECCOES EIRELI",
    "CONFECCOES FRANOELDA MAGNEUDA DE MEDEIROS ARAUJO LTDA": (
        "CONFECCOES FRANOELDA M. M. ARAUJO EIRELI"
    ),
    "CONFECÇÕES FRANOELDA MAGNEUDA DE MEDEIROS ARAÚJO EIRELI": (
        "CONFECCOES FRANOELDA M. M. ARAUJO EIRELI"
    ),
    "LINEA INDUSTRIA, COMERCIO & SERVICOS DE CONFECCOES LTDA": (
        "LINEA IND. COM. SER. CONFECCOES LTDA"
    ),
    "LINEA IND., COM. & S. DE CONFECCOES LTDA": "LINEA IND. COM. SER. CONFECCOES LTDA",
    "CABUGI IND. E COM. DE CONFECCOES LTDA": "CABUGI CONFECCOES LTDA.",
    "M A P FORTE FORTEX PRODUCAO TEXTIL": "FORTE FORTEX PRODUÇÃO TEXTIL",
    "P A VITURINO SERVIÇOES E CONFECÇÕES LTDA": "P A VITURINO SERVIÇOS E CONFECÇÕES LTDA",
    "JOLI TEXTIL SERVICOS E COMERCIO LTD": "JOLI TEXTIL SERVICOS E COMERCIO LTDA",
    "ARAUJO CAMARA LTDA": "ARAUJO & CAMARA LTDA",
    "IVANILDO JOSE DE SOUZA": "IVANILDO JOSE DE SOUSA - ME",
    "F&K CONFECÇÕES": "F & K FACCAO LTDA",
    "JF CONFECÇÕES LTDA": "J F CONFECCOES LTDA",
    "MK INDUSTRIA TÊXTIL LTDA": "M K INDUSTRIA TEXTIL LTDA",
    # Nome incompleto / apelido usado no dia a dia
    "GENESIS": "CONFECCOES GENESIS LTDA ME",
    "CONFECÇÃO GENESIS LTDA ME": "CONFECCOES GENESIS LTDA ME",
    "JOSENI": "JOSENI MARIA DE MEDEIROS",
    "JOSENI MARIA": "JOSENI MARIA DE MEDEIROS",
    "JOSÉ MEDEIROS": "JOSE MEDEIROS DE ARAUJO",
    "EVALBER CASTRO": "EVALBER DE CASTRO DANTAS ME",
    "FORTE FORTEX": "FORTE FORTEX PRODUÇÃO TEXTIL",
    "FORTEX": "FORTE FORTEX PRODUÇÃO TEXTIL",
    "PEDRO E ODAIR": "PEDRO E ODAIR CONFECÇÕES LTDA",
    "LEANDRO MATIAS": "LEANDRO MATIAS DA SILVA - ME",
    "EBENEZER INDUSTRIA": "EBENEZER INDUSTRIA TEXTIL LTDA",
    "DANTAS E PAULINO": "DANTAS E PAULINO CONFECCOES LTDA",
    "MAXWELA ARAUJO": "MAXWELA ARAÚJO SILVA LTDA",
    "VITALIZE": "VITALIZE CONFECCOES LTDA",
    "ACAUÃ": "ACAUÃ CONFECÇÕES LTDA",
    "AJG": "AJG CONFECÇÕES LTDA",
    "ARAUJO E M": "ARAUJO E M CONFECCOES EIRELI",
    "AMORIM E PEDRO": "AMORIM & PEDRO CONFECCOES LTDA - ME",
    "DONA TICA CONFECÇÕES": "DONA TICA CONFECCOES MATRIZ",
    "NS CONSTANTINO": "N S CONSTANTINO",
    "AS CONFECÇÕES LTDA": "A S CONFECCOES LTDA",
    "JS & SILVA LTDA": "J. S. & SILVA LTDA",
    "FENIX INDUSTRIA": "FENIX INDUSTRIA TÊXTIL LTDA",
    "FERREIRA ARAUJO": "FERREIRA E ARAUJO CONFECCOES LTDA",
    "JOLI TÊXTIL": "JOLI TEXTIL SERVICOS E COMERCIO LTDA",
    # Unidade (matriz/filial) escrita de forma abreviada
    "F&L AZEVEDO MATRIZ": "F & L AZEVEDO CONFECCAO LTDA - ME MATRIZ",
    "F E L MATRIZ": "F & L AZEVEDO CONFECCAO LTDA - ME MATRIZ",
    "FEL AZEVEDO CONFECÇÃO": "F & L AZEVEDO CONFECCAO LTDA",
    "JM CONFECCOES MATRIZ": "J M CONFECÇÕES & CIA LTDA MATRIZ",
    "JM CONFECÇÕES FILIAL": "J M CONFECÇÕES & CIA LTDA FILIAL",
    "JM CONFECÇÕES & CIA LTDA": "J M CONFECÇÕES & CIA LTDA",
    "J M CONFECCOES & CIA LTDA": "J M CONFECÇÕES & CIA LTDA",
    "FILIAL FIOS DO SERTÃO": "FIOS DO SERTÃO LTDA - FILIAL",
    # Erros de digitação
    "IDEAL CONGFEÇÕES LTDA": "IDEAL CONFECCOES LTDA",
    "CONFECÃO SAO SEBASTIAO": "CONFECÇÃO SÃO SEBASTIÃO LTDA",
    "B&N SILVA CONFECOES": "B&N SILVA CONFECCOES LTDA",
    "AJG CONFEÇÕES LTDA ME": "AJG CONFECÇÕES LTDA",
    "ALANIIS SANTOS LTDA": "ALANIS SANTOS LTDA",
    "MAXELA ARAUJO SILVA LTDA": "MAXWELA ARAÚJO SILVA LTDA",
}

# Nomes de oficina inválidos (dado de teste/lixo) — chamados com esses
# valores são descartados do dashboard.
OFICINA_INVALID_NAMES_RAW: list[str] = [
    "aaaaaa",
]

# ---------------------------------------------------------------------------
# Cadastro oficial de oficinas (fonte da verdade para Reposições)
# ---------------------------------------------------------------------------
# Transcrição da planilha "Nomes.xlsx" (aba Planilha2) mantida pelo time de
# cadastro. É a lista fechada de razões sociais válidas: a canonicalização
# usa esses nomes como destino, então a grafia AQUI é a que aparece nos
# KPIs, gráficos e exportações. Para incluir/renomear uma oficina, edite
# esta lista — não os aliases.
OFICINAS_OFICIAIS_RAW: list[str] = [
    "ACAUÃ CONFECÇÕES LTDA",
    "A S CONFECCOES LTDA",
    "A X DA PENHA FILHO LTDA",
    "ACARI TÊXTIL LTDA",
    "AJG CONFECÇÕES LTDA",
    "A DE M DIAS ALVES LIMITADA",
    "A. S. EMPREENDIMENTOS LTDA",
    "ALINE RODRIGUES DE LIMA ARAUJO",
    "ALVES CONFECCOES LIMITADA",
    "FREIRE SILVA CONFECÇÕES LTDA",
    "ALANIS QUEIROZ LTDA",
    "ALANIS SANTOS LTDA",
    "ARAUJO & CAMARA LTDA",
    "ARAUJO E M CONFECCOES EIRELI",
    "ASA CONFECCOES LTDA - ME",
    "CONFECCAO G. B. DA S. JUNIOR & CIA LTDA",
    "AMORIM & PEDRO CONFECCOES LTDA - ME",
    "ANTONIO IGOR DANTAS DE SOUZA",
    "CONFECÇÃO SÃO SEBASTIÃO LTDA",
    "CONFECCOES FRANOELDA M. M. ARAUJO EIRELI",
    "CONFECCOES GENESIS LTDA ME",
    "CONFECCOES GENESIS LTDA ME TEAR",
    "DANTAS E PAULINO CONFECCOES LTDA",
    "B&N SILVA CONFECCOES LTDA",
    "DONA TICA CONFECCOES MATRIZ",
    "DONA TICA MATRIZ",
    "CABUGI CONFECCOES LTDA.",
    "EBENEZER INDUSTRIA TEXTIL LTDA",
    "EVALBER DE CASTRO DANTAS ME",
    "F & K FACCAO LTDA",
    "CLARA A DE MEDEIROS LEITE",
    "CONFECCOES J.S. LTDA",
    "DANJAN CONFECCOES LTDA",
    "F & K FACCAO LTDA PÓLO",
    "F & L AZEVEDO CONFECCAO LTDA - ME MATRIZ",
    "F & L AZEVEDO CONFECCAO LTDA FILIAL",
    "DI3 CONFECCOES LTDA",
    "F A N CONFECCOES LTDA",
    "F DA SILVA JUNIOR",
    "FACCAO ELLO LTDA - ME",
    "FACCAO SANTANENSE LTDA - ME",
    "FENIX INDUSTRIA TÊXTIL LTDA",
    "F J DE AZEVEDO - ME",
    "FENIX INDUSTRIA TÊXTIL LTDA BÁSICO",
    "F. W. DE SOUZA CONFECCOES",
    "FLAVIA GEORGIA B SILVA CONFECCOES EIRELI",
    "FENIX INDUSTRIA TÊXTIL LTDA ELABORADO",
    "FERREIRA E ARAUJO CONFECCOES LTDA",
    "FIOS DO SERTÃO LTDA",
    "FIOS DO SERTÃO LTDA - FILIAL",
    "FORTE FORTEX PRODUÇÃO TEXTIL",
    "FORTE FORTEX PRODUÇÃO TEXTIL TEAR",
    "GEFERSON ALAN DOS SANTOS SILVA",
    "IDEAL CONFECCOES LTDA BÁSICO",
    "IDEAL CONFECCOES LTDA POLO",
    "G&C EMPREENDIMENTOS TEXTIL LTDA",
    "G4 INDUSTRIA E COMERCIO DO VESTUARIO LTDA",
    "IVANILDO JOSE DE SOUSA - ME",
    "J M CONFECÇÕES & CIA LTDA FILIAL",
    "J M CONFECÇÕES & CIA LTDA MATRIZ",
    "J. S. & SILVA LTDA",
    "JOSE MEDEIROS DE ARAUJO",
    "JOSENI MARIA DE MEDEIROS",
    "KSW CONFECÇÕES LTDA",
    "I M DE OLIVEIRA SILVA",
    "J F CONFECCOES LTDA",
    "LAJEDO JEANS CONFECÇÕES LTDA",
    "JAKELINE F DE AZEVEDO - ME",
    "LC TÊXTIL LTDA.",
    "LD CONFECÇÕES LTDA",
    "LEANDRO MATIAS DA SILVA - ME",
    "JANUNCIO NOBREGA DE AZEVEDO",
    "LIMA CONFECCOES LTDA-ME",
    "M C CONFECCOES LTDA",
    "M K DE AZEVEDO MEDEIROS INDUSTRIA TEXTIL",
    "JK INDUSTRIA TEXTIL LTDA",
    "JOLI TEXTIL SERVICOS E COMERCIO LTDA",
    "JUCURUTU TEXTIL LTDA ME",
    "LINEA IND. COM. SER. CONFECCOES LTDA",
    "LIVIA REBOUCAS DE CARVALHO - ME",
    "M K INDUSTRIA TEXTIL LTDA",
    "MARIONETE M DE A CAMARA - ME",
    "MAXWELA ARAÚJO SILVA LTDA",
    "NOEL PEREIRA DE AZEVEDO CONFECCAO",
    "NOVA CONFECCOES LTDA",
    "M DALISON DE MEDEIROS",
    "M. & F. EMPREENDIMENTOS LTDA",
    "OFICINA DE COSTURA SANTOS LTDA",
    "M. A. VIEIRA DE ALMEIDA - ME",
    "P A VITURINO SERVIÇOS E CONFECÇÕES LTDA",
    "POTENGI TEXTIL LTDA",
    "MANSOUR & DANTAS CONFECÇÕES LTDA",
    "N S CONSTANTINO",
    "POTENGI TEXTIL LTDA PÓLO",
    "SOLIS CONFECCOES LTDA",
    "SOLY BRASIL LTDA",
    "P & A CONFECCOES LTDA",
    "SOLY BRASIL LTDA ELABORADO",
    "PEDRO E ODAIR CONFECÇÕES LTDA",
    "POEST INDUSTRIA COMERCIO VESTUARIO LTDA",
    "TENDENCIA CONFECCOES LTDA - ME",
    "S RAMOS DE AZEVEDO NETO CONFECCOES",
    "SERRANA TEXTIL LTDA",
    "TROPICALLIZ CONFECCOES LTDA",
    "TECE COSTURAS E CONFECCOES LTDA",
    "UNIAO CONFECCOES LTDA ME",
    "VITALIZE CONFECCOES LTDA",
    "W A 2 CONFECCOES LTDA",
    # Unidades que aparecem na planilha de Reposições sem indicação de
    # matriz/filial — segundo o time, essas linhas formam um grupo próprio
    # e não devem ser somadas a nenhuma das duas unidades.
    "J M CONFECÇÕES & CIA LTDA",
    "F & L AZEVEDO CONFECCAO LTDA",
]

# Sufixos que indicam a LINHA DE MATÉRIA-PRIMA atendida pela oficina
# (básico, elaborado, pólo, tear), não uma unidade diferente da empresa.
# O dashboard de Reposições agrega por oficina independente da matéria-prima,
# então esses sufixos são removidos do fim do nome antes de comparar —
# "IDEAL CONFECCOES LTDA POLO" e "IDEAL CONFECCOES LTDA BÁSICO" viram ambos
# "IDEAL CONFECCOES LTDA". Sufixos de UNIDADE (MATRIZ/FILIAL) são
# preservados, porque aí sim são cadastros distintos.
OFICINA_SUFIXOS_MATERIA_PRIMA: tuple[str, ...] = (
    "BÁSICO",
    "BASICO",
    "ELABORADO",
    "PÓLO",
    "POLO",
    "TEAR",
)

# Lixo específico da planilha de Reposições: linhas de teste e linhas em
# que o "Nome da tarefa" não permite identificar a oficina. Somadas às de
# OFICINA_INVALID_NAMES_RAW, são descartadas do dashboard de Reposições.
OFICINA_INVALID_NAMES_REPOSICAO_RAW: list[str] = [
    "teste",
    "Não informado",
]
