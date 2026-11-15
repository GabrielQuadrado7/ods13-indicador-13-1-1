import os

import pytest
from dotenv import load_dotenv

from ods13.db import criar_engine, preparar_banco


@pytest.fixture(scope="session")
def engine():
    load_dotenv()
    url = os.getenv("ODS13_TEST_DATABASE_URL")
    if not url:
        pytest.exit("Defina ODS13_TEST_DATABASE_URL no arquivo .env (copie config.example.env)", returncode=2)
    eng = criar_engine(url)
    preparar_banco(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def engine_carregado(engine):
    from pathlib import Path

    from ods13.etl import carregar, ler_planilha

    carregar(engine, ler_planilha(Path("dados/13-1-1.xlsx")))
    return engine
