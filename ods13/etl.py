"""Leitura, validação e carga da planilha do indicador 13.1.1."""
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

CODIGO = "13.1.1"
UNIDADE = "por 100 mil habitantes"
SEM_DADO = {"", "...", "-"}


class ErroValidacao(ValueError):
    """A planilha não tem o formato ou o conteúdo esperado."""


@dataclass
class ResumoCarga:
    linhas: int
    nulos: list[tuple[str, int]] = field(default_factory=list)


def _espacos(texto) -> str:
    return re.sub(r"\s+", " ", str(texto)).strip()


def _valor(celula) -> float:
    if celula is None or (isinstance(celula, float) and pd.isna(celula)):
        return float("nan")
    if isinstance(celula, str):
        celula = celula.strip()
        if celula in SEM_DADO:
            return float("nan")
    return float(celula)


def ler_planilha(caminho: Path) -> pd.DataFrame:
    bruto = pd.read_excel(caminho, header=None, dtype=object)
    titulo = _espacos(bruto.iat[0, 0])
    anos = [int(a) for a in bruto.iloc[1, 1:] if pd.notna(a)]
    fonte = ""
    registros = []
    for _, linha in bruto.iloc[2:].iterrows():
        nome = _espacos(linha.iat[0]) if pd.notna(linha.iat[0]) else ""
        if not nome:
            continue
        if nome.startswith("Fonte"):
            fonte = nome
            continue
        for i, ano in enumerate(anos, start=1):
            registros.append((nome, ano, _valor(linha.iat[i])))
    df = pd.DataFrame(registros, columns=["localidade", "ano", "valor"])
    df["valor"] = df["valor"].astype(float)
    df.attrs["descricao"] = re.sub(r"^Indicador\s+13\.1\.1\s*-\s*", "", titulo)
    df.attrs["fonte"] = fonte
    return df


def validar(df: pd.DataFrame, nomes_conhecidos: set[str], nulos_esperados: int = 4) -> None:
    desconhecidas = sorted(set(df.localidade) - set(nomes_conhecidos))
    if desconhecidas:
        raise ErroValidacao(f"Localidades não cadastradas na tabela localidade: {', '.join(desconhecidas)}")
    negativos = df[df.valor < 0]
    if not negativos.empty:
        casos = ", ".join(f"{r.localidade} {r.ano} ({r.valor})" for r in negativos.itertuples())
        raise ErroValidacao(f"Valor negativo encontrado: {casos}")
    nulos = int(df.valor.isna().sum())
    if nulos != nulos_esperados:
        raise ErroValidacao(f"Esperados {nulos_esperados} valores nulos (\"...\"), encontrados {nulos}")


def carregar(engine: Engine, df: pd.DataFrame) -> ResumoCarga:
    with engine.connect() as conn:
        nomes = {n for (n,) in conn.execute(text("SELECT nome FROM ods13.localidade"))}
    validar(df, nomes)
    with engine.begin() as conn:
        id_indicador = conn.execute(text("""
            INSERT INTO ods13.indicador (codigo, ods, descricao, unidade, fonte)
            VALUES (:codigo, 13, :descricao, :unidade, :fonte)
            ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao,
                unidade = EXCLUDED.unidade, fonte = EXCLUDED.fonte
            RETURNING id_indicador"""),
            {"codigo": CODIGO, "descricao": df.attrs["descricao"], "unidade": UNIDADE,
             "fonte": df.attrs["fonte"]}).scalar_one()
        parametros = [
            {"nome": r.localidade, "ind": id_indicador, "ano": int(r.ano),
             "valor": None if pd.isna(r.valor) else float(r.valor)}
            for r in df.itertuples()]
        conn.execute(text("""
            INSERT INTO ods13.observacao (id_localidade, id_indicador, ano, valor)
            SELECT id_localidade, :ind, :ano, :valor FROM ods13.localidade WHERE nome = :nome
            ON CONFLICT (id_localidade, id_indicador, ano) DO UPDATE SET valor = EXCLUDED.valor"""),
            parametros)
    nulos = [(r.localidade, int(r.ano)) for r in df[df.valor.isna()].itertuples()]
    return ResumoCarga(linhas=len(df), nulos=nulos)
