# ⚙️ Quest 2B-1 — Create the Managed Airflow Environment

<Objective lane="pipeline">

**🎯 What you'll do.** Click create on a Managed Service for Apache Airflow Gen 3 environment (Airflow 3.1, default image). ~25 minutes of waiting — the **longest single wait of the day**. Don't refresh, don't cancel; while it provisions, read the *While you wait* steps so you know what you're orchestrating.

**🤝 Why it matters.** This environment is the **brain of the pipeline** — it wakes up on a schedule, pulls the Data Engineer's AlloyDB data into BigQuery, and tells Gemini to compose poems. Without your DAG running, the federation query just sits there and Streamlit is stuck on placeholder verse forever. You are the bottleneck on the path to a live pipeline — get the Create button clicked as early in the day as you can.

</Objective>

> Lane A · 1 of 3. ~28 minutes wall-clock (~3 min hands-on).

<QuickPath>

```bash
# Replace <garage_id> with your Garage ID from the workbench card (e.g. g01)
gcloud composer environments create the-laureate-bureau \
  --location=europe-west1 \
  --image-version=composer-3-airflow-3 \
  --service-account="composer-runner-<garage_id>@$(gcloud config get-value project).iam.gserviceaccount.com"
# ✅ Blocks for ~25 min, then prints the environment details when ready.
```

</QuickPath>

The command blocks until the environment is fully provisioned (~25 min). Don't cancel and retry — you'll only restart the clock. While it runs, read the *While you wait* section below.

<Concept title="What is Managed Airflow — and what is a DAG?">

**Apache Airflow** is a scheduler for data pipelines. Think of it as a smart alarm clock that runs your tasks in order, on a schedule, and retries if something fails. Instead of writing one long script that does steps A → B → C, you declare the steps and their dependencies as a **DAG** — a Directed Acyclic Graph.

The name sounds academic, but the idea is simple — think of a vehicle assembly line:

- **Directed:** tasks flow in a specific direction (welding must happen *before* painting).
- **Acyclic:** no loops (painting cannot loop back and re-weld the same chassis).
- **Graph:** a network of tasks connected by dependency lines.

Your DAG has two tasks: `federate_pothole_reports` (pull data from AlloyDB into BigQuery) then `ask_the_laureate` (call Gemini to compose poems). Airflow makes sure the second never runs until the first finishes.

**"Managed"** means Google runs all the Airflow infrastructure — the scheduler, the workers, the database, the web server — inside a Google-managed project you never see. You upload your DAG file, and Google handles everything else. The Console URL still says `composer` because the product was originally called Cloud Composer; the current brand is **Managed Service for Apache Airflow**, but it's the same service.

</Concept>

---

### Step 1 — Click CREATE ENVIRONMENT

Open: `https://console.cloud.google.com/composer/environments?project=<your-project-id>`

> The URL still uses `composer` for legacy reasons. The product is now branded **Managed Service for Apache Airflow** but the underlying API kept the original name.

<Screenshot src="/quest/pothole-poet/img/composer_environments_page.png" caption="The Composer Environments page — click CREATE ENVIRONMENT at the top." />

Click **CREATE ENVIRONMENT**. Pick **Gen 3** (*not* Gen 2 or Legacy).

Fill in these fields exactly:

| Field | Value |
|---|---|
| Name | `the-laureate-bureau` |
| Location | `europe-west1` |
| Image version | leave default (latest Gen 3 + Airflow 3.x) |
| Environment size | leave default (small) |
| Service account | `composer-runner-<garage_id>@<your-project-id>.iam.gserviceaccount.com` (pick from dropdown — `<garage_id>` is on your workbench card) |

Click **CREATE**.

<Screenshot src="/quest/pothole-poet/img/composer_create_form.png" caption="The Create Environment form — pick Gen 3, fill in Name / Location / Service account, leave everything else default." />

✅ **Expect:** Environment status shows ⏳ **CREATING**. Takes ~25 minutes.

<Screenshot src="/quest/pothole-poet/img/composer_creating_status.png" caption="the-laureate-bureau in CREATING state — the spinner is normal. This takes ~25 minutes." />

> **Do not** cancel and retry — you'll only restart the 25-minute clock.

<Concept title="What does a Managed Airflow environment actually contain?">

When you click CREATE, Google assembles managed infrastructure split across two projects:

**In a Google-managed "Tenant" Project (hidden from you):**
- A **GKE cluster** running the Airflow scheduler, triggerers, workers, and web server pods.
- A **Cloud SQL** database for Airflow's metadata (DAG runs, task states).

**In your Garage's GCP Project:**
- A **Cloud Storage bucket** that hosts your DAG files and logs.
- The **service account** that workers impersonate to interact with BigQuery.

You don't see or manage the GKE cluster or the database — the Console exposes only the Airflow UI and the DAGs bucket. The 25-minute provisioning time is Google spinning up that dedicated tenant infrastructure on your behalf.

</Concept>

<Concept title="Service account dropdown — what are you really picking?">

Every workload on Google Cloud runs *as* an identity — and that identity is what GCP checks when the workload tries to read BigQuery, talk to AlloyDB, or call any other service.

The platform pre-created `composer-runner-<garage_id>` for you because granting it the right BigQuery roles is boring plumbing, not the educational moment of the lab. When you pick it from the dropdown, you're telling Composer *"every task in my DAG should impersonate this identity"*.

Q2D uses a different identity model — Workload Identity Federation directly on a Kubernetes ServiceAccount — but the underlying idea is the same: workloads run *as* identities, identities have IAM roles, IAM roles decide what's allowed.

</Concept>

### Step 2 — While you wait (~25 min): be useful

a) **Read the DAG.** In your Workstation IDE, open `pothole-poet/airflow/compose_the_odes.py`. Two tasks. ~70 lines. As you read, look for answers to these:

   - Which Python class runs each task? (Hint: both use the same one.)
   - Where does the SQL come from — is it inline or read from files?
   - Look at the very last line: `federate_pothole_reports >> ask_the_laureate`. What does `>>` do?

<Concept title="The >> operator — how Airflow chains tasks">

In Python, `>>` is normally a bitwise right-shift. Airflow overloads it to mean **"runs before"**. So:

```python
federate_pothole_reports >> ask_the_laureate
```

tells the scheduler: *"Do not start `ask_the_laureate` until `federate_pothole_reports` completes successfully."* It's the equivalent of drawing an arrow between two boxes on a flowchart. If the first task fails, the second never runs — Airflow marks it as `upstream_failed`.

Both tasks use `BigQueryInsertJobOperator`, which tells BigQuery to run a SQL job. The Airflow worker doesn't process data itself — it just submits the job to BigQuery and waits for the result. The heavy lifting happens inside BigQuery's engine.

</Concept>

b) **Read the SQL.**
   - `pothole-poet/airflow/sql/01_federate.sql` — the federation pull. Note the `EXTERNAL_QUERY` against `alloydb_archive` (the connection the Data Engineer creates in Q2C-2).
   - `pothole-poet/airflow/sql/02_enrich.sql` — the AI moment. Read the prompt fed to Gemini. **This is the file the team edits during Quest 5 to change the Laureate's voice.** What voice does the default Laureate use? What data does the prompt draw on?

c) **Pair with the Data Engineer.** They're working in the AlloyDB sub-lane (Q2A-1..3) AND the BigQuery sub-lane (Q2C-1..3). You can't successfully run the DAG until BOTH AlloyDB is seeded AND BigQuery federation is wired.

d) **Stretch — brainstorm voices for Quest 5.** Open `02_enrich.sql` and think: pirate captain? IKEA assembly manual? ABBA chorus? Volvo press release? You'll edit this in Quest 5 — start thinking now.

### Step 3 — Verify environment is RUNNING

```bash
gcloud composer environments describe the-laureate-bureau \
  --location=europe-west1 \
  --format='value(state)'
```

✅ **Expect:** `RUNNING`

In the Console, the environment shows a green checkmark next to the name.

<Screenshot src="/quest/pothole-poet/img/composer_running_status.png" caption="Environment RUNNING — green checkmark in the Environments list. You're ready to upload the DAG." />

<Gotchas>
- <strong>Composer takes ~25 min &mdash; that&rsquo;s normal.</strong> Don&rsquo;t cancel and retry; you&rsquo;ll just restart the clock.
- <strong>Wrong Gen picked.</strong> Must be <strong>Gen 3</strong>. If you accidentally picked Gen 2 or Legacy, delete and re-create &mdash; the SQL we use depends on Airflow 3.x operators only available in Gen 3.
- <strong>Service account not in dropdown / wrong project.</strong> The SA dropdown filters to the current project. Confirm <code>gcloud config get-value project</code> matches your Garage&rsquo;s project_id, then refresh.
- <strong>Stuck CREATING for &gt;30 min.</strong> Past 30 min, flag a Sherpa &mdash; the GKE underneath may have hit a quota or transient issue.
- <strong>CREATING failed with <code>permission denied</code>.</strong> Composer&rsquo;s Service Agent needs <code>roles/composer.serviceAgentV2Ext</code> on the project &mdash; should be pre-bound by the platform; flag a Sherpa if you see this.
</Gotchas>

<Shipped>
The orchestration host is up. <strong>Composer environment <code>the-laureate-bureau</code> is RUNNING in <code>europe-west1</code>.</strong> Empty so far &mdash; the next page uploads the DAG.
</Shipped>

⚙️ **Q2B-1 done.** Environment ready.

➡️ Next: **Q2B-2 — Upload the DAG to GCS** (sidebar on the left).
