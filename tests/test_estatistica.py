import pandas as pd
from pytest import approx
from sqlalchemy import text

from ods13.estatistica import (carregar_observacoes, classe_modal, descritiva, descritiva_por_ano,
                               descritiva_por_localidade, regressao, regressoes)

BRASIL = pd.Series([86.2, 214.1, 873.6, 1032.8, 440.4, 369.1, 670.5])


def test_descritiva_brasil():
    d = descritiva(BRASIL)
    assert d["n"] == 7 and d["ausentes"] == 0
    assert d["media"] == approx(526.6714, abs=1e-3) and d["mediana"] == 440.4
    assert d["variancia"] == approx(120199.9524, abs=1e-3)
    assert d["desvio_padrao"] == approx(346.6986, abs=1e-3)
    assert d["minimo"] == 86.2 and d["maximo"] == 1032.8


def test_descritiva_ignora_nan():
    d = descritiva(pd.Series([1.0, float("nan"), 3.0]))
    assert d["n"] == 2 and d["ausentes"] == 1 and d["media"] == 2.0


def test_classe_modal_simples():
    inf, sup, f = classe_modal(pd.Series([0, 1, 2, 3, 100.0]))
    assert inf == 0 and sup == 25 and f == 4


def test_regressao_brasil():
    r = regressao("Brasil", pd.Series(range(2018, 2025)), BRASIL)
    assert r.serie == "Brasil"
    assert r.a == approx(58.2036, abs=1e-3) and r.b == approx(-117102.7464, abs=1e-2)
    assert r.b_ano_2018 == approx(352.0607, abs=1e-3) and r.r == approx(0.36266, abs=1e-4)
    assert r.n == 7 and r.r2 == approx(r.r ** 2)


def test_regressao_ignora_pares_com_nan():
    r = regressao("x", pd.Series([2018, 2019, 2020, 2021]), pd.Series([1.0, float("nan"), 3.0, 4.0]))
    assert r.n == 3


def test_regressoes_com_banco(engine_carregado):
    rs = {r.serie: r for r in regressoes(carregar_observacoes(engine_carregado))}
    assert list(rs) == ["Brasil", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste", "UFs (agrupadas)"]
    assert rs["Norte"].a == approx(144.8464, abs=1e-3) and rs["Sul"].r == approx(0.79121, abs=1e-4)
    u = rs["UFs (agrupadas)"]
    assert u.n == 185 and u.a == approx(57.2652, abs=1e-3)
    assert u.b_ano_2018 == approx(452.3691, abs=1e-3) and u.r == approx(0.10356, abs=1e-4)


def test_por_ano_so_ufs_e_bate_com_view(engine_carregado):
    t = descritiva_por_ano(carregar_observacoes(engine_carregado))
    assert list(t.index) == list(range(2018, 2025))
    assert t.loc[2018, "n"] == 24 and t.loc[2018, "ausentes"] == 3
    assert t.loc[2021, "media"] == approx(1213.7889, abs=1e-3)
    assert {"classe_modal_inf", "classe_modal_sup", "classe_modal_freq"} <= set(t.columns)
    with engine_carregado.connect() as c:
        view = {r.ano: r for r in c.execute(text("SELECT * FROM ods13.vw_descritiva_ano_uf"))}
    for ano, linha in t.iterrows():
        for col in ("media", "mediana", "desvio_padrao", "variancia"):
            assert linha[col] == approx(float(getattr(view[ano], col)), abs=1e-6)


def test_por_localidade(engine_carregado):
    t = descritiva_por_localidade(carregar_observacoes(engine_carregado))
    assert len(t) == 33
    assert t.nome.iloc[0] == "Brasil" and list(t.nivel.iloc[1:6]) == ["regiao"] * 5
    assert (t.nivel.iloc[6:] == "uf").all()
    b = t.set_index("nome").loc["Brasil"]
    assert b["media"] == approx(526.6714, abs=1e-3)


def test_classe_modal_ufs_agrupadas(engine_carregado):
    df = carregar_observacoes(engine_carregado)
    inf, sup, f = classe_modal(df[df.nivel == "uf"].valor)
    assert inf == 0 and sup == approx(802.2444, abs=1e-3) and f == 147
