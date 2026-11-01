-- Migração 002: perfil (protetor ou ONG) e divulgação de animais na página pública.

ALTER TABLE usuarios
  ADD COLUMN tipo ENUM('PROTETOR','ONG') NOT NULL DEFAULT 'PROTETOR',
  ADD COLUMN cidade VARCHAR(100) NULL;

ALTER TABLE animais
  ADD COLUMN visivel_publico TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN info_saude VARCHAR(500) NULL;