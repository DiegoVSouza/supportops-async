CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('queued','running','retrying','done','failed','cancelled')),
  payload JSONB NOT NULL,
  step TEXT,
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0),
  result JSONB,
  error TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  worker_id TEXT,
  lease_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS idempotency (
  idem_key TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES tasks(task_id)
);
CREATE TABLE IF NOT EXISTS checkpoints (
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  step TEXT NOT NULL,
  state JSONB NOT NULL,
  PRIMARY KEY (task_id, step)
);
CREATE TABLE IF NOT EXISTS effects (
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  step TEXT NOT NULL,
  result JSONB NOT NULL,
  PRIMARY KEY (task_id, step)
);
CREATE TABLE IF NOT EXISTS event_outbox (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMPTZ
);
