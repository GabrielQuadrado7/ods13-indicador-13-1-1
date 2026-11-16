"""Preenche o template do artigo com os resultados do indicador 13.1.1.

Uso (depois de etl/carregar.py e analise/analisar.py):
    python artigo/montar_artigo.py
Gera Artigo_ODS13_Indicador_13-1-1.docx na raiz do projeto a partir de saida/.
Os textos com números citados estão neste script; revise-os se os dados mudarem.
"""
import copy
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

RAIZ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "saida"
G = SAIDA / "graficos"
d = docx.Document(RAIZ / "Template_Artigo_Cientifico_Projeto_ODS (1).docx")
P = list(d.paragraphs)  # índices do template original
MODELO = copy.deepcopy(P[10]._p)  # parágrafo de corpo: Arial, 1,5, justificado


# ---------------------------------------------------------------- utilitários
def limpar(p):
    for r in list(p._p):
        if r.tag in (qn("w:r"), qn("w:hyperlink")):
            p._p.remove(r)


def run(p, texto, bold=False, italic=False, size=None, mono=False, destacar=False):
    r = p.add_run(texto)
    r.font.name = "Courier New" if mono else "Arial"
    r._r.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), r.font.name)
    r.bold = bold or None
    r.italic = italic or None
    if size:
        r.font.size = Pt(size)
    if destacar:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return r


def escrever(p, partes):
    """partes: str ou lista de (texto, dict de formatação)."""
    if isinstance(partes, str):
        partes = [(partes, {})]
    for texto, fmt in partes:
        run(p, texto, **fmt)
    return p


def substituir(p, partes):
    limpar(p)
    return escrever(p, partes)


def apos(ancora, partes="", alinhamento=None, tamanho=None, recuo=True, espaco=None):
    novo = copy.deepcopy(MODELO)
    ancora_el = ancora._p if hasattr(ancora, "_p") else ancora
    ancora_el.addnext(novo)
    p = docx.text.paragraph.Paragraph(novo, ancora._parent if hasattr(ancora, "_parent") else d._body)
    limpar(p)
    if recuo:
        p.paragraph_format.first_line_indent = Cm(1.25)
    if alinhamento is not None:
        p.alignment = alinhamento
        p.paragraph_format.first_line_indent = Cm(0)
    if espaco is not None:
        p.paragraph_format.line_spacing = espaco
    if partes:
        if tamanho:
            partes = [(t, {**f, "size": tamanho}) for t, f in
                      ([(partes, {})] if isinstance(partes, str) else partes)]
        escrever(p, partes)
    return p


def remover(p):
    p._p.getparent().remove(p._p)


class Cursor:
    """Insere blocos em sequência após uma âncora."""

    def __init__(self, ancora):
        self.atual = ancora

    def par(self, partes, **kw):
        self.atual = apos(self.atual, partes, **kw)
        return self.atual

    def legenda(self, texto):
        p = self.par([(texto, {"bold": True})], alinhamento=WD_ALIGN_PARAGRAPH.CENTER, tamanho=10,
                     espaco=1.0)
        p.paragraph_format.keep_with_next = True
        return p

    def fonte(self, texto="Fonte: elaboração própria a partir de dados do S2ID (MIDR/SEDEC) e do IBGE."):
        return self.par(texto, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, tamanho=10, espaco=1.0)

    def figura(self, titulo, arquivo, largura=15):
        self.legenda(titulo)
        p = self.par("", alinhamento=WD_ALIGN_PARAGRAPH.CENTER, espaco=1.0)
        p.add_run().add_picture(str(G / arquivo), width=Cm(largura))
        p.paragraph_format.keep_with_next = True
        self.fonte()

    def tabela(self, titulo, cabecalho, linhas, larguras, fonte=None):
        self.legenda(titulo)
        t = d.add_table(rows=1 + len(linhas), cols=len(cabecalho))
        t.alignment = 1
        bordas_abnt(t)
        for i, linha in enumerate([cabecalho, *linhas]):
            for j, valor in enumerate(linha):
                cel = t.cell(i, j)
                cel.width = Cm(larguras[j])
                p = cel.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                run(p, str(valor), bold=(i == 0), size=9)
        self.atual._p.addnext(t._tbl)
        self.atual = t._tbl
        self.fonte(fonte) if fonte else self.fonte()

    def codigo(self, linhas):
        for linha in linhas:
            p = self.par([(linha, {"mono": True, "size": 8})], alinhamento=WD_ALIGN_PARAGRAPH.LEFT, espaco=1.0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)


def bordas_abnt(tabela):
    """Tabela no padrão IBGE/ABNT: só linhas horizontais (topo, cabeçalho, base)."""
    tbl_pr = tabela._tbl.tblPr
    bordas = OxmlElement("w:tblBorders")
    for lado in ("top", "bottom"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "8"); b.set(qn("w:color"), "000000")
        bordas.append(b)
    for lado in ("left", "right", "insideV", "insideH"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "nil")
        bordas.append(b)
    tbl_pr.append(bordas)
    for cel in tabela.rows[0].cells:
        tc_pr = cel._tc.get_or_add_tcPr()
        tb = OxmlElement("w:tcBorders")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6"); b.set(qn("w:color"), "000000")
        tb.append(b)
        tc_pr.append(tb)


def br(v, casas=2):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ---------------------------------------------------------------- dados
import csv  # noqa: E402


def ler(nome):
    with open(SAIDA / "tabelas" / nome, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    return [{k: (float(v.replace(",", ".")) if k not in ("nome", "nivel", "serie", "sigla") and v != "" else v)
             for k, v in l.items()} for l in linhas]


loc = {r["nome"]: r for r in ler("descritiva_por_localidade.csv")}
ano = ler("descritiva_por_ano.csv")
reg = {r["serie"]: r for r in ler("regressoes.csv")}

# conferência: os números citados no texto batem com as tabelas geradas
assert round(loc["Brasil"]["media"], 2) == 526.67 and round(reg["Brasil"]["a"], 2) == 58.20
assert round(reg["Sul"]["p_valor"], 4) == 0.0341 and reg["UFs (agrupadas)"]["n"] == 185

# ---------------------------------------------------------------- cabeçalho
substituir(P[0], "DESASTRES NO BRASIL: ANÁLISE ESTATÍSTICA DO INDICADOR 13.1.1 DO ODS 13 ENTRE 2018 E 2024")
remover(P[1])
alunos = ["Caio de Souza Leal", "Luigi Matheus Gomes", "Vinicius Silva Morais", "Gabriel Delmondes Quadrado"]
for p, nome in zip(P[3:7], alunos):
    substituir(p, [(f"{nome} – ", {}), ("RA", {"destacar": True}), (" – ", {}), ("Curso", {"destacar": True}),
                   (" – Fatec São Bernardo do Campo – Adib Moisés Dib", {})])
remover(P[7])

# ---------------------------------------------------------------- resumo
RESUMO = (
    "Este trabalho analisa o indicador 13.1.1 do Objetivo de Desenvolvimento Sustentável (ODS) 13 – número de "
    "mortes, pessoas desaparecidas e pessoas diretamente afetadas atribuído a desastres por 100 mil habitantes – "
    "para o Brasil, as cinco Grandes Regiões e as 27 Unidades da Federação (UFs), de 2018 a 2024. Os dados, "
    "originados do Sistema Integrado de Informações sobre Desastres (S2ID) e das estimativas populacionais do "
    "IBGE, foram tratados e armazenados em um banco de dados relacional PostgreSQL e analisados com Python. "
    "Calcularam-se média, mediana, moda (classe modal), variância e desvio padrão, e ajustaram-se modelos de "
    "regressão linear simples tendo o ano como variável independente. No Brasil, a média do período foi de "
    "526,67 pessoas por 100 mil habitantes, com pico de 1.032,8 em 2021 e alta variabilidade (desvio padrão de "
    "346,70). A Região Norte apresentou a maior média (1.352,07) e o Centro-Oeste a menor (115,09). A reta "
    "ajustada para o Brasil (ŷ = 58,20x − 117.102,75) indica crescimento médio de 58,20 pessoas por 100 mil "
    "habitantes ao ano, porém com correlação fraca (r = 0,363) e sem significância estatística (p = 0,424). "
    "Apenas a Região Sul apresentou tendência de alta significativa (r = 0,791; p = 0,034), influenciada pelas "
    "enchentes de 2024 no Rio Grande do Sul. Conclui-se que o impacto dos desastres é elevado, irregular e "
    "desigual entre os territórios, o que reforça a necessidade de políticas de prevenção e adaptação "
    "previstas na meta 13.1."
)
substituir(P[10], RESUMO)
remover(P[11])
substituir(P[14], "ODS 13; Desastres; Estatística Descritiva; Regressão Linear; Banco de Dados; Análise de Dados.")

# ---------------------------------------------------------------- introdução
substituir(P[17], (
    "O ODS 13 da Agenda 2030 propõe medidas urgentes para combater a mudança do clima e seus impactos, e a meta "
    "13.1 trata do reforço da resiliência e da capacidade de adaptação a riscos e desastres naturais. O indicador "
    "13.1.1 mede quantas pessoas morrem, desaparecem ou são diretamente afetadas por desastres a cada 100 mil "
    "habitantes, permitindo comparar territórios de tamanhos diferentes. O Relatório Nacional Voluntário de 2024 "
    "apontou crescimento desse indicador em quase todas as regiões brasileiras, o que motiva a análise "
    "estatística dos dados mais recentes, até 2024."
))
remover(P[18])

# ---------------------------------------------------------------- objetivo
substituir(P[21], (
    "Objetivo geral: realizar uma análise estatística descritiva e de regressão linear dos dados do indicador "
    "13.1.1 no Brasil, nas Grandes Regiões e nas UFs entre 2018 e 2024, avaliando sua evolução no período e "
    "relacionando os resultados ao ODS 13."
))
c = Cursor(P[21])
c.par("Objetivos específicos: (a) estruturar os dados em um banco de dados relacional normalizado; (b) calcular "
      "média, mediana, moda, variância e desvio padrão por ano e por localidade; (c) ajustar retas de regressão "
      "linear entre o valor do indicador e o ano, avaliando o sentido e a força da tendência; e (d) identificar "
      "as regiões e UFs mais afetadas.")
remover(P[22])

# ---------------------------------------------------------------- fundamentação
substituir(P[25], (
    "Os ODS, adotados pela ONU em 2015, organizam 17 objetivos e 169 metas monitorados por indicadores. A "
    "estatística descritiva resume um conjunto de dados por medidas de posição (média, mediana e moda) e de "
    "dispersão (variância e desvio padrão). A regressão linear simples ajusta a reta ŷ = ax + b pelo método dos "
    "mínimos quadrados, e o coeficiente de correlação de Pearson (r) mede a força da relação linear entre X e Y "
    "(BUSSAB; MORETTIN, 2017). Um banco de dados relacional organiza os dados em tabelas ligadas por chaves, "
    "garantindo integridade e consultas reprodutíveis em SQL."
))
remover(P[26])

# ---------------------------------------------------------------- metodologia
escrever(P[30], " Plataforma de Indicadores ODS Brasil (IBGE), com dados de origem do Sistema Integrado de "
                "Informações sobre Desastres (S2ID), do Ministério da Integração e do Desenvolvimento Regional, e "
                "das estimativas populacionais do IBGE.")
escrever(P[31], " 13.1.1 – Número de mortes, pessoas desaparecidas e pessoas diretamente afetadas atribuído a "
                "desastres por 100 mil habitantes.")
escrever(P[32], " ODS 13 – Ação contra a mudança global do clima (meta 13.1).")
escrever(P[33], " 2018 a 2024 (sete anos).")
escrever(P[34], " planilha com 33 linhas (Brasil, 5 Grandes Regiões e 27 UFs) e uma coluna por ano, totalizando "
                "231 valores. Quatro células não possuíam dado (“...”): Tocantins em 2019 e Paraíba, Sergipe e "
                "Distrito Federal em 2018.")

substituir(P[37], (
    "A planilha foi lida com a biblioteca pandas (Python 3.13). Os nomes das localidades foram padronizados "
    "(remoção de espaços), a linha de fonte foi descartada e as células “...” foram convertidas em valores nulos "
    "(NULL), e não em zero, para não distorcer as médias. Os dados passaram do formato largo (uma coluna por ano) "
    "para o formato longo (uma linha por localidade e ano). Antes da gravação, o programa valida as 33 "
    "localidades, os anos de 2018 a 2024, a ausência de duplicidades e de valores negativos."
))
c = Cursor(P[37])
c.par("O armazenamento foi feito no PostgreSQL 18 (o template sugere MySQL; optou-se pelo PostgreSQL por "
      "oferecer nativamente o cálculo da mediana em SQL). O modelo relacional possui três tabelas: localidade "
      "(Brasil, regiões e UFs, com a hierarquia UF → região → Brasil), indicador (código, descrição, unidade e "
      "fonte) e observacao (localidade, indicador, ano e valor), totalizando 231 registros. A carga é feita em "
      "uma única transação: se alguma validação falhar, o banco permanece inalterado.")

substituir(P[40], (
    "Os cálculos foram feitos com Python (pandas, NumPy e SciPy) a partir de consultas ao banco e conferidos "
    "com visões (views) SQL do PostgreSQL (funções AVG, PERCENTILE_CONT, VAR_SAMP e STDDEV_SAMP). Foram usadas "
    "a variância e o desvio padrão amostrais. A estatística foi calculada de duas formas: por ano, entre as 27 "
    "UFs, e por localidade, ao longo dos sete anos. Brasil e regiões não foram somados às UFs, pois já são "
    "agregados delas. Como os valores são contínuos e quase não se repetem, a moda foi apresentada como classe "
    "modal de uma distribuição de frequências com número de classes definido pela regra de Sturges "
    "(k = 1 + 3,322·log n). Os gráficos foram gerados com a biblioteca matplotlib."
))

substituir(P[43], [("Variável dependente (Y): ", {}), ("valor do indicador 13.1.1 (pessoas mortas, "
                   "desaparecidas ou diretamente afetadas por 100 mil habitantes).", {})])
substituir(P[44], [("Variável independente (X): ", {}), ("ano (2018 a 2024).", {})])
substituir(P[45], [("Coeficiente de correlação (r): ", {}), ("r = 0,363 para o Brasil (r² = 0,132; n = 7); os "
                   "valores das regiões e das UFs estão na Tabela 3.", {})])
escrever(P[46], [(". Para o Brasil: ŷ = 58,20x − 117.102,75, em que x é o ano. De forma equivalente, "
                  "ŷ = 58,20·(ano − 2018) + 352,06.", {})])
substituir(P[47], (
    "Interpretação dos coeficientes: o coeficiente angular a = 58,20 indica que, em média, o indicador aumentou "
    "58,20 pessoas por 100 mil habitantes a cada ano. O coeficiente linear b = −117.102,75 corresponde ao ano "
    "zero e não tem interpretação prática; por isso apresenta-se também a forma com x = ano − 2018, cujo "
    "intercepto (352,06) é o valor estimado pela reta para 2018. A significância da inclinação foi avaliada pelo "
    "teste t (p-valor), ao nível de 5%. Foram ajustadas retas para o Brasil, para cada Grande Região e para "
    "todas as UFs em conjunto (n = 185 observações)."
))

# ---------------------------------------------------------------- resultados: descritiva
b = loc["Brasil"]
cv = b["desvio_padrao"] / b["media"] * 100
substituir(P[51], (
    f"No Brasil, o indicador partiu de 86,2 pessoas por 100 mil habitantes em 2018, atingiu o máximo de "
    f"1.032,8 em 2021 e encerrou 2024 em 670,5. A média do período foi de {br(b['media'])}, a mediana de "
    f"{br(b['mediana'])}, a variância de {br(b['variancia'])} e o desvio padrão de {br(b['desvio_padrao'])}, o que "
    f"corresponde a um coeficiente de variação de {br(cv, 1)}%: a série é muito irregular de um ano para outro. "
    f"A Tabela 1 resume as medidas do Brasil e das Grandes Regiões."
))
c = Cursor(P[51])
linhas = []
for nome in ["Brasil", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]:
    r = loc[nome]
    linhas.append([nome, br(r["media"]), br(r["mediana"]), br(r["variancia"]), br(r["desvio_padrao"]),
                   br(r["minimo"], 1), br(r["maximo"], 1)])
c.tabela("Tabela 1 – Estatística descritiva do indicador 13.1.1 por localidade, 2018–2024 "
         "(pessoas por 100 mil habitantes)",
         ["Localidade", "Média", "Mediana", "Variância", "Desvio padrão", "Mínimo", "Máximo"], linhas,
         [2.6, 1.9, 1.9, 2.6, 2.1, 1.7, 1.7])
c.par(
    "A Região Norte apresentou a maior média (1.352,07) e manteve valores acima da média nacional em todos os "
    "anos; o Centro-Oeste teve a menor média (115,09). No Sul, a média (724,34) é mais de três vezes a mediana "
    "(216,70), porque a série é puxada por 2023 (955,9) e, sobretudo, por 2024 (2.685,4), ano das enchentes no "
    "Rio Grande do Sul. No Sudeste, o pico ocorreu em 2020 (1.385,6). A Figura 1 mostra a evolução das séries.")
c.figura("Figura 1 – Evolução do indicador 13.1.1 no Brasil e nas Grandes Regiões, 2018–2024",
         "evolucao_brasil_regioes.png")

a18, a21, a24 = ano[0], ano[3], ano[6]
c.par(
    f"Considerando apenas as UFs (Tabela 2), a média anual variou de {br(a18['media'])} em 2018 a "
    f"{br(a21['media'])} em 2021. Em todos os anos a mediana ficou muito abaixo da média (em 2021, "
    f"{br(a21['mediana'])} contra {br(a21['media'])}), o que indica forte assimetria à direita: a maioria das UFs "
    f"registra valores baixos, enquanto poucas UFs concentram valores muito altos. O maior desvio padrão ocorreu "
    f"em 2024 ({br(a24['desvio_padrao'])}), em razão do valor recorde do Rio Grande do Sul (7.220,2). Em 2018, "
    f"apenas 24 UFs tinham dado disponível e, em 2019, 26.")
linhas = [[str(int(r["ano"])), str(int(r["n"])), br(r["media"]), br(r["mediana"]), br(r["desvio_padrao"]),
           f"{br(r['classe_modal_inf'])} – {br(r['classe_modal_sup'])} ({int(r['classe_modal_freq'])})"]
          for r in ano]
c.tabela("Tabela 2 – Estatística descritiva do indicador 13.1.1 entre as UFs, por ano",
         ["Ano", "UFs (n)", "Média", "Mediana", "Desvio padrão", "Classe modal (frequência)"], linhas,
         [1.3, 1.5, 2.0, 2.0, 2.4, 4.6])
c.figura("Figura 2 – Média do indicador 13.1.1 entre as UFs, por ano", "media_ufs_por_ano.png", 13)
c.par(
    "Em relação à moda, quase nenhum valor se repete na série: a moda dos valores brutos das UFs é 0,0 (cinco "
    "ocorrências, em Roraima, Paraíba e Distrito Federal). Por isso, adotou-se a classe modal. Agrupando todas as "
    "UFs e anos (185 valores, k = 9 classes pela regra de Sturges), a classe modal é de 0,00 a 802,24, com 147 "
    "valores (79,5% do total), como mostra a Figura 3. A concentração na primeira classe confirma a assimetria "
    "da distribuição.")
c.figura("Figura 3 – Distribuição de frequências dos valores das UFs, 2018–2024", "histograma_ufs.png", 13)
top = sorted((r for r in loc.values() if r["nivel"] == "uf"), key=lambda r: -r["media"])
c.par(
    f"Entre as UFs (Figura 4), as maiores médias do período foram as do Amazonas ({br(top[0]['media'])}), do Acre "
    f"({br(top[1]['media'])}), do Rio Grande do Sul ({br(top[2]['media'])}), do Pará ({br(top[3]['media'])}) e do "
    f"Rio Grande do Norte ({br(top[4]['media'])}). As menores foram as de Goiás ({br(loc['Goiás']['media'])}), da "
    f"Paraíba ({br(loc['Paraíba']['media'])}) e do Ceará ({br(loc['Ceará']['media'])}).")
c.figura("Figura 4 – Média do indicador 13.1.1 por UF, 2018–2024", "media_por_uf.png", 12)

# ---------------------------------------------------------------- resultados: regressão
rb = reg["Brasil"]
substituir(P[54], (
    f"A reta ajustada para o Brasil é ŷ = 58,20x − 117.102,75 (Figura 5). A inclinação positiva indica tendência "
    f"de alta de 58,20 pessoas por 100 mil habitantes ao ano. Contudo, a correlação é fraca (r = "
    f"{br(rb['r'], 3)}) e o ano explica apenas {br(rb['r2'] * 100, 1)}% da variação do indicador (r² = "
    f"{br(rb['r2'], 3)}). O p-valor de {br(rb['p_valor'], 3)} mostra que a tendência não é estatisticamente "
    f"significativa ao nível de 5%. Os pontos de 2020 e 2021 ficam bem acima da reta, e os de 2022 e 2023 abaixo, "
    f"o que evidencia que a série oscila mais do que cresce de forma linear."
))
c = Cursor(P[54])
c.figura("Figura 5 – Dispersão do indicador 13.1.1 no Brasil em função do ano, com reta ajustada",
         "dispersao_brasil.png", 14)
c.par("A Tabela 3 apresenta as retas ajustadas para as Grandes Regiões e para o conjunto das UFs.")
linhas = []
for nome in ["Brasil", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste", "UFs (agrupadas)"]:
    r = reg[nome]
    sinal = "−" if r["b_ano_2018"] < 0 else "+"
    a_txt = ("−" + br(abs(r["a"]))) if r["a"] < 0 else br(r["a"])
    linhas.append([nome, f"ŷ = {a_txt}·(ano − 2018) {sinal} {br(abs(r['b_ano_2018']))}",
                   br(r["r"], 3).replace("-", "−"), br(r["r2"], 3), br(r["p_valor"], 3), str(int(r["n"]))])
c.tabela("Tabela 3 – Regressão linear simples do indicador 13.1.1 em função do ano, 2018–2024",
         ["Série", "Equação", "r", "r²", "p-valor", "n"], linhas, [2.8, 6.0, 1.5, 1.5, 1.6, 1.0])
c.par(
    "A Região Sul foi a única com tendência de alta estatisticamente significativa (r = 0,791; r² = 0,626; "
    "p = 0,034), com aumento médio de 344,85 pessoas por 100 mil habitantes ao ano (Figura 6). Essa tendência é "
    "fortemente influenciada pelos valores de 2023 e 2024; o intercepto negativo (−310,21 em 2018) mostra que a "
    "reta descreve a tendência do período, e não deve ser usada para estimar anos isolados. O Norte apresentou "
    "inclinação positiva (144,85 ao ano), mas sem significância (p = 0,328). O Nordeste (r = 0,123) e o Sudeste "
    "(r = −0,047) praticamente não apresentam relação linear com o tempo, e o Centro-Oeste tem tendência de queda "
    "(−29,36 ao ano; r = −0,481), também não significativa. Com as 185 observações das UFs, a inclinação "
    "(57,27 ao ano) é próxima à do Brasil, mas a correlação é muito fraca (r = 0,104; p = 0,161).")
c.figura("Figura 6 – Dispersão do indicador 13.1.1 na Região Sul em função do ano, com reta ajustada",
         "dispersao_sul.png", 14)

# ---------------------------------------------------------------- discussão
substituir(P[57], (
    "Os resultados mostram que o impacto dos desastres no Brasil é elevado e muito irregular. A média nacional "
    "de 526,67 pessoas por 100 mil habitantes entre 2018 e 2024 é superior à média de 430,7 relatada no "
    "Relatório Nacional Voluntário (BRASIL, 2024) para 2016–2022, e a média do Norte (1.352,07) também supera o "
    "valor de 1.060,6 do relatório. A comparação deve ser cautelosa, pois os períodos são diferentes, mas ela "
    "indica que os anos mais recentes, em especial 2024, mantiveram o indicador em patamar alto."
))
c = Cursor(P[57])
c.par("Para a meta 13.1, que busca reforçar a resiliência e a capacidade de adaptação, os dados revelam duas "
      "implicações. Primeiro, a desigualdade territorial: a Região Norte e UFs como Amazonas, Acre e Pará "
      "estão entre as maiores médias do período, o que sugere a necessidade de priorizar prevenção, "
      "sistemas de alerta e adaptação nessas áreas. Segundo, a ocorrência de eventos extremos concentrados, como "
      "o do Rio Grande do Sul em 2024, que sozinho elevou a média e a dispersão do país e determinou a única "
      "tendência significativa observada.")
c.par("O estudo tem limitações. A série tem apenas sete anos, o que torna as regressões do Brasil e das regiões "
      "pouco robustas e sensíveis a anos de pico. O indicador agrega mortos, desaparecidos e afetados em uma "
      "única taxa, sem distinguir a gravidade, e depende do registro das ocorrências no S2ID. Quatro valores não "
      "estavam disponíveis. Por fim, a regressão com todas as UFs trata observações da mesma UF em anos "
      "diferentes como independentes, o que pode tornar o p-valor otimista; ela foi usada apenas como análise "
      "complementar. O ano, sozinho, explica pouco da variação: fatores como chuvas extremas, ocupação de áreas "
      "de risco e vulnerabilidade social, não analisados aqui, tendem a ter papel maior.")

# ---------------------------------------------------------------- conclusão
substituir(P[60], (
    "Os dados do indicador 13.1.1 entre 2018 e 2024 mostram que, no Brasil, a cada ano centenas de pessoas por "
    "100 mil habitantes foram mortas, desaparecidas ou diretamente afetadas por desastres, com média de 526,67 e "
    "pico em 2021. A tendência nacional é de alta (58,20 ao ano), mas fraca e não significativa; somente a Região "
    "Sul apresentou crescimento significativo, ligado aos eventos de 2023 e 2024. O impacto é desigual: o Norte "
    "concentra os maiores valores e a distribuição entre as UFs é muito assimétrica."
))
c = Cursor(P[60])
c.par("Como contribuição, o trabalho entrega uma base de dados relacional reprodutível no PostgreSQL e scripts "
      "que recalculam todas as tabelas e gráficos a partir dos dados originais. Sugere-se, em estudos futuros, "
      "ampliar a série histórica, separar mortos, desaparecidos e afetados, e incluir variáveis explicativas como "
      "precipitação, tipo de desastre e indicadores socioeconômicos.")

# ---------------------------------------------------------------- referências
refs = [
    "BRASIL. Ministério da Integração e do Desenvolvimento Regional. Sistema Integrado de Informações sobre "
    "Desastres – S2ID. Brasília, [s.d.]. Disponível em: https://s2id.mi.gov.br. Acesso em: 15 nov. 2026.",
    "BRASIL. Secretaria-Geral da Presidência da República. Comissão Nacional para os Objetivos de Desenvolvimento "
    "Sustentável. Relatório Nacional Voluntário 2024: progresso nas metas e objetivos da Agenda 2030 no Brasil. "
    "Brasília, 2024. Disponível em: https://www.gov.br/secretariageral/pt-br/cnods/RNV_Brasil/portugues/"
    "relatorio-nacional-voluntario-brasileiro. Acesso em: 3 nov. 2026.",
    "BUSSAB, W. O.; MORETTIN, P. A. Estatística básica. 9. ed. São Paulo: Saraiva, 2017.",
    "IBGE. Objetivos de Desenvolvimento Sustentável: indicador 13.1.1. Rio de Janeiro: IBGE, [s.d.]. "
    "Disponível em: https://odsbrasil.gov.br/objetivo13/indicador1311. Acesso em: 15 nov. 2026.",
    "IPCC. Climate Change 2023: Synthesis Report. Summary for Policymakers. Geneva: Intergovernmental Panel on "
    "Climate Change, 2023. Disponível em: https://www.ipcc.ch/report/ar6/syr/summary-for-policymakers/. "
    "Acesso em: 3 nov. 2026.",
    "THE POSTGRESQL GLOBAL DEVELOPMENT GROUP. PostgreSQL 18 Documentation. [S.l.], 2025. Disponível em: "
    "https://www.postgresql.org/docs/18/. Acesso em: 15 nov. 2026.",
    "VIRTANEN, P. et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods, "
    "v. 17, p. 261–272, 2020.",
]
substituir(P[63], refs[0])
c = Cursor(P[63])
for ref in refs[1:]:
    p = c.par(ref, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, espaco=1.0)
for p in [P[63], *[]]:
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0

# ---------------------------------------------------------------- anexos
substituir(P[65], [("Anexos", {"bold": True})])
substituir(P[66], (
    "Anexo A – Estrutura do banco de dados e visão de estatística descritiva (trechos de sql/01_schema.sql e "
    "sql/03_views.sql). Os códigos completos (ETL em Python, análise estatística e geração de gráficos) estão "
    "nos arquivos do projeto: etl/carregar.py, ods13/etl.py, ods13/estatistica.py e ods13/graficos.py."
))
c = Cursor(P[66])
c.codigo([
    "CREATE TABLE ods13.localidade (",
    "    id_localidade INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,",
    "    nome   VARCHAR(60) NOT NULL UNIQUE,",
    "    sigla  CHAR(2) NULL,",
    "    nivel  ods13.nivel_localidade NOT NULL,  -- 'pais' | 'regiao' | 'uf'",
    "    id_pai INTEGER NULL REFERENCES ods13.localidade (id_localidade));",
    "",
    "CREATE TABLE ods13.observacao (",
    "    id_localidade INTEGER NOT NULL REFERENCES ods13.localidade,",
    "    id_indicador  INTEGER NOT NULL REFERENCES ods13.indicador,",
    "    ano   SMALLINT NOT NULL CHECK (ano BETWEEN 2000 AND 2100),",
    "    valor NUMERIC(10,1) NULL CHECK (valor >= 0),  -- NULL = \"...\"",
    "    PRIMARY KEY (id_localidade, id_indicador, ano));",
    "",
    "CREATE VIEW ods13.vw_descritiva_ano_uf AS",
    "SELECT ano, count(valor) AS n, count(*) - count(valor) AS ausentes,",
    "       avg(valor) AS media,",
    "       percentile_cont(0.5) WITHIN GROUP (ORDER BY valor) AS mediana,",
    "       var_samp(valor) AS variancia, stddev_samp(valor) AS desvio_padrao",
    "FROM ods13.vw_observacao WHERE nivel = 'uf'",
    "GROUP BY ano ORDER BY ano;",
])
c.par("Anexo B – Valores do indicador 13.1.1 por localidade e ano (pessoas por 100 mil habitantes).",
      recuo=False)
with open(SAIDA / "tabelas" / "observacoes.csv", encoding="utf-8-sig") as f:
    obs = list(csv.reader(f, delimiter=";"))
cab = ["Localidade", *obs[0][3:]]
corpo = [[r[0], *[(v if v else "...") for v in r[3:]]] for r in obs[1:]]
c.tabela("Tabela B.1 – Indicador 13.1.1 por localidade, 2018–2024", cab, corpo,
         [4.0, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6],
         fonte="Fonte: S2ID (MIDR/SEDEC); IBGE. “...”: dado não disponível.")

destino = RAIZ / "Artigo_ODS13_Indicador_13-1-1.docx"
try:
    d.save(destino)
except PermissionError:
    sys.exit(f"Não foi possível gravar {destino.name}: feche o arquivo no Word e rode de novo.")
print(f"Artigo gerado: {destino}")
