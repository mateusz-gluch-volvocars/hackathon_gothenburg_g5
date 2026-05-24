# 🛢 Quest 2A-2 — Run the Schema in Studio

<Objective lane="data">

**🎯 What you'll do.** Open AlloyDB Studio, paste the contents of `pothole-poet/alloydb/schema.sql`, and hit RUN. Creates one table (`pothole_reports`) with the columns and indexes the rest of the pipeline expects. Under a minute of hands-on work.

**🤝 Why it matters.** Without this table the next page (seed) has nowhere to put 5,000 rows, and your own BigQuery federation query (Q2C-2) has nothing to read against. The schema is small but every column matters — the Pipeline-author's DAG groups by `neighbourhood`, ranks by `severity`, and pulls `reporter_quote` and `swallowed_object` straight into Gemini's prompt.

</Objective>

> Lane B · 2 of 3. ~3 minutes hands-on.

<QuickPath>

```bash
# Run the schema via psql (alternative to Studio click-through)
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
export PGPASSWORD='buildwithgemini2026'
psql "host=$ALLOYDB_HOST user=postgres dbname=postgres sslmode=require" \
  -f ~/quest/pothole-poet/alloydb/schema.sql
# ✅ Expect: CREATE EXTENSION / CREATE TABLE / CREATE INDEX / CREATE INDEX

# Verify
psql "host=$ALLOYDB_HOST user=postgres dbname=postgres sslmode=require" \
  -c "\dt pothole_reports"
# ✅ Expect: one row showing pothole_reports
```

</QuickPath>

The cluster is up and empty. Time to install the table that holds citizen pothole reports. The walkthrough below uses **AlloyDB Studio** — an in-browser SQL editor that ships with AlloyDB. No psql install, no client setup; just a query tab and a RUN button.

---

### Step 1 — Open AlloyDB Studio

In the AlloyDB console, click into your `pothole-archive` cluster, then click **AlloyDB Studio** in the left navigation.

✅ **Expect:** A sign-in dialog appears.

<Screenshot src="/quest/pothole-poet/img/alloydb_cluster_overview.png" caption="Cluster overview showing READY status. The AlloyDB Studio link appears in the left nav once the cluster is up." />

### Step 2 — Sign in as `postgres`

| Field | Value |
|---|---|
| Database | `postgres` |
| User | `postgres` |
| Password | `buildwithgemini2026` |

✅ **Expect:** Studio opens with a blank query tab + Explorer panel on the left.

<Concept title="Why Studio instead of pgAdmin or DBeaver?">

You absolutely could install pgAdmin or DBeaver locally and connect over the AlloyDB Auth Proxy. For a one-off schema run during a lab, that's friction with no payoff. Studio:

- Is already authenticated against your GCP identity (no key download, no proxy install).
- Lives in the same Console tab where you created the cluster.
- Survives Workstation idle-outs (it's just a browser tab on your laptop).

For day-to-day work where you need a real desktop SQL client, pgAdmin or DBeaver against the AlloyDB Auth Proxy is the right call. For today, Studio.

</Concept>

### Step 3 — Paste and run the schema

Open `pothole-poet/alloydb/schema.sql` in your Workstation IDE. Select all, copy, then in Studio click **+ NEW TAB**, paste, and hit **RUN**.

✅ **Expect** (in the bottom output panel):
- `CREATE EXTENSION` (the `pgcrypto` extension we use for `gen_random_uuid()` default IDs)
- `CREATE TABLE` (the `pothole_reports` table)
- Three `CREATE INDEX` (on `neighbourhood`, `reported_at`, and `citizen_id`)

### Step 4 — Verify the schema landed

In a new Studio tab, run:

```sql
-- The table exists.
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';
```

✅ **Expect:** at least one row, `pothole_reports`.

```sql
-- The columns are right.
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'pothole_reports'
ORDER BY ordinal_position;
```

✅ **Expect:** 11 rows — `id, reported_at, neighbourhood, latitude, longitude, severity_iron_marks, weather, reporter_mood, swallowed_object, reporter_quote, citizen_id`.

<Gotchas>
- <strong>Studio sign-in fails: <code>connection refused</code> or timeout.</strong> Cluster isn&rsquo;t fully READY yet &mdash; wait 30 sec and retry. If still failing past 2 min, the primary instance may still be initialising.
- <strong>Wrong password error.</strong> Re-set with <code>gcloud alloydb users set-password postgres --cluster=pothole-archive --region=europe-west1</code>.
- <strong>Schema run partial.</strong> Re-run the whole file. The schema uses <code>CREATE TABLE IF NOT EXISTS</code> and <code>CREATE EXTENSION IF NOT EXISTS</code> &mdash; idempotent.
- <strong>Created a new database by accident.</strong> No harm done, but the rest of the Quest assumes <code>postgres</code> as the database name. Use <code>postgres</code> from now on.
- <strong><code>permission denied for schema public</code>.</strong> You signed in as a different user than <code>postgres</code>. Sign out and back in.
</Gotchas>

<Shipped>
The schema is installed. <strong>The <code>pothole_reports</code> table exists in the <code>postgres</code> database with all 10 expected columns and two indexes.</strong> Empty so far &mdash; next page fills it with 5,000 rows.
</Shipped>

🛢 **Q2A-2 done.** Schema installed.

➡️ Next: **Q2A-3 — Seed from the Terminal** (sidebar on the left).
