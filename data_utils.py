"""
data_utils.py
=============
Funções centrais de carga, limpeza, engenharia de atributos, cálculo de KPIs
e persistência em banco de dados (SQLite via SQLAlchemy) para o projeto
"Indicadores Econômicos do Brasil (2015-2024)".

Este módulo é compartilhado pelo notebook de análise e pelo dashboard Streamlit,
garantindo que a mesma regra de negócio seja aplicada nos dois lugares.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Caminhos padrão do projeto
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_PADRAO = BASE_DIR / "dados" / "simulacao_indicadores_economicos_brasil.csv"
DB_PADRAO = BASE_DIR / "database" / "indicadores.db"

# Colunas numéricas de indicadores econômicos
COLUNAS_INDICADORES = [
    "pib", "inflacao", "taxa_juros", "taxa_desemprego", "cambio_dolar",
    "renda_media", "consumo_familias", "investimento", "exportacoes", "importacoes",
]

# Rótulos amigáveis (usados nos gráficos e filtros do dashboard)
ROTULOS = {
    "pib": "PIB (R$ milhões)",
    "inflacao": "Inflação (%)",
    "taxa_juros": "Taxa de juros / Selic (%)",
    "taxa_desemprego": "Desemprego (%)",
    "cambio_dolar": "Câmbio (R$/US$)",
    "renda_media": "Renda média (R$)",
    "consumo_familias": "Consumo das famílias (índice)",
    "investimento": "Investimento (índice)",
    "exportacoes": "Exportações (US$ bi)",
    "importacoes": "Importações (US$ bi)",
    "saldo_comercial": "Saldo comercial (US$ bi)",
    "indice_miseria": "Índice de miséria (infl.+desemp.)",
    "pib_var_anual": "Crescimento do PIB a/a (%)",
    "pib_var_tri": "Variação do PIB t/t (%)",
}


# ---------------------------------------------------------------------------
# 1. Carga e limpeza
# ---------------------------------------------------------------------------
def carregar_dados(fonte=CSV_PADRAO) -> pd.DataFrame:
    """Lê o CSV (caminho ou objeto file-like, ex.: upload do Streamlit).

    Faz a limpeza mínima: remove espaços/BOM dos nomes de coluna, converte
    tipos, remove duplicatas e ordena cronologicamente.
    """
    df = pd.read_csv(fonte)

    # Normaliza nomes de coluna (remove BOM/espaços e padroniza minúsculas)
    df.columns = (
        df.columns.str.strip()
        .str.replace("\ufeff", "", regex=False)
        .str.lower()
    )

    # Conversões de tipo
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for col in COLUNAS_INDICADORES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ano"] = df["ano"].astype(int)
    df["trimestre"] = df["trimestre"].astype(int)
    df["nivel_economico"] = df["nivel_economico"].astype(str).str.strip().str.title()

    # Qualidade: duplicatas e ordenação
    df = df.drop_duplicates().sort_values("data").reset_index(drop=True)
    return df


def diagnostico_qualidade(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo de qualidade por coluna (tipo, nulos, % nulos, valores únicos)."""
    diag = pd.DataFrame({
        "tipo": df.dtypes.astype(str),
        "nulos": df.isna().sum(),
        "pct_nulos": (df.isna().mean() * 100).round(2),
        "unicos": df.nunique(),
    })
    return diag


# ---------------------------------------------------------------------------
# 2. Engenharia de atributos
# ---------------------------------------------------------------------------
def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Cria atributos derivados com significado econômico."""
    df = df.copy().sort_values("data").reset_index(drop=True)

    # Rótulo de período (ex.: 2015-T1) e período pandas
    df["ano_tri"] = df["ano"].astype(str) + "-T" + df["trimestre"].astype(str)
    df["periodo"] = df["data"].dt.to_period("Q").astype(str)

    # Saldo comercial (balança comercial)
    df["saldo_comercial"] = df["exportacoes"] - df["importacoes"]

    # Índice de miséria = inflação + desemprego (clássico da macroeconomia)
    df["indice_miseria"] = df["inflacao"] + df["taxa_desemprego"]

    # Variação do PIB trimestre a trimestre (t/t) e ano a ano (a/a)
    df["pib_var_tri"] = df["pib"].pct_change() * 100
    df["pib_var_anual"] = df["pib"].pct_change(periods=4) * 100

    # Poder de consumo relativo (consumo em relação à renda)
    df["consumo_sobre_renda"] = df["consumo_familias"] / df["renda_media"] * 1000

    return df


# ---------------------------------------------------------------------------
# 3. KPIs
# ---------------------------------------------------------------------------
def calcular_kpis(df: pd.DataFrame) -> dict:
    """Retorna o dicionário de KPIs exigidos pelo tema.

    Quando possível, inclui o 'delta' (comparação do último período filtrado
    com o período imediatamente anterior) para alimentar KPIs dinâmicos.
    """
    if df.empty:
        return {}

    def _delta(col):
        s = df[col].dropna()
        if len(s) < 2:
            return None
        return float(s.iloc[-1] - s.iloc[-2])

    kpis = {
        "pib_medio": float(df["pib"].mean()),
        "inflacao_media": float(df["inflacao"].mean()),
        "desemprego_medio": float(df["taxa_desemprego"].mean()),
        "juros_medio": float(df["taxa_juros"].mean()),
        "dolar_medio": float(df["cambio_dolar"].mean()),
        # Crescimento econômico médio = média do crescimento do PIB a/a
        "crescimento_medio": float(df["pib_var_anual"].mean(skipna=True))
        if "pib_var_anual" in df else np.nan,
        # Deltas (último vs. penúltimo período) para KPIs dinâmicos
        "pib_delta": _delta("pib"),
        "inflacao_delta": _delta("inflacao"),
        "desemprego_delta": _delta("taxa_desemprego"),
        "juros_delta": _delta("taxa_juros"),
        "dolar_delta": _delta("cambio_dolar"),
    }
    return kpis


def resumo_por_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Médias anuais dos principais indicadores (para gráficos de barras)."""
    agg = {
        "pib": "mean", "inflacao": "mean", "taxa_juros": "mean",
        "taxa_desemprego": "mean", "cambio_dolar": "mean", "renda_media": "mean",
        "consumo_familias": "mean", "investimento": "mean",
        "saldo_comercial": "mean",
    }
    agg = {k: v for k, v in agg.items() if k in df.columns}
    return df.groupby("ano").agg(agg).round(2).reset_index()


def matriz_correlacao(df: pd.DataFrame) -> pd.DataFrame:
    """Correlação de Pearson entre os indicadores econômicos."""
    cols = [c for c in COLUNAS_INDICADORES if c in df.columns]
    return df[cols].corr(method="pearson").round(3)


# ---------------------------------------------------------------------------
# 4. Persistência em banco de dados (SQLAlchemy + SQLite)
#    Modelagem relacional: tabela fato (indicadores) + dimensão (niveis).
# ---------------------------------------------------------------------------
def criar_banco(df: pd.DataFrame, caminho_db=DB_PADRAO):
    """Cria/atualiza um banco SQLite com modelagem relacional simples.

    - Tabela dimensão `niveis`  : id_nivel, nivel_economico, descricao
    - Tabela fato      `indicadores` : dados + id_nivel (chave estrangeira)

    Demonstra: persistência em banco, modelagem relacional e integração
    entre tabelas (JOIN em `consultar_banco`).
    """
    from sqlalchemy import (Column, Float, ForeignKey, Integer, String,
                            create_engine)
    from sqlalchemy.orm import declarative_base, relationship, sessionmaker

    caminho_db = Path(caminho_db)
    caminho_db.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{caminho_db}", echo=False)
    Base = declarative_base()

    class Nivel(Base):
        __tablename__ = "niveis"
        id_nivel = Column(Integer, primary_key=True)
        nivel_economico = Column(String, unique=True, nullable=False)
        descricao = Column(String)
        registros = relationship("Indicador", back_populates="nivel")

    class Indicador(Base):
        __tablename__ = "indicadores"
        id = Column(Integer, primary_key=True, autoincrement=True)
        ano = Column(Integer)
        trimestre = Column(Integer)
        data = Column(String)
        pib = Column(Float)
        inflacao = Column(Float)
        taxa_juros = Column(Float)
        taxa_desemprego = Column(Float)
        cambio_dolar = Column(Float)
        renda_media = Column(Float)
        consumo_familias = Column(Float)
        investimento = Column(Float)
        exportacoes = Column(Float)
        importacoes = Column(Float)
        id_nivel = Column(Integer, ForeignKey("niveis.id_nivel"))
        nivel = relationship("Nivel", back_populates="registros")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    sessao = Session()

    descricoes = {
        "Crise": "Retração ou forte instabilidade da atividade econômica.",
        "Estabilidade": "Atividade econômica estável, sem grandes oscilações.",
        "Crescimento": "Expansão da atividade econômica.",
    }
    mapa_nivel = {}
    for i, nivel in enumerate(sorted(df["nivel_economico"].unique()), start=1):
        obj = Nivel(id_nivel=i, nivel_economico=nivel,
                    descricao=descricoes.get(nivel, ""))
        sessao.add(obj)
        mapa_nivel[nivel] = i
    sessao.commit()

    for _, linha in df.iterrows():
        sessao.add(Indicador(
            ano=int(linha["ano"]), trimestre=int(linha["trimestre"]),
            data=str(pd.to_datetime(linha["data"]).date()),
            pib=float(linha["pib"]), inflacao=float(linha["inflacao"]),
            taxa_juros=float(linha["taxa_juros"]),
            taxa_desemprego=float(linha["taxa_desemprego"]),
            cambio_dolar=float(linha["cambio_dolar"]),
            renda_media=float(linha["renda_media"]),
            consumo_familias=float(linha["consumo_familias"]),
            investimento=float(linha["investimento"]),
            exportacoes=float(linha["exportacoes"]),
            importacoes=float(linha["importacoes"]),
            id_nivel=mapa_nivel[linha["nivel_economico"]],
        ))
    sessao.commit()
    sessao.close()
    return caminho_db


def consultar_banco(sql: str, caminho_db=DB_PADRAO) -> pd.DataFrame:
    """Executa uma consulta SQL arbitrária no banco e devolve um DataFrame.

    Usado pelo dashboard para demonstrar integração entre tabelas (JOIN).
    """
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{Path(caminho_db)}", echo=False)
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


# ---------------------------------------------------------------------------
# Execução direta: (re)constrói o banco a partir do CSV padrão
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = preparar_dados(carregar_dados())
    print(f"Registros carregados: {len(df)}")
    print("KPIs:", {k: round(v, 2) for k, v in calcular_kpis(df).items()
                    if v is not None})
    destino = criar_banco(df)
    print(f"Banco criado em: {destino}")
