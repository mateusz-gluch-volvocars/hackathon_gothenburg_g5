# ☸ Quest 2D-3 — Bind Pod Identity to BigQuery

<Screenshot src="/quest/pothole-poet/img/wif_identity_map.png" caption="Workload Identity Federation: Keyless connection between Volvo GKE Pods and BigQuery via Google Cloud IAM" />

<Objective lane="infra">

**🎯 What you'll do.** Give your Streamlit app permission to read BigQuery, without passwords or key files. You'll create an identity for your app and then grant that identity two specific BigQuery roles. ~5 minutes hands-on.

**🤝 Why it matters.** Right now your app has no way to reach the poems in BigQuery. After this page, it does, using the modern keyless approach Google Cloud recommends. This is the bridge between "container deployed" and "app shows live data."

</Objective>

> Lane D · 3 of 5. ~5 minutes hands-on.

## The problem: your app can't reach BigQuery yet

Your Streamlit app runs inside a container (a **Pod**) on GKE. That Pod needs to query BigQuery to fetch the neighbourhood odes. But right now it can't. On GKE Autopilot, **every Pod starts with zero Google Cloud permissions**. It can't read BigQuery, it can't write to Cloud Storage, it can't do anything outside its own container. This is by design: no app gets access unless you explicitly grant it.

So the question is: **how does your app prove to BigQuery that it's allowed to read data?**

## Two ways to solve it (and why you're using the better one)

**The old way: key files.** You create a service-account JSON key (essentially a password file), store it as a Kubernetes Secret, and mount it inside the container. The app reads the file and presents it to BigQuery. This works, but the key is a static credential that never expires. If someone accidentally commits it to git, copies it to a laptop, or logs it in an error message, anyone who finds it has permanent access to your BigQuery data. You also have to remember to rotate it. Most production security incidents involving GCP start with a leaked service-account key.

**The modern way: Workload Identity Federation (WIF).** Instead of giving your app a secret file, you give it an **identity**, a name that Google Cloud recognizes. Then you tell BigQuery: "when something with this identity asks to read data, allow it." There is no key file. The Pod proves who it is using a **short-lived token** (valid for minutes, not forever) that GKE's infrastructure creates and refreshes automatically. If the Pod is deleted, the token disappears with it. Nothing to leak, nothing to rotate.

**This is the approach you'll use on this page.** It's the same idea as how you log into Google Cloud with your Volvo corporate account. You don't carry a key file around; your identity is verified through a federation trust, and you get short-lived session credentials. WIF does the same thing for your app.

## What you're doing, concretely

Two things:

1. **Creating an identity for your app.** A Kubernetes ServiceAccount named `pothole-laureate` in a namespace called `laureate`. Think of it as your app's employee badge inside the cluster.

2. **Granting that identity two BigQuery permissions.** You'll bind two IAM roles to the identity using a **principal URI** (a long address string that tells Google Cloud exactly which Kubernetes identity you mean):
   - **`roles/bigquery.dataViewer`** lets the Pod see tables and read rows
   - **`roles/bigquery.jobUser`** lets the Pod run queries

After this, when your Pod starts and tries to call BigQuery, here's what happens behind the scenes:

```
Pod starts → GKE gives it a short-lived token proving "I am pothole-laureate"
    → Pod presents token to BigQuery
        → BigQuery checks IAM: "does pothole-laureate have dataViewer + jobUser?"
            → Yes → query runs, poems returned
```

No key file in the picture. The token refreshes automatically. If you delete the Pod, the credentials vanish with it.

<Concept title="If you've used Azure AD or corporate SSO, it's the same idea">

In a corporate environment, you don't log into every internal tool with a separate password. Your identity is managed centrally (Azure AD, Okta, etc.), and each tool checks with the identity provider: "is this person allowed in?" Your access is scoped to specific roles, and your session token expires.

WIF works identically, but for apps instead of people. The Kubernetes cluster is the identity provider. Google Cloud IAM is the access-control layer. The principal URI is the "username" that connects the two worlds. The only difference is that you have to construct that username (the URI) yourself, and get it exactly right.

</Concept>

<Concept title="🤖 Or drive this with Antigravity CLI">

The principal URI is the easy part to get wrong. Antigravity CLI's **`wif-binding-helper`** skill reads both project identifiers fresh from `gcloud`, builds the URI for you, and proposes both binding commands for your approval. Make sure you're in the Quest repo so the workspace plugin loads:

```bash
cd ~/quest
agy
```

then ask:

> *"Bind the pothole-laureate Kubernetes ServiceAccount to the BigQuery dataViewer and jobUser roles via direct Workload Identity."*

Either path (manual or agentic) lands the same bindings. The agentic path just removes the chance of a typo.

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

## The one trap on this page

The identity binding uses a long string called a **principal URI**. It contains two project identifiers that look similar but are different things:

- **`PROJECT_NUMBER`** is all digits (e.g. `624958632298`). Goes after `projects/`.
- **`PROJECT_ID`** is human-readable (e.g. `vcc-ic-g01`). Goes before `.svc.id.goog`.

**Swap them and the binding silently succeeds but nothing works.** The command won't show an error, but when your app tries to query BigQuery it gets `AccessDenied`. This is the single most common mistake of the day. The steps below make sure you get it right.

---

### Step 1 — Confirm your project identifiers

You set these in Q2D-1 Step 1. Confirm they're still in your shell:

```bash
echo "PROJECT_NUMBER=$PROJECT_NUMBER  PROJECT_ID=$PROJECT_ID"
```

✅ **Expect:**
- `PROJECT_NUMBER` is **all digits**, a 12-digit number like `624958632298`
- `PROJECT_ID` is **human-readable**, lowercase + digits + hyphens, matches your workbench card

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

Every Kubernetes workload runs inside a **namespace** (a logical boundary) and *as* a **ServiceAccount** (an identity). You're creating both now: the namespace `laureate` and the ServiceAccount `pothole-laureate` inside it.

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

The file you just applied is minimal. It only defines the two resources:

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

The namespace groups all your Quest resources. The ServiceAccount is the identity your Pod will run as, and the identity you're about to grant BigQuery access to. In Q2D-4, the Deployment manifest references `serviceAccountName: pothole-laureate` to ensure every Pod runs with this identity.

</Concept>

### Step 4 — Build the principal URI and bind both roles

This is the critical step. You're constructing a **principal URI**, a long string that uniquely identifies your Kubernetes ServiceAccount to Google Cloud IAM, and then binding two BigQuery roles to it.

First, understand the URI structure:

```
principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/laureate/sa/pothole-laureate
                                        ^^^^^^^^^^^^^^                                       ^^^^^^^^^^
                                        all digits here                                      human-readable here
```

- `projects/<PROJECT_NUMBER>` is where IAM resolves projects by number internally (numbers are immutable).
- `<PROJECT_ID>.svc.id.goog` is the workload identity pool, always named after the project ID.
- `subject/ns/laureate/sa/pothole-laureate` means "the ServiceAccount named `pothole-laureate` in namespace `laureate`."

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

> You need **both** roles: `dataViewer` lets the Pod see tables and read rows, `jobUser` lets it run queries. Either one alone fails with a different error. Missing `dataViewer` returns "table not found", missing `jobUser` returns "access denied on query execution".

<Concept title="Why --condition=None?">

Without this flag, `gcloud` drops into an interactive prompt asking you to type an IAM condition expression. In a scripted workflow (or a hackathon where you're copying commands), this looks like the command is hung. `--condition=None` means "unconditional binding, this identity always has this role."

</Concept>

<Concept title="How does Workload Identity Federation actually work?">

Every Pod runs *as* a Kubernetes ServiceAccount. Autopilot automatically mounts a **projected token** into every Pod, a short-lived JWT that proves "I am `pothole-laureate` in namespace `laureate`."

When your Pod's Google client library asks for credentials, the **GKE metadata server** (a Google-managed component on every node) intercepts the call. It exchanges the Kubernetes projected token for a short-lived Google access token via the Security Token Service, and hands it back to the Pod. The token auto-refreshes; the Pod never sees a static key; Cloud Audit Logs show the federated principal.

This is why no annotation or intermediate Google Service Account is needed. The direct principal URI approach is Google's current recommendation (as of May 2026). The older approach (creating a Google SA, annotating the KSA, binding `workloadIdentityUser`) still works but adds unnecessary moving parts.

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

If you see both lines, the identity is wired. If you see nothing, the principal URI was wrong. Go back to Step 4 and check `PROJECT_NUMBER` vs `PROJECT_ID`.

<Gotchas>
- <strong>Cryptic <code>permission denied</code> when the Pod queries BigQuery later.</strong> 9 times out of 10, you mixed up <code>PROJECT_NUMBER</code> and <code>PROJECT_ID</code> in the principal URI. Re-run Step 1; <code>PROJECT_NUMBER</code> must be all digits. If in doubt, re-run Step 4 from scratch; re-binding with the same principal and role is idempotent (safe to repeat).
- <strong>gcloud hangs after typing the bind command.</strong> You forgot <code>--condition=None</code>. gcloud is waiting for you to type a condition expression interactively. Ctrl-C, re-run with the flag.
- <strong>IAM binding takes 2-7 minutes to propagate.</strong> Per Google's WIF docs: &ldquo;New bindings take two to seven minutes to apply.&rdquo; If your first Pod startup in Q2D-4 hits permission errors, wait 5 minutes and try again. The GKE metadata server also takes a few seconds on fresh Pod starts; client libraries retry transparently.
- <strong><code>kubectl: command not found</code>.</strong> Run <code>gcloud components install kubectl</code> once. Pre-installed on Workstations.
- <strong>Bindings show in <code>get-iam-policy</code> but the Pod still can&rsquo;t read.</strong> Check the namespace (<code>laureate</code>) and KSA name (<code>pothole-laureate</code>) match the Deployment manifest in Q2D-4 exactly. A typo on either side breaks the principal match silently.
- <strong>Two empty lines from the verify command instead of two roles.</strong> The <code>--filter</code> uses a substring match on <code>pothole-laureate</code>. If the principal URI used a different KSA name (typo), the filter finds nothing. Re-echo <code>$PRINCIPAL</code> and check the <code>sa/</code> segment.
</Gotchas>

<Shipped>
Identity is wired. <strong>The Kubernetes ServiceAccount <code>laureate/pothole-laureate</code> can read and query BigQuery without any service-account key.</strong> No secrets to leak. No annotations to drift. No intermediate Google Service Account to maintain.
</Shipped>

☸ **Q2D-3 done.** Identity bound.

➡️ Next: **Q2D-4 — Deploy the Workload** (sidebar on the left).
