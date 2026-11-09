-- Migração 006: chave Pix do usuário, usada nas campanhas de doação
ALTER TABLE usuarios ADD COLUMN chave_pix VARCHAR(77) NULL;