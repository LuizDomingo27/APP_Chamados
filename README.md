# APP_PPCHAMADO — Central de Acompanhamento de Chamados & Reposições

Dashboard em Streamlit com duas páginas:

- **Chamados** — análise dos chamados exportados da "Central de Ajuda".
- **Reposições** — acompanhamento das reposições solicitadas pelas oficinas de costura (novo módulo).

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Um menu de navegação aparece na barra lateral para trocar entre as duas páginas. Cada página tem seu próprio upload de arquivo e seus próprios filtros — dá pra deixar as duas carregadas ao mesmo tempo.

- Em **Chamados**, envie o arquivo `Central de Ajuda.xlsx` (aba **Dados Consolidados**).
- Em **Reposições**, envie o arquivo de Reposições (aba **Dados Consolidados**).

## Estrutura (camadas)

```
APP_PPCHAMADO/
├── app.py                        # Ponto de entrada — só define a navegação (st.navigation)
├── pages/
│   ├── chamados.py                # Página de Chamados (upload → services → UI)
│   └── reposicoes.py              # Página de Reposições (upload → services → UI)
├── core/
│   ├── config.py                  # Constantes, nomes de coluna, paleta de cores
│   ├── text_normalize.py          # Normalização de texto p/ comparação/agrupamento
│   └── utils.py                   # Helpers genéricos (select_all_popover, formatação)
├── services/                      # Lógica pura — sem import de streamlit
│   ├── data_loader.py              # Leitura/validação do Excel (compartilhado)
│   ├── filter_service.py           # Filtros de Chamados (data, nº chamado, oficina)
│   ├── parser_service.py           # Regex de Chamados + canonicalização de oficinas (compartilhada)
│   ├── kpi_service.py              # KPIs genéricos, reaproveitados pelas duas páginas
│   ├── export_service.py           # Excel exportável (Chamados e Reposições)
│   ├── reposicao_parser_service.py # Extrai nº/oficina/ordem de produção/parte da peça/motivo
│   ├── reposicao_filter_service.py # Filtros de Reposições (data, nº reposição, oficina)
│   └── reposicao_kpi_service.py    # KPIs específicos: tendência semanal/mensal, tempo de
│                                    # atendimento, ranking de solicitantes, oficinas pendentes
└── ui/
    ├── styles.py                   # CSS tema light neon cyan-green (compartilhado)
    ├── components.py               # Cards, header, tabela estilizada (compartilhados)
    └── charts.py                   # Gráficos ECharts (compartilhados)
```

A canonicalização de nomes de oficina (`services/parser_service.py`) é reaproveitada pelas Reposições, já que são as mesmas oficinas parceiras nos dois módulos.

## KPIs — Chamados

- Total de chamados + totais agregados por oficina e por categoria
- Totais por status: Concluída / Não iniciado / Em andamento
- Totais por prioridade (Urgente / Importante / Média) + tabela ordenada pela fila de prioridade
- Filtros: período (Criado em), número do chamado, oficina (multi-seleção com popover)
- Gráfico de linha de tendência diária com linha de média do período
- Gráfico de ranking das oficinas com mais chamados (Top 10)
- Cards de destaque: dia com mais pedidos, oficina com mais pedidos, tipo de solicitação mais comum
- Exportação dos dados filtrados em Excel

## KPIs — Reposições

- Total de reposições + totais por status (Concluída / Não iniciado / Em andamento)
- **Pendências**: quantas reposições estão pendentes, quantas oficinas têm pendência e qual a espera mais longa
- **Oficinas com reposição em aberto**: tabela com quantidade pendente, data da solicitação mais antiga e há quantos dias está em aberto (ordenada da espera mais longa para a mais curta)
- Totais por prioridade
- Destaques do período: dia com mais solicitações, oficina que mais solicita, categoria mais comum
- **Tempo de atendimento**: média, mediana, mínimo e máximo (em dias), calculado sobre reposições já concluídas (Concluído em − Criado em)
- Tendência de reposições por **dia, semana e mês**
- Ranking de oficinas que mais solicitam (Top 10) e ranking de quem mais solicita (campo "Criado por")
- Totais agregados por oficina e por categoria
- Tabela detalhada ordenada por prioridade, com colunas de apoio "Dias em Aberto" (pendentes) e "Tempo de Atendimento (dias)" (concluídas)
- Exportação dos dados filtrados em Excel (3 abas: Reposições Filtradas, Por Oficina, Oficinas Pendentes)

### Extração dos dados de Reposições

O campo "Nome da tarefa" da planilha de Reposições concentra número da reposição / ordem de produção / oficina / parte da peça em texto livre, mas a ordem desses pedaços não é 100% consistente entre linhas. Por isso a extração usa como âncora os campos já rotulados dentro de "Notas" (`Ordem de Produção Mestre`, `Parte da peça`, `Motivo`, `Quantidade`), presentes em praticamente todas as linhas — a oficina é obtida por eliminação (o que sobra depois de remover a ordem de produção e a parte da peça já conhecidas). Ver `services/reposicao_parser_service.py`.

## Observações técnicas

- Os gráficos usam **Apache ECharts** renderizado via `st.iframe` com HTML/JS
  (a lib `streamlit-echarts` está incompatível com o Streamlit instalado —
  essa abordagem evita a dependência extra e dá controle total de estilo).
- Datas trafegam como `datetime` nativo pelo pipeline e só são formatadas
  (`DD/MM/AAAA`) na camada de exibição/exportação.
- A navegação entre páginas usa `st.navigation` / `st.Page` (Streamlit ≥ 1.36); cada página mantém seu próprio estado de upload (`ppc_*` em Chamados, `rep_*` em Reposições), então as duas podem ficar carregadas ao mesmo tempo sem conflito.
- Testado com `py_compile` + `streamlit.testing.v1.AppTest` simulando upload
  dos arquivos reais (846 chamados e 1.470 reposições).

