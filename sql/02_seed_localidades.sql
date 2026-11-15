-- Localidades: Brasil, 5 Grandes Regiões e 27 UFs (nomes iguais aos da planilha).
INSERT INTO ods13.localidade (nome, sigla, nivel, id_pai) VALUES ('Brasil', NULL, 'pais', NULL);

INSERT INTO ods13.localidade (nome, sigla, nivel, id_pai)
SELECT r.nome, NULL, 'regiao', (SELECT id_localidade FROM ods13.localidade WHERE nome = 'Brasil')
FROM (VALUES ('Norte'), ('Nordeste'), ('Sudeste'), ('Sul'), ('Centro-Oeste')) AS r (nome);

INSERT INTO ods13.localidade (nome, sigla, nivel, id_pai)
SELECT u.nome, u.sigla, 'uf', p.id_localidade
FROM (VALUES
    ('Rondônia', 'RO', 'Norte'),
    ('Acre', 'AC', 'Norte'),
    ('Amazonas', 'AM', 'Norte'),
    ('Roraima', 'RR', 'Norte'),
    ('Pará', 'PA', 'Norte'),
    ('Amapá', 'AP', 'Norte'),
    ('Tocantins', 'TO', 'Norte'),
    ('Maranhão', 'MA', 'Nordeste'),
    ('Piauí', 'PI', 'Nordeste'),
    ('Ceará', 'CE', 'Nordeste'),
    ('Rio Grande do Norte', 'RN', 'Nordeste'),
    ('Paraíba', 'PB', 'Nordeste'),
    ('Pernambuco', 'PE', 'Nordeste'),
    ('Alagoas', 'AL', 'Nordeste'),
    ('Sergipe', 'SE', 'Nordeste'),
    ('Bahia', 'BA', 'Nordeste'),
    ('Minas Gerais', 'MG', 'Sudeste'),
    ('Espírito Santo', 'ES', 'Sudeste'),
    ('Rio de Janeiro', 'RJ', 'Sudeste'),
    ('São Paulo', 'SP', 'Sudeste'),
    ('Paraná', 'PR', 'Sul'),
    ('Santa Catarina', 'SC', 'Sul'),
    ('Rio Grande do Sul', 'RS', 'Sul'),
    ('Mato Grosso do Sul', 'MS', 'Centro-Oeste'),
    ('Mato Grosso', 'MT', 'Centro-Oeste'),
    ('Goiás', 'GO', 'Centro-Oeste'),
    ('Distrito Federal', 'DF', 'Centro-Oeste')
) AS u (nome, sigla, regiao)
JOIN ods13.localidade p ON p.nome = u.regiao;
