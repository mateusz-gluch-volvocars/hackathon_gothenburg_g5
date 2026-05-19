---
name: bq-federation-helper
description: Sets up and writes federated BigQuery queries against AlloyDB for Q2C-2 of the Iron & Cloud Pothole Poet quest. Creates the alloydb_archive connection via the platform script if missing, runs the 5000-row smoke query, and composes ad-hoc EXTERNAL_QUERY statements with project ID substitution and the PostgreSQL UUID-to-TEXT cast handled automatically. Use when the BigQuery Lead asks about federation, alloydb_archive, EXTERNAL_QUERY syntax, writing federated queries, or debugging zero-row or UUID-type federation errors.
---

# BigQuery federation helper (Q2C-2)

**Codelab counterpart:** Q2C-2 — `~/quest/pothole-poet/codelab/quest-2c-federation.md`.

Use this skill when the BigQuery Lead is wiring up or using the AlloyDB → BigQuery federation.

## What's already in place (pre-provisioned)

- BigQuery dataset `pothole_laureate` in `europe-west1` (shell only — populated by the Pipeline-author's DAG).
- BigQuery `gemini` connection bound to Vertex AI for `AI.GENERATE` calls.
- AlloyDB cluster `pothole-archive` with the seeded `pothole_reports` table (Q2A-3 finishes this).

The participant in Q2C-2 creates the `alloydb_archive` connection that wires BigQuery to AlloyDB.

## Steps

### 1. Confirm the connection state
```bash
bq query --use_legacy_sql=false \
  "SELECT connection_id FROM \`region-europe-west1.INFORMATION_SCHEMA.CONNECTIONS\` WHERE connection_id = 'alloydb_archive'"
```
- If empty, propose running the platform's setup script (it uses the modern connector framework with `connector_id: "google-alloydb"` — do NOT roll your own `bq mk --connection_type=CLOUD_SQL`, which rejects AlloyDB paths):
  ```bash
  export PROJECT_ID="$(gcloud config get-value project)"
  export REGION="europe-west1"
  bash ~/quest/pothole-poet/bigquery/setup_alloydb_connection.sh
  ```
- If the script reports "already exists", that's fine — the connection is in place.

### 2. Run the 5000-row smoke test
Always read `PROJECT_ID` fresh — don't hard-code:
```bash
PROJECT_ID="$(gcloud config get-value project)"
bq query --use_legacy_sql=false "$(cat <<EOF
SELECT count(*) AS row_count
FROM EXTERNAL_QUERY(
  'projects/${PROJECT_ID}/locations/europe-west1/connections/alloydb_archive',
  'SELECT id::TEXT AS id FROM pothole_reports'
)
EOF
)"
```
Expect `row_count: 5000`.

### 3. Write ad-hoc federated queries
For any federated query the participant requests:

- **Always substitute `${PROJECT_ID}` via the bash heredoc form above** — never leave a literal `<your-project-id>` placeholder. If the participant insists on the Studio path, surface the warning that they must Find-and-Replace before running.
- **Always cast PostgreSQL UUID columns to TEXT inside the federated SQL.** BigQuery doesn't natively support PG's `UUID` type. The pattern is `SELECT id::TEXT AS id, <other_columns> FROM pothole_reports`.
- **Push filters and projections into the inner PostgreSQL query.** BigQuery streams the entire result back, so narrowing in AlloyDB is much cheaper.

Example — "severity ≥ 3 in Hisingen":
```sql
SELECT *
FROM EXTERNAL_QUERY(
  'projects/${PROJECT_ID}/locations/europe-west1/connections/alloydb_archive',
  $$SELECT id::TEXT AS id, reported_at, neighbourhood, severity_iron_marks, reporter_quote
    FROM pothole_reports
    WHERE neighbourhood = 'Hisingen' AND severity_iron_marks >= 3$$
);
```

### 4. Two-connection sanity check
```bash
bq query --use_legacy_sql=false \
  "SELECT connection_id, connection_type FROM \`region-europe-west1.INFORMATION_SCHEMA.CONNECTIONS\` WHERE connection_id IN ('gemini', 'alloydb_archive')"
```
Expect two rows. If `gemini` is missing, that's a pre-provisioning issue — flag a Sherpa.

## Common failure modes

- **`connection not found: projects/<your-project-id>/...`** — the placeholder didn't get substituted. Re-run with the bash heredoc form.
- **`PostgreSQL type UUID in column id is not supported in BigQuery`** — add the `id::TEXT AS id` cast inside the inner SELECT.
- **`0 rows returned`** — either AlloyDB isn't `READY`, the cluster/instance ID in the connector config doesn't match Q2A-1, or the seed (Q2A-3) hasn't run yet. Check `gcloud alloydb clusters list --region=europe-west1` and confirm `pothole_reports` has rows.
- **`permission denied`** — the connection service account is missing `roles/alloydb.client` on the project. Pre-provisioning should bind it; flag a Sherpa if missing.

## Don't

- Don't use `--connection_type=CLOUD_SQL`. It's legacy and rejects AlloyDB instance paths.
- Don't propose the regional Gemini endpoint for `AI.GENERATE`. Use `locations/global` — Gemini 3 is global-endpoint-only.
- Don't pull whole tables into BigQuery via `EXTERNAL_QUERY` when a `WHERE` clause inside the PostgreSQL query would narrow it 100×.
