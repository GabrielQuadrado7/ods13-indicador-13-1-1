"""Conexão com o PostgreSQL e execução dos scripts SQL do projeto."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql"


class ErroConfiguracao(RuntimeError):
    """Configuração de conexão ausente ou inválida."""


def url_do_ambiente(variavel: str = "DATABASE_URL") -> str:
    load_dotenv()
    url = (os.getenv(variavel) or "").strip()
    if not url:
        raise ErroConfiguracao(f"Defina {variavel} no arquivo .env (copie config.example.env)")
    return url


def criar_engine(url: str) -> Engine:
    return create_engine(url)


def executar_sql(engine: Engine, caminho: Path) -> None:
    sql = Path(caminho).read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def preparar_banco(engine: Engine) -> None:
    for arquivo in sorted(PASTA_SQL.glob("*.sql")):
        executar_sql(engine, arquivo)
