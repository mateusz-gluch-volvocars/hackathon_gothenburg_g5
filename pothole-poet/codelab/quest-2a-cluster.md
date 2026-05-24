# 🛢 Quest 2A-1 — Create the AlloyDB Cluster

<Objective lane="data">

**🎯 What you'll do.** Create an AlloyDB cluster (PostgreSQL 16) with one primary instance sized 2 vCPU / 16 GB, then capture its private IP for the next two pages. ~12 minutes total — about 10 of those is just waiting for the cluster to come up.

**🤝 Why it matters.** This cluster is the operational store **every other persona reads from**. The Pipeline-author can't run their DAG without the rows you're about to plant. Your own BigQuery sub-lane (Q2C) can't wire the federation connection without the private IP you'll capture at the end. Without you, the Office of the Pothole Poet Laureate has nothing to be a Laureate *about*.

</Objective>

> Lane B · 1 of 3. ~12 minutes wall-clock (~2 min hands-on).

<QuickPath>

Run each command in turn. `gcloud` prints progress and blocks until the operation finishes — no polling loop needed.

Create the cluster (~2 min):

```bash
gcloud alloydb clusters create pothole-archive \
  --region=europe-west1 \
  --network=garage-vpc \
  --password=buildwithgemini2026
```

Create the primary instance (~8 min):

```bash
gcloud alloydb instances create pothole-archive-primary \
  --cluster=pothole-archive \
  --region=europe-west1 \
  --instance-type=PRIMARY \
  --availability-type=ZONAL \
  --cpu-count=2
```

Print the private IP — you'll paste it into Q2A-2 and Q2A-3:

```bash
gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive \
  --region=europe-west1 \
  --format='value(ipAddress)'
```

Expected output: `10.x.x.x`

</QuickPath>

You provision a **cluster** (the management unit) and a **primary instance** (the database server) — the Console wizard does both in one wizard. While you wait for it to come up, read the schema and pair with the BigQuery Lead.

---

### Step 1 — Click CREATE CLUSTER

Open the AlloyDB console: `https://console.cloud.google.com/alloydb/clusters?project=<your-project-id>` (in your laptop's browser — the Workstation has no browser).

Click **CREATE CLUSTER**. Pick **Basic** (single instance, single zone — right choice for a 3.5-hour workload; HA would just burn compute on a standby you'll never failover to).

Fill in these fields exactly:

| Field | Value |
|---|---|
| Cluster ID | `pothole-archive` |
| Password | `buildwithgemini2026` |
| Region | `europe-west1` |
| Network | `garage-vpc` |
| PostgreSQL version | 16 (default) |

Click **CONFIGURE PRIMARY INSTANCE** → fill the next page → **CREATE PRIMARY INSTANCE** → **CREATE CLUSTER**.

| Field | Value |
|---|---|
| Instance ID | `pothole-archive-primary` |
| Machine type | smallest (2 vCPU, 16 GB) — **at the top** of the dropdown |
| Availability | Zonal (single zone) |

✅ **Expect:** Cluster status shows ⏳ **CREATING**. Takes ~10 minutes.

<Concept title="AlloyDB has two layers: cluster + instance. Why?">

A **cluster** is the management unit — owns storage, backup policy, network attachment, IAM, user accounts. Doesn't run any database workload by itself.

An **instance** is the database server — attaches to a cluster and is the thing you connect to with `psql`. A cluster has one **PRIMARY** (read+write) and optionally read-pool / secondary instances. We only need a primary today.

</Concept>

### Step 2 — While you wait (~10 min): be useful

a) **Read the schema.** Open `pothole-poet/alloydb/schema.sql` in your Workstation IDE. Notice `swallowed_object` and `reporter_quote` — those are the columns that later make Gemini's poems funny.

b) **Read the seed quotes.** Open `pothole-poet/seed/citizen_quotes.txt`. These 120 lines are what we feed Gemini.

c) **Hand off cluster details to your BigQuery sub-lane (yourself, in Q2C).** Note these for federation setup in Q2C-2:

> *Cluster `pothole-archive`, primary instance `pothole-archive-primary`, region `europe-west1`. Password is the standard one.*

### Step 3 — Grab the private IP

Once the Console shows ✅ **READY**, pull the primary's private IP from your Workstation terminal — you'll paste it into Q2A-2 and Q2A-3:

```bash
gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive \
  --region=europe-west1 \
  --format='value(ipAddress)'
```

Expected output: `10.x.x.x` (jot it down).

<Gotchas>
- <strong>Cluster stuck on CREATING for &gt;15 min.</strong> Refresh the cluster list (don&rsquo;t click Create again). Past 18 min, flag a Sherpa.
- <strong>Wrong network on cluster create.</strong> If you picked something other than <code>garage-vpc</code> (or your Console didn&rsquo;t show <code>garage-vpc</code> in the dropdown), BigQuery federation will fail later. Easiest fix: delete and recreate (still takes ~10 min, but unblocks Q2C).
- <strong>Smallest machine type missing from dropdown.</strong> Look at the <em>top</em> of the dropdown, not the bottom. The 2 vCPU/16 GB option is the smallest AlloyDB supports.
- <strong>Forgot the password.</strong> The Console doesn&rsquo;t reveal it after create. Reset with <code>gcloud alloydb users set-password postgres --cluster=pothole-archive --region=europe-west1 --password=...</code>.
- <strong>"Network is not configured for service networking" error.</strong> The platform&rsquo;s service-networking peering didn&rsquo;t run. Flag a Sherpa &mdash; this is pre-provisioned plumbing.
</Gotchas>

<Shipped>
The cluster is up. <strong>AlloyDB cluster <code>pothole-archive</code> is READY in <code>europe-west1</code> with a primary instance on a private IP.</strong> Empty so far &mdash; the next page installs the schema.
</Shipped>

🛢 **Q2A-1 done.** Cluster live, no tables yet.

➡️ Next: **Q2A-2 — Run the Schema in Studio** (sidebar on the left).
