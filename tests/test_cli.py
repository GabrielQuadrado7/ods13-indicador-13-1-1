import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _modulo(caminho):
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("script", ["etl/carregar.py", "analise/analisar.py"])
def test_senha_errada_mensagem_clara(script, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:senha_errada_xyz@localhost:5432/ods13_teste")
    assert _modulo(RAIZ / script).main() == 1
    saida = capsys.readouterr().out
    assert "Não foi possível conectar ao PostgreSQL" in saida and "Traceback" not in saida
