# 📊 Quest 2C-2 — Wire BigQuery → AlloyDB Federation

<Objective lane="data">

**🎯 What you'll do.** Run `bigquery/setup_alloydb_connection.sh` from the Workstation terminal to create a BigQuery connection that reads from your AlloyDB cluster, then run a smoke query and confirm it returns 5,000 rows. ~5 minutes total once your AlloyDB sub-lane (Q2A-3) has finished seeding.

**🤝 Why it matters.** This connection is **what the Pipeline-author's DAG uses to pull AlloyDB rows into BigQuery** — without it, the DAG fails on its very first task. Once 5,000 rows come back from the smoke query, the federation half of the pipeline is proven and the Pipeline-author is unblocked.

</Objective>

> Lane C · 2 of 3. ~5 minutes hands-on.

<Concept title="🤖 Or drive this with Antigravity CLI">

**Antigravity CLI** has a **`bq-federation-helper`** skill that handles the two annoying parts of this lane: substituting your real `PROJECT_ID` into the federation path (no `<your-project-id>` Find-and-Replace) and adding the PostgreSQL `UUID` → `TEXT` cast inside the inner SELECT. Launch it from any terminal:

```bash
agy
```

then ask:

> *"Run the federation smoke test against alloydb_archive and confirm 5000 rows."*

or, for any ad-hoc federated query:

> *"Write a federation query that returns all pothole reports with severity ≥ 3 in Hisingen."*

The QuickPath and Studio paths below still work — the skill just bakes in the substitutions for you.

</Concept>

<QuickPath>

```bash
# 1. Set env vars for the script
export PROJECT_ID="$(gcloud config get-value project)"
export REGION="europe-west1"

# 2. Create the federation connection
bash ~/quest/pothole-poet/bigquery/setup_alloydb_connection.sh
# ✅ Expect: Connection alloydb_archive successfully created

# 3. Smoke test — should return 5000 rows from AlloyDB via BigQuery
bq query --use_legacy_sql=false "$(cat <<EOF
SELECT count(*) AS row_count
FROM EXTERNAL_QUERY(
  'projects/${PROJECT_ID}/locations/${REGION}/connections/alloydb_archive',
  'SELECT id::TEXT AS id FROM pothole_reports'
)
EOF
)"
# ✅ Expect: row_count=5000
```

</QuickPath>

The Pipeline-author's DAG starts with a federation pull. Without the `alloydb_archive` connection it fails on its first task. The platform shipped a script (`setup_alloydb_connection.sh`) that runs the right `bq mk` invocation for you.

---

### Step 1 — Skim the federation setup script

```bash
cat ~/quest/pothole-poet/bigquery/setup_alloydb_connection.sh
```

It calls `bq mk --connection` with a JSON `--connector_configuration` payload that names the AlloyDB cluster + instance as the federation target. Reads `PROJECT_ID` and `REGION` from environment variables.

<Concept title="What does federation mean here?">

**Federated query** means BigQuery sends a query to *another* database (AlloyDB), gets the rows back, and includes them in a SQL result as if they were a normal BigQuery table. You write something like:

```sql
SELECT * FROM EXTERNAL_QUERY('projects/.../connections/alloydb_archive',
                             'SELECT * FROM pothole_reports')
```

The string in single quotes is **PostgreSQL** sent to AlloyDB; the surrounding statement is BigQuery SQL. The DAG's `01_federate.sql` uses this pattern to materialise AlloyDB rows into a BigQuery staging table — no manual data export, no scheduled CSV dump.

</Concept>

<Concept title="Connector framework, not the legacy CLOUD_SQL flag">

AlloyDB uses BigQuery's modern **connector framework** (`--connector_configuration` with `connector_id: "google-alloydb"`). The legacy `--connection_type=CLOUD_SQL` flag predates this and only accepts CloudSQL instance names like `project:region:instance` — it rejects AlloyDB instance paths.

The script we run uses the connector framework. If you try the legacy flag with an AlloyDB instance path, you'll get a confusing "instance name format invalid" error. Worth knowing because it's the kind of thing you'd reach for if you Googled "BigQuery AlloyDB" and landed on an old StackOverflow answer.

</Concept>

### Step 2 — Run the script

```bash
export PROJECT_ID="$(gcloud config get-value project)"
export REGION="europe-west1"

bash ~/quest/pothole-poet/bigquery/setup_alloydb_connection.sh
```

✅ **Expect:** `Connection alloydb_archive successfully created`

> The script uses the same cluster + instance names your AlloyDB sub-lane picked (`pothole-archive` / `pothole-archive-primary`). If you used different names, edit the env vars at the top of the script first.
> 
> Re-running the script on an existing connection fails with "already exists" — safe to ignore; the connection is already there.

### Step 3 — Run the federation smoke query

In your Workstation terminal:

```bash
bq query --use_legacy_sql=false "$(cat <<EOF
SELECT count(*) AS row_count
FROM EXTERNAL_QUERY(
  'projects/${PROJECT_ID}/locations/${REGION}/connections/alloydb_archive',
  'SELECT id::TEXT AS id FROM pothole_reports'
)
EOF
)"
```

✅ **Expect:** `row_count: 5000`

<Concept title="The PostgreSQL UUID gotcha — why id::TEXT?">

BigQuery doesn't natively support PostgreSQL's `UUID` type. AlloyDB's `pothole_reports` table has an `id UUID` column (auto-generated by `gen_random_uuid()` from the `pgcrypto` extension). If you write `EXTERNAL_QUERY` against `SELECT * FROM pothole_reports`, BigQuery refuses with `PostgreSQL type UUID in column id is not supported in BigQuery`.

The fix: cast it inside the federated query — `SELECT id::TEXT AS id, ...`. The DAG SQL already does this. Only matters if you write your own ad-hoc federated query against the table.

</Concept>

<Cheat title="Or run from BigQuery Studio (with manual project_id substitution)">

In Studio's editor, paste this — **first** replace `<your-project-id>` (Studio's Find & Replace is fastest, Ctrl+H):

```sql
SELECT count(*) AS row_count
FROM EXTERNAL_QUERY(
  'projects/<your-project-id>/locations/europe-west1/connections/alloydb_archive',
  'SELECT id::TEXT AS id FROM pothole_reports'
);
```

If you forget the replacement, BigQuery returns `connection not found: projects/<your-project-id>/...` — that's the missing substitution, not a real error.

</Cheat>

### Step 4 — Verify both connections exist

```bash
bq query --use_legacy_sql=false \
  "SELECT connection_id, connection_type FROM \`region-europe-west1.INFORMATION_SCHEMA.CONNECTIONS\` WHERE connection_id IN ('gemini', 'alloydb_archive')"
```

✅ **Expect:** Two rows — `gemini` (CLOUD_RESOURCE) and `alloydb_archive` (CLOUD_RESOURCE).

<Gotchas>
- <strong><code>bq mk --connection_type=CLOUD_SQL</code> rejects the AlloyDB instance path.</strong> Use the modern connector framework: <code>--connector_configuration</code> with <code>connector_id: "google-alloydb"</code> &mdash; the existing script does this; don&rsquo;t roll your own.
- <strong>Federation query returns 0 rows or hangs.</strong> Either AlloyDB isn&rsquo;t READY yet, or the cluster/instance ID in the connector config doesn&rsquo;t match what you provisioned in Q2A-1. Confirm with <code>gcloud alloydb clusters list --region=europe-west1</code>.
- <strong><code>PostgreSQL type UUID in column id is not supported in BigQuery</code>.</strong> Cast it: <code>SELECT id::TEXT AS id, ...</code>. The DAG SQL and <code>test_federation.sql</code> already do this; only matters if you write your own ad-hoc query.
- <strong><code>&#36;&#123;PROJECT_ID&#125;</code> appears literally in the error message.</strong> You missed a Find &amp; Replace in Studio. Either replace it manually with your project_id, or use the <code>bq query</code> bash form in QuickPath above (which expands env vars automatically).
- <strong>Connection shows up in <code>INFORMATION_SCHEMA</code> but federation fails with permission errors.</strong> The connection&rsquo;s service account needs <code>roles/alloydb.client</code> on your project &mdash; should be pre-bound by the platform; flag a Sherpa.
</Gotchas>

<Shipped>
The analytical layer is wired. <strong>BigQuery dataset <code>pothole_laureate</code> is live, the <code>alloydb_archive</code> federation connection returns 5000 rows from AlloyDB, and the <code>gemini</code> connection is bound for <code>AI.GENERATE</code>.</strong> The Pipeline-author can now run the DAG; the App Dev / Guardian can read from this dataset for Silver tier.
</Shipped>

📊 **Q2C-2 done.** Federation is live.

Tell the Pipeline-author:
> *"BigQuery is set, `alloydb_archive` connection exists, federation returns 5000. You're clear to upload and trigger the DAG."*

➡️ Next: **Q2C-3 — The Analyst's Bench** to flex on the 6 pre-loaded tables (Phase A) and join today's federated data into them once Q3 lands (Phase B).
