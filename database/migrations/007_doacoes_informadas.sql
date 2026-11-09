-- Migração 007: avisos de doação feitos pelos visitantes, confirmados pelo dono da campanha
CREATE TABLE IF NOT EXISTS doacoes_informadas (
    id            INT NOT NULL AUTO_INCREMENT,
    campanha_id   INT NOT NULL,
    valor         DECIMAL(10,2) NOT NULL,
    status        ENUM('pendente', 'confirmada', 'recusada') NOT NULL DEFAULT 'pendente',
    transacao_id  INT NULL,
    criado_em     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analisado_em  TIMESTAMP NULL,
    PRIMARY KEY (id),
    CONSTRAINT chk_doacoes_valor CHECK (valor > 0),
    CONSTRAINT fk_doacoes_campanha  FOREIGN KEY (campanha_id)  REFERENCES campanhas(id)  ON DELETE CASCADE,
    CONSTRAINT fk_doacoes_transacao FOREIGN KEY (transacao_id) REFERENCES transacoes(id) ON DELETE SET NULL,
    KEY idx_doacoes_campanha_status (campanha_id, status)
);