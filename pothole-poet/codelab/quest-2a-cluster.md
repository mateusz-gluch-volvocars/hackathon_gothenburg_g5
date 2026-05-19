# 🛢 Quest 2A-1 — Create the AlloyDB Cluster

<Objective lane="data">

**🎯 What you'll do.** Create an AlloyDB cluster (PostgreSQL 16) with one primary instance sized 2 vCPU / 16 GB, then capture its private IP for the next two pages. ~12 minutes total — about 10 of those is just waiting for the cluster to come up.

**🤝 Why it matters.** This cluster is the operational store **every other persona reads from**. The Pipeline-author can't run their DAG without the rows you're about to plant. Your own BigQuery sub-lane (Q2C) can't wire the federation connection without the private IP you'll capture at the end. Without you, the Office of the Pothole Poet Laureate has nothing to be a Laureate *about*.

</Objective>

> Lane B · 1 of 3. ~12 minutes wall-clock (~2 min hands-on).

<QuickPath>

```bash
# 1. Create cluster + primary instance (~10 min provisioning)
gcloud alloydb clusters create pothole-archive \
  --region=europe-west1 \
  --network=default \
  --password=buildwithgemini2026

gcloud alloydb instances create pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --instance-type=PRIMARY --availability-type=REGIONAL \
  --cpu-count=2

# 2. Wait until READY (polls every 20 sec)
until [ "$(gcloud alloydb clusters describe pothole-archive --region=europe-west1 --format='value(state)')" = "READY" ]; do
  echo "still CREATING..."; sleep 20
done
# ✅ Expect: READY

# 3. Capture the private IP (use this in Q2A-2 / Q2A-3)
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
echo "AlloyDB private IP: $ALLOYDB_HOST"
```

</QuickPath>

You provision a **cluster** (the management unit) and a **primary instance** (the database server) — the Console wizard does both in one wizard. While you wait for it to come up, read the schema and pair with the BigQuery Lead.

---

### Step 1 — Click CREATE CLUSTER

Open the AlloyDB console: `https://console.cloud.google.com/alloydb/clusters?project=<your-project-id>` (in your laptop's browser — the Workstation has no browser).

Click **CREATE CLUSTER**. Pick **Highly available**.

Fill in these fields exactly:

| Field | Value |
|---|---|
| Cluster ID | `pothole-archive` |
| Password | `buildwithgemini2026` |
| Region | `europe-west1` |
| Network | `default` |
| PostgreSQL version | 16 (default) |

Click **CONFIGURE PRIMARY INSTANCE** → fill the next page → **CREATE PRIMARY INSTANCE** → **CREATE CLUSTER**.

| Field | Value |
|---|---|
| Instance ID | `pothole-archive-primary` |
| Machine type | smallest (2 vCPU, 16 GB) — **at the top** of the dropdown |
| Availability | Highly available |

✅ **Expect:** Cluster status shows ⏳ **CREATING**. Takes ~10 minutes.

<Concept title="AlloyDB has two layers: cluster + instance. Why?">

A **cluster** is the management unit — owns storage, backup policy, network attachment, IAM, user accounts. Doesn't run any database workload by itself.

An **instance** is the database server — attaches to a cluster and is the thing you connect to with `psql`. A cluster has one **PRIMARY** (read+write) and optionally read-pool / secondary instances. We only need a primary today.

</Concept>

<Concept title="Why pick 'Highly Available' for a 3-hour hackathon?">

For 3.5 hours of demo workload you'd never see a failover — so why not pick "Basic"? Two reasons:

1. The create form is identical either way — there's no extra clicking.
2. HA is the right default for any production workload, and building the muscle here means you do the right thing when you ship for real.

The only cost is a small bump in compute that you'll never notice on the smallest machine type.

</Concept>

### Step 2 — While you wait (~10 min): be useful

a) **Read the schema.** Open `pothole-poet/alloydb/schema.sql` in your Workstation IDE. Notice `swallowed_object` and `reporter_quote` — those are the columns that later make Gemini's poems funny.

b) **Read the seed quotes.** Open `pothole-poet/seed/citizen_quotes.txt`. These 120 lines are what we feed Gemini.

c) **Hand off cluster details to your BigQuery sub-lane (yourself, in Q2C).** Note these for federation setup in Q2C-2:

> *Cluster `pothole-archive`, primary instance `pothole-archive-primary`, region `europe-west1`. Password is the standard one.*

### Step 3 — Verify cluster is READY

Once the Console shows ✅ **READY**:

```bash
gcloud alloydb clusters describe pothole-archive \
  --region=europe-west1 \
  --format='value(state)'
```

✅ **Expect:** `READY`

Capture the private IP for Q2A-2 + Q2A-3:

```bash
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
echo "AlloyDB private IP: $ALLOYDB_HOST"
```

✅ **Expect:** `AlloyDB private IP: 10.x.x.x`

<Gotchas>
- <strong>Cluster stuck on CREATING for &gt;15 min.</strong> Refresh the cluster list (don&rsquo;t click Create again). Past 18 min, flag a Sherpa.
- <strong>Wrong network on cluster create.</strong> If you picked something other than <code>default</code>, BigQuery federation will fail later. Easiest fix: delete and recreate (still takes ~10 min, but unblocks Q2C).
- <strong>Smallest machine type missing from dropdown.</strong> Look at the <em>top</em> of the dropdown, not the bottom. The 2 vCPU/16 GB option is the smallest AlloyDB supports.
- <strong>Forgot the password.</strong> The Console doesn&rsquo;t reveal it after create. Reset with <code>gcloud alloydb users set-password postgres --cluster=pothole-archive --region=europe-west1 --password=...</code>.
- <strong>"Network is not configured for service networking" error.</strong> The platform&rsquo;s service-networking peering didn&rsquo;t run. Flag a Sherpa &mdash; this is pre-provisioned plumbing.
</Gotchas>

<Shipped>
The cluster is up. <strong>AlloyDB cluster <code>pothole-archive</code> is READY in <code>europe-west1</code> with a primary instance on a private IP.</strong> Empty so far &mdash; the next page installs the schema.
</Shipped>

🛢 **Q2A-1 done.** Cluster live, no tables yet.

➡️ Next: **Q2A-2 — Run the Schema in Studio** (sidebar on the left).
