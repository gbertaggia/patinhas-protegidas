-- Migração 001: base do módulo Pet Finanças
-- Banco: MySQL 8.4 (Aiven)

-- 1) Valor monetário nos registros de saúde
ALTER TABLE vacinas      ADD COLUMN valor DECIMAL(10,2) NOT NULL DEFAULT 0.00;
ALTER TABLE medicamentos ADD COLUMN valor DECIMAL(10,2) NOT NULL DEFAULT 0.00;
ALTER TABLE consultas    ADD COLUMN valor DECIMAL(10,2) NOT NULL DEFAULT 0.00;

-- 2) Categorias (lista fixa)
CREATE TABLE categorias (
    id   INT NOT NULL AUTO_INCREMENT,
    tipo ENUM('RECEITA','DESPESA') NOT NULL,
    nome VARCHAR(60) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_categoria (tipo, nome)
);

INSERT INTO categorias (tipo, nome) VALUES
    ('DESPESA', 'Vacina'),
    ('DESPESA', 'Consulta'),
    ('DESPESA', 'Medicamento'),
    ('DESPESA', 'Castração'),
    ('DESPESA', 'Exame'),
    ('DESPESA', 'Cirurgia'),
    ('DESPESA', 'Alimentação'),
    ('DESPESA', 'Higiene e limpeza'),
    ('DESPESA', 'Aluguel e contas'),
    ('DESPESA', 'Transporte'),
    ('DESPESA', 'Outros'),
    ('RECEITA', 'Doação via Pix'),
    ('RECEITA', 'Doação direta'),
    ('RECEITA', 'Outras receitas');

-- 3) Transações (a tabela antiga estava vazia e usava outro desenho)
DROP TABLE transacoes;

CREATE TABLE transacoes (
    id             INT NOT NULL AUTO_INCREMENT,
    usuario_id     INT NOT NULL,
    animal_id      INT NULL,
    categoria_id   INT NOT NULL,
    tipo           ENUM('RECEITA','DESPESA') NOT NULL,
    valor          DECIMAL(10,2) NOT NULL,
    descricao      VARCHAR(255) NULL,
    data_transacao DATE NOT NULL,
    origem_tipo    ENUM('MANUAL','VACINA','MEDICAMENTO','CONSULTA') NOT NULL DEFAULT 'MANUAL',
    origem_id      INT NULL,
    criado_em      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT chk_transacoes_valor CHECK (valor > 0),
    CONSTRAINT fk_transacoes_usuario   FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON DELETE RESTRICT,
    CONSTRAINT fk_transacoes_animal    FOREIGN KEY (animal_id)    REFERENCES animais(id)    ON DELETE RESTRICT,
    CONSTRAINT fk_transacoes_categoria FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
    UNIQUE KEY uq_transacoes_origem (origem_tipo, origem_id),
    KEY idx_transacoes_usuario_data (usuario_id, data_transacao),
    KEY idx_transacoes_animal (animal_id)
);