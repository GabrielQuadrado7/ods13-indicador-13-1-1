from ods13.formatacao import fmt, formatar_equacao


def test_fmt():
    assert fmt(1213.7889) == "1.213,79"
    assert fmt(-117102.7464) == "-117.102,75"
    assert fmt(0.36266, 4) == "0,3627"


def test_formatar_equacao_virgula_decimal():
    assert formatar_equacao(58.2036, -117102.7464) == "ŷ = 58,20·x − 117.102,75"
    assert formatar_equacao(58.2036, 352.0607, "(ano − 2018)") == "ŷ = 58,20·(ano − 2018) + 352,06"
    assert formatar_equacao(-11.5036, 486.6821) == "ŷ = −11,50·x + 486,68"
