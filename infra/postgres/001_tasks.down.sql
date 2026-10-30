-- Destroys task history. Back up first.
DROP TABLE IF EXISTS event_outbox;
DROP TABLE IF EXISTS effects;
DROP TABLE IF EXISTS checkpoints;
DROP TABLE IF EXISTS idempotency;
DROP TABLE IF EXISTS tasks;
