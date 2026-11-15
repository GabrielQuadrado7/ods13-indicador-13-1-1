"""Tabelas CSV, gráficos e resumo.md a partir do banco."""
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from ods13.db import ErroConfiguracao
from ods13.estatistica import (ANO_BASE, _ordenar_localidades, carregar_observacoes,
                               classe_modal, descritiva_por_ano, descritiva_por_localidade,
                               regressoes)
from ods13.formatacao import fmt, formatar_equacao
from ods13.graficos import gerar_graficos

__all__ = ["fmt", "gerar_saidas"]

AVISO_N7 = ("Regressões nacionais e regionais têm n = 7: baixa robustez; "
            "os picos de 2020–2021 pesam muito.")
RNV = ("Referência (RNV 2024, período 2016–2022): média nacional de 430,7 e Região Norte "
       "de 1.060,6 pessoas mortas, desaparecidas ou afetadas por 100 mil habitantes.")


def _csv(df: pd.DataFrame, caminho: Path, index: bool = False) -> None:
    df.round(4).to_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig", index=index)


def _verificar_banco(engine: Engine) -> None:
    with engine.connect() as c:
        existe = c.execute(text("SELECT to_regclass('ods13.vw_observacao')")).scalar()
    if existe is None:
        raise ErroConfiguracao("O banco ainda não tem os dados. Rode primeiro: python etl/carregar.py")


def _observacoes_largo(df: pd.DataFrame) -> pd.DataFrame:
    valores = df.pivot(index="nome", columns="ano", values="valor")
    valores.columns = [str(c) for c in valores.columns]
    meta = df[["nome", "sigla", "nivel", "regiao"]].drop_duplicates()
    largo = meta.merge(valores, left_on="nome", right_index=True)
    return _ordenar_localidades(largo).drop(columns=["regiao"])


def _resumo(df, por_ano, regs, modal_total) -> str:
    nulos = df[df.valor.isna()].sort_values(["ano", "nome"])
    anos = sorted(df.ano.unique())
    L = ["# Indicador 13.1.1 — resumo dos resultados", "",
         f"- Período: {anos[0]}–{anos[-1]} · {df.nome.nunique()} localidades "
         "(Brasil, 5 Grandes Regiões, 27 UFs)",
         f"- Valores sem dado (\"...\"): {', '.join(f'{r.nome} {r.ano}' for r in nulos.itertuples())}",
         "", "## Estatística descritiva por ano (entre as UFs)", "",
         "| Ano | n | Média | Mediana | Desvio padrão | Classe modal (freq.) |",
         "|---|---|---|---|---|---|"]
    for ano, r in por_ano.iterrows():
        L.append(f"| {ano} | {int(r.n)} | {fmt(r.media)} | {fmt(r.mediana)} | {fmt(r.desvio_padrao)} | "
                 f"[{fmt(r.classe_modal_inf)}; {fmt(r.classe_modal_sup)}) ({int(r.classe_modal_freq)}) |")
    inf, sup, f = modal_total
    contagem = df[df.nivel == "uf"].valor.dropna().value_counts()
    L += ["", f"Classe modal de todas as UFs agrupadas (Sturges): [{fmt(inf)}; {fmt(sup)}) com {f} valores. "
          "A distribuição é muito assimétrica (maioria dos valores baixos).", "",
          f"Moda dos valores brutos (UFs agrupadas): {fmt(contagem.index[0])} "
          f"({int(contagem.iloc[0])} ocorrências); como quase nenhum valor se repete, "
          "a classe modal descreve melhor a distribuição.",
          "", "## Regressão linear simples (Y = taxa, X = ano)", ""]
    for g in regs:
        L += [f"### {g.serie}", "",
              f"- {formatar_equacao(g.a, g.b)}",
              f"- {formatar_equacao(g.a, g.b_ano_2018, f'(ano − {ANO_BASE})')}",
              f"- r = {fmt(g.r, 4)} · r² = {fmt(g.r2, 4)} · p-valor = {fmt(g.p_valor, 4)} · n = {g.n}", ""]
    L += ["## Observações para a Discussão", "", f"- {AVISO_N7}", f"- {RNV}", ""]
    return "\n".join(L)


def gerar_saidas(engine: Engine, pasta: Path) -> None:
    _verificar_banco(engine)
    pasta = Path(pasta)
    tabelas = pasta / "tabelas"
    tabelas.mkdir(parents=True, exist_ok=True)
    df = carregar_observacoes(engine)
    por_ano = descritiva_por_ano(df)
    regs = regressoes(df)
    _csv(por_ano, tabelas / "descritiva_por_ano.csv", index=True)
    _csv(descritiva_por_localidade(df), tabelas / "descritiva_por_localidade.csv")
    _csv(pd.DataFrame([asdict(g) for g in regs]), tabelas / "regressoes.csv")
    _csv(_observacoes_largo(df), tabelas / "observacoes.csv")
    gerar_graficos(df, pasta / "graficos")
    modal = classe_modal(df[df.nivel == "uf"].valor)
    (pasta / "resumo.md").write_text(_resumo(df, por_ano, regs, modal), encoding="utf-8")
