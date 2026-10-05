"""
gerar_figuras.py
================
Gera as visualizações estáticas (Matplotlib + Seaborn) usadas no README,
na página de apresentação (index.html) e como referência do notebook.
Salva tudo em imagens/.

Uso:  python gerar_figuras.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Patch

import data_utils as du

# ---------------------------------------------------------------------------
# Identidade visual (consistente com o dashboard e a página)
# ---------------------------------------------------------------------------
INK = "#0E1420"
TINTA = "#1A2234"
AMBAR = "#E8A33D"
TEAL = "#3BA89A"
VERMELHO = "#C65D4B"
NEUTRO = "#8A93A6"
PAPEL = "#EEF1F4"

CORES_NIVEL = {"Crise": VERMELHO, "Estabilidade": AMBAR, "Crescimento": TEAL}

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": NEUTRO,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "grid.color": "#DDE2EA",
})

PASTA = du.BASE_DIR / "imagens"
PASTA.mkdir(exist_ok=True)


def salvar(fig, nome):
    caminho = PASTA / nome
    fig.savefig(caminho, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("gerado:", caminho.name)


def main():
    df = du.preparar_dados(du.carregar_dados())

    # 1. Evolução do PIB com faixas de nível econômico -----------------------
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df["data"], df["pib"], color=INK, lw=2, marker="o",
            markersize=4, zorder=3)
    for nivel, cor in CORES_NIVEL.items():
        sub = df[df["nivel_economico"] == nivel]
        ax.scatter(sub["data"], sub["pib"], color=cor, s=55,
                   zorder=4, label=nivel, edgecolor="white", linewidth=0.8)
    ax.set_title("Evolução do PIB trimestral (2015–2024)")
    ax.set_ylabel("PIB (R$ milhões)")
    ax.set_xlabel("")
    ax.legend(title="Nível econômico", frameon=False, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M"))
    salvar(fig, "pib_evolucao.png")

    # 2. Dispersão inflação x desemprego + tendência -------------------------
    fig, ax = plt.subplots(figsize=(7, 5.2))
    for nivel, cor in CORES_NIVEL.items():
        sub = df[df["nivel_economico"] == nivel]
        ax.scatter(sub["inflacao"], sub["taxa_desemprego"], color=cor,
                   s=70, label=nivel, edgecolor="white", linewidth=0.8)
    # linha de tendência
    coef = np.polyfit(df["inflacao"], df["taxa_desemprego"], 1)
    xs = np.linspace(df["inflacao"].min(), df["inflacao"].max(), 50)
    ax.plot(xs, np.polyval(coef, xs), "--", color=NEUTRO, lw=1.6)
    r = df["inflacao"].corr(df["taxa_desemprego"])
    ax.set_title("Inflação x Desemprego")
    ax.set_xlabel("Inflação (%)")
    ax.set_ylabel("Desemprego (%)")
    ax.legend(title="Nível econômico", frameon=False)
    ax.text(0.98, 0.02, f"correlação r = {r:.2f}", transform=ax.transAxes,
            ha="right", va="bottom", color=NEUTRO, fontsize=10)
    salvar(fig, "inflacao_desemprego.png")

    # 3. Heatmap de correlação ----------------------------------------------
    corr = du.matriz_correlacao(df)
    corr.index = [du.ROTULOS.get(c, c).split(" (")[0] for c in corr.index]
    corr.columns = [du.ROTULOS.get(c, c).split(" (")[0] for c in corr.columns]
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0,
                linewidths=0.5, linecolor="white", square=True,
                cbar_kws={"shrink": 0.7}, annot_kws={"size": 8}, ax=ax)
    ax.set_title("Matriz de correlação dos indicadores")
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
    salvar(fig, "heatmap_correlacao.png")

    # 4. Heatmap trimestral do PIB (ano x trimestre) ------------------------
    piv = df.pivot_table(index="ano", columns="trimestre", values="pib")
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(piv / 1e6, annot=True, fmt=".2f", cmap="YlGnBu",
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "PIB (R$ milhões/1e6)"}, ax=ax)
    ax.set_title("PIB por ano e trimestre")
    ax.set_xlabel("Trimestre")
    ax.set_ylabel("Ano")
    salvar(fig, "heatmap_trimestral.png")

    # 5. Barras comparativas por nível econômico ----------------------------
    med = (df.groupby("nivel_economico")[["pib", "inflacao", "taxa_desemprego",
           "taxa_juros", "cambio_dolar"]].mean())
    ordem = [n for n in ["Crise", "Estabilidade", "Crescimento"]
             if n in med.index]
    med = med.reindex(ordem)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, col, titulo in zip(
        axes,
        ["pib", "inflacao", "taxa_desemprego"],
        ["PIB médio", "Inflação média (%)", "Desemprego médio (%)"],
    ):
        valores = med[col] / (1e6 if col == "pib" else 1)
        cores = [CORES_NIVEL[n] for n in med.index]
        ax.bar(med.index, valores, color=cores, edgecolor="white")
        ax.set_title(titulo)
        ax.set_xlabel("")
        for i, v in enumerate(valores):
            ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    fig.suptitle("Indicadores médios por nível econômico", y=1.03,
                 fontsize=14, fontweight="bold")
    salvar(fig, "barras_comparativas.png")

    # 6. Radar de indicadores por nível econômico ---------------------------
    cols_radar = ["pib", "inflacao", "taxa_juros", "taxa_desemprego",
                  "cambio_dolar", "consumo_familias"]
    norm = (df.groupby("nivel_economico")[cols_radar].mean())
    norm = (norm - df[cols_radar].min()) / (df[cols_radar].max() - df[cols_radar].min())
    rotulos = [du.ROTULOS.get(c, c).split(" (")[0] for c in cols_radar]
    angulos = np.linspace(0, 2 * np.pi, len(cols_radar), endpoint=False).tolist()
    angulos += angulos[:1]
    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True))
    for nivel in ordem:
        valores = norm.loc[nivel].tolist()
        valores += valores[:1]
        ax.plot(angulos, valores, color=CORES_NIVEL[nivel], lw=2, label=nivel)
        ax.fill(angulos, valores, color=CORES_NIVEL[nivel], alpha=0.12)
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(rotulos, fontsize=9)
    ax.set_yticklabels([])
    ax.set_title("Radar de indicadores (normalizado) por nível", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=False)
    salvar(fig, "radar_indicadores.png")

    print("\nTodas as figuras foram geradas em:", PASTA)


if __name__ == "__main__":
    main()
