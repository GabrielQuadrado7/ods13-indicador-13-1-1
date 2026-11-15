from pathlib import Path

import openpyxl
import pandas as pd
import pytest
from sqlalchemy import text

from ods13.etl import ErroValidacao, carregar, ler_planilha, recarregar, validar

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
        validar(_df([("Atlântida", 2018, 1.0)]), {"Acre"}, nulos_esperados=0, anos_esperados=[2018])


def test_validar_rejeita_negativo():
    with pytest.raises(ErroValidacao, match="negativo"):
        validar(_df([("Acre", 2018, -1.0)]), {"Acre"}, nulos_esperados=0, anos_esperados=[2018])


def test_validar_rejeita_quantidade_de_nulos():
    with pytest.raises(ErroValidacao, match="nulos"):
        validar(_df([("Acre", a, None) for a in range(2018, 2023)]), {"Acre"}, nulos_esperados=4,
                anos_esperados=range(2018, 2023))


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


def _mini(tmp_path, cabecalho, linhas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Indicador 13.1.1 -  Teste"])
    ws.append(["Brasil, Grande Região e UF", *cabecalho])
    for linha in linhas:
        ws.append(linha)
    ws.append(["Fonte: teste"])
    arquivo = tmp_path / "mini.xlsx"
    wb.save(arquivo)
    return arquivo


def test_recarregar_invalido_preserva_dados(engine):
    carregar(engine, ler_planilha(PLANILHA))
    ruim = ler_planilha(PLANILHA)
    ruim.loc[0, "valor"] = -1.0
    with pytest.raises(ErroValidacao, match="negativo"):
        recarregar(engine, ruim)
    assert _contar(engine, "SELECT count(*), count(valor) FROM ods13.observacao") == (231, 227)


def test_recarregar_valido(engine):
    resumo = recarregar(engine, ler_planilha(PLANILHA))
    assert resumo.linhas == 231
    assert _contar(engine, "SELECT count(*) FROM ods13.observacao") == (231,)


def test_validar_rejeita_localidade_faltando():
    df = ler_planilha(PLANILHA)
    df = df[df.localidade != "Acre"]
    with pytest.raises(ErroValidacao, match="Acre"):
        validar(df, set(ler_planilha(PLANILHA).localidade))


def test_validar_rejeita_duplicada():
    df = ler_planilha(PLANILHA)
    df = pd.concat([df, df[(df.localidade == "Brasil") & (df.ano == 2018)].assign(valor=999.9)])
    with pytest.raises(ErroValidacao, match="duplicad"):
        validar(df, set(df.localidade))


def test_validar_rejeita_anos_diferentes():
    df = ler_planilha(PLANILHA)
    df.loc[df.ano == 2024, "ano"] = 2042
    with pytest.raises(ErroValidacao, match="2042"):
        validar(df, set(df.localidade))


def test_celula_numerica_invalida_nomeia_localidade(tmp_path):
    arquivo = _mini(tmp_path, [2018], [["Acre", "1.234,5"]])
    with pytest.raises(ErroValidacao, match="Acre.*2018"):
        ler_planilha(arquivo)


def test_coluna_vazia_no_cabecalho_nao_desalinha(tmp_path):
    arquivo = _mini(tmp_path, [2018, None, 2019], [["Acre", 1, 99, 2]])
    df = ler_planilha(arquivo).set_index("ano").valor
    assert df[2018] == 1.0 and df[2019] == 2.0
