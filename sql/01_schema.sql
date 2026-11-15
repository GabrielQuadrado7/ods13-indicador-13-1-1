-- Indicador 13.1.1 (ODS 13): estrutura do banco.
-- O schema é recriado a cada carga; os dados vêm sempre da planilha original.
DROP SCHEMA IF EXISTS ods13 CASCADE;
CREATE SCHEMA ods13;

CREATE TYPE ods13.nivel_localidade AS ENUM ('pais', 'regiao', 'uf');

CREATE TABLE ods13.localidade (
    id_localidade  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome           VARCHAR(60) NOT NULL UNIQUE,
    sigla          CHAR(2) NULL,
    nivel          ods13.nivel_localidade NOT NULL,
    id_pai         INTEGER NULL REFERENCES ods13.localidade (id_localidade)
);
COMMENT ON TABLE  ods13.localidade        IS 'Brasil, Grandes Regiões e Unidades da Federação';
COMMENT ON COLUMN ods13.localidade.sigla  IS 'Sigla da UF; nula para Brasil e regiões';
COMMENT ON COLUMN ods13.localidade.nivel  IS 'pais, regiao ou uf';
COMMENT ON COLUMN ods13.localidade.id_pai IS 'Hierarquia: UF -> região -> Brasil';

CREATE TABLE ods13.indicador (
    id_indicador   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo         VARCHAR(10) NOT NULL UNIQUE,
    ods            SMALLINT NOT NULL,
    descricao      VARCHAR(255) NOT NULL,
    unidade        VARCHAR(50) NOT NULL,
    fonte          TEXT NOT NULL
);
COMMENT ON TABLE ods13.indicador IS 'Indicadores ODS armazenados (aqui, apenas o 13.1.1)';

CREATE TABLE ods13.observacao (
    id_localidade  INTEGER NOT NULL REFERENCES ods13.localidade (id_localidade),
    id_indicador   INTEGER NOT NULL REFERENCES ods13.indicador (id_indicador),
    ano            SMALLINT NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    valor          NUMERIC(10, 1) NULL CHECK (valor >= 0),
    PRIMARY KEY (id_localidade, id_indicador, ano)
);
COMMENT ON TABLE  ods13.observacao       IS 'Valor do indicador por localidade e ano';
COMMENT ON COLUMN ods13.observacao.valor IS 'Taxa por 100 mil habitantes; NULL = dado não disponível ("...")';
