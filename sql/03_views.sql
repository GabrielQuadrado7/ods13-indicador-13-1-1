-- Views de apoio à análise do indicador 13.1.1.

CREATE VIEW ods13.vw_observacao AS
SELECT l.nome,
       l.sigla,
       l.nivel::text AS nivel,
       CASE l.nivel WHEN 'uf' THEN p.nome
                    WHEN 'regiao' THEN l.nome
       END AS regiao,
       o.ano,
       o.valor
FROM ods13.observacao o
JOIN ods13.localidade l ON l.id_localidade = o.id_localidade
LEFT JOIN ods13.localidade p ON p.id_localidade = l.id_pai;
COMMENT ON VIEW ods13.vw_observacao IS
    'Observações com nome, sigla, nível e região de cada localidade';

-- Estatística descritiva por ano, apenas entre as UFs (Brasil e regiões ficam de fora
-- para não contar a mesma população duas vezes). NULL ("...") é ignorado e contado em "ausentes".
CREATE VIEW ods13.vw_descritiva_ano_uf AS
SELECT ano,
       count(valor)                                         AS n,
       count(*) - count(valor)                              AS ausentes,
       avg(valor)                                           AS media,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY valor)   AS mediana,
       var_samp(valor)                                      AS variancia,
       stddev_samp(valor)                                   AS desvio_padrao,
       min(valor)                                           AS minimo,
       max(valor)                                           AS maximo
FROM ods13.vw_observacao
WHERE nivel = 'uf'
GROUP BY ano
ORDER BY ano;
COMMENT ON VIEW ods13.vw_descritiva_ano_uf IS
    'Média, mediana, variância e desvio padrão amostrais entre as 27 UFs, por ano';

-- Estatística descritiva de cada localidade ao longo dos anos.
CREATE VIEW ods13.vw_descritiva_localidade AS
SELECT nome,
       nivel,
       count(valor)                                         AS n,
       count(*) - count(valor)                              AS ausentes,
       avg(valor)                                           AS media,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY valor)   AS mediana,
       var_samp(valor)                                      AS variancia,
       stddev_samp(valor)                                   AS desvio_padrao,
       min(valor)                                           AS minimo,
       max(valor)                                           AS maximo
FROM ods13.vw_observacao
GROUP BY nome, nivel;
COMMENT ON VIEW ods13.vw_descritiva_localidade IS
    'Média, mediana, variância e desvio padrão amostrais de cada localidade, 2018-2024';
