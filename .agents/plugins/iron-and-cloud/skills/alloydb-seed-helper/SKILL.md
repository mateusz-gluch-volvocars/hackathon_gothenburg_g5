---
name: alloydb-seed-helper
description: Seeds and debugs the AlloyDB pothole_reports table for Q2A-3 of the Iron & Cloud Pothole Poet quest. Discovers the AlloyDB private IP, inspects the live schema, constructs the psql \copy from the seed CSV, and validates the 5000-row load. Use when the AlloyDB Lead asks to seed AlloyDB, debug seed failures, check pothole_reports schema, verify row counts, or run the seed for the first time.
---

# AlloyDB seed helper (Q2A-3)

**Codelab counterpart:** Q2A-3 — `~/quest/pothole-poet/codelab/quest-2a-seed.md`.

Use this skill when the AlloyDB Lead is seeding or debugging the seed of the `pothole_reports` table. Drive each step interactively; do not auto-run writes without HITL approval.

## What you can rely on

- The participant has completed Q2A-1 (cluster created) and Q2A-2 (schema applied).
- Seed CSV path: `~/quest/pothole-poet/seed/pothole_reports.csv` — 5,000 rows with header.
- Cluster name: `pothole-archive`. Primary instance name: `pothole-archive-primary`.
- Region: `europe-west1`. Database: `postgres`. User: `postgres`. Password: `buildwithgemini2026`.

## Steps

### 1. Resolve the AlloyDB private IP
```bash
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
echo "ALLOYDB_HOST=$ALLOYDB_HOST"
```
- If the IP is empty: confirm the cluster exists with `gcloud alloydb clusters list --region=europe-west1`. If missing, route the participant back to Q2A-1.
- If the cluster exists but state is not `READY`: surface the state value and tell them to wait — fresh AlloyDB clusters take ~12 minutes to become READY.

### 2. Inspect the live schema
```bash
PGPASSWORD=buildwithgemini2026 psql -h "$ALLOYDB_HOST" -U postgres -d postgres -c '\d pothole_reports'
```

Confirm the columns match the seed CSV header:
`id, reported_at, neighbourhood, severity_iron_marks, weather, reporter_mood, reporter_quote, citizen_id, swallowed_object`.

If the table doesn't exist, the schema script from Q2A-2 wasn't applied. Surface the issue rather than re-creating — Q2A-2 is the canonical place for schema work.

### 3. Pre-flight check the CSV
```bash
head -1 ~/quest/pothole-poet/seed/pothole_reports.csv
wc -l ~/quest/pothole-poet/seed/pothole_reports.csv
```
Expect a header row matching `\d pothole_reports`, and `5001` lines total (header + 5000 rows).

### 4. Propose the seed (HITL approval required)
```bash
PGPASSWORD=buildwithgemini2026 psql -h "$ALLOYDB_HOST" -U postgres -d postgres \
  -c "\copy pothole_reports FROM '$HOME/quest/pothole-poet/seed/pothole_reports.csv' WITH (FORMAT csv, HEADER true)"
```
Explain to the participant that `\copy` runs client-side (uses the participant's psql session, not server-side superuser COPY) so the CSV path is read from the Workstation filesystem.

### 5. Verify
```bash
PGPASSWORD=buildwithgemini2026 psql -h "$ALLOYDB_HOST" -U postgres -d postgres \
  -c 'SELECT count(*) AS rows, count(DISTINCT neighbourhood) AS neighbourhoods FROM pothole_reports'
```
Expect `rows = 5000` and `neighbourhoods = 12`.

## Common failure modes

- **`COPY 0`** — the file path didn't expand. Use `$HOME` instead of `~` inside the single-quoted `\copy` argument (psql does not expand tilde inside the quoted path).
- **`ERROR: column "..." of relation "pothole_reports" does not exist`** — schema doesn't match CSV header. Re-run Q2A-2 to re-apply the schema.
- **`could not translate host name` / `connection refused`** — AlloyDB private IP unreachable from the Workstation. Confirm both are in the same VPC; check `gcloud alloydb clusters describe pothole-archive --region=europe-west1 --format='value(state)'` is `READY`.
- **`password authentication failed`** — the password is `buildwithgemini2026` (it's the same across the dry-run; Garages may rotate it).

## Don't

- Don't drop and re-create the table to "fix" the seed. The schema is owned by Q2A-2.
- Don't propose a server-side `COPY` (without backslash) — it requires superuser-level filesystem access on the AlloyDB instance, which the participant doesn't have.
