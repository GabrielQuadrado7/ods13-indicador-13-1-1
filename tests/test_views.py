from pytest import approx
from sqlalchemy import text


def _mapas(engine, sql):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql))]


def test_vw_observacao(engine_carregado):
    linhas = _mapas(engine_carregado, "SELECT * FROM ods13.vw_observacao")
    assert len(linhas) == 231
    assert set(linhas[0]) == {"nome", "sigla", "nivel", "regiao", "ano", "valor"}
    ro = next(r for r in linhas if r["nome"] == "Rondônia")
    assert ro["regiao"] == "Norte" and ro["sigla"] == "RO" and ro["nivel"] == "uf"
    assert {r["regiao"] for r in linhas if r["nome"] == "Brasil"} == {None}
    assert {r["regiao"] for r in linhas if r["nome"] == "Sul"} == {"Sul"}


def test_descritiva_ano_uf(engine_carregado):
    t = {r["ano"]: r for r in _mapas(engine_carregado, "SELECT * FROM ods13.vw_descritiva_ano_uf")}
    assert sorted(t) == list(range(2018, 2025))
    assert t[2018]["n"] == 24 and t[2018]["ausentes"] == 3
    assert float(t[2018]["media"]) == approx(139.2417, abs=1e-3)
    assert float(t[2018]["mediana"]) == approx(46.25, abs=1e-3)
    assert t[2019]["n"] == 26 and t[2019]["ausentes"] == 1
    assert float(t[2021]["media"]) == approx(1213.7889, abs=1e-3)
    assert float(t[2021]["mediana"]) == approx(406.4, abs=1e-3)
    assert float(t[2021]["desvio_padrao"]) == approx(1501.0991, abs=1e-3)


def test_descritiva_localidade_brasil(engine_carregado):
    linhas = _mapas(engine_carregado, "SELECT * FROM ods13.vw_descritiva_localidade")
    assert len(linhas) == 33
    b = next(r for r in linhas if r["nome"] == "Brasil")
    assert b["n"] == 7 and b["ausentes"] == 0 and b["nivel"] == "pais"
    assert float(b["media"]) == approx(526.6714, abs=1e-3)
    assert float(b["mediana"]) == approx(440.4, abs=1e-3)
    assert float(b["variancia"]) == approx(120199.9524, abs=1e-3)
    assert float(b["desvio_padrao"]) == approx(346.6986, abs=1e-3)
