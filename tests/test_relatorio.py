import pandas as pd
import pytest
from pytest import approx
from sqlalchemy import text

from ods13.db import ErroConfiguracao, preparar_banco
from ods13.relatorio import fmt, gerar_saidas


def test_fmt_reexportado():
    assert fmt(1213.7889) == "1.213,79"


def test_gerar_saidas(engine_carregado, tmp_path):
    gerar_saidas(engine_carregado, tmp_path)
    ler = lambda nome: pd.read_csv(tmp_path / "tabelas" / nome, sep=";", decimal=",", encoding="utf-8-sig")
    t = ler("descritiva_por_localidade.csv")
    assert t.set_index("nome").loc["Brasil", "media"] == approx(526.6714, abs=1e-3)
    assert "São Paulo" in set(t.nome)
    ano = ler("descritiva_por_ano.csv").set_index("ano")
    assert ano.loc[2018, "n"] == 24 and ano.loc[2021, "media"] == approx(1213.7889, abs=1e-3)
    reg = ler("regressoes.csv").set_index("serie")
    assert reg.loc["Brasil", "a"] == approx(58.2036, abs=1e-3) and reg.loc["UFs (agrupadas)", "n"] == 185
    obs = ler("observacoes.csv")
    assert len(obs) == 33 and {"2018", "2024"} <= set(obs.columns)
    r = (tmp_path / "resumo.md").read_text(encoding="utf-8")
    assert "ŷ = 58,20·x − 117.102,75" in r and "352,06" in r and "n = 7" in r
    assert "430,7" in r and "Tocantins 2019" in r
    assert "Moda dos valores brutos (UFs agrupadas): 0,00 (5 ocorrências)" in r
    assert "não se repetem" not in r
    assert len(list((tmp_path / "graficos").glob("*.png"))) == 11


def test_sem_views_da_erro_claro(engine, tmp_path):
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA ods13 CASCADE"))
    try:
        with pytest.raises(ErroConfiguracao, match="etl/carregar.py"):
            gerar_saidas(engine, tmp_path)
    finally:
        preparar_banco(engine)
