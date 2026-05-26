# ⚙️ Quest 2B-3 — Trigger the DAG

<Objective lane="pipeline">

**🎯 What you'll do.** Trigger the `compose_the_odes` DAG manually from the Airflow UI (or one gcloud command) and watch all three tasks finish (~30 sec federation, ~5 sec verification, ~30-60 sec AI enrichment). Verify BigQuery now has 12 rows in `pothole_laureate.neighbourhood_odes`, one Gemini-composed three-line ode per Goteborg neighbourhood.

**🤝 Why it matters.** This is the moment the **whole pipeline lights up for the first time**. The Data Engineer's federation finally gets used, their table finally gets read, Gemini finally gets called, and BigQuery finally has poems. After this page, the App Dev / Guardian can switch Streamlit's `MODE` to `live` and the audience sees real AI verse instead of placeholder text. **You are the persona that completes the Foundation.**

</Objective>

> Lane A · 3 of 3. ~3 minutes hands-on.

<QuickPath>

```bash
# 1. Trigger the DAG (returns immediately; runs ~1-2 min in background)
gcloud composer environments run the-laureate-bureau \
  --location=europe-west1 \
  dags trigger -- compose_the_odes

# 2. Wait ~2 min, then verify in BigQuery
bq query --use_legacy_sql=false \
  'SELECT count(*) AS n FROM `pothole_laureate.neighbourhood_odes`'
# ✅ Expect: n=12

bq query --use_legacy_sql=false --format=prettyjson \
  'SELECT neighbourhood, ode FROM `pothole_laureate.neighbourhood_odes` ORDER BY pothole_count DESC LIMIT 1'
# ✅ Expect: a real three-line poem (probably about Hisingen)
```

</QuickPath>

DAG is in the bucket, parsed, sitting ready in the Airflow UI. Now we trigger it manually (don't wait for the scheduled run) and watch the AI moment unfold.

<Callout type="critical" title="Two lanes must be done before you trigger">

1. **AlloyDB Lead must finish Q2A-3 (Seed).** The DAG federates data from AlloyDB into BigQuery. If AlloyDB has no data, the `verify_federation` task catches it and **fails with a clear error message** pointing back to Q2A-3. This is the guard rail: it prevents the expensive Gemini AI call from running on an empty table.
2. **BigQuery Lead must finish Q2C-2 (Federation).** The DAG's first task reads via the `alloydb_archive` BigQuery connection. If it doesn't exist yet, the task fails with `connection alloydb_archive not found`.

</Callout>

Here's what will happen when you trigger: Airflow runs the three tasks in order. First, `federate_pothole_reports` submits a BigQuery SQL job that pulls AlloyDB data via the federation connection. When that finishes, `verify_federation` runs a quick row-count check on the staging table; if it's empty (AlloyDB wasn't seeded), the DAG fails here instead of wasting time on the AI call. If the count is good, `ask_the_laureate` submits a second BigQuery SQL job that aggregates the data and calls Gemini via `AI.GENERATE` to compose 12 poems. The SQL jobs execute inside BigQuery's engine; the Airflow worker just submits them and waits.

---

### Step 1 — Unpause the DAG (if paused)

New DAGs in Airflow start **paused** by default, the scheduler won't run them until you unpause.

In the Airflow UI **DAGs** tab, find `compose_the_odes`. If the toggle next to its name shows a **pause icon** (⏸ or a blue slider), click it to **unpause**. If the toggle is already in the "on" position, skip this step.

<Screenshot src="/quest/pothole-poet/img/airflow_unpause_toggle.png" caption="The pause/unpause toggle next to the DAG name. Click it so it turns to the 'on' (unpaused) position." />

### Step 2 — Trigger the DAG

In the Airflow UI, click into `compose_the_odes`, then click the **Trigger DAG** button (top-right ▶ play icon). Confirm in the dialog.

<Screenshot src="/quest/pothole-poet/img/airflow_trigger_button.png" caption="Inside the DAG view, the Trigger DAG button is the play icon (▶) in the top-right area." />

✅ **Expect:** The DAG run appears in the Grid view with a yellow ⏳ "running" status.

<Cheat title="Or trigger from the CLI">

```bash
gcloud composer environments run the-laureate-bureau \
  --location=europe-west1 \
  dags trigger -- compose_the_odes
```

> **Expect a ~30-second pause before output.** This command tunnels through Google's secure control plane to reach the Airflow worker inside a GKE cluster. The delay is normal; don't press Ctrl+C thinking it's hung.

The CLI returns after the trigger is submitted; check the UI for run status.

</Cheat>

### Step 3 — Watch the run go green (~1-2 min)

In the **Grid view** (the default view when you click into a DAG), each square represents one task run. The colour tells you the status: **green** = success, **yellow** = running, **red** = failed, **grey** = not yet started. Click any red square to see its error logs.

All three tasks should turn green in sequence:

- `federate_pothole_reports` (~30 sec): pulls AlloyDB rows into BigQuery via the federation connection.
- `verify_federation` (~5 sec): confirms the staging table has rows. If this goes red, AlloyDB wasn't seeded yet.
- `ask_the_laureate` (~30-60 sec): Gemini composes 12 odes via `AI.GENERATE`.

✅ **Expect:** Three green squares in the Grid view. If any goes red, click into it and read the logs.

<Screenshot src="/quest/pothole-poet/img/airflow_grid_view.png" caption="Successful DAG run with all three tasks green in the Airflow Grid view." />

Click any task square to open the **task instance view**. Airflow 3 takes you straight to a tabbed page showing the task name, status badge, start/end dates, and duration in the header, with the **Logs** tab open by default.

<Screenshot src="/quest/pothole-poet/img/airflow_task_detail.png" caption="Airflow 3 task instance view, header shows task name, status, and timing; tabs below give access to Logs, Rendered Templates, XCom, and more." />

If a task failed, the Logs tab shows the full execution output. Scroll to the bottom for the actual error, look for lines marked `ERROR` or `FAILED`. You can filter by log level using the dropdown above the log output. Common errors are covered in the gotchas at the bottom of this page.

> **Bonus:** click the `verify_federation` task square, then the **XCom** tab. You'll see `{"federated_rows": 5000}`, the row count the `@task` function returned. This is how Airflow passes small data between tasks: the return value of a `@task` function is automatically stored as XCOM. Operators use XCOM too, but they push it explicitly; TaskFlow makes it automatic.

<Screenshot src="/quest/pothole-poet/img/airflow_task_logs.png" caption="Logs tab showing a successful ask_the_laureate run. 'BigQuery job completed successfully. 12 rows' confirms the odes landed." />

<Concept title="The AI moment">

`ask_the_laureate` is the task where everything you've built becomes real. It only runs after `verify_federation` confirms the staging table has data (so you never burn Gemini tokens on empty input). It runs a single BigQuery `CREATE OR REPLACE TABLE ... AS SELECT` that:

1. Aggregates the 5,000 federated reports per neighbourhood (group by, count, avg severity, dominant weather/mood).
2. Calls `AI.GENERATE` against a Gemini 3 Flash endpoint with a per-neighbourhood prompt that reads back actual citizen quotes and asks for a three-line poem in the Laureate's voice.
3. Writes the result to `pothole_laureate.neighbourhood_odes`.

12 LLM calls, one per neighbourhood, all in a single BigQuery statement via `AI.GENERATE`. Takes ~30-60 seconds total. When the task completes, Airflow marks the `neighbourhood_odes` **Asset** as updated (visible in the Assets tab).

</Concept>

Back on the Airflow home page, the dashboard confirms a healthy environment: all health checks green, successful runs, and the **Asset Events** panel on the right shows each time `compose_the_odes` updated the `neighbourhood_odes` asset.

<Screenshot src="/quest/pothole-poet/img/airflow_home_dashboard.png" caption="Airflow home: health checks green, successful DAG runs, and Asset Events showing neighbourhood_odes updates from compose_the_odes." />

### Step 4 — Read at least one of the odes out loud

In BigQuery Studio:

```sql
SELECT neighbourhood, ode
FROM `pothole_laureate.neighbourhood_odes`
ORDER BY pothole_count DESC
LIMIT 3;
```

✅ **Expect:** Three rows, each with a real Gemini-composed three-line poem about a Gothenburg neighbourhood. Hisingen first, then Frölunda, then Kortedala.

If the poem mentions cinnamon buns, weather, Eurovision, or Carl, you've made the Laureate proud.

<Screenshot src="/quest/pothole-poet/img/bq_neighbourhood_odes.png" caption="BigQuery Studio showing the neighbourhood_odes query result, real Gemini-composed poetry for each Gothenburg neighbourhood." />

### Step 5 — Verify the full set

```sql
SELECT count(*) FROM `pothole_laureate.neighbourhood_odes`;
```

✅ **Expect:** `12` (one per neighbourhood)

```sql
SELECT neighbourhood, dominant_weather, dominant_mood, composed_at
FROM `pothole_laureate.neighbourhood_odes`
ORDER BY composed_at DESC
LIMIT 5;
```

✅ **Expect:** 5 rows with recent `composed_at` timestamps and real values for `dominant_weather` and `dominant_mood`.

<Cheat title="View task logs in your terminal (without the Airflow UI)">

If you prefer a terminal-centric workflow, you can query Cloud Logging directly for the task output:

```bash
PROJECT_ID="$(gcloud config get-value project)"

gcloud logging read \
  --project="$PROJECT_ID" \
  --format="value(textPayload)" \
  --order=asc \
  --limit=100 \
  "resource.type=cloud_composer_environment \
   resource.labels.location=europe-west1 \
   resource.labels.environment_name=the-laureate-bureau \
   labels.workflow=compose_the_odes"
```

This pulls the recent execution logs, including any errors from the BigQuery jobs or the Gemini `AI.GENERATE` call.

</Cheat>

<Gotchas>
- <strong><code>federate_pothole_reports</code> fails: <code>connection alloydb_archive not found</code>.</strong> The Data Engineer&rsquo;s BigQuery sub-lane (Q2C-2) hasn&rsquo;t created the federation connection yet. Wait for them, then re-trigger.
- <strong><code>ask_the_laureate</code> fails on <code>AI.GENERATE</code> with <code>permission denied</code>.</strong> The <code>gemini</code> connection&rsquo;s service account is missing <code>roles/aiplatform.user</code>. Should be pre-bound by the platform; flag a Sherpa.
- <strong><code>gemini-3-flash</code> not found error.</strong> Gemini 3 is global-endpoint only. The DAG SQL uses the full URL <code>https://aiplatform.googleapis.com/v1/projects/&lt;project&gt;/locations/global/publishers/google/models/gemini-3-flash-preview</code>. if you edited it and dropped the URL form, restore it.
- <strong><code>verify_federation</code> goes red: &ldquo;Federation pulled 0 rows&rdquo;.</strong> AlloyDB has no data. The AlloyDB Lead must finish Q2A-3 (Seed), then you re-trigger. The guard caught what used to be a silent failure.
- <strong>DAG ran green but <code>neighbourhood_odes</code> shows 0 rows.</strong> Should not happen with the verification guard. If it does, check that the staging table <code>pothole_reports_raw</code> has data: <code>SELECT count(*) FROM pothole_laureate.pothole_reports_raw</code>.
- <strong>Odes appear as raw JSON, not poetry.</strong> The <code>AI.GENERATE</code> response wasn&rsquo;t unwrapped; check that <code>02_enrich.sql</code> reads <code>.result</code> off the AI.GENERATE call.
- <strong>Trigger button greyed out or DAG not firing.</strong> The DAG may still be paused. Go back to the DAGs list and click the toggle next to <code>compose_the_odes</code> to unpause (Step 1 on this page).
- <strong>CLI command hangs for 30+ seconds.</strong> Normal. <code>gcloud composer environments run</code> tunnels through Google&rsquo;s control plane to reach the Airflow worker, the initial connection takes ~30 seconds. Don&rsquo;t press Ctrl+C.
- <strong>Any task goes red and the Airflow UI logs are unclear.</strong> Open the Logs Explorer (Q1-5) and filter: Resource Type = <code>cloud_composer_environment</code>, then add <code>labels.workflow=compose_the_odes</code> in the Query pane. Composer Gen 3 stores all task logs exclusively in Cloud Logging; this is often more detailed than what the Airflow UI shows.
</Gotchas>

<Shipped>
The orchestration layer is fully live. <strong>The <code>compose_the_odes</code> DAG ran green end-to-end: federation, verification, and AI enrichment. 12 Gemini-composed odes now sit in <code>pothole_laureate.neighbourhood_odes</code>.</strong> The App Dev / Guardian can now switch Streamlit to live pipeline data.
</Shipped>

⚙️ **Lane A done.** Tell the App Dev / Guardian:

> *"DAG is green. `pothole_laureate.neighbourhood_odes` has 12 rows. Swap the data source."*

➡️ Next: **Quest 3 — Wire the Pipeline** (sidebar on the left). The team converges; you celebrate with them.
