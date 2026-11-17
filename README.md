# ODS 13 — Indicador 13.1.1

Base de dados e análise estatística do indicador **13.1.1 — número de mortes, pessoas desaparecidas e pessoas diretamente afetadas atribuído a desastres por 100 mil habitantes** (Brasil, Grandes Regiões e UFs, 2018–2024). Projeto de extensão FATEC, 4º semestre.

Fonte dos dados: MI/SEDEC – S2ID; IBGE – estimativas populacionais (`dados/13-1-1.xlsx`).

📘 **Documentação completa** (modelo de dados, consultas ao banco, pgAdmin, problemas comuns): [DOCUMENTACAO.md](DOCUMENTACAO.md)

📄 **Artigo:** [Artigo_ODS13_Indicador_13-1-1.docx](Artigo_ODS13_Indicador_13-1-1.docx)

## Pré-requisitos

- Python 3.13
- PostgreSQL 18 (o `psql` fica em `C:\Program Files\PostgreSQL\18\bin\psql.exe`)

## Preparação (uma vez)

Forma rápida: cria `.venv`, `.env` e os bancos, e com `-Carregar` já gera `saida/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Carregar
```

Forma manual:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE ods13 ENCODING 'UTF8' TEMPLATE template0"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE ods13_teste ENCODING 'UTF8' TEMPLATE template0"

copy config.example.env .env   # depois troque SUA_SENHA pela senha do usuário postgres
```

## Uso

```powershell
.venv\Scripts\python etl\carregar.py      # recria o schema ods13 e carrega a planilha
.venv\Scripts\python analise\analisar.py  # gera saida\ (tabelas, gráficos, resumo.md)
.venv\Scripts\python artigo\montar_artigo.py  # gera o artigo .docx (feche-o no Word antes)
.venv\Scripts\python -m pytest            # testes (usam o banco ods13_teste)
```

## Onde cada coisa entra no artigo

| Seção do artigo | Material |
|---|---|
| Metodologia — Tratamento e armazenamento | `sql/01_schema.sql`, `sql/02_seed_localidades.sql`, `ods13/etl.py` (`...` → NULL, formato largo → longo, validação) |
| Metodologia — Estatística descritiva | `sql/03_views.sql`, `ods13/estatistica.py` |
| Resultados — Estatística descritiva | `saida/tabelas/descritiva_por_ano.csv`, `descritiva_por_localidade.csv`, gráficos `evolucao_brasil_regioes.png`, `media_por_uf.png`, `media_ufs_por_ano.png`, `histograma_ufs.png` |
| Resultados — Regressão linear | `saida/tabelas/regressoes.csv`, gráficos `dispersao_*.png`, equações em `saida/resumo.md` |
| Discussão | avisos e referência RNV 2024 no fim de `saida/resumo.md` |
| Anexos | `sql/*.sql`, `ods13/*.py`, `saida/tabelas/observacoes.csv`, prints do pgAdmin |

As tabelas CSV usam `;` e vírgula decimal e abrem direto no Excel em português.

## Observações

- O template do artigo cita MySQL; este projeto usa **PostgreSQL**. Na Metodologia, cite PostgreSQL.
- Variância e desvio padrão são **amostrais**. Os valores `...` da planilha (Tocantins 2019, Paraíba 2018, Sergipe 2018, Distrito Federal 2018) ficam como ausentes, nunca como zero.
- A estatística "entre UFs" usa só as 27 UFs; Brasil e regiões são analisados como séries próprias.
- As regressões do Brasil e das regiões têm n = 7: tendência fraca e pouco robusta.
- Toda saída é regenerada pelos dois comandos acima; não edite os números à mão no artigo.
