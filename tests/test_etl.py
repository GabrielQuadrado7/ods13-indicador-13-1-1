from pathlib import Path

import openpyxl
import pandas as pd
import pytest
from sqlalchemy import text

from ods13.etl import ErroValidacao, carregar, ler_planilha, validar

PLANILHA = Path("dados/13-1-1.xlsx")


def _contar(engine, sql):
    with engine.connect() as c:
        return c.execute(text(sql)).one()


def _df(linhas):
    return pd.DataFrame(linhas, columns=["localidade", "ano", "valor"])


def test_ler_planilha_formato_longo():
    df = ler_planilha(PLANILHA)
    assert len(df) == 231 and df.localidade.nunique() == 33
    assert sorted(df.ano.unique()) == list(range(2018, 2025))
    assert not df.localidade.str.startswith("Fonte").any()
    assert df.attrs["descricao"].startswith("Número de mortes")
    assert df.attrs["fonte"].startswith("Fonte:") and "S2ID" in df.attrs["fonte"]


def test_valores_e_nulos():
    df = ler_planilha(PLANILHA)
    v = df.set_index(["localidade", "ano"]).valor
    assert v["Brasil", 2018] == 86.2 and v["Rio Grande do Sul", 2024] == 7220.2
    assert v["Roraima", 2023] == 0.0
    nulos = set(df[df.valor.isna()][["localidade", "ano"]].itertuples(index=False, name=None))
    assert nulos == {("Tocantins", 2019), ("Paraíba", 2018), ("Sergipe", 2018), ("Distrito Federal", 2018)}


def test_espacos_e_reticencias_com_espaco(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Indicador 13.1.1 -  Teste"])
    ws.append(["Brasil, Grande Região e UF", 2018, 2019])
    ws.append(["  Acre  ", " ... ", "5"])
    ws.append(["\n   Fonte: teste"])
    arquivo = tmp_path / "mini.xlsx"
    wb.save(arquivo)
    df = ler_planilha(arquivo)
    assert df.localidade.tolist() == ["Acre", "Acre"]
    assert df.valor.isna().sum() == 1 and df.valor.dropna().tolist() == [5.0]


def test_validar_rejeita_desconhecida():
    with pytest.raises(ErroValidacao, match="Atlântida"):
        validar(_df([("Atlântida", 2018, 1.0)]), {"Acre"}, nulos_esperados=0)


def test_validar_rejeita_negativo():
    with pytest.raises(ErroValidacao, match="negativo"):
        validar(_df([("Acre", 2018, -1.0)]), {"Acre"}, nulos_esperados=0)


def test_validar_rejeita_quantidade_de_nulos():
    with pytest.raises(ErroValidacao, match="nulos"):
        validar(_df([("Acre", 2018, None)] * 5), {"Acre"}, nulos_esperados=4)


def test_carregar_idempotente(engine):
    df = ler_planilha(PLANILHA)
    r1 = carregar(engine, df)
    r2 = carregar(engine, df)
    assert r1.linhas == r2.linhas == 231 and len(r2.nulos) == 4
    assert _contar(engine, "SELECT count(*), count(valor) FROM ods13.observacao") == (231, 227)
    assert _contar(engine, "SELECT count(*) FROM ods13.indicador") == (1,)


def test_carregar_invalido_nao_grava(engine):
    carregar(engine, ler_planilha(PLANILHA))
    antes = _contar(engine, "SELECT count(*) FROM ods13.observacao")
    ruim = _df([("Atlântida", 2018, 1.0)])
    ruim.attrs = {"descricao": "x", "fonte": "y"}
    with pytest.raises(ErroValidacao):
        carregar(engine, ruim)
    assert _contar(engine, "SELECT count(*) FROM ods13.observacao") == antes
