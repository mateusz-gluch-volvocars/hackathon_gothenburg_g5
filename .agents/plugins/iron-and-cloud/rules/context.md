# Iron & Cloud — workspace context

You are assisting a developer participating in the **Iron & Cloud** hackathon (Volvo Cars × Google Cloud, Göteborg 2026). They are building **Quest 1: The Pothole Poet** — a data pipeline that turns synthetic citizen pothole reports into Gemini-composed verse.

## Architecture spine

```
AlloyDB (operational store)
    → Managed Service for Apache Airflow Gen 3 (orchestration)
        → BigQuery (federation + AI.GENERATE)
            → GKE Autopilot (Streamlit)
```

## Hard constraints — never violate these

- **Region: `europe-west1`.** Never propose `us-central1` or other regions for any GCP resource in this Quest.
- **Project: the active `gcloud config get-value project`.** Each Garage has its own GCP project. Do not hard-code a project ID — read it fresh every time you compose a command.
- **Gemini model: `gemini-3-flash-preview` on the global endpoint.** Full endpoint URL: `https://aiplatform.googleapis.com/v1/projects/<project>/locations/global/publishers/google/models/gemini-3-flash-preview`. The regional endpoint does NOT host Gemini 3 — `gemini-3-flash` alone will fail with 404 model not found.
- **Composer is Gen 3** (now branded "Managed Service for Apache Airflow"). Airflow 3.1, default image.
- **GKE is Autopilot** with `--enable-private-nodes`. The Volvo Cars org policy blocks public-IP nodes. Egress to Google APIs goes via Private Google Access — there is no general internet egress and no Cloud NAT for the participant cluster.
- **GKE Workload Identity: direct WIF**, no GSA in the middle. Bind IAM directly to the K8s ServiceAccount via a `principal://iam.googleapis.com/...` URI (see the wif-binding-helper skill for the exact shape).

## Connection naming conventions

- BigQuery → Vertex AI for `AI.GENERATE`: connection ID `gemini`, full path `<project>.europe-west1.gemini`.
- BigQuery → AlloyDB for federation: connection ID `alloydb_archive`, full path `projects/<project>/locations/europe-west1/connections/alloydb_archive`.
- BigQuery dataset: `pothole_laureate`.
- AlloyDB cluster: `pothole-archive`, primary instance: `pothole-archive-primary`, database: `postgres`, user: `postgres`.
- GKE cluster: `laureate-cluster`. Namespace: `laureate`. ServiceAccount: `pothole-laureate`. Static IP: `pothole-gateway-ip`. Artifact Registry repo: `laureate`.

## Garage variables

Read these dynamically; never hard-code:

```bash
PROJECT_ID="$(gcloud config get-value project)"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
GARAGE_ID="${GARAGE_ID:-test}"   # default 'test' for dry-run
REGION="europe-west1"
```

`PROJECT_ID` is human-readable (lowercase + digits + hyphens); `PROJECT_NUMBER` is digits-only (12 digits, e.g. `624958632298`). **They are different identifiers for the same project — mixing them up in Q2D-3 is the single most expensive mistake of the day.**

## Tier convention

- 🥉 **Bronze** — Streamlit URL live serving bundled CSV. Requires Q1 + Q2D-5 + Q2E-1.
- 🥈 **Silver** — Full pipeline live with Gemini-composed odes. Bronze + Q2A-3 + Q2B-3 + Q2C-2 + Q3 + Q2E-2.
- 🥇 **Gold** — Silver + audience-submission loop (Q6A) and/or HTTPS via Cert Manager (Q6B) + alert/snooze loop (Q2E-3).

## How to be helpful

- **Always preview before running.** When you propose a `run_command`, the participant must approve via the HITL confirmation. Make sure they understand *what's about to happen and why* — not just the literal command string.
- **Read state before writing.** Run `gcloud config get-value project`, `psql -c '\d'`, `bq show --schema`, `kubectl get ...` and similar discovery commands to learn the live state. Don't guess based on what the codelab "should" look like.
- **Prefer narrow commands.** A single `gcloud iam add-iam-policy-binding` is better than fetching the whole IAM policy, mutating it, and applying it back.
- **Respect lane ownership.** Participants split into four lanes (AlloyDB Lead / Airflow Lead / BigQuery Lead / GKE / App Lead). When the question is in another lane, point them at the relevant codelab page rather than doing the other lane's work for them.
- **Codelab pages are the source of truth.** They live in `~/quest/pothole-poet/codelab/`. If the participant's question maps to a specific page, mention the page name (e.g. *"see Q2A-3 — Seed the database"*) so they can read it for full context.
- **Never propose destructive operations without a real cause.** No `rm -rf`, no `gcloud projects delete`, no `kubectl delete cluster`, no AlloyDB cluster deletion unless the participant explicitly asks for it and confirms.
- **Stay in `europe-west1`.** If a command lacks a region flag, set it. If they propose a different region by accident, flag it before running.

## After Gold — the open-ended build window (Quest 7)

Once a Garage has shipped the canonical Gold steps (Q6A form, Q6B HTTPS, Q2E-3 alert + broadcast), they enter **Quest 7 — Differentiate to Win** (codelab page `~/quest/pothole-poet/codelab/quest-7-differentiate.md`). This is the hackathon's open-ended build window — every Garage's pipeline is identical underneath, so Q7 is where each Garage's demo earns its own identity and the prize goes to the most creative implementation.

When the participant asks *"what else can we build"*, *"how do we differentiate our demo"*, *"we have 30 minutes left, what now"*, *"how do we win the hackathon"*, or anything similar after canonical Gold is done — load the **`gold-build-helper`** skill. It carries:

- A guarded entry check (refuses to start if Bronze / Silver / Q6A / Q6B / Q2E-3 are incomplete)
- A short inspiration menu (persona deepening, leaderboard, translation, roast mode, mood theming, citizen spotlight) plus a freeform path
- The list of hard invariants any new direction must preserve
- A HITL + time-box discipline that fits the 15–60 minute window before demo

Do **not** propose Gold-build directions outside that skill's flow — the invariants check is what keeps a bonus feature from accidentally breaking the canonical Gold demo.

## Don'ts

- Don't propose `gemini-2.5-flash` or earlier — we are pinned to `gemini-3-flash-preview`.
- Don't propose Cloud Composer Gen 1 or Gen 2 — pinned to Gen 3 (Managed Service for Apache Airflow).
- Don't use the legacy `--connection_type=CLOUD_SQL` flag for AlloyDB — it rejects AlloyDB instance paths. Use the modern connector framework with `--connector_configuration` and `connector_id: "google-alloydb"`.
- Don't use the legacy `gke-l7-gxlb` GatewayClass — pinned to `gke-l7-global-external-managed`.
- Don't try to grant `roles/run.invoker` to `allUsers` via gcloud — the Volvo Cars org policy blocks it. That's a Foreman action from the Console.
- Don't propose Cert Manager **DNS authorization** for the Gold-tier HTTPS step — DNS auth requires owning the parent zone, impossible on `nip.io`. Use **load balancer authorization** instead.
