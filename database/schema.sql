-- Estrutura do banco do Patinhas Protegidas (MySQL 8.4).
-- Gerado em 13/11/2026 a partir de uma exportação só da estrutura do banco real.
-- Já inclui todas as mudanças de database/migrations (001 a 008). Para criar um banco
-- novo, rode este arquivo uma vez. Não há DROP: se as tabelas já existem, nada é alterado.

USE defaultdb;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) DEFAULT NULL,
    tipo ENUM('PROTETOR','ONG') NOT NULL DEFAULT 'PROTETOR',
    cidade VARCHAR(100) DEFAULT NULL,
    uf CHAR(2) DEFAULT NULL,
    logo_url VARCHAR(500) DEFAULT NULL,
    link_formulario_adocao VARCHAR(500) DEFAULT NULL,
    missao TEXT,
    chave_pix VARCHAR(77) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS animais (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    idade VARCHAR(50) DEFAULT NULL,
    raca VARCHAR(100) DEFAULT NULL,
    foto_url VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    castrado TINYINT(1) DEFAULT '0',
    data_castracao DATE DEFAULT NULL,
    chip VARCHAR(100) DEFAULT NULL,
    visivel_publico TINYINT(1) NOT NULL DEFAULT '0',
    info_saude VARCHAR(500) DEFAULT NULL,
    jornada_concluida_em TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY chip (chip),
    KEY usuario_id (usuario_id),
    CONSTRAINT animais_ibfk_1 FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS vacinas (
    id INT NOT NULL AUTO_INCREMENT,
    animal_id INT NOT NULL,
    nome_vacina VARCHAR(100) DEFAULT NULL,
    data_vacina DATE DEFAULT NULL,
    status_vacina VARCHAR(100) DEFAULT 'Agendado',
    dose_vacina VARCHAR(100) DEFAULT NULL,
    valor DECIMAL(10,2) NOT NULL DEFAULT '0.00',
    PRIMARY KEY (id),
    KEY fk_vacinas_animais (animal_id),
    CONSTRAINT fk_vacinas_animais FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS medicamentos (
    id INT NOT NULL AUTO_INCREMENT,
    animal_id INT NOT NULL,
    nome_medicamento VARCHAR(100) NOT NULL,
    dose_medicamento VARCHAR(100) DEFAULT NULL,
    frequencia VARCHAR(50) DEFAULT NULL,
    horarios VARCHAR(255) DEFAULT NULL,
    data_inicio_medicamento DATE DEFAULT NULL,
    duracao_medicamento VARCHAR(100) DEFAULT NULL,
    valor DECIMAL(10,2) NOT NULL DEFAULT '0.00',
    PRIMARY KEY (id),
    KEY animal_id (animal_id),
    CONSTRAINT medicamentos_ibfk_1 FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS consultas (
    id INT NOT NULL AUTO_INCREMENT,
    data_consulta DATE NOT NULL,
    hora_consulta TIME DEFAULT NULL,
    clinica VARCHAR(150) DEFAULT NULL,
    veterinario VARCHAR(100) DEFAULT NULL,
    motivo VARCHAR(255) DEFAULT NULL,
    animal_id INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL DEFAULT '0.00',
    PRIMARY KEY (id),
    KEY fk_consultas_animais (animal_id),
    CONSTRAINT fk_consultas_animais FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS historico_veterinario (
    id INT NOT NULL AUTO_INCREMENT,
    data_registro DATE NOT NULL,
    peso VARCHAR(50) DEFAULT NULL,
    temperatura VARCHAR(50) DEFAULT NULL,
    tipo_atendimento VARCHAR(100) DEFAULT NULL,
    sintomas TEXT,
    diagnostico TEXT,
    tratamento TEXT,
    clinica VARCHAR(150) DEFAULT NULL,
    anexo_url VARCHAR(255) DEFAULT NULL,
    animal_id INT NOT NULL,
    PRIMARY KEY (id),
    KEY fk_historico_animais (animal_id),
    CONSTRAINT fk_historico_animais FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS categorias (
    id INT NOT NULL AUTO_INCREMENT,
    tipo ENUM('RECEITA','DESPESA') NOT NULL,
    nome VARCHAR(60) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_categoria (tipo, nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS campanhas (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    animal_id INT DEFAULT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    meta DECIMAL(10,2) NOT NULL,
    arrecadado DECIMAL(10,2) NOT NULL DEFAULT '0.00',
    foto_url VARCHAR(500) DEFAULT NULL,
    status ENUM('ativa','concluida','cancelada') NOT NULL DEFAULT 'ativa',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_campanhas_usuario (usuario_id),
    KEY idx_campanhas_animal (animal_id),
    CONSTRAINT fk_campanhas_animal FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE SET NULL,
    CONSTRAINT fk_campanhas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT,
    CONSTRAINT chk_campanhas_meta CHECK (meta > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS transacoes (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    animal_id INT DEFAULT NULL,
    categoria_id INT NOT NULL,
    tipo ENUM('RECEITA','DESPESA') NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    descricao VARCHAR(255) DEFAULT NULL,
    data_transacao DATE NOT NULL,
    origem_tipo ENUM('MANUAL','VACINA','MEDICAMENTO','CONSULTA','CAMPANHA') NOT NULL DEFAULT 'MANUAL',
    origem_id INT DEFAULT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    campanha_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_transacoes_origem (origem_tipo, origem_id),
    KEY fk_transacoes_categoria (categoria_id),
    KEY idx_transacoes_usuario_data (usuario_id, data_transacao),
    KEY idx_transacoes_animal (animal_id),
    KEY fk_transacoes_campanha (campanha_id),
    CONSTRAINT fk_transacoes_animal FOREIGN KEY (animal_id) REFERENCES animais (id) ON DELETE RESTRICT,
    CONSTRAINT fk_transacoes_campanha FOREIGN KEY (campanha_id) REFERENCES campanhas (id) ON DELETE SET NULL,
    CONSTRAINT fk_transacoes_categoria FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE RESTRICT,
    CONSTRAINT fk_transacoes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT,
    CONSTRAINT chk_transacoes_valor CHECK (valor > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS doacoes_informadas (
    id INT NOT NULL AUTO_INCREMENT,
    campanha_id INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    status ENUM('pendente','confirmada','recusada') NOT NULL DEFAULT 'pendente',
    transacao_id INT DEFAULT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analisado_em TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY fk_doacoes_transacao (transacao_id),
    KEY idx_doacoes_campanha_status (campanha_id, status),
    CONSTRAINT fk_doacoes_campanha FOREIGN KEY (campanha_id) REFERENCES campanhas (id) ON DELETE CASCADE,
    CONSTRAINT fk_doacoes_transacao FOREIGN KEY (transacao_id) REFERENCES transacoes (id) ON DELETE SET NULL,
    CONSTRAINT chk_doacoes_valor CHECK (valor > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Categorias iniciais (migrações 001 e 005). O INSERT IGNORE não repete as que já existem.
INSERT IGNORE INTO categorias (tipo, nome) VALUES
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
    ('RECEITA', 'Outras receitas'),
    ('RECEITA', 'Doação via Campanha');
