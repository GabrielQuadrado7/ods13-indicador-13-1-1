"""Gráficos do indicador 13.1.1 (PNG, 300 dpi, rótulos em português)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ods13.estatistica import (REGIOES, bordas_sturges, descritiva_por_ano,  # noqa: E402
                               descritiva_por_localidade, regressoes)
from ods13.formatacao import fmt, formatar_equacao  # noqa: E402

EIXO_Y = "Mortos, desaparecidos e afetados por 100 mil hab."
FONTE = "Fonte: MI/SEDEC – S2ID; IBGE – estimativas populacionais. Elaboração própria."
DPI = 300


def _slug(nome: str) -> str:
    return nome.lower().replace("-", "_").replace(" ", "_")


def _salvar(fig, pasta: Path, nome: str) -> Path:
    fig.text(0.01, 0.005, FONTE, fontsize=7, color="#555555", ha="left", va="bottom")
    caminho = pasta / nome
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return caminho


def _virgula(eixo):
    eixo.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v, 0)))


def _evolucao(df, pasta):
    fig, ax = plt.subplots(figsize=(9, 5))
    for nome in ["Brasil", *REGIOES]:
        s = df[(df.nome == nome) & (df.nivel != "uf")].sort_values("ano")
        estilo = {"linewidth": 3, "color": "black"} if nome == "Brasil" else {"linewidth": 1.6}
        ax.plot(s.ano, s.valor, marker="o", label=nome, **estilo)
    ax.set(title="Indicador 13.1.1 – Brasil e Grandes Regiões, 2018–2024", xlabel="Ano", ylabel=EIXO_Y)
    ax.set_xticks(sorted(df.ano.unique()))
    _virgula(ax)
    ax.grid(alpha=0.3)
    ax.legend()
    return _salvar(fig, pasta, "evolucao_brasil_regioes.png")


def _media_por_uf(df, pasta):
    t = descritiva_por_localidade(df)
    ufs = t[t.nivel == "uf"].merge(df[["nome", "sigla"]].drop_duplicates(), on="nome")
    ufs = ufs.sort_values("media")
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.barh(ufs.sigla, ufs.media, color="#2b6cb0")
    ax.set(title="Média do indicador 13.1.1 por UF, 2018–2024", xlabel=EIXO_Y, ylabel="UF")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v, 0)))
    ax.grid(axis="x", alpha=0.3)
    return _salvar(fig, pasta, "media_por_uf.png")


def _media_ufs_por_ano(df, pasta):
    t = descritiva_por_ano(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    barras = ax.bar(t.index.astype(str), t.media, color="#2f855a")
    ax.bar_label(barras, labels=[fmt(v, 1) for v in t.media], fontsize=8)
    ax.set(title="Média entre as UFs por ano – indicador 13.1.1", xlabel="Ano", ylabel=EIXO_Y)
    _virgula(ax)
    ax.grid(axis="y", alpha=0.3)
    return _salvar(fig, pasta, "media_ufs_por_ano.png")


def _dispersao(df, reg, pasta):
    if reg.serie == "UFs (agrupadas)":
        s = df[df.nivel == "uf"].dropna(subset=["valor"])
        nome_arquivo, titulo = "dispersao_ufs.png", "todas as UFs"
    else:
        s = df[(df.nome == reg.serie) & (df.nivel != "uf")]
        nome_arquivo, titulo = f"dispersao_{_slug(reg.serie)}.png", reg.serie
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(s.ano, s.valor, color="#c05621", alpha=0.7, label="Observado")
    xs = np.array([s.ano.min(), s.ano.max()], dtype=float)
    rotulo = f"{formatar_equacao(reg.a, reg.b)}\nr = {fmt(reg.r, 4)}   r² = {fmt(reg.r2, 4)}   n = {reg.n}"
    ax.plot(xs, reg.a * xs + reg.b, color="#2b6cb0", linewidth=2, label=rotulo)
    ax.set(title=f"Regressão linear (taxa × ano) – {titulo}", xlabel="Ano", ylabel=EIXO_Y)
    ax.set_xticks(sorted(df.ano.unique()))
    _virgula(ax)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return _salvar(fig, pasta, nome_arquivo)


def _histograma(df, pasta):
    valores = df[df.nivel == "uf"].valor.dropna()
    bordas = bordas_sturges(valores)
    freq, _ = np.histogram(valores, bins=bordas)
    modal = int(np.argmax(freq))
    fig, ax = plt.subplots(figsize=(8, 5))
    cores = ["#c53030" if i == modal else "#a0aec0" for i in range(len(freq))]
    ax.bar(bordas[:-1], freq, width=np.diff(bordas), align="edge", color=cores, edgecolor="white")
    ax.set(title=f"Distribuição dos valores das UFs, 2018–2024 (Sturges, k = {len(freq)})",
           xlabel=EIXO_Y, ylabel="Frequência")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v, 0)))
    ax.annotate(f"Classe modal: [{fmt(bordas[modal])}; {fmt(bordas[modal + 1])})\n{freq[modal]} valores",
                xy=(bordas[modal + 1], freq[modal]), xytext=(10, -20), textcoords="offset points", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    return _salvar(fig, pasta, "histograma_ufs.png")


def gerar_graficos(df: pd.DataFrame, pasta: Path) -> list[Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = [_evolucao(df, pasta), _media_por_uf(df, pasta), _media_ufs_por_ano(df, pasta)]
    arquivos += [_dispersao(df, reg, pasta) for reg in regressoes(df)]
    arquivos.append(_histograma(df, pasta))
    return arquivos
