# 📊 Indicadores Econômicos do Brasil (2015–2024)

Projeto **G1 — Análise e Visualização de Dados com Python · Tema 17**.

Aplicação analítica sobre a economia brasileira a partir de uma base simulada
de indicadores trimestrais (PIB, inflação, Selic, desemprego, câmbio, renda,
consumo, investimento e comércio exterior). O projeto entrega um **notebook de
análise**, um **dashboard interativo em Streamlit** e uma **página de
apresentação** publicada no GitHub Pages.

> ⚠️ **A base é simulada.** As conclusões servem para exercitar a metodologia de
> análise de dados, não para descrever a história econômica real do Brasil.

---

## 🔗 Links de entrega

Substitua pelos seus endereços após publicar:

| Plataforma | Objetivo | Link |
|---|---|---|
| GitHub | Código-fonte | `https://github.com/gabryelduartepessanha/projeto-indicadores-economicos` |
| GitHub Pages | Página do projeto | `https://gabryelduartepessanha.github.io/projeto-indicadores-economicos/#` |
| Streamlit Cloud | Dashboard | `https://projeto-indicadores-economicos.streamlit.app/` |

---

## 🗂️ Estrutura do projeto

```
projeto-indicadores-economicos/
├── app.py                     # Dashboard Streamlit (multipágina)
├── data_utils.py              # Carga, limpeza, atributos, KPIs e banco (compartilhado)
├── gerar_figuras.py           # Gera as imagens estáticas em imagens/
├── requirements.txt           # Dependências
├── README.md
├── index.html                 # Página de apresentação (GitHub Pages)
├── LICENSE
├── .streamlit/
│   └── config.toml            # Tema do dashboard
├── dados/
│   └── simulacao_indicadores_economicos_brasil.csv
├── database/                  # Banco SQLite gerado em tempo de execução
├── notebooks/
│   └── analise_indicadores_economicos.ipynb
└── imagens/                   # Figuras usadas no README e na página
```

---

## ▶️ Como executar localmente

Pré-requisito: **Python 3.10+**.

```bash
# 1. Clonar e entrar na pasta
git clone https://github.com/SEU-USUARIO/projeto-indicadores-economicos.git
cd projeto-indicadores-economicos

# 2. (Opcional) ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Rodar o dashboard
streamlit run app.py
```

O dashboard abre em `http://localhost:8501`.

**Gerar as figuras** (opcional, já incluídas):

```bash
python gerar_figuras.py
```

**Criar o banco SQLite** manualmente (opcional; o app cria sob demanda):

```bash
python data_utils.py
```

**Abrir o notebook:**

```bash
jupyter notebook notebooks/analise_indicadores_economicos.ipynb
```

---

## 🧭 O dashboard (multipágina)

| Página | Conteúdo |
|---|---|
| **Visão geral** | Título, descrição do problema, KPIs dinâmicos, série temporal e composição dos períodos. |
| **Análise temporal** | Série + média móvel ajustável, crescimento ano a ano, heatmap trimestral. |
| **Relações & correlação** | Dispersões inflação×desemprego e juros×consumo com tendência, matriz de correlação. |
| **Comparativo por nível** | Barras, radar e tabela resumida via **consulta SQL com JOIN** no banco. |
| **Explorar dados (SQL)** | Tabela dinâmica filtrável, download em CSV e estatísticas descritivas. |
| **Conclusão executiva** | Síntese textual automática do período filtrado. |

**Filtros** (barra lateral): ano (intervalo), trimestre, nível econômico,
indicador em destaque e **upload de um CSV próprio**.

---

## ✅ Funcionalidades e critérios atendidos

**Tecnologias obrigatórias:** Python · Pandas · Matplotlib · Seaborn ·
Streamlit · GitHub. **Recomendadas usadas:** NumPy · Plotly · SQLAlchemy · SQLite.

**Funcionalidades intermediárias** (mín. 2):
filtros múltiplos · KPIs dinâmicos · gráficos interativos · análise temporal ·
visualizações comparativas · dashboard em seções · upload de arquivos.

**Funcionalidades avançadas** (mín. 2):
dashboard multipágina · persistência em banco (SQLAlchemy + SQLite) ·
modelagem relacional (fato + dimensão com JOIN) · correlação estatística ·
séries temporais avançadas · integração de múltiplas fontes (CSV + banco).

| Critério de avaliação | Onde é atendido |
|---|---|
| Organização do projeto | Estrutura de pastas, módulo `data_utils` reutilizado, README |
| Tratamento dos dados | `carregar_dados` / `preparar_dados` / `diagnostico_qualidade` |
| Análise exploratória | Notebook (seções 6–8) e página "Relações & correlação" |
| Qualidade dos gráficos | `imagens/` (Matplotlib/Seaborn) + Plotly no dashboard |
| Uso correto do Streamlit | `app.py` multipágina com filtros, KPIs e seções |
| Funcionalidades avançadas | Banco relacional, multipágina, correlação, séries temporais |
| Interatividade | Filtros, média móvel ajustável, upload, download, gráficos Plotly |
| Interpretação e conclusão | Blocos de interpretação em cada página + conclusão executiva |

---

## 🚀 Publicação

### 1. GitHub (código)
```bash
git init
git add .
git commit -m "Projeto G1 - Indicadores Econômicos do Brasil"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/projeto-indicadores-economicos.git
git push -u origin main
```

### 2. GitHub Pages (página)
No repositório: **Settings → Pages → Source: Deploy from a branch →
Branch: `main` / `(root)` → Save**. Em alguns minutos a página estará em
`https://SEU-USUARIO.github.io/projeto-indicadores-economicos/`.
Depois, edite os links no topo do `index.html` (e na tabela acima).

### 3. Streamlit Community Cloud (dashboard)
Acesse <https://share.streamlit.io>, conecte o repositório, defina
**Main file path: `app.py`** e publique. O `requirements.txt` é instalado
automaticamente.

---

## 🧱 Decisões técnicas

- **`data_utils.py` compartilhado**: a mesma lógica de limpeza, atributos e
  KPIs alimenta o notebook e o dashboard, evitando divergências.
- **Modelagem relacional**: tabela fato `indicadores` ligada à dimensão
  `niveis` por chave estrangeira; o comparativo por nível usa um `JOIN`.
- **Base simulada**: as correlações aparecem fracas; o código e a metodologia
  são diretamente aplicáveis a dados reais (IBGE, Banco Central, IPEA).

---

## 📄 Licença

Distribuído sob a licença MIT — veja [`LICENSE`](LICENSE).
