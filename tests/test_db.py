import pytest
from sqlalchemy import text

from ods13.db import ErroConfiguracao, preparar_banco, url_do_ambiente


def _linhas(engine, sql):
    with engine.connect() as c:
        return c.execute(text(sql)).all()


def test_url_ausente_da_erro_claro(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("ods13.db.load_dotenv", lambda *a, **k: None)
    with pytest.raises(ErroConfiguracao, match="config.example.env"):
        url_do_ambiente()


def test_url_vazia_da_erro_claro(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "  ")
    monkeypatch.setattr("ods13.db.load_dotenv", lambda *a, **k: None)
    with pytest.raises(ErroConfiguracao, match="config.example.env"):
        url_do_ambiente()


def test_seed_tem_33_localidades_por_nivel(engine):
    contagem = dict(_linhas(engine, "SELECT nivel::text, count(*) FROM ods13.localidade GROUP BY nivel"))
    assert contagem == {"pais": 1, "regiao": 5, "uf": 27}


def test_hierarquia(engine):
    pais = _linhas(engine, """
        SELECT f.nivel::text, p.nivel::text, count(*) FROM ods13.localidade f
        LEFT JOIN ods13.localidade p ON p.id_localidade = f.id_pai
        GROUP BY 1, 2 ORDER BY 1""")
    assert sorted(pais) == [("pais", None, 1), ("regiao", "pais", 5), ("uf", "regiao", 27)]
    pai_brasil = _linhas(engine, """
        SELECT DISTINCT p.nome FROM ods13.localidade f
        JOIN ods13.localidade p ON p.id_localidade = f.id_pai WHERE f.nivel = 'regiao'""")
    assert pai_brasil == [("Brasil",)]
    detalhes = dict((n, (s, p)) for n, s, p in _linhas(engine, """
        SELECT f.nome, f.sigla, p.nome FROM ods13.localidade f
        JOIN ods13.localidade p ON p.id_localidade = f.id_pai
        WHERE f.nome IN ('Rondônia', 'Distrito Federal')"""))
    assert detalhes == {"Rondônia": ("RO", "Norte"), "Distrito Federal": ("DF", "Centro-Oeste")}


def test_preparar_banco_e_reexecutavel(engine):
    preparar_banco(engine)
    preparar_banco(engine)
    assert _linhas(engine, "SELECT count(*) FROM ods13.localidade") == [(33,)]
