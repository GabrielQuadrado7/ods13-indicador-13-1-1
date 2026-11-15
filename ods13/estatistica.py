"""Estatística descritiva, classe modal e regressão linear (Y = taxa, X = ano)."""
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import Engine

REGIOES = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]
ORDEM_NIVEL = {"pais": 0, "regiao": 1, "uf": 2}
ANO_BASE = 2018


@dataclass
class Regressao:
    serie: str
    a: float
    b: float
    b_ano_2018: float
    r: float
    r2: float
    p_valor: float
    n: int


def carregar_observacoes(engine: Engine) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM ods13.vw_observacao", engine)
    df["valor"] = df["valor"].astype(float)
    df["ano"] = df["ano"].astype(int)
    return df


def descritiva(valores: pd.Series) -> dict:
    v = pd.Series(valores, dtype=float)
    presentes = v.dropna()
    return {
        "n": int(presentes.size),
        "ausentes": int(v.isna().sum()),
        "media": float(presentes.mean()),
        "mediana": float(presentes.median()),
        "variancia": float(presentes.var(ddof=1)),
        "desvio_padrao": float(presentes.std(ddof=1)),
        "minimo": float(presentes.min()),
        "maximo": float(presentes.max()),
    }


def bordas_sturges(valores: pd.Series) -> np.ndarray:
    v = pd.Series(valores, dtype=float).dropna().to_numpy()
    k = math.ceil(1 + 3.322 * math.log10(v.size))
    return np.histogram_bin_edges(v, bins=k)


def classe_modal(valores: pd.Series) -> tuple[float, float, int]:
    v = pd.Series(valores, dtype=float).dropna().to_numpy()
    freq, bordas = np.histogram(v, bins=bordas_sturges(v))
    i = int(np.argmax(freq))
    return float(bordas[i]), float(bordas[i + 1]), int(freq[i])


def descritiva_por_ano(df: pd.DataFrame) -> pd.DataFrame:
    ufs = df[df.nivel == "uf"]
    linhas = {}
    for ano, grupo in ufs.groupby("ano"):
        d = descritiva(grupo.valor)
        d["classe_modal_inf"], d["classe_modal_sup"], d["classe_modal_freq"] = classe_modal(grupo.valor)
        linhas[int(ano)] = d
    t = pd.DataFrame.from_dict(linhas, orient="index").sort_index()
    t.index.name = "ano"
    return t


def _ordenar_localidades(df: pd.DataFrame) -> pd.DataFrame:
    chave_regiao = {r: i for i, r in enumerate(REGIOES)}
    return df.assign(
        _n=df.nivel.map(ORDEM_NIVEL),
        _r=df.regiao.map(chave_regiao).fillna(-1),
    ).sort_values(["_n", "_r", "nome"]).drop(columns=["_n", "_r"])


def descritiva_por_localidade(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for (nome, nivel, regiao), grupo in df.groupby(["nome", "nivel", df.regiao.fillna("")]):
        linhas.append({"nome": nome, "nivel": nivel, "regiao": regiao or None, **descritiva(grupo.valor)})
    t = _ordenar_localidades(pd.DataFrame(linhas))
    return t.drop(columns=["regiao"]).reset_index(drop=True)


def regressao(serie: str, x: pd.Series, y: pd.Series) -> Regressao:
    pares = pd.DataFrame({"x": pd.Series(x, dtype=float).to_numpy(),
                          "y": pd.Series(y, dtype=float).to_numpy()}).dropna()
    res = stats.linregress(pares.x, pares.y)
    return Regressao(
        serie=serie,
        a=float(res.slope),
        b=float(res.intercept),
        b_ano_2018=float(res.intercept + res.slope * ANO_BASE),
        r=float(res.rvalue),
        r2=float(res.rvalue ** 2),
        p_valor=float(res.pvalue),
        n=int(len(pares)),
    )


def regressoes(df: pd.DataFrame) -> list[Regressao]:
    resultado = []
    for nome in ["Brasil", *REGIOES]:
        s = df[(df.nome == nome) & (df.nivel != "uf")].sort_values("ano")
        resultado.append(regressao(nome, s.ano, s.valor))
    ufs = df[df.nivel == "uf"]
    resultado.append(regressao("UFs (agrupadas)", ufs.ano, ufs.valor))
    return resultado
