# 🛢 Quest 2A-1 — Create the AlloyDB Cluster

<Objective lane="data">

**🎯 What you'll do.** Create an AlloyDB cluster with one primary instance sized 2 vCPU / 16 GB, then capture its private IP for the next two pages. ~12 minutes total, about 10 of those is just waiting for the cluster to come up.

**🤝 Why it matters.** This cluster is the operational store **every other persona reads from**. The Pipeline-author can't run their DAG without the rows you're about to plant. Your own BigQuery sub-lane (Q2C) can't wire the federation connection without the private IP you'll capture at the end. Without you, the Office of the Pothole Poet Laureate has nothing to be a Laureate *about*.

</Objective>

> Lane B · 1 of 3. ~12 minutes wall-clock (~2 min hands-on).

<QuickPath>

Run each command in turn. `gcloud` prints progress and blocks until the operation finishes, no polling loop needed.

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

Print the private IP. you'll paste it into Q2A-2 and Q2A-3:

```bash
gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive \
  --region=europe-west1 \
  --format='value(ipAddress)'
```

Expected output: `10.x.x.x`

</QuickPath>

AlloyDB has two layers: a **cluster** (the management shell: storage, backup policy, network, user accounts) and a **primary instance** (the actual database server you connect to with `psql`). The Console creates both on a **single page** with two sections, one above the other. While you wait for it to come up, read the schema and pair with the BigQuery Lead.

---

<Callout type="critical" title="Use these exact names — later steps depend on them">

The names `pothole-archive` (cluster) and `pothole-archive-primary` (instance) are referenced by scripts and commands across Q2A, Q2C, and Q6. **We strongly recommend using the defaults.** If you choose different names, click any highlighted name in the code blocks on this page (look for the gold underline); your change propagates to every command across the entire Quest automatically.

</Callout>

### Step 1 — Open the AlloyDB Console and click CREATE CLUSTER

Open the AlloyDB console: `https://console.cloud.google.com/alloydb/clusters?project=<your-project-id>` (in your laptop's browser, the Workstation has no browser).

Click **CREATE CLUSTER**.

<Callout type="critical" title="You may see a trial prompt or a cluster-type picker">

If a banner about an AlloyDB trial appears, scroll past it. If you see cluster-type options (e.g. "Basic", "Standard", "Enterprise"), pick **Basic** (single zone). For a 3.5-hour hackathon you do not need high availability or Enterprise features.

</Callout>

### Step 2 — Fill in the single-page form

The wizard is one page split into two sections. Work through them top to bottom.

**Section 1 — "Configure your cluster"** (top half of the page)

| Field | What to enter |
|---|---|
| **Cluster ID** | `pothole-archive` |
| **Password** | `buildwithgemini2026` |
| **Create an IAM database user** | Leave checked (default); harmless |
| **Database version** | `PostgreSQL 17` (the default; 16 also works if you prefer it) |
| **Region** | `europe-west1` |

Now scroll down to the **Connectivity** section (still inside "Configure your cluster"). You need to pick a network:

| Field | What to enter |
|---|---|
| **Private IP** | Leave enabled (always on) |
| **Connection method** | **Private Services Access (PSA)** (should already be selected) |
| **Network** | `garage-vpc` (open the dropdown; do **not** leave it on `default`, which does not exist in your project) |
| **Allocated IP range** | `Automatic` (default) |
| **Public IP** | Leave unchecked |

If the Console shows a note about "network requires a private services access connection", that is fine; the platform pre-configured PSA on `garage-vpc`.

**Section 2 — "Configure your primary instance"** (bottom half of the same page)

| Field | What to enter |
|---|---|
| **Instance ID** | `pothole-archive-primary` |
| **Zonal availability** | **Single zone** (the first radio button; do not pick "Multiple zones") |
| **Machine Series** | `N2` (default) |
| **Machine Type** | `2 vCPU, 16 GB` (the **smallest** option in the dropdown; it defaults to 8 vCPU, so you must change it) |

Leave everything else at its default (SSL encryption, no flags).

Click **CREATE CLUSTER** at the bottom.

✅ **Expect:** Cluster status shows ⏳ **CREATING**. Takes ~10 minutes.

### Step 3 — While you wait (~10 min): be useful

a) **Read the schema.** Open `pothole-poet/alloydb/schema.sql` in your Workstation IDE. Notice `swallowed_object` and `reporter_quote`. those are the columns that later make Gemini's poems funny.

b) **Read the seed quotes.** Open `pothole-poet/seed/citizen_quotes.txt`. These 120 lines are what we feed Gemini.

c) **Hand off cluster details to your BigQuery sub-lane (yourself, in Q2C).** Note these for federation setup in Q2C-2:

> *Cluster `pothole-archive`, primary instance `pothole-archive-primary`, region `europe-west1`. Password is the standard one.*

### Step 4 — Grab the private IP

Once the Console shows ✅ **READY**, pull the primary's private IP from your Workstation terminal; you'll paste it into Q2A-2 and Q2A-3:

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
- <strong>Machine type defaults to 8 vCPU/64 GB.</strong> You must change it. Open the Machine Type dropdown and select <strong>2 vCPU, 16 GB</strong> (the smallest N2 option). Leaving it on 8 vCPU works but wastes budget.
- <strong>Forgot the password.</strong> The Console doesn&rsquo;t reveal it after create. Reset with <code>gcloud alloydb users set-password postgres --cluster=pothole-archive --region=europe-west1 --password=...</code>.
- <strong>"Network is not configured for service networking" error.</strong> The platform&rsquo;s service-networking peering didn&rsquo;t run. Flag a Sherpa, this is pre-provisioned plumbing.
</Gotchas>

<Shipped>
The cluster is up. <strong>AlloyDB cluster <code>pothole-archive</code> is READY in <code>europe-west1</code> with a primary instance on a private IP.</strong> Empty so far, the next page installs the schema.
</Shipped>

🛢 **Q2A-1 done.** Cluster live, no tables yet.

➡️ Next: **Q2A-2 — Run the Schema in Studio** (sidebar on the left).
