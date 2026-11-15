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
