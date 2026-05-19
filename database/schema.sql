USE defaultdb;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
      
CREATE TABLE IF NOT EXISTS animais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    raca VARCHAR(50) DEFAULT 'SRD',
    idade INT,
    foto_url VARCHAR(255),
    castrado BOOLEAN DEFAULT FALSE,
    data_castracao DATE NULL,
    chip VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS vacinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    nome_vacina VARCHAR(100),
    data_vacina DATE,
    status_vacina VARCHAR(100) DEFAULT 'Agendado',
    dose_vacina VARCHAR(100),

    FOREIGN KEY (animal_id) REFERENCES animais(id)
);

CREATE TABLE IF NOT EXISTS medicamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    nome_medicamento VARCHAR(100) NOT NULL,
    dose_medicamento VARCHAR(100),
    frequencia VARCHAR(50),      
    horarios VARCHAR(255),       
    data_inicio_medicamento DATE, 
    duracao_medicamento VARCHAR(100), 
    FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
);

CREATE TABLE consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_pet VARCHAR(100) NOT NULL,
    data_consulta DATE NOT NULL,
    hora_consulta TIME,
    clinica VARCHAR(150),
    veterinario VARCHAR(100),
    motivo VARCHAR(255)
);

CREATE TABLE historico_veterinario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_pet VARCHAR(100) NOT NULL,
    data_registro DATE NOT NULL,
    peso VARCHAR(50),
    temperatura VARCHAR(50),
    tipo_atendimento VARCHAR(100),
    sintomas TEXT,
    diagnostico TEXT,
    tratamento TEXT
);