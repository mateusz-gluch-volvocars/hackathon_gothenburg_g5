# 🛢 Quest 2A-3 — Seed the Pothole Archive

<Objective lane="data">

**🎯 What you'll do.** Bulk-load 5,000 synthetic citizen pothole reports into your `pothole_reports` table from the seed CSV via `psql \copy`. ~5 min total; the actual copy is sub-second.

**🤝 Why it matters.** This is the *content* the entire Quest is about. Without these synthetic-but-suspiciously-Volvo-coded quotes (*"my V90 said 'good morning' and then 'goodbye'"*), Gemini has no material to riff on. Once these rows land, the Pipeline-author's DAG has data to enrich and your own BigQuery sub-lane (Q2C) has rows to federate against.

</Objective>

> Lane B · 3 of 3. ~5 minutes hands-on.

<Concept title="🤖 Or drive this with Antigravity CLI">

**Antigravity CLI** has an **`alloydb-seed-helper`** skill that does this end-to-end: resolves the AlloyDB private IP, inspects the live `pothole_reports` schema, pre-flights the CSV row count, proposes the `\copy` for your approval, and verifies the 5000-row load. Make sure you're in the Quest repo so the workspace plugin loads:

```bash
cd ~/quest
agy
```

then ask:

> *"Seed the AlloyDB pothole_reports table from the seed CSV in my repo."*

Read-only checks run on their own; the `\copy` itself pauses for your `y`. The QuickPath below is exactly what the skill runs under the hood, pick whichever you prefer.

</Concept>

<QuickPath>

```bash
# 1. Get AlloyDB private IP
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
[ -z "$ALLOYDB_HOST" ] && { echo "ERROR: empty IP — check cluster name"; exit 1; }
echo "AlloyDB private IP: $ALLOYDB_HOST"

# 2. Seed the table (~5 sec)
export PGPASSWORD='buildwithgemini2026'
psql "host=$ALLOYDB_HOST user=postgres dbname=postgres sslmode=require" \
  -c "\copy pothole_reports FROM '/home/user/quest/pothole-poet/seed/pothole_reports.csv' WITH (FORMAT csv, HEADER true, NULL '')"
# ✅ Expect: COPY 5000

# 3. Verify in AlloyDB Studio
# SELECT count(*) FROM pothole_reports;  → 5000
```

</QuickPath>

The CSV lives in your Workstation. AlloyDB Studio can't read your local filesystem (it's a browser app), so this part runs from the **Workstation terminal** with `psql` and `\copy`.

---

### Step 1 — Get the cluster's private IP

The cluster's private IP lives on the primary instance's **Connect** panel. It looks like `10.x.x.x`. the cluster name itself won't work as a host.

```bash
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
[ -z "$ALLOYDB_HOST" ] && { echo "ERROR: empty IP — check cluster name"; exit 1; }
echo "AlloyDB private IP: $ALLOYDB_HOST"
```

✅ **Expect:** `AlloyDB private IP: 10.x.x.x`

<Cheat title="Or read it from the Console">

Open the AlloyDB cluster page → click `pothole-archive-primary` → **Connect** panel (top-right) → copy the private IPv4. Then in your terminal:

```bash
export ALLOYDB_HOST=10.x.x.x   # paste the IP you copied
```

</Cheat>

### Step 2 — Seed the table with `\copy`

Set `PGPASSWORD` so psql doesn't prompt, then `\copy` the CSV in one command:

```bash
export PGPASSWORD='buildwithgemini2026'

psql "host=$ALLOYDB_HOST user=postgres dbname=postgres sslmode=require" \
  -c "\copy pothole_reports FROM '/home/user/quest/pothole-poet/seed/pothole_reports.csv' WITH (FORMAT csv, HEADER true, NULL '')"
```

✅ **Expect:** `COPY 5000` (sub-second)

<Concept title="Why \copy from the terminal, not Studio?">

`\copy` is a **psql client-side** command; it reads a file from wherever the psql binary is running and streams it to the server. AlloyDB Studio is a browser app: there is no client-side filesystem to read from. Studio can run server-side `COPY` (no backslash) but that needs the file to already exist on the AlloyDB server, which you can't put files on.

Your Workstation has the CSV at `~/quest/pothole-poet/seed/pothole_reports.csv` and a real psql binary. So `psql` from the terminal is the right tool: it reads the local CSV and streams it over the SSL connection to AlloyDB.

</Concept>

<Concept title="What does sslmode=require do?">

AlloyDB rejects unencrypted connections; every client must use TLS. `sslmode=require` is the psql way of saying *"demand TLS, but don't verify the server certificate."* For a private IP inside your VPC that's fine: the network path is already private and the AlloyDB control plane issues valid certs.

For higher-assurance environments you'd use `sslmode=verify-full` and provide the cluster's CA cert, but that's outside today's scope.

</Concept>

### Step 3 — Verify in AlloyDB Studio

In Studio's SQL editor, run:

```sql
SELECT count(*) FROM pothole_reports;
```

✅ **Expect:** `5000`

Optional sanity checks (paste them all at once, run separately):

```sql
-- Distribution: 12 neighbourhoods, Hisingen heaviest, Lorensberg lightest.
SELECT neighbourhood, count(*) AS reports
FROM pothole_reports
GROUP BY neighbourhood
ORDER BY reports DESC;

-- Sample five random rows. Citizen quotes should sound like real Gothenburg
-- complaints. If you see "It contains weather." — the Laureate will love it.
SELECT neighbourhood, severity_iron_marks, swallowed_object, reporter_quote
FROM pothole_reports
ORDER BY random()
LIMIT 5;
```

<Gotchas>
- <strong><code>psql: command not found</code>.</strong> Shouldn&rsquo;t happen. <code>psql</code> 16 is baked into the Iron &amp; Cloud workstation image. If it&rsquo;s genuinely missing, your workstation may be running an outdated image; flag a Sherpa.
- <strong><code>could not connect to server</code> or connection times out.</strong> <code>ALLOYDB_HOST</code> must be the cluster&rsquo;s <strong>private IP</strong> (a <code>10.x.x.x</code>), not the cluster name. Re-run the <code>gcloud alloydb instances describe</code> from Step 1.
- <strong><code>psql \copy</code> says <code>permission denied</code>.</strong> You&rsquo;re likely in <strong>AlloyDB Studio</strong>. <code>\copy</code> only works from a real shell. Studio has no filesystem.
- <strong><code>SSL connection required</code>.</strong> Add <code>sslmode=require</code> to the connection string. AlloyDB rejects unencrypted connections.
- <strong><code>COPY 0</code> instead of <code>COPY 5000</code>.</strong> Either the CSV path is wrong (<code>ls -la /home/user/quest/pothole-poet/seed/pothole_reports.csv</code> to confirm) or you forgot <code>HEADER true</code> and the column header row was treated as data and rejected.
- <strong>Re-running the seed shows "duplicate key value".</strong> The CSV has <code>id</code> values; re-running collides on the primary key. To re-seed cleanly: <code>TRUNCATE pothole_reports;</code> first, then re-run Step 2.
</Gotchas>

<Shipped>
The Garage&rsquo;s operational database is live. <strong>AlloyDB cluster <code>pothole-archive</code> is READY in <code>europe-west1</code>, with 5,000 citizen reports planted across 12 neighbourhoods.</strong> The BigQuery Lead can now wire federation against it; the Airflow Lead&rsquo;s DAG can pull from it.
</Shipped>

🛢 **AlloyDB sub-lane done.** Now switch to your BigQuery sub-lane.

If you already started **Q2C-3 (Analyst's Bench) Phase A** during the AlloyDB wait, keep going. Either way, your next critical-path task is **Q2C-2 (Federation)**: the Pipeline-author's DAG cannot run until the `alloydb_archive` connection exists. That handoff is on you.

➡️ Next: **Q2C-1 — BigQuery Tour** if you haven't started it, or **Q2C-2 — Federation** if you have.
