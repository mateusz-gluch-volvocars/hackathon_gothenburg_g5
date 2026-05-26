# 📊 Quest 2C-1 — Tour BigQuery Studio

<Objective lane="data">

**🎯 What you'll do.** Open BigQuery Studio in the Console, locate the pre-provisioned `pothole_laureate` dataset (already loaded with **6 reference tables** for The Analyst's Bench) and the `gemini` external connection, then run one warm-up query against a pre-loaded table to confirm everything is wired. ~5 minutes, pure orientation.

**🤝 Why it matters.** BigQuery Studio is where every BigQuery sub-lane task lives for the rest of the day. The `gemini` connection is what the Pipeline-author's DAG calls when it asks Gemini to compose; every "AI poems aren't appearing" support question traces back to it. And the 6 pre-loaded tables (neighbourhoods, crews, citizens, weather_daily, work_orders, social_sentiment) mean **Q2C-3 starts immediately**. you're not blocked on the Pipeline lane.

</Objective>

> Lane C · 1 of 3. ~5 minutes hands-on.

<QuickPath>

```bash
# 1. Confirm dataset + connection are pre-provisioned
bq ls --project_id="$(gcloud config get-value project)" pothole_laureate
bq ls --connection --project_id="$(gcloud config get-value project)" --location=europe-west1
# ✅ Expect: 6 pre-loaded tables (neighbourhoods, crews, citizens, weather_daily,
#            work_orders, social_sentiment); gemini connection listed

# 2. Warm-up query against a pre-loaded table
bq query --use_legacy_sql=false \
  'SELECT crew_name, foreman_name, motto FROM `pothole_laureate.crews` LIMIT 12'
# ✅ Expect: 12 rows, "Crew Hammer of Hisingen", "Crew Asphalt-and-Tonic", etc.
```

</QuickPath>

You don't need to create the dataset, the platform pre-provisioned `pothole_laureate` plus 6 reference tables for The Analyst's Bench (Q2C-3) plus the `gemini` external connection. You'll add one more connection in Q2C-2: the AlloyDB federation connection that lets the DAG land `pothole_reports_raw` alongside the pre-loaded tables.

---

### Step 1 — Open BigQuery Studio

Open `https://console.cloud.google.com/bigquery?project=<your-project-id>` in your laptop's browser.

✅ **Expect:** The Explorer panel runs down the left side. Top-level entries are projects you have access to.

### Step 2 — Confirm the pre-provisioned resources appear

In the Explorer panel, expand your project node, then expand `pothole_laureate`. Look for:

- **6 pre-loaded tables**. `citizens`, `crews`, `neighbourhoods`, `social_sentiment`, `weather_daily`, `work_orders`.
- `gemini` connection, under the **External connections** sub-folder.

✅ **Expect:** All 6 tables and the connection visible. If any are missing, the platform's provisioning didn't run; flag a Sherpa.

<Screenshot src="/quest/pothole-poet/img/bq_studio_explorer.png" caption="BigQuery Studio Explorer panel showing the pre-loaded tables and gemini connection." />

<Concept title="What's a dataset vs, an external connection?">

A **dataset** is BigQuery's container for tables, views, materialised views, and ML models; same idea as a *schema* in PostgreSQL. Names are scoped per-project; full table addresses look like `<project>.<dataset>.<table>`. Today's dataset is `pothole_laureate`, already populated with 6 reference tables for The Analyst's Bench. The DAG will add two more later: `pothole_reports_raw` (staging table from federation) and `neighbourhood_odes` (12 rows of Gemini-composed verse).

An **external connection** is a credentialed permission package that lets BigQuery reach *outside* itself:
- **Cloud-resource connection** (the pre-provisioned `gemini`): lets BigQuery call Vertex AI, so `AI.GENERATE` works. The connection has its own service account granted `roles/aiplatform.user`.
- **AlloyDB connector** (the `alloydb_archive` you'll create in Q2C-2): lets BigQuery query the AlloyDB cluster directly with `EXTERNAL_QUERY(...)`. The connection has its own SA granted `roles/alloydb.client`.

</Concept>

<Concept title="What are the 6 pre-loaded tables for?">

They're the analyst's **bench**. reference data that the BigQuery sub-lane works with from minute 1 (in Q2C-3), independent of the Pipeline lane's progress. When `pothole_reports_raw` and `neighbourhood_odes` land later, they join into these tables to answer richer questions.

| Table | Rows | What it is |
|---|---|---|
| `neighbourhoods` | 12 | Göteborg districts: population, road_km, iron_heritage_score, cobblestone_pct |
| `crews` | 12 | Fix crews with foreman + motto |
| `citizens` | 3,000 | Reporter identities, joins to `pothole_reports_raw.citizen_id` once it lands |
| `weather_daily` | 1,825 | 5 years of Göteborg weather with `freeze_thaw_event` flag |
| `work_orders` | 12,000 | 3 years of pothole repair history with SLA breach flag |
| `social_sentiment` | 3,150 | 3 years of citizen posts about road conditions |

</Concept>

### Step 3 — Warm-up query against a pre-loaded table

In Studio's editor, paste and **RUN**:

```sql
SELECT crew_name, base_neighbourhood, foreman_name, motto
FROM `pothole_laureate.crews`
ORDER BY founded_year;
```

✅ **Expect:** 12 rows of fix crews. Crew Old Forge (Gamlestaden) is oldest at 1953; Crew Gentle Slope (Örgryte) is newest at 2014. The Job History panel shows the run.

### Step 4 — While you wait for the AlloyDB sub-lane

a) **Read the federation script.** Open `pothole-poet/bigquery/setup_alloydb_connection.sh` in the Workstation IDE. Skim it; you'll run it in Q2C-2.

b) **Read the federation SQL files.** `pothole-poet/bigquery/test_federation.sql` and `pothole-poet/airflow/sql/01_federate.sql`. The latter is what the DAG runs against your federation connection; confirm you understand the `EXTERNAL_QUERY` shape.

c) **Open Q2C-3 in another tab and start the bench's Phase A.** The 6 pre-loaded tables mean you have ~30 minutes of real analyst work to do *before* the Pipeline lane's data lands. Don't sit idle.

<Gotchas>
- <strong>Empty Explorer panel.</strong> Project mismatch, the project selector at the top of the Console isn&rsquo;t set to your Garage&rsquo;s project. Switch it.
- <strong><code>pothole_laureate</code> dataset missing.</strong> The platform&rsquo;s pre-provisioning didn&rsquo;t run for your project. Flag a Sherpa.
- <strong><code>gemini</code> connection missing.</strong> Same as above, pre-provisioning issue.
- <strong>Public-dataset query fails with <code>billing not enabled</code>.</strong> The project doesn&rsquo;t have BigQuery billing wired. Flag a Sherpa.
- <strong>Studio shows the wrong project in the SQL editor header.</strong> Check the project selector at the top of the Console. Studio uses whatever&rsquo;s selected there for default table resolution.
</Gotchas>

<Shipped>
You&rsquo;re oriented. <strong>The pre-provisioned <code>pothole_laureate</code> dataset and <code>gemini</code> connection are visible in Explorer; Studio is responsive and your account can run queries.</strong> Ready to wire the AlloyDB federation.
</Shipped>

📊 **Q2C-1 done.** Oriented and warmed up.

➡️ Next: **Q2C-2 — Wire BigQuery → AlloyDB Federation**. This is the critical path: the Pipeline-author's DAG cannot run until you create the `alloydb_archive` connection. Start Q2C-2 as soon as Q2A-3 (seed) is done.

While you wait for the seed, open **Q2C-3 (Analyst's Bench) Phase A** in another tab. The 6 pre-loaded tables let you do ~30 min of real analyst work right now, no dependencies.
