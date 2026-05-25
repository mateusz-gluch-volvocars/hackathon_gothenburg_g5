-- schema.sql — The Pothole Poet's operational store.
--
-- Run this in AlloyDB Studio (or via psql) after Lane B's cluster + primary
-- instance are READY.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- for gen_random_uuid()

CREATE TABLE IF NOT EXISTS pothole_reports (
  id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  reported_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  neighbourhood       TEXT         NOT NULL,
  latitude            NUMERIC(9,6) NOT NULL,
  longitude           NUMERIC(9,6) NOT NULL,
  severity_iron_marks INT          NOT NULL
                                   CHECK (severity_iron_marks BETWEEN 1 AND 5),
  weather             TEXT         NOT NULL,
  reporter_mood       TEXT         NOT NULL,
  swallowed_object    TEXT,
  reporter_quote      TEXT         NOT NULL,
  citizen_id          TEXT                       -- nullable: ~10% of reports are anonymous
);

CREATE INDEX IF NOT EXISTS idx_neighbourhood ON pothole_reports (neighbourhood);
CREATE INDEX IF NOT EXISTS idx_reported_at   ON pothole_reports (reported_at);
CREATE INDEX IF NOT EXISTS idx_citizen_id    ON pothole_reports (citizen_id);

-- Grant read access to all roles so BigQuery federation (which connects as
-- the alloydb IAM service agent) can query the table without ownership issues.
GRANT SELECT ON pothole_reports TO PUBLIC;
