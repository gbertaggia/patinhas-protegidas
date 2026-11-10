-- Migração 008: data em que o animal foi movido para "Jornadas concluídas" (vazio = em andamento)
ALTER TABLE animais ADD COLUMN jornada_concluida_em TIMESTAMP NULL;