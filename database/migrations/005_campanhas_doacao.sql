-- 1. Nova categoria de receita para campanhas
INSERT IGNORE INTO categorias (tipo, nome) VALUES ('RECEITA', 'Doação via Campanha');

-- 2. Tabela de campanhas de arrecadação
CREATE TABLE IF NOT EXISTS campanhas (
    id             INT NOT NULL AUTO_INCREMENT,
    usuario_id     INT NOT NULL,
    animal_id      INT NULL,
    titulo         VARCHAR(150) NOT NULL,
    descricao      TEXT NOT NULL,
    meta           DECIMAL(10,2) NOT NULL,
    arrecadado     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    foto_url       VARCHAR(500) NULL,
    status         ENUM('ativa', 'concluida', 'cancelada') NOT NULL DEFAULT 'ativa',
    criado_em      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT chk_campanhas_meta CHECK (meta > 0),
    CONSTRAINT fk_campanhas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_campanhas_animal  FOREIGN KEY (animal_id)  REFERENCES animais(id)  ON DELETE SET NULL,
    KEY idx_campanhas_usuario (usuario_id),
    KEY idx_campanhas_animal (animal_id)
);

-- 3. Permitir 'CAMPANHA' como origem e adicionar a chave estrangeira em transacoes
ALTER TABLE transacoes 
    MODIFY COLUMN origem_tipo ENUM('MANUAL','VACINA','MEDICAMENTO','CONSULTA','CAMPANHA') NOT NULL DEFAULT 'MANUAL',
    ADD COLUMN campanha_id INT NULL,
    ADD CONSTRAINT fk_transacoes_campanha FOREIGN KEY (campanha_id) REFERENCES campanhas(id) ON DELETE SET NULL;