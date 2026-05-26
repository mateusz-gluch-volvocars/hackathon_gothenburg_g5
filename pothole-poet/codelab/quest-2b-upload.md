# ⚙️ Quest 2B-2 — Upload the DAG

<Objective lane="pipeline">

**🎯 What you'll do.** Copy `pothole-poet/airflow/compose_the_odes.py` and the two SQL files (`01_federate.sql`, `02_enrich.sql`) into your Composer environment's Cloud Storage bucket. Then wait 3-5 minutes for Airflow to sync and parse the file, surfacing the new DAG in the UI.

**🤝 Why it matters.** Until the DAG file is in the bucket, Airflow doesn't know `compose_the_odes` exists, the next page (trigger) has nothing to fire. Read the SQL files while you upload them: the two-task structure (federate AlloyDB → BigQuery, then enrich-with-AI) is what you'll demo to your teammates when they ask "wait, where do the poems actually come from?".

</Objective>

> Lane A · 2 of 3. ~3 minutes hands-on (~5 min for Airflow to parse).

<QuickPath>

```bash
# 1. Find the DAGs bucket path
DAGS_BUCKET="$(gcloud composer environments describe the-laureate-bureau \
  --location=europe-west1 \
  --format='value(config.dagGcsPrefix)')"
echo "DAGs bucket: $DAGS_BUCKET"

# 2. Upload DAG + sql/ folder (both needed)
gcloud storage cp -r ~/quest/pothole-poet/airflow/* "$DAGS_BUCKET/"

# 3. Verify upload
gcloud storage ls "$DAGS_BUCKET/" "$DAGS_BUCKET/sql/"
# ✅ Expect: compose_the_odes.py + sql/01_federate.sql + sql/02_enrich.sql

# 4. Wait 3-5 min, then check Airflow UI shows compose_the_odes (no error pill)
```

</QuickPath>

Apache Airflow doesn't read DAGs from your laptop; it reads them from a directory the scheduler scans on a fixed interval. Managed Airflow auto-creates a **Cloud Storage bucket** for this purpose; anything you put in `<bucket>/dags/` gets parsed and shows up in the Airflow UI.

<Concept title="What is Cloud Storage?">

Cloud Storage is Google's object storage service, the equivalent of Amazon S3 or Azure Blob Storage. Files are stored in **buckets** (containers with globally unique names). You interact with them through `gcloud storage` commands in the terminal, or through the Google Cloud Console in your browser.

Paths look like `gs://bucket-name/folder/file.txt`. the `gs://` prefix tells CLI tools to target Cloud Storage instead of your local filesystem.

</Concept>

---

### Step 1 — Find the DAGs bucket path

```bash
DAGS_BUCKET="$(gcloud composer environments describe the-laureate-bureau \
  --location=europe-west1 \
  --format='value(config.dagGcsPrefix)')"
echo "DAGs bucket: $DAGS_BUCKET"
```

✅ **Expect:** `gs://europe-west1-the-laureate-bu-1a2b3c4d-bucket/dags`

<Concept title="Why is the bucket name unpredictable?">

Composer auto-generates the bucket name with a region prefix + the environment name (truncated) + a hash. That makes the name deterministic per environment but not predictable from the env name alone, always look it up via `config.dagGcsPrefix` rather than guessing.

</Concept>

### Step 2 — Upload the DAG + `sql/` folder

`gcloud storage cp -r` uploads the DAG file and recurses into the `sql/` folder in one command. Multi-threading is automatic, no extra flags needed.

```bash
gcloud storage cp -r ~/quest/pothole-poet/airflow/* "$DAGS_BUCKET/"
```

> If you've seen `gsutil cp` in other tutorials or Stack Overflow answers, it does the same thing. `gcloud storage` is the modern replacement.

✅ **Expect:** confirmation lines for each file. Lands as:
- `<bucket>/dags/compose_the_odes.py`
- `<bucket>/dags/sql/01_federate.sql`
- `<bucket>/dags/sql/02_enrich.sql`

<Concept title="Why upload the sql/ folder too?">

`compose_the_odes.py` uses `BigQueryInsertJobOperator(configuration={"query": {"query": ..., "useLegacySql": False}})` and reads its SQL bodies from sibling paths like `sql/01_federate.sql` via Python's `Path(__file__).parent / "sql"`. At runtime, those paths resolve relative to the DAG file's location *inside the bucket*. specifically `/home/airflow/gcs/dags/sql/`.

If you upload only the `.py` file, the DAG parses fine but every task fails on first run with a "no such file" error. Upload the whole `airflow/` directory. DAG + sql/ folder, and the relative paths resolve.

</Concept>

<Concept title="Why gcloud storage cp instead of the official gcloud composer dags import?">

Google's official DAG upload command is `gcloud composer environments storage dags import --source=<file>`. It works well for a single Python file, but our DAG ships with a `sql/` subfolder alongside it. Using `gcloud storage cp -r` with a shell glob (`airflow/*`) copies both the `.py` file and the `sql/` directory in one command, preserving the folder structure Airflow expects.

</Concept>

<Cheat title="Or drag and drop in the Console">

From the Composer console: click your environment → **OPEN DAGS FOLDER** → drag the files into the GCS UI. Slower but no terminal needed.

</Cheat>

<Concept title="Why does verify_federation import inside the function body?">

Open `compose_the_odes.py` and find the `verify_federation` function. Notice the `from google.cloud import bigquery` line is *inside* the function, not at the top of the file.

This is intentional. Airflow's scheduler **parses** the DAG file (runs all top-level Python) every 30 seconds to build the task graph, but it never *executes* task code at parse time. Imports at the top of the file run during every parse cycle. Imports inside a `@task` function only run when that task actually executes on a worker.

For lightweight standard-library imports the difference doesn't matter. For heavy libraries like `google.cloud.bigquery` (which initializes HTTP clients and credential chains), importing at parse time wastes scheduler resources and can cause import errors if a library upgrade is mid-deploy. The rule from teams running Airflow at scale: **business logic and heavy imports go inside the task function, not at module level.**

</Concept>

<Concept title="What is the Asset declaration for?">

Near the top of `compose_the_odes.py` you'll see:

```python
from airflow.sdk import Asset

neighbourhood_odes = Asset(
    "bigquery://{project}/pothole_laureate/neighbourhood_odes".format(
        project=os.environ.get("GCP_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or "unknown"
    )
)
```

and on the final task:

```python
ask_the_laureate = BigQueryInsertJobOperator(
    ...,
    outlets=[neighbourhood_odes],
)
```

This declares that the DAG *produces* a data asset called `neighbourhood_odes`. When the task finishes successfully, Airflow marks the asset as "updated" in the **Assets** tab of the UI.

With one DAG, the declaration is a signal, not a trigger. But in a production environment with dozens of pipelines, assets are how Airflow 3 connects them: a `delivery` pipeline can schedule itself to run whenever the `verified_build` asset is updated by the `gate_out` pipeline. Instead of cron-based scheduling ("run every hour and hope the upstream data is fresh"), asset-aware scheduling means "run when the data I need actually changes."

We have one pipeline today; the pattern is here so you recognize it when you see it at scale.

</Concept>

### Step 3 — Verify the upload

```bash
gcloud storage ls "$DAGS_BUCKET/"
gcloud storage ls "$DAGS_BUCKET/sql/"
```

✅ **Expect:** the `dags/` listing shows `compose_the_odes.py`; the `sql/` listing shows both `.sql` files.

### Step 4 — Wait for Airflow to parse, then check the UI

After uploading, Managed Airflow syncs the bucket contents to its internal workers and parses the Python files. Per Google's documentation, **changes propagate within 3-5 minutes**. On a quiet environment with few DAGs, it can be as fast as 1-2 minutes, but plan for 5.

Open the Airflow UI:

1. In the Google Cloud Console, navigate to **Composer** → **Environments** (or use the URL from Q2B-1).
2. Find `the-laureate-bureau` in the list.
3. In the **Airflow webserver** column, click **Open Airflow UI**. this opens a new browser tab.

<Screenshot src="/quest/pothole-poet/img/composer_open_airflow_ui.png" caption="The Environments list, click the Airflow UI link in the Airflow webserver column." />

4. In the Airflow dashboard, click the **DAGs** tab.

✅ **Expect:** `compose_the_odes` listed alongside the built-in `airflow_monitoring` DAG. No red error pill. No banner at the top of the page.

<Screenshot src="/quest/pothole-poet/img/airflow_dags_list.png" caption="Airflow DAGs tab showing compose_the_odes parsed and ready to trigger." />

Click into `compose_the_odes`, then the **Tasks** tab. You should see the three tasks, their operator types, and retry counts:

<Screenshot src="/quest/pothole-poet/img/airflow_tasks_tab.png" caption="Tasks tab: two BigQueryInsertJobOperators (federation + enrichment) and one @task (verification), each with its own retry count." />

<Gotchas>
- <strong>DAG doesn&rsquo;t appear in the UI after 5 min.</strong> Check the <strong>DAG Errors</strong> banner at the top of the Airflow UI. it&rsquo;ll show the parse error. Most common: forgot the <code>sql/</code> folder upload, or there&rsquo;s a Python syntax error.
- <strong>DAG appears with red error pill.</strong> Click into it to see the import error. If it says &ldquo;No such file: <code>sql/01_federate.sql</code>&rdquo;. re-run the upload step with the <code>-r</code> flag to include the directory.
- <strong>Folder flattening via Console drag-and-drop.</strong> If you use the GCS Console UI instead of the terminal, <strong>do not select individual files inside the sql/ directory</strong>. The &ldquo;Upload files&rdquo; button flattens them directly into <code>/dags/</code> instead of <code>/dags/sql/</code>. At runtime, Airflow crashes with <code>No such file: sql/01_federate.sql</code>. To fix: click <strong>Create Folder</strong> in the bucket browser, name it <code>sql</code>, navigate into it, then upload the <code>.sql</code> files there.
- <strong>Wrong bucket path.</strong> The path must come from <code>config.dagGcsPrefix</code>. don&rsquo;t guess. Composer auto-generates the bucket name with a hash; it&rsquo;s not predictable.
- <strong><code>gcloud storage</code> errors with <code>access denied</code>.</strong> The Workstation SA needs <code>roles/storage.objectAdmin</code> on the bucket, pre-bound by the platform; flag a Sherpa if missing.
- <strong>Uploaded files but the timestamps don&rsquo;t update.</strong> <code>gcloud storage cp</code> skips files that haven&rsquo;t changed. To force re-upload, edit and re-save the DAG file to bump its timestamp, then re-upload.
</Gotchas>

<Shipped>
The DAG is in the bucket and parsed by Airflow. <strong><code>compose_the_odes</code> appears in the Airflow UI, ready to trigger.</strong> Three tasks defined: <code>federate_pothole_reports</code> (federation), <code>verify_federation</code> (row-count guard), and <code>ask_the_laureate</code> (AI enrichment).
</Shipped>

⚙️ **Q2B-2 done.** DAG uploaded and parsed.

➡️ Next: **Q2B-3 — Trigger the DAG** (sidebar on the left).
