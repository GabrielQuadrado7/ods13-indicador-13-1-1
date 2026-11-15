# Design — Base de dados e análise estatística do indicador 13.1.1 (ODS 13)

Data: 2026-11-15 · Projeto de extensão FATEC, 4º semestre

## 1. Intenção e porquê

O grupo vai produzir um artigo científico (template `Template_Artigo_Cientifico_Projeto_ODS (1).docx`)
sobre o **ODS 13**, usando o **indicador 13.1.1 — número de mortes, pessoas desaparecidas e pessoas
diretamente afetadas atribuído a desastres por 100 mil habitantes**. O template exige:

- armazenamento dos dados em banco relacional — o template cita **MySQL**, mas o grupo decidiu usar
  **PostgreSQL** (ver §6: o texto do artigo deve dizer PostgreSQL);
- **estatística descritiva**: média, mediana, moda, variância, desvio padrão, tabelas e gráficos
  (barras, linhas ou setores);
- **regressão linear simples**: Y, X, coeficiente de correlação r, equação ŷ = ax + b, interpretação
  e gráfico de dispersão com reta ajustada;
- **anexos** com códigos, SQL, tabelas ou prints.

O sistema existe para gerar, de forma reproduzível, todos os números, tabelas e gráficos que entram
nas seções Metodologia, Resultados e Anexos do artigo.

## 2. Objetivos, não-objetivos, anti-objetivos

**Objetivos**
- Modelar o indicador num banco relacional normalizado no PostgreSQL.
- Carregar a planilha `13-1-1.xlsx` no banco com limpeza documentada.
- Calcular estatística descritiva **por ano** (entre UFs) e **por localidade** (ao longo dos anos).
- Ajustar regressão linear **Y = taxa do indicador, X = ano** (decisão do grupo).
- Exportar tabelas (CSV) e gráficos (PNG) prontos para colar no artigo.
- Deixar SQL legível (DDL + views) para os anexos.

**Não-objetivos**
- Interface web, dashboard ou API.
- Outras variáveis explicativas (PIB, chuva, desmatamento) — descartado pelo grupo.
- Modelos além da regressão linear simples (séries temporais, previsão, multivariada).
- Atualização automática a partir do S2ID/IBGE.

**Anti-objetivos (seria fracasso mesmo funcionando)**
- Tratar "..." (sem dado) como zero — distorce médias e a regressão.
- Misturar níveis (Brasil, regiões, UFs) no mesmo cálculo — o Brasil e as regiões já são agregados
  das UFs; somá-los juntos conta a mesma população duas vezes.
- Números no artigo que não podem ser regenerados pelos scripts.

## 3. Os dados de entrada

`13-1-1.xlsx`, planilha única "Sheet 1", formato largo:

- Linha 1: título do indicador. Linha 2: cabeçalho `Brasil, Grande Região e UF | 2018 … 2024`.
- Linhas 3–35: 33 localidades — Brasil, 5 Grandes Regiões, 27 UFs, cada UF listada logo abaixo
  da sua região (Norte → RO, AC, AM, RR, PA, AP, TO; Nordeste → …; etc.).
- Valores numéricos (taxa por 100 mil hab.). `...` = dado não disponível — **4 células**:
  Tocantins 2019, Paraíba 2018, Sergipe 2018, Distrito Federal 2018 (logo, 2018 tem
  só 24 UFs com dado). `0` é valor real. Valores das UFs vão de 0 a 7.220,2, muito assimétricos.
- Linha 36: nota de fonte (MI/SEDEC – S2ID; IBGE – estimativas populacionais). Não é dado.
- Só existe a taxa pronta; não há mortes/desaparecidos/afetados nem população em separado.

## 4. Abordagens consideradas

| Abordagem | Como | Trade-off |
|---|---|---|
| **A. Banco relacional + Python** ✅ escolhida | Python faz ETL para o banco e a análise lendo dele; SQL views para estatísticas básicas | Reproduzível, cobre tudo do template, gera SQL para anexos. Exige Python + libs no grupo. |
| B. Só SQL + Excel | Estatísticas e regressão em SQL; gráficos no Excel | Muito SQL para mostrar, gráficos manuais. |
| C. Banco só como depósito; análise em Excel/Power BI | Import pelo Workbench, análise em planilha | Menos código, mas não reproduzível e banco sem papel real. |

O grupo escolheu **A** porque atende ao template inteiro e mantém o banco como fonte única dos números.
Inicialmente com MySQL; depois o grupo decidiu **migrar para PostgreSQL** (já instalado na máquina:
PostgreSQL 18). A arquitetura não muda; muda o SGBD e o driver.

## 5. Arquitetura

```
13-1-1.xlsx ──► etl/carregar.py ──► PostgreSQL (ods13) ──► analise/analisar.py ──► saida/
                (lê, limpa,          tabelas + views     (descritiva,           tabelas/*.csv
                 normaliza,                               regressão,             graficos/*.png
                 insere)                                  gráficos)              resumo.md
```

Estrutura de pastas proposta:

```
ODS13/
  dados/13-1-1.xlsx            (mover o arquivo original para cá)
  sql/01_schema.sql            DDL
  sql/02_seed_localidades.sql  Brasil, regiões, UFs com siglas e hierarquia
  sql/03_views.sql             views de apoio
  etl/carregar.py
  analise/analisar.py
  saida/{tabelas,graficos}/
  config.example.env           host, porta, usuário, senha, banco
  requirements.txt             pandas, openpyxl, SQLAlchemy, psycopg[binary], scipy, matplotlib, python-dotenv
  README.md                    passo a passo para o grupo rodar
```

### 5.1 Banco de dados (PostgreSQL 18, encoding `UTF8`, schema `ods13`)

```sql
CREATE TYPE nivel_localidade AS ENUM ('pais','regiao','uf');

localidade (
  id_localidade  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome           VARCHAR(60) NOT NULL UNIQUE,   -- "Rondônia"
  sigla          CHAR(2) NULL,                  -- "RO"; NULL para Brasil/regiões
  nivel          nivel_localidade NOT NULL,
  id_pai         INTEGER NULL REFERENCES localidade  -- UF→região→Brasil
)
indicador (
  id_indicador   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  codigo         VARCHAR(10) NOT NULL UNIQUE,   -- "13.1.1"
  ods            SMALLINT NOT NULL,             -- 13
  descricao      VARCHAR(255) NOT NULL,
  unidade        VARCHAR(50) NOT NULL,          -- "por 100 mil habitantes"
  fonte          TEXT NOT NULL
)
observacao (
  id_localidade  INTEGER REFERENCES localidade,
  id_indicador   INTEGER REFERENCES indicador,
  ano            SMALLINT CHECK (ano BETWEEN 2000 AND 2100),
  valor          NUMERIC(10,1) NULL CHECK (valor >= 0),  -- NULL = "..." na planilha
  PRIMARY KEY (id_localidade, id_indicador, ano)
)
```

Volume esperado: 33 localidades × 7 anos = **231 linhas** em `observacao`.

Views (vão para os anexos):
- `vw_observacao` — junção legível (nome, sigla, nível, região-pai, ano, valor).
- `vw_descritiva_ano_uf` — por ano, entre as 27 UFs: COUNT, AVG, MIN, MAX, VAR_SAMP, STDDEV_SAMP e
  mediana (`PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor)`), que o PostgreSQL faz nativamente.
- `vw_descritiva_localidade` — por localidade, ao longo dos anos: as mesmas medidas.

### 5.2 ETL (`etl/carregar.py`)

1. Ler a planilha com pandas pulando a linha de título; descartar a linha de fonte (texto que começa
   com "Fonte").
2. Converter `...` (e células vazias) em NULL; demais valores em número.
3. Normalizar nomes (strip de espaços).
4. Transformar de largo para longo (`melt`: localidade, ano, valor).
5. Validar: 33 localidades, exatamente 4 valores NULL, todas presentes na tabela `localidade` (seed); anos 2018–2024; nenhum
   valor negativo. Falhar com mensagem clara se não bater.
6. Inserir/atualizar `indicador` e `observacao` de forma **idempotente** (rodar duas vezes não
   duplica — `INSERT … ON CONFLICT (…) DO UPDATE`).
7. Imprimir resumo: linhas carregadas, quantos NULL e quais.

A hierarquia (UF → região) vem do seed SQL, não da ordem das linhas da planilha.

### 5.3 Análise (`analise/analisar.py`)

Lê sempre do PostgreSQL (via `vw_observacao`), nunca da planilha.

**Estatística descritiva** (média, mediana, moda, variância amostral, desvio padrão amostral,
mínimo, máximo, n, nº de valores ausentes):
- **Por ano**, considerando as 27 UFs → tabela 7 linhas.
- **Por localidade**, ao longo dos 7 anos → Brasil, cada região e cada UF.
- **Moda**: como os valores são contínuos e quase nunca se repetem, reportar a **classe modal** de
  uma tabela de frequência (classes por Sturges) e registrar no artigo que a série é amodal nos
  valores brutos. *(Decisão de implementação)* A classe modal é calculada **por ano (entre UFs)** e
  **para todas as UFs agrupadas** (um histograma, do conjunto agrupado). Não se calcula moda por
  localidade (n = 7 é pequeno demais). Como os dados são muito assimétricos, a classe modal tende a
  ser a primeira; isso é registrado no artigo como característica da distribuição.
- NULLs são excluídos dos cálculos e contados em coluna própria.

**Regressão linear simples (Y = taxa, X = ano)** com `scipy.stats.linregress`: a (inclinação),
b (intercepto), r, r², p-valor, n.
- **Principal: Brasil** (n = 7).
- **Por Grande Região** (5 regressões, n = 7 cada).
- **Todas as UFs juntas** (até 189 pontos, excluindo NULL) como análise complementar.
- Para legibilidade da equação, usar X = ano real (ex.: 2018) e também informar a versão com
  X = ano − 2018; a decisão de qual entra no artigo fica com o grupo (ver §7).

**Gráficos (PNG, 300 dpi, rótulos em português)**
- Linha: evolução do Brasil e das 5 regiões, 2018–2024.
- Barras: média por UF no período (ordenada).
- Barras: média entre UFs por ano.
- Dispersão + reta ajustada: Brasil; uma por região; UFs agrupadas.
- Histograma usado na classe modal.

**Saídas**: `saida/tabelas/*.csv` (separador `;`, decimal `,` para abrir direto no Excel brasileiro),
`saida/graficos/*.png`, e `saida/resumo.md` com os números principais (equações, r, médias) para
copiar no texto do artigo.

## 6. Restrições

- Ambiente: Windows 11, Python 3.13 instalado; **pandas/scipy/matplotlib ainda não instalados**.
  **PostgreSQL 18** instalado localmente (serviço `postgresql-x64-18`); `psql` não está no PATH
  (usar caminho completo ou pgAdmin). Os prints dos anexos podem vir do pgAdmin.
- O template do artigo diz "armazenamento no MySQL": o texto da Metodologia deve citar PostgreSQL.
  Se o professor exigir MySQL, só o DDL e o driver mudam (o SQL foi mantido simples).
- Credenciais do banco ficam em `.env` local, nunca no código.
- Série curta (7 anos): o artigo deve registrar na Discussão que a regressão nacional tem n = 7 e
  baixa robustez; anos de pico (2020–2021) pesam muito.
- Referência para comparação na Discussão: RNV 2024 cita média nacional de 430,7 e Norte 1.060,6
  (2016–2022), período diferente do analisado aqui (2018–2024).

## 7. Deixado para quem constrói / decisões de implementação

- Biblioteca de conexão (SQLAlchemy + psycopg proposto), estilo dos gráficos, nomes exatos dos
  arquivos de saída.
- Se a equação do artigo usa ano real ou ano − 2018 — ambos são gerados; o grupo escolhe ao redigir.
- Testes: verificação mínima do ETL (contagens e NULLs esperados) e conferência de um cálculo
  descritivo contra valor feito à mão.
