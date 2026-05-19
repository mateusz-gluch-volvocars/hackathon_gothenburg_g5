# ☸ Quest 2D-3 — Bind Pod Identity to BigQuery

<Objective lane="infra">

**🎯 What you'll do.** Create a Kubernetes namespace + ServiceAccount, then bind that KSA **directly** to two BigQuery IAM roles using a Workload Identity Federation principal URI. No Google Service Account in the middle, no annotation. ~5 minutes if you get the principal URI exactly right; possibly 30 if you confuse `PROJECT_NUMBER` with `PROJECT_ID`.

**🤝 Why it matters.** This is **how your Pod authenticates to BigQuery without ever touching a key file**. The principal URI is the single most error-prone string in the entire Quest. Get it wrong and Silver-tier Streamlit returns `AccessDenied` the moment you flip `TIER` in Q3 — and you waste the convergence moment debugging IAM instead of demoing poems.

</Objective>

> Lane D · 3 of 5. ~5 minutes hands-on.

<Concept title="🤖 Or drive this with Antigravity CLI (strongly recommended for this step)">

This is the **single most expensive mistake of the hackathon day** if you confuse `PROJECT_ID` (human-readable, the value printed on your workbench card) with `PROJECT_NUMBER` (a 12-digit number, looks like `624958632298`) in the principal URI. Antigravity CLI's **`wif-binding-helper`** skill reads both identifiers fresh from `gcloud`, constructs the principal URI in the right shape, and proposes both `add-iam-policy-binding` commands for your approval — so the only way to get it wrong is to skip reading the surfaced values before pressing `y`. Launch it from any terminal:

```bash
agy
```

then ask:

> *"Bind the pothole-laureate Kubernetes ServiceAccount to the BigQuery dataViewer and jobUser roles via direct Workload Identity."*

The QuickPath below is what the skill runs under the hood. Either path lands the same bindings; the agentic path just makes the principal URI bulletproof.

</Concept>

<QuickPath>

```bash
# 0. Sanity check: PROJECT_NUMBER must be all digits (set in Q2D-1 Step 1)
echo "PROJECT_NUMBER=$PROJECT_NUMBER  PROJECT_ID=$PROJECT_ID"

# 1. Point kubectl at the cluster
gcloud container clusters get-credentials laureate-cluster \
  --region=$REGION --project=$PROJECT_ID

# 2. Create the namespace + KSA
cd ~/quest/pothole-poet/streamlit
kubectl apply -f k8s/namespace-and-sa.yaml
# ✅ Expect: namespace/laureate created  +  serviceaccount/pothole-laureate created

# 3. Build the principal URI ONCE, bind both roles
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" --role="roles/bigquery.dataViewer" --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" --role="roles/bigquery.jobUser" --condition=None

# 4. Verify both bindings stuck
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:principal*pothole-laureate" \
  --format="table(bindings.role)"
# ✅ Expect: bigquery.dataViewer + bigquery.jobUser
```

</QuickPath>

In Silver and Gold tiers your Streamlit app reads from `pothole_laureate.neighbourhood_odes` in BigQuery. The Pod needs a Google identity with BigQuery permissions, but you should **never** mount a service-account JSON key as a Secret. The current best practice is **Workload Identity Federation for GKE**: bind IAM roles directly to the Kubernetes ServiceAccount the Pod runs as.

---

### Step 1 — Sanity-check `PROJECT_NUMBER` and `PROJECT_ID`

The principal URI uses both. They are **different identifiers for the same project** and they go in **different positions** in the URI. Confirm they're set correctly:

```bash
echo "PROJECT_NUMBER=$PROJECT_NUMBER  PROJECT_ID=$PROJECT_ID"
```

✅ **Expect:**
- `PROJECT_NUMBER` is **all digits** — a 12-digit number, looks like `624958632298`
- `PROJECT_ID` is **human-readable** — lowercase + digits + hyphens, matches what's printed on your workbench card

If either is empty or wrong, re-run Q2D-1 Step 1.

<Concept title="Why PROJECT_NUMBER and PROJECT_ID are different in the URI">

The principal URI is:

```
principal://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<PROJECT_ID>.svc.id.goog/subject/ns/<NS>/sa/<KSA>
```

- `projects/<PROJECT_NUMBER>` — IAM resolves projects by number internally (numbers are immutable, project IDs aren't).
- `<PROJECT_ID>.svc.id.goog` — the **workload identity pool name**, which is hard-coded to `<PROJECT_ID>.svc.id.goog`.

If you swap them — `projects/<PROJECT_ID>` and `<PROJECT_NUMBER>.svc.id.goog` — the URI is syntactically valid but matches no principal. Your binding succeeds (because IAM doesn't validate principals exist), but every Pod request fails with `permission denied`.

This is the most expensive mistake in the day. Capture both values explicitly, never mix them up.

</Concept>

### Step 2 — Point kubectl at the cluster

```bash
gcloud container clusters get-credentials laureate-cluster \
  --region=$REGION --project=$PROJECT_ID
```

✅ **Expect:** `kubeconfig entry generated for laureate-cluster.`

From now on, `kubectl` commands target `laureate-cluster`.

### Step 3 — Create the namespace and ServiceAccount

```bash
cd ~/quest/pothole-poet/streamlit
kubectl apply -f k8s/namespace-and-sa.yaml
```

✅ **Expect:**
- `namespace/laureate created`
- `serviceaccount/pothole-laureate created`

### Step 4 — Bind IAM directly to the KSA

Build the principal URI once, then bind both roles. The `--condition=None` flag is required — without it, gcloud prompts interactively for an IAM condition and your script hangs.

```bash
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/bigquery.dataViewer" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/bigquery.jobUser" \
  --condition=None
```

✅ **Expect** (twice): `Updated IAM policy for project [...]` followed by the policy bindings showing your `principal://...` member.

> You need **both** roles: `dataViewer` lets the Pod see tables, `jobUser` lets it run queries against them. Either one alone fails.

<Concept title="How does Workload Identity Federation actually work?">

Every Pod runs *as* a Kubernetes ServiceAccount (KSA). Each KSA in the cluster is automatically issued a **projected token** mounted into every Pod that uses it. When your Pod's Google client library asks for credentials, the GKE metadata server intercepts the call, exchanges that projected token for a short-lived Google access token via the Security Token Service, and hands it back. The token auto-refreshes; the Pod never sees a static key; the audit trail in Cloud Audit Logs shows the federated principal.

</Concept>

### Step 5 — Verify both bindings

```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:principal*pothole-laureate" \
  --format="table(bindings.role)"
```

✅ **Expect:**

```
ROLE
roles/bigquery.dataViewer
roles/bigquery.jobUser
```

<Gotchas>
- <strong>Cryptic <code>permission denied</code> when the Pod queries BigQuery later.</strong> 9 times out of 10, you mixed up <code>PROJECT_NUMBER</code> and <code>PROJECT_ID</code> in the principal URI. Re-run Step 1 sanity check; PROJECT_NUMBER must be all digits.
- <strong>gcloud hangs after typing the bind command.</strong> You forgot <code>--condition=None</code>. gcloud is waiting for you to type a condition expression interactively. Ctrl-C, re-run with the flag.
- <strong>IAM binding takes 2-7 minutes to propagate.</strong> Per Google's own WIF docs (updated May 2026): "New bindings take two to seven minutes to apply." If your first Pod startup hits permission errors, wait and re-trigger. The GKE metadata server also takes a few seconds on fresh Pod starts &mdash; client libs retry transparently.
- <strong><code>kubectl: command not found</code>.</strong> Run <code>gcloud components install kubectl</code> once. Pre-installed on Workstations.
- <strong>Bindings show in <code>get-iam-policy</code> but the Pod still can&rsquo;t read.</strong> Check the namespace (<code>laureate</code>) and KSA name (<code>pothole-laureate</code>) match the Deployment exactly. A typo on either side breaks the principal match.
</Gotchas>

<Shipped>
Identity is wired. <strong>The Kubernetes ServiceAccount <code>laureate/pothole-laureate</code> can read and query BigQuery without any service-account key.</strong> No secrets to leak. No annotations to drift.
</Shipped>

☸ **Q2D-3 done.** Identity bound.

➡️ Next: **Q2D-4 — Deploy the Workload** (sidebar on the left).
