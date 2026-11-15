"""Formatação de números no padrão brasileiro (vírgula decimal, ponto de milhar)."""

MENOS = "\u2212"


def fmt(numero: float, casas: int = 2) -> str:
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def formatar_equacao(a: float, b: float, variavel: str = "x") -> str:
    coef = f"{MENOS}{fmt(abs(a))}" if a < 0 else fmt(a)
    sinal = MENOS if b < 0 else "+"
    return f"ŷ = {coef}·{variavel} {sinal} {fmt(abs(b))}"
