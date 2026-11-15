"""Gera tabelas, gráficos e resumo do indicador 13.1.1 a partir do banco.

Uso: python analise/analisar.py   (rode antes: python etl/carregar.py)
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ods13.db import ErroConfiguracao, criar_engine, url_do_ambiente  # noqa: E402
from ods13.relatorio import gerar_saidas  # noqa: E402


def main() -> int:
    saida = RAIZ / "saida"
    try:
        gerar_saidas(criar_engine(url_do_ambiente()), saida)
    except ErroConfiguracao as erro:
        print(f"Erro: {erro}")
        return 1
    print(f"Saídas geradas em {saida}:")
    print("  - tabelas/ (CSV para Excel)\n  - graficos/ (PNG 300 dpi)\n  - resumo.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
