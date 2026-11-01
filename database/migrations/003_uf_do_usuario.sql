-- Migração 003: estado (UF) do usuário, para a divulgação de animais.

ALTER TABLE usuarios
  ADD COLUMN uf CHAR(2) NULL AFTER cidade;