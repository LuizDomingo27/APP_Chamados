# APP_PPCHAMADO — Central de Acompanhamento de Chamados

Dashboard em Streamlit para análise dos chamados exportados da "Central de Ajuda" (Dados Consolidados).

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Depois é só fazer upload do arquivo `Central de Ajuda.xlsx` (precisa conter a aba **Dados Consolidados**).

## Estrutura (camadas)

```
APP_PPCHAMADO/
├── app.py                  # Orquestração (UI ↔ services), sem regra de negócio
├── core/
│   ├── config.py           # Constantes, nomes de coluna, paleta de cores
│   └── utils.py            # Helpers genéricos (select_all_popover, formatação)
├── services/                # Lógica pura — sem import de streamlit
│   ├── data_loader.py       # Leitura/validação do Excel
│   ├── parser_service.py    # Regex: extrai nº chamado / oficina / solicitação
│   ├── filter_service.py    # Filtros (data, nº chamado, oficina)
│   └── kpi_service.py       # Todos os cálculos de KPI
├── ui/
│   ├── styles.py             # CSS tema light neon cyan-green
│   ├── components.py         # Cards, header, tabela estilizada
│   └── charts.py              # Gráficos ECharts (linha de tendência, ranking, categorias)
└── .streamlit/config.toml    # Tema padrão do Streamlit
```

## KPIs implementados

- Total de chamados + totais agregados por oficina e por categoria
- Totais por status: Concluída / Não iniciado / Em andamento
- Totais por prioridade (Urgente / Importante / Média) + tabela ordenada pela fila de prioridade
- Filtros: período (Criado em), número do chamado, oficina (multi-seleção com popover)
- Gráfico de linha de tendência diária com linha de média do período
- Gráfico de ranking das oficinas com mais chamados (Top 10)
- Cards de destaque: dia com mais pedidos, oficina com mais pedidos, tipo de solicitação mais comum
- Exportação dos dados filtrados em Excel

## Observações técnicas

- Os gráficos usam **Apache ECharts** renderizado via `st.iframe` com HTML/JS
  (a lib `streamlit-echarts` está incompatível com o Streamlit instalado —
  essa abordagem evita a dependência extra e dá controle total de estilo).
- Datas trafegam como `datetime` nativo pelo pipeline e só são formatadas
  (`DD/MM/AAAA`) na camada de exibição/exportação.
- Testado com `py_compile` + `streamlit.testing.v1.AppTest` simulando upload
  do arquivo real (846 chamados).
