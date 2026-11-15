"""Carrega a planilha do indicador 13.1.1 no PostgreSQL.

Uso: python etl/carregar.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ods13.db import ErroConfiguracao, criar_engine, preparar_banco, url_do_ambiente  # noqa: E402
from ods13.etl import ErroValidacao, carregar, ler_planilha  # noqa: E402

PLANILHA = Path(__file__).resolve().parent.parent / "dados" / "13-1-1.xlsx"


def main() -> int:
    try:
        engine = criar_engine(url_do_ambiente())
        preparar_banco(engine)
        resumo = carregar(engine, ler_planilha(PLANILHA))
    except (ErroConfiguracao, ErroValidacao) as erro:
        print(f"Erro: {erro}")
        return 1
    print(f"{resumo.linhas} linhas carregadas em ods13.observacao.")
    print(f"{len(resumo.nulos)} valores sem dado (\"...\" -> NULL):")
    for nome, ano in resumo.nulos:
        print(f"  - {nome} {ano}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
