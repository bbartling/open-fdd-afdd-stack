CREATE TABLE IF NOT EXISTS onboard_ingest_state (
    state_key text PRIMARY KEY,
    backfill_done boolean NOT NULL DEFAULT FALSE,
    last_poll_end timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);
