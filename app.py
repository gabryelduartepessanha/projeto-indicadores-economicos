import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_utils as du

# ---------------------------------------------------------------------------
# Configuração geral
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Indicadores Econômicos do Brasil",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK, AMBAR, TEAL, VERMELHO, NEUTRO = "#0E1420", "#E8A33D", "#3BA89A", "#C65D4B", "#8A93A6"
CORES_NIVEL = {"Crise": VERMELHO, "Estabilidade": AMBAR, "Crescimento": TEAL}
SEQ = [INK, AMBAR, TEAL, VERMELHO, "#6C7A96", "#B9772E"]

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: #0E1420; }}
      section[data-testid="stSidebar"] {{ background-color: #141C2B; }}
      h1, h2, h3, h4 {{ color: #F3F5F8; }}
      p, label, span, div {{ color: #CBD3E0; }}
      div[data-testid="stMetric"] {{
          background: #1A2234; border: 1px solid #263250;
          border-radius: 12px; padding: 14px 16px;
      }}
      div[data-testid="stMetricValue"] {{ color: {AMBAR}; font-weight: 700; }}
      .bloco {{ background:#1A2234; border:1px solid #263250; border-radius:12px;
                padding:18px 22px; margin-bottom:8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

TEMA_PLOTLY = dict(
    template="plotly_dark",
    paper_bgcolor="#1A2234",
    plot_bgcolor="#1A2234",
    font=dict(color="#CBD3E0"),
    margin=dict(l=10, r=10, t=50, b=10),
)


# ---------------------------------------------------------------------------
# Carga de dados (CSV padrão ou upload)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def carregar(fonte=None):
    df = du.carregar_dados(fonte) if fonte is not None else du.carregar_dados()
    return du.preparar_dados(df)


@st.cache_resource(show_spinner=False)
def preparar_banco(_df: pd.DataFrame):
    """Cria o banco SQLite (fato + dimensão) e devolve o caminho."""
    return du.criar_banco(_df)


# ---------------------------------------------------------------------------
# Barra lateral: upload, navegação e filtros
# ---------------------------------------------------------------------------
st.sidebar.title("📊 Indicadores BR")
st.markdown(
    "**Aluno:** Gabryel Duarte Pessanha \n"
    "**Professor: Alexandre Louzada \n"
    "**Materia: Linguagens de programação \n"
)
st.divider()
st.sidebar.caption("Economia brasileira · 2015–2024")

arquivo = st.sidebar.file_uploader(
    "Enviar outro CSV (opcional)", type=["csv"],
    help="Substitui a base padrão por um CSV com as mesmas colunas.",
)
try:
    df = carregar(arquivo) if arquivo is not None else carregar()
    if arquivo is not None:
        st.sidebar.success(f"Base carregada: {len(df)} registros.")
except Exception as erro:
    st.sidebar.error(f"Não foi possível ler o CSV: {erro}")
    st.stop()

PAGINAS = [
    "Visão geral",
    "Análise temporal",
    "Relações & correlação",
    "Comparativo por nível",
    "Explorar dados (SQL)",
    "Conclusão executiva",
]
pagina = st.sidebar.radio("Navegação", PAGINAS)

st.sidebar.markdown("### Filtros")
anos = sorted(df["ano"].unique())
faixa = st.sidebar.slider("Período (ano)", min(anos), max(anos),
                          (min(anos), max(anos)))
tris = st.sidebar.multiselect("Trimestre", [1, 2, 3, 4], default=[1, 2, 3, 4])
niveis = st.sidebar.multiselect(
    "Nível econômico", sorted(df["nivel_economico"].unique()),
    default=sorted(df["nivel_economico"].unique()),
)
indicadores_num = ["pib", "inflacao", "taxa_juros", "taxa_desemprego",
                   "cambio_dolar", "renda_media", "consumo_familias",
                   "investimento", "exportacoes", "importacoes"]
indicador = st.sidebar.selectbox(
    "Indicador em destaque", indicadores_num,
    format_func=lambda c: du.ROTULOS.get(c, c),
)

# Aplica filtros
dff = df[
    df["ano"].between(faixa[0], faixa[1])
    & df["trimestre"].isin(tris if tris else [1, 2, 3, 4])
    & df["nivel_economico"].isin(niveis if niveis else df["nivel_economico"].unique())
].copy()

if dff.empty:
    st.warning("Nenhum registro corresponde aos filtros. Ajuste a seleção.")
    st.stop()


# ---------------------------------------------------------------------------
# Componentes reutilizáveis
# ---------------------------------------------------------------------------
def painel_kpis(dados: pd.DataFrame):
    k = du.calcular_kpis(dados)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("PIB médio", f"R$ {k['pib_medio']/1e6:.2f}M",
              f"{k['pib_delta']/1e3:+.0f} mil" if k.get("pib_delta") else None)
    c2.metric("Inflação média", f"{k['inflacao_media']:.2f}%",
              f"{k['inflacao_delta']:+.2f} p.p." if k.get("inflacao_delta") else None,
              delta_color="inverse")
    c3.metric("Desemprego médio", f"{k['desemprego_medio']:.2f}%",
              f"{k['desemprego_delta']:+.2f} p.p." if k.get("desemprego_delta") else None,
              delta_color="inverse")
    c4.metric("Juros médio (Selic)", f"{k['juros_medio']:.2f}%",
              f"{k['juros_delta']:+.2f} p.p." if k.get("juros_delta") else None)
    c5.metric("Dólar médio", f"R$ {k['dolar_medio']:.2f}",
              f"{k['dolar_delta']:+.2f}" if k.get("dolar_delta") else None,
              delta_color="inverse")
    cresc = k.get("crescimento_medio")
    c6.metric("Crescimento médio a/a",
              f"{cresc:.2f}%" if pd.notna(cresc) else "—")


# ===========================================================================
# PÁGINA 1 — VISÃO GERAL
# ===========================================================================
if pagina == "Visão geral":
    st.title("Indicadores Econômicos do Brasil")
    st.markdown(
        "**Problema.** Como a economia brasileira se comportou entre 2015 e "
        "2024? Este painel reúne PIB, inflação, juros (Selic), desemprego, "
        "câmbio e outros indicadores trimestrais para identificar períodos de "
        "crise, estabilidade e crescimento, e as relações entre as variáveis."
    )
    st.divider()

    st.subheader("Indicadores-chave (período filtrado)")
    painel_kpis(dff)

    st.subheader(f"Evolução de {du.ROTULOS.get(indicador, indicador)}")
    fig = px.line(dff, x="data", y=indicador, markers=True,
                  color_discrete_sequence=[AMBAR])
    fig.update_traces(line=dict(width=3))
    fig.update_layout(**TEMA_PLOTLY, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Composição dos períodos")
        cont = dff["nivel_economico"].value_counts().reset_index()
        cont.columns = ["nivel", "trimestres"]
        figp = px.pie(cont, names="nivel", values="trimestres", hole=0.5,
                      color="nivel", color_discrete_map=CORES_NIVEL)
        figp.update_layout(**TEMA_PLOTLY)
        st.plotly_chart(figp, use_container_width=True)
    with col2:
        st.subheader("Interpretação")
        n_crise = int((dff["nivel_economico"] == "Crise").sum())
        pct = n_crise / len(dff) * 100
        st.markdown(
            f"""
            <div class="bloco">
            No recorte atual há <b>{len(dff)}</b> trimestres. Deles,
            <b>{n_crise}</b> ({pct:.0f}%) foram classificados como de
            <b>crise</b>. O PIB médio do período é de
            <b>R$ {du.calcular_kpis(dff)['pib_medio']/1e6:.2f} milhões</b> e a
            inflação média, de
            <b>{du.calcular_kpis(dff)['inflacao_media']:.2f}%</b>. Use os filtros
            à esquerda para recortar anos, trimestres e níveis econômicos.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ===========================================================================
# PÁGINA 2 — ANÁLISE TEMPORAL (séries temporais avançadas)
# ===========================================================================
elif pagina == "Análise temporal":
    st.title("Análise temporal")
    st.caption("Séries temporais, média móvel e crescimento ano a ano.")

    st.subheader(f"Série e média móvel — {du.ROTULOS.get(indicador, indicador)}")
    janela = st.slider("Janela da média móvel (trimestres)", 2, 8, 4)
    temp = dff.sort_values("data").copy()
    temp["media_movel"] = temp[indicador].rolling(janela, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temp["data"], y=temp[indicador], name="Observado",
                             mode="lines+markers", line=dict(color=NEUTRO)))
    fig.add_trace(go.Scatter(x=temp["data"], y=temp["media_movel"],
                             name=f"Média móvel ({janela}T)",
                             line=dict(color=AMBAR, width=3)))
    fig.update_layout(**TEMA_PLOTLY, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Crescimento do PIB ano a ano (a/a)")
    pib_aa = dff.dropna(subset=["pib_var_anual"])
    if not pib_aa.empty:
        figb = px.bar(pib_aa, x="ano_tri", y="pib_var_anual",
                      color="pib_var_anual", color_continuous_scale="RdYlGn")
        figb.update_layout(**TEMA_PLOTLY, xaxis_title="", yaxis_title="% a/a",
                           coloraxis_showscale=False)
        st.plotly_chart(figb, use_container_width=True)
    else:
        st.info("Amplie o período para calcular a variação ano a ano (requer 4+ trimestres).")

    st.subheader("Heatmap trimestral do PIB")
    piv = dff.pivot_table(index="ano", columns="trimestre", values="pib")
    figh = px.imshow(piv / 1e6, text_auto=".2f", aspect="auto",
                     color_continuous_scale="YlGnBu",
                     labels=dict(color="PIB (M/1e6)", x="Trimestre", y="Ano"))
    figh.update_layout(**TEMA_PLOTLY)
    st.plotly_chart(figh, use_container_width=True)

# ===========================================================================
# PÁGINA 3 — RELAÇÕES & CORRELAÇÃO (correlação estatística)
# ===========================================================================
elif pagina == "Relações & correlação":
    st.title("Relações entre indicadores")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inflação x Desemprego")
        fig1 = px.scatter(dff, x="inflacao", y="taxa_desemprego",
                          color="nivel_economico", color_discrete_map=CORES_NIVEL,
                          trendline="ols", size="pib", size_max=18)
        fig1.update_layout(**TEMA_PLOTLY, xaxis_title="Inflação (%)",
                           yaxis_title="Desemprego (%)")
        st.plotly_chart(fig1, use_container_width=True)
        r1 = dff["inflacao"].corr(dff["taxa_desemprego"])
        st.caption(f"Correlação de Pearson: r = {r1:.2f}")
    with col2:
        st.subheader("Juros x Consumo das famílias")
        fig2 = px.scatter(dff, x="taxa_juros", y="consumo_familias",
                          color="nivel_economico", color_discrete_map=CORES_NIVEL,
                          trendline="ols", size="pib", size_max=18)
        fig2.update_layout(**TEMA_PLOTLY, xaxis_title="Taxa de juros (%)",
                           yaxis_title="Consumo (índice)")
        st.plotly_chart(fig2, use_container_width=True)
        r2 = dff["taxa_juros"].corr(dff["consumo_familias"])
        st.caption(f"Correlação de Pearson: r = {r2:.2f}")

    st.subheader("Matriz de correlação")
    corr = du.matriz_correlacao(dff)
    corr.index = [du.ROTULOS.get(c, c).split(" (")[0] for c in corr.index]
    corr.columns = [du.ROTULOS.get(c, c).split(" (")[0] for c in corr.columns]
    figc = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                     zmin=-1, zmax=1, aspect="auto")
    figc.update_layout(**TEMA_PLOTLY, height=600)
    st.plotly_chart(figc, use_container_width=True)
    st.markdown(
        '<div class="bloco">Valores próximos de <b>+1</b> indicam que os '
        "indicadores sobem juntos; próximos de <b>-1</b>, que se movem em "
        "sentidos opostos; próximos de <b>0</b>, ausência de relação linear.</div>",
        unsafe_allow_html=True,
    )

# ===========================================================================
# PÁGINA 4 — COMPARATIVO POR NÍVEL (barras + radar + JOIN no banco)
# ===========================================================================
elif pagina == "Comparativo por nível":
    st.title("Comparativo por nível econômico")

    medias = dff.groupby("nivel_economico")[indicadores_num].mean().reset_index()
    ordem = [n for n in ["Crise", "Estabilidade", "Crescimento"]
             if n in medias["nivel_economico"].values]

    st.subheader(f"Média de {du.ROTULOS.get(indicador, indicador)} por nível")
    figb = px.bar(medias, x="nivel_economico", y=indicador,
                  color="nivel_economico", color_discrete_map=CORES_NIVEL,
                  category_orders={"nivel_economico": ordem}, text_auto=".2f")
    figb.update_layout(**TEMA_PLOTLY, xaxis_title="", yaxis_title="",
                       showlegend=False)
    st.plotly_chart(figb, use_container_width=True)

    st.subheader("Radar de indicadores (normalizado)")
    cols_radar = ["pib", "inflacao", "taxa_juros", "taxa_desemprego",
                  "cambio_dolar", "consumo_familias"]
    base = dff.groupby("nivel_economico")[cols_radar].mean()
    norm = (base - dff[cols_radar].min()) / (dff[cols_radar].max() - dff[cols_radar].min())
    rotulos = [du.ROTULOS.get(c, c).split(" (")[0] for c in cols_radar]
    figr = go.Figure()
    for nivel in ordem:
        figr.add_trace(go.Scatterpolar(
            r=norm.loc[nivel].tolist() + [norm.loc[nivel].tolist()[0]],
            theta=rotulos + [rotulos[0]], fill="toself", name=nivel,
            line=dict(color=CORES_NIVEL[nivel])))
    figr.update_layout(**TEMA_PLOTLY,
                       polar=dict(bgcolor="#141C2B",
                                  radialaxis=dict(visible=True, range=[0, 1])))
    st.plotly_chart(figr, use_container_width=True)

    st.subheader("Resumo por nível (consulta SQL com JOIN no banco)")
    try:
        preparar_banco(df)
        sql = """
            SELECT n.nivel_economico AS "Nível",
                   n.descricao       AS "Descrição",
                   COUNT(*)          AS "Trimestres",
                   ROUND(AVG(i.pib)/1e6, 2)      AS "PIB médio (M)",
                   ROUND(AVG(i.inflacao), 2)     AS "Inflação média",
                   ROUND(AVG(i.taxa_desemprego), 2) AS "Desemprego médio"
            FROM indicadores i
            JOIN niveis n ON i.id_nivel = n.id_nivel
            GROUP BY n.nivel_economico
            ORDER BY "PIB médio (M)" DESC
        """
        st.dataframe(du.consultar_banco(sql), use_container_width=True,
                     hide_index=True)
        st.caption("Dados lidos do banco SQLite (tabela fato `indicadores` "
                   "integrada à dimensão `niveis`).")
    except Exception as erro:
        st.info(f"Banco indisponível neste ambiente ({erro}). "
                "Mostrando agregação direta do CSV.")
        st.dataframe(dff.groupby("nivel_economico")[indicadores_num]
                     .mean().round(2), use_container_width=True)

# ===========================================================================
# PÁGINA 5 — EXPLORAR DADOS (tabela dinâmica + download)
# ===========================================================================
elif pagina == "Explorar dados (SQL)":
    st.title("Explorar os dados")
    st.caption("Tabela dinâmica filtrável e exportação.")

    colunas = st.multiselect(
        "Colunas exibidas",
        ["ano_tri", "nivel_economico"] + indicadores_num
        + ["saldo_comercial", "indice_miseria", "pib_var_anual"],
        default=["ano_tri", "nivel_economico", "pib", "inflacao",
                 "taxa_desemprego", "taxa_juros", "cambio_dolar"],
    )
    tabela = dff[colunas] if colunas else dff
    st.dataframe(tabela, use_container_width=True, hide_index=True)
    st.caption(f"{len(tabela)} registros · {len(tabela.columns)} colunas.")

    st.download_button(
        "⬇️ Baixar seleção (CSV)",
        data=tabela.to_csv(index=False).encode("utf-8"),
        file_name="indicadores_filtrados.csv", mime="text/csv",
    )

    st.subheader("Estatísticas descritivas")
    st.dataframe(dff[indicadores_num].describe().round(2),
                 use_container_width=True)

# ===========================================================================
# PÁGINA 6 — CONCLUSÃO EXECUTIVA
# ===========================================================================
elif pagina == "Conclusão executiva":
    st.title("Conclusão executiva")
    k = du.calcular_kpis(dff)
    corr = du.matriz_correlacao(dff)
    r_infl_des = corr.loc["inflacao", "taxa_desemprego"]
    r_juros_cons = corr.loc["taxa_juros", "consumo_familias"]
    nivel_top = (dff.groupby("nivel_economico")["pib"].mean().idxmax())

    st.markdown(
        f"""
        <div class="bloco">
        <h3>Síntese do período analisado</h3>
        <ul>
          <li>O <b>PIB médio</b> foi de <b>R$ {k['pib_medio']/1e6:.2f} milhões</b>,
              com crescimento médio de <b>{k['crescimento_medio']:.2f}% a/a</b>.</li>
          <li>A <b>inflação média</b> ficou em <b>{k['inflacao_media']:.2f}%</b> e o
              <b>desemprego médio</b>, em <b>{k['desemprego_medio']:.2f}%</b>.</li>
          <li>A <b>Selic média</b> foi de <b>{k['juros_medio']:.2f}%</b> e o
              <b>dólar médio</b>, de <b>R$ {k['dolar_medio']:.2f}</b>.</li>
          <li>O maior PIB médio ocorreu em trimestres de
              <b>{nivel_top}</b>.</li>
        </ul>
        <h3>Relações observadas</h3>
        <ul>
          <li>Inflação × desemprego: correlação <b>r = {r_infl_des:.2f}</b>
              — {"relação inversa (indício de curva de Phillips)" if r_infl_des < -0.3 else "relação linear fraca neste recorte"}.</li>
          <li>Juros × consumo: correlação <b>r = {r_juros_cons:.2f}</b>
              — {"juros mais altos acompanham menor consumo" if r_juros_cons < -0.3 else "sem relação linear forte neste recorte"}.</li>
        </ul>
        <h3>Leitura econômica</h3>
        <p>Trata-se de uma base <b>simulada</b>; por isso, várias relações
        aparecem fracas e as séries oscilam sem a tendência suave de dados
        reais. Ainda assim, o painel cumpre o objetivo analítico: permite
        recortar o período, comparar níveis econômicos, acompanhar a evolução
        temporal e quantificar correlações entre os indicadores — a mesma
        metodologia que se aplicaria a dados oficiais (IBGE, Bacen, IPEA).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Rodapé
st.sidebar.divider()
st.sidebar.caption("Projeto G1 · Tema 17 · Python + Streamlit")
