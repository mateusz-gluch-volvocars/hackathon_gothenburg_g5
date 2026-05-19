---
name: wif-binding-helper
description: Constructs the direct Workload Identity Federation principal URI and binds BigQuery roles to the pothole-laureate Kubernetes ServiceAccount for Q2D-3 of the Iron & Cloud Pothole Poet quest. Handles the PROJECT_ID vs PROJECT_NUMBER convention that is the single most expensive mistake of the day. Use when the GKE / App Lead asks to bind Workload Identity, grant the Pod BigQuery dataViewer or jobUser, configure direct WIF, or debug Pod 403s against BigQuery.
---

# WIF binding helper (Q2D-3)

**Codelab counterpart:** Q2D-3 — `~/quest/pothole-poet/codelab/quest-2d-identity.md`.

This is **the most expensive mistake of the hackathon day** if the participant confuses `PROJECT_ID` with `PROJECT_NUMBER` in the principal URI. This skill makes it bulletproof.

## The principal URI shape — memorise this

```
principal://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<PROJECT_ID>.svc.id.goog/subject/ns/laureate/sa/pothole-laureate
```

| Segment | Value | Format |
|---|---|---|
| `projects/<PROJECT_NUMBER>` | digits | e.g. `624958632298` |
| `<PROJECT_ID>.svc.id.goog` | human-readable | e.g. `<your-garage-project-id>.svc.id.goog` |
| `ns/<namespace>` | K8s namespace | `laureate` |
| `sa/<sa-name>` | K8s ServiceAccount | `pothole-laureate` |

**The first segment uses PROJECT_NUMBER. The second uses PROJECT_ID.** They are different identifiers for the same project. Mixing them gives a binding that "looks right" but never authorizes the Pod, and the failure surfaces only at Q4 render time when the Streamlit page 403s on its BigQuery read.

## Bindings to apply

The `pothole-laureate` K8s ServiceAccount needs two project-level BigQuery roles:
- `roles/bigquery.dataViewer` — to read `pothole_laureate.*` tables.
- `roles/bigquery.jobUser` — to run query jobs.

## Steps

### 1. Capture both identifiers (read fresh, never hard-code)
```bash
PROJECT_ID="$(gcloud config get-value project)"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"
echo "PROJECT_ID:     $PROJECT_ID"
echo "PROJECT_NUMBER: $PROJECT_NUMBER"
echo "PRINCIPAL:      $PRINCIPAL"
```
**Surface all three to the participant** and ask them to glance at the principal URI to confirm the digits in the first segment match the human-readable ID in the second.

### 2. Confirm the GKE cluster + Workload Identity Pool exist
The pool `<PROJECT_ID>.svc.id.goog` is created by GKE on first Autopilot cluster create. If Q2D-1 isn't done yet, the bindings below will fail with `Identity Pool does not exist`.

```bash
gcloud container clusters list --region=europe-west1 --filter='name=laureate-cluster' --format='value(name,status)'
```
Expect a row showing `laureate-cluster  RUNNING`. If empty, route the participant back to Q2D-1.

### 3. Propose both bindings (HITL approval required)
```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="$PRINCIPAL" --role=roles/bigquery.dataViewer

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="$PRINCIPAL" --role=roles/bigquery.jobUser
```
Run them as two separate proposals so the participant explicitly approves each role grant.

### 4. Verify both bindings landed
```bash
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten='bindings[].members' \
  --filter="bindings.members:$PRINCIPAL" \
  --format='table(bindings.role)'
```
Expect two rows: `roles/bigquery.dataViewer` and `roles/bigquery.jobUser`.

### 5. End-to-end probe from a Pod (optional but reassuring)
If the participant has already deployed the Streamlit Pod, you can confirm the binding actually works from inside the cluster:

```bash
kubectl run bq-probe -n laureate \
  --image=google/cloud-sdk:slim --restart=Never --rm -it \
  --overrides='{"spec":{"serviceAccountName":"pothole-laureate"}}' \
  -- bq query --use_legacy_sql=false "SELECT 1 AS ok"
```
If this returns `ok = 1`, the binding is fully wired.

## Common failure modes

- **`Identity Pool does not exist`** — GKE cluster wasn't created yet. Pool creation is lazy on first cluster create. Run Q2D-1 first.
- **`Principal not found` or binding accepted but Pod still 403s** — typo in namespace (`laureate`) or SA name (`pothole-laureate`). Re-read the principal URI character by character.
- **Pod still 403s after a valid binding** — IAM propagation lag. Wait 30–60 seconds and retry. If it persists past 2 minutes, re-check the principal URI digits vs. the project ID once more.
- **Wrong PROJECT_NUMBER used (most common)** — the most common form is using the human-readable ID in both segments. Re-run step 1 to refresh both values from `gcloud`.

## Don't

- Don't propose `gcloud iam service-accounts add-iam-policy-binding` against a Google Service Account — that's the legacy WIF-via-GSA pattern. This Quest uses **direct WIF** (no GSA in the middle).
- Don't pre-bind these in Terraform. The pool doesn't exist until the GKE cluster is created, so Terraform-time binding fails with `Identity Pool does not exist`. Procedural binding in Q2D-3 is the deliberate design.
- Don't grant `roles/bigquery.admin`. Least privilege: `dataViewer` + `jobUser` is exactly what the Pod needs.
