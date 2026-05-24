# ☸ Quest 2D-3 — Bind Pod Identity to BigQuery

<Objective lane="infra">

**🎯 What you'll do.** Create a Kubernetes namespace + ServiceAccount, then tell Google Cloud "this Kubernetes identity is allowed to read BigQuery" by binding two IAM roles to it. No key files, no secrets — just an identity mapping. ~5 minutes if you get the principal URI exactly right; possibly 30 if you confuse `PROJECT_NUMBER` with `PROJECT_ID`.

**🤝 Why it matters.** This is **how your Pod authenticates to BigQuery without ever touching a key file**. The principal URI is the single most error-prone string in the entire Quest. Get it wrong and Silver-tier Streamlit returns `AccessDenied` the moment you flip `TIER` in Q3 — and you waste the convergence moment debugging IAM instead of demoing poems.

</Objective>

> Lane D · 3 of 5. ~5 minutes hands-on.

<Concept title="Why can't the Pod just access BigQuery automatically?">

On GKE Autopilot, every Pod is **locked out of Google Cloud APIs by default**. Unlike a VM where the Compute Engine service account might have broad access, Autopilot uses **Workload Identity Federation** — which is always enabled and cannot be turned off. This means:

- Your Pod gets a Kubernetes identity (a ServiceAccount), but that identity starts with **zero Google Cloud permissions**.
- The Pod cannot fall back to the node's credentials — Autopilot blocks that path entirely.
- You must explicitly tell Google Cloud: *"this specific Kubernetes identity is allowed to do these specific things."*

That's what this page does. You're creating a permission mapping between a Kubernetes identity and Google Cloud IAM roles. Think of it like a badge system: you're issuing a badge (`pothole-laureate`) and then programming the door locks (BigQuery) to accept that badge.

</Concept>

<Concept title="🤖 Or drive this with Antigravity CLI (strongly recommended for this step)">

This is the **single most expensive mistake of the hackathon day** if you confuse `PROJECT_ID` with `PROJECT_NUMBER` in the principal URI. Antigravity CLI's **`wif-binding-helper`** skill reads both identifiers fresh from `gcloud`, constructs the URI in the right shape, and proposes both `add-iam-policy-binding` commands for your approval. Launch it from any terminal:

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

This page has **one big idea** and **one dangerous string**.

The big idea: your Pod needs to read BigQuery, but you should never mount a service-account JSON key as a Kubernetes Secret. Instead, you use **Workload Identity Federation** — Google's recommended way to let GKE pods call Google Cloud APIs. You bind IAM roles directly to the Kubernetes ServiceAccount the Pod runs as.

The dangerous string: the **principal URI**. It contains both your `PROJECT_NUMBER` (all digits) and `PROJECT_ID` (human-readable) in different positions. Swap them and the binding silently succeeds but every Pod request fails.

---

### Step 1 — Confirm your project identifiers

The principal URI needs both `PROJECT_NUMBER` and `PROJECT_ID`. They are **two different identifiers for the same project** and they go in **different positions** in the URI. You set them in Q2D-1 Step 1 — confirm they're still in your shell:

```bash
echo "PROJECT_NUMBER=$PROJECT_NUMBER  PROJECT_ID=$PROJECT_ID"
```

✅ **Expect:**
- `PROJECT_NUMBER` is **all digits** — a 12-digit number like `624958632298`
- `PROJECT_ID` is **human-readable** — lowercase + digits + hyphens, matches your workbench card

If either is empty, re-set them:

```bash
export PROJECT_ID="$(gcloud config get-value project)"
export PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
export REGION="europe-west1"
```

### Step 2 — Point kubectl at the cluster

```bash
gcloud container clusters get-credentials laureate-cluster \
  --region=$REGION --project=$PROJECT_ID
```

✅ **Expect:** `kubeconfig entry generated for laureate-cluster.`

### Step 3 — Create the namespace and ServiceAccount

Every Kubernetes workload runs inside a **namespace** (a logical boundary) and *as* a **ServiceAccount** (an identity). You're creating both now — the namespace `laureate` and the ServiceAccount `pothole-laureate` inside it.

```bash
cd ~/quest/pothole-poet/streamlit
kubectl apply -f k8s/namespace-and-sa.yaml
```

✅ **Expect:**
```
namespace/laureate created
serviceaccount/pothole-laureate created
```

<Concept title="What's inside the manifest?">

The file you just applied is minimal — it only defines the two resources:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: laureate
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pothole-laureate
  namespace: laureate
```

The namespace groups all your Quest resources. The ServiceAccount is the identity your Pod will run as — and the identity you're about to grant BigQuery access to. In Q2D-4, the Deployment manifest references `serviceAccountName: pothole-laureate` to ensure every Pod runs with this identity.

</Concept>

### Step 4 — Build the principal URI and bind both roles

This is the critical step. You're constructing a **principal URI** — a long string that uniquely identifies your Kubernetes ServiceAccount to Google Cloud IAM — and then binding two BigQuery roles to it.

First, understand the URI structure:

```
principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/laureate/sa/pothole-laureate
                                        ^^^^^^^^^^^^^^                                       ^^^^^^^^^^
                                        all digits here                                      human-readable here
```

- `projects/<PROJECT_NUMBER>` — IAM resolves projects by number internally (numbers are immutable).
- `<PROJECT_ID>.svc.id.goog` — the workload identity pool, always named after the project ID.
- `subject/ns/laureate/sa/pothole-laureate` — "the ServiceAccount named `pothole-laureate` in namespace `laureate`."

Now build it and bind:

```bash
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

echo "Binding: $PRINCIPAL"
```

**Read the output.** Confirm `projects/` is followed by digits and `.svc.id.goog` is preceded by the human-readable ID. Then bind both roles:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/bigquery.dataViewer" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/bigquery.jobUser" \
  --condition=None
```

✅ **Expect** (twice): `Updated IAM policy for project [...]`

> You need **both** roles: `dataViewer` lets the Pod see tables and read rows, `jobUser` lets it run queries. Either one alone fails with a different error — missing `dataViewer` returns "table not found", missing `jobUser` returns "access denied on query execution".

<Concept title="Why --condition=None?">

Without this flag, `gcloud` drops into an interactive prompt asking you to type an IAM condition expression. In a scripted workflow (or a hackathon where you're copying commands), this looks like the command is hung. `--condition=None` means "unconditional binding — this identity always has this role."

</Concept>

<Concept title="How does Workload Identity Federation actually work?">

Every Pod runs *as* a Kubernetes ServiceAccount. Autopilot automatically mounts a **projected token** into every Pod — a short-lived JWT that proves "I am `pothole-laureate` in namespace `laureate`."

When your Pod's Google client library asks for credentials, the **GKE metadata server** (a Google-managed component on every node) intercepts the call. It exchanges the Kubernetes projected token for a short-lived Google access token via the Security Token Service, and hands it back to the Pod. The token auto-refreshes; the Pod never sees a static key; Cloud Audit Logs show the federated principal.

This is why no annotation or intermediate Google Service Account is needed — the direct principal URI approach is Google's current recommendation (as of May 2026). The older approach (creating a Google SA, annotating the KSA, binding `workloadIdentityUser`) still works but adds unnecessary moving parts.

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

If you see both lines, the identity is wired. If you see nothing, the principal URI was wrong — go back to Step 4 and check `PROJECT_NUMBER` vs `PROJECT_ID`.

<Gotchas>
- <strong>Cryptic <code>permission denied</code> when the Pod queries BigQuery later.</strong> 9 times out of 10, you mixed up <code>PROJECT_NUMBER</code> and <code>PROJECT_ID</code> in the principal URI. Re-run Step 1; <code>PROJECT_NUMBER</code> must be all digits. If in doubt, re-run Step 4 from scratch &mdash; re-binding with the same principal and role is idempotent (safe to repeat).
- <strong>gcloud hangs after typing the bind command.</strong> You forgot <code>--condition=None</code>. gcloud is waiting for you to type a condition expression interactively. Ctrl-C, re-run with the flag.
- <strong>IAM binding takes 2-7 minutes to propagate.</strong> Per Google's WIF docs: &ldquo;New bindings take two to seven minutes to apply.&rdquo; If your first Pod startup in Q2D-4 hits permission errors, wait 5 minutes and try again. The GKE metadata server also takes a few seconds on fresh Pod starts &mdash; client libraries retry transparently.
- <strong><code>kubectl: command not found</code>.</strong> Run <code>gcloud components install kubectl</code> once. Pre-installed on Workstations.
- <strong>Bindings show in <code>get-iam-policy</code> but the Pod still can&rsquo;t read.</strong> Check the namespace (<code>laureate</code>) and KSA name (<code>pothole-laureate</code>) match the Deployment manifest in Q2D-4 exactly. A typo on either side breaks the principal match silently.
- <strong>Two empty lines from the verify command instead of two roles.</strong> The <code>--filter</code> uses a substring match on <code>pothole-laureate</code>. If the principal URI used a different KSA name (typo), the filter finds nothing. Re-echo <code>$PRINCIPAL</code> and check the <code>sa/</code> segment.
</Gotchas>

<Shipped>
Identity is wired. <strong>The Kubernetes ServiceAccount <code>laureate/pothole-laureate</code> can read and query BigQuery without any service-account key.</strong> No secrets to leak. No annotations to drift. No intermediate Google Service Account to maintain.
</Shipped>

☸ **Q2D-3 done.** Identity bound.

➡️ Next: **Q2D-4 — Deploy the Workload** (sidebar on the left).
