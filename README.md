# Dashboard Cerveja Zero no Brasil

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Ativo-brightgreen)

Dashboard interativo para análise do mercado de cerveja zero no Brasil, com dados de 2021 a 2026 (incluindo projeções).

## Funcionalidades

- **KPIs com Delta**: Cards mostram variação vs. ano anterior com setas de tendência
- **Sparklines**: Mini-gráficos de tendência em cada KPI
- **Mapa Interativo**: Visualização geográfica da densidade de cervejarias por estado
- **Simulador de Cenários**: Projeções 2025–2026 com parâmetros ajustáveis
- **Sistema de Gamificação**: Pontos, badges, níveis e quizzes
- **Análise de Mercado**: Concentração, estilos de cerveja, comércio exterior

## Estrutura do Projeto

```
beer/
├── Home.py              # Dashboard principal (Streamlit)
├── data_pipeline.py     # Pipeline de carregamento e transformação de dados
├── metrics.py           # Cálculos de KPIs e métricas
├── ui_sections.py       # Componentes de interface reutilizáveis
├── requirements.txt     # Dependências Python
├── data/                # Dados em CSV
│   ├── zero_vs_regular_beer_volume.csv
│   ├── mapa_breweries_history.csv
│   ├── consumption_per_capita.csv
│   ├── brewery_density_by_state.csv
│   ├── market_concentration.csv
│   ├── beer_styles.csv
│   ├── inflation_ipca.csv
│   ├── exports_detailed_2024.csv
│   ├── mapa_state_breweries_selected.csv
│   ├── mapa_region_highlights.csv
│   ├── mapa_trade_2024.csv
│   └── alcoholic_beverage_spending_2025.csv
└── LICENSE
```

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/beer.git
cd beer

# 2. (Recomendado) Crie um ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o dashboard
streamlit run Home.py
```

> Requer conexão à internet para buscar dados atualizados do MAPA (opcional — fallback para dados locais).

## Fontes de Dados

| Fonte | Dados |
|---|---|
| MAPA (Ministério da Agricultura) | Cervejarias registradas, produção |
| IBGE | Consumo per capita, inflação IPCA |
| Euromonitor | Projeções de mercado |
| Kirin Holdings | Rankings globais |

## Métricas Disponíveis

- Volume cerveja zero e tradicional (bi L)
- Market share cerveja zero (%)
- Número de cervejarias e densidade por estado
- Gastos com bebidas por estado (R$ bi)
- Inflação IPCA cerveja
- Exportações (volume e receita)
- Concentração de mercado
- Consumo per capita (L/hab/ano)

## Filtros Disponíveis

- Ano de análise: 2021–2026
- Tipo de dado: Oficial / Estimado
- Estado: todos os estados brasileiros

## Simulador de Cenários

| Parâmetro | Intervalo |
|---|---|
| Crescimento cerveja zero | -20% a +120% |
| Variação cerveja tradicional | -20% a +20% |
| Elasticidade gasto | -15% a +15% |

## Atualização de Dados

O dashboard busca dados oficiais automaticamente com cache de 24 horas.
Para forçar atualização, limpe o cache do Streamlit (`streamlit cache clear`).

## Destaques (dados 2024)

- Cerveja zero: **757,4 M litros** (oficial MAPA 2025)
- Crescimento: **+537%** vs. 2023
- Market share: **4,9%** do mercado total
- Cervejarias: **1.949** estabelecimentos registrados
- Ranking global: **2º lugar** em consumo de zero

## Dependências

```
streamlit>=1.51.0
pandas>=2.2.0
altair>=5.0.0
requests>=2.31.0
plotly>=5.18.0
```

## Troubleshooting

**Erro ao carregar dados**
```bash
# Verifique se os CSVs estão na pasta /data
ls data/
```

**Mapa não aparece**
```bash
pip install plotly>=5.18.0
```

**Erro de import**
```bash
pip install -r requirements.txt --upgrade
```

## Proximos Passos

- [ ] Integração com banco de dados
- [ ] Export de relatórios em PDF
- [ ] Alertas automáticos
- [ ] Dashboard mobile-friendly
- [ ] Testes automatizados

## Licença

MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Versão**: 2.0 | **Última atualização**: Fevereiro 2025
