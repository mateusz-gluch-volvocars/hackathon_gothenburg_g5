# 🛡 Quest 2E-2 — OpenTelemetry: see what your users see

<Objective lane="guardian">

**🎯 What you'll do.** Wire the Streamlit Pod to ship **OpenTelemetry traces** straight to Google's new unified OTLP endpoint at `telemetry.googleapis.com`. Add three custom spans (`read_broadcast`, `load_silver`, `load_bronze`) and watch the BigQuery client's spans appear as their children. ~20 min, mostly waiting for the rebuild.

**🤝 Why it matters.** Uptime checks tell you *if* the door is open. Traces tell you *what users do once they're inside* — which queries are slow, which dependencies fail, where time goes. Once your spans are landing in Cloud Trace your team has a single shared surface to answer "why was the page slow at 2:14pm?" without anyone having to guess.

</Objective>

> Silver tier · ~20 min hands-on (much of it waiting for `gcloud builds submit`).

<QuickPath>

```bash
# 0. Bind the Pod's WIF principal to the two OTel IAM roles. These can't be
#    pre-provisioned (the GKE Workload Identity Pool only exists after Q2D-1),
#    so the Guardian binds them once GKE is up.
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" --role="roles/cloudtrace.agent"      --condition=None
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" --role="roles/monitoring.metricWriter" --condition=None

# 1. Edit app.py — paste the setup_otel() block + wrap 3 functions (see Steps 1-2)
cd ~/quest/pothole-poet/streamlit

# 2. Uncomment OTEL_ENABLED in deployment.yaml
sed -i 's|# - name: OTEL_ENABLED|- name: OTEL_ENABLED|; s|#   value: "true"|  value: "true"|' k8s/deployment.yaml
grep OTEL_ENABLED k8s/deployment.yaml
# ✅ Expect: - name: OTEL_ENABLED \n   value: "true"

# 3. Build + roll out — build from pothole-poet/ (NOT streamlit/) so the
#    Bronze seed CSV is in the build context (see Q2D-2 Concept).
cd ~/quest/pothole-poet
gcloud builds submit \
  --tag="europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel" \
  --region=$REGION

kubectl apply -f streamlit/k8s/deployment.yaml
kubectl set image deployment/pothole-laureate \
  pothole-laureate=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel \
  -n laureate
kubectl rollout status deployment/pothole-laureate -n laureate

# 4. Generate traffic + verify spans land
for i in 1 2 3 4 5; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 1; done
sleep 60   # spans take ~30-60 sec to land in Cloud Trace
gcloud trace traces list --limit=5 --format="value(traceId)"
# ✅ Expect: 5 trace IDs printed
```

</QuickPath>

Google rolled out a unified OpenTelemetry Protocol (OTLP) endpoint at `telemetry.googleapis.com` — one URL accepts traces, metrics, and logs in vendor-neutral OTLP format. Before this, each signal had its own Google API; now your app speaks the same protocol it would to any other backend, and Google handles the rest.

For your Streamlit app this is **two changes**: a `setup_otel()` initialisation block at the top of `app.py`, and `with tracer.start_as_current_span(...)` wrappers around three functions. The BigQuery and Cloud Storage clients auto-emit their own spans that attach as children of yours.

---

### Step 0 — Bind the Pod's WIF principal to the OTel IAM roles

OpenTelemetry export to `telemetry.googleapis.com` needs two project-level IAM roles on the Pod's identity: `roles/cloudtrace.agent` (lets the Pod write spans) and `roles/monitoring.metricWriter` (lets it write metrics).

These can't live in the per-Garage Terraform module — the GKE Workload Identity Pool `<PROJECT_ID>.svc.id.goog` is only created when your Infra-Admin runs `gcloud container clusters create-auto` in Q2D-1. IAM rejects bindings to pool members that don't exist yet, so the Guardian binds them here, after the cluster is up.

```bash
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/cloudtrace.agent" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="$PRINCIPAL" \
  --role="roles/monitoring.metricWriter" \
  --condition=None
```

✅ **Expect** (twice): `Updated IAM policy for project [...]` followed by the policy bindings showing your `principal://...` member with the new role.

Same principal URI format as Q2D-3 — `PROJECT_NUMBER` in the `projects/` segment, `PROJECT_ID` in the `.svc.id.goog` pool name. If either is empty, re-export them from Q2D-1.

> IAM propagation takes 2–7 minutes per Google's WIF docs. The OTel exporter retries silently — first traces may appear ~7 min after the rollout, not the ~60 s shown in Step 6.

### Step 1 — Paste the `setup_otel()` block at the top of `app.py`

Open `streamlit/app.py` in your Workstation IDE. Right after the existing `import` block, paste this:

```python
# ── OpenTelemetry → telemetry.googleapis.com (Telemetry OTLP API) ──────────
# 1. Auth: read pod identity credentials (Workload Identity)
import os
import grpc
import google.auth
import google.auth.transport.requests
from google.auth.transport.grpc import AuthMetadataPlugin

# 2. OpenTelemetry SDK
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_otel():
    """Wire OpenTelemetry to telemetry.googleapis.com. Idempotent + safe to skip."""
    if os.environ.get("OTEL_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    try:
        # 3. Build authenticated gRPC channel to the Telemetry API
        credentials, project_id = google.auth.default()
        request = google.auth.transport.requests.Request()
        auth_plugin = AuthMetadataPlugin(credentials=credentials, request=request)
        channel_creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            grpc.metadata_call_credentials(auth_plugin),
        )

        # 4. Resource attributes (show up in Cloud Trace as labels)
        resource = Resource.create({
            SERVICE_NAME: "pothole-laureate",
            "gcp.project_id": project_id or "unknown",
        })

        # 5. Tracer provider + OTLP exporter
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(
            OTLPSpanExporter(
                credentials=channel_creds,
                endpoint="https://telemetry.googleapis.com:443/v1/traces",
            )
        ))
        trace.set_tracer_provider(provider)
    except Exception as e:
        # Don't break the app if OTel can't initialise — just log and continue.
        print(f"[otel] setup skipped: {e}", flush=True)

setup_otel()
tracer = trace.get_tracer(__name__)
```

The shape: **load credentials → wrap them in a gRPC auth plugin → build a TracerProvider with the OTLP exporter pointing at the new endpoint.** The `OTEL_ENABLED` env-var gate means you can flip it on without touching code (Step 3).

✅ **Expect:** No syntax errors when you save. The block defines `tracer` as a module-level global ready for Step 2.

<Concept title="Why in-process and not a sidecar collector?">

Production deployments at scale often run a **Google-built OpenTelemetry Collector** (sidecar or DaemonSet) that handles auth, batching, and sampling — the app just speaks OTLP to localhost. For a hackathon Pod doing a few requests per minute, the in-process exporter is simpler: no extra YAML, no second container, all the auth + endpoint logic lives in one Python file you can read end-to-end. **In production you'd graduate to a collector** (or to the new managed-OTel-for-GKE preview), but the API surface in your app stays identical.

</Concept>

### Step 2 — Wrap your three functions with custom spans

Find these three functions in `app.py` and wrap their bodies with `tracer.start_as_current_span(...)`:

```python
def read_broadcast() -> str:
    with tracer.start_as_current_span("read_broadcast"):
        # ... existing body ...

def load_silver(...):
    with tracer.start_as_current_span("load_silver"):
        # ... existing BigQuery query body ...

def load_bronze(...):
    with tracer.start_as_current_span("load_bronze"):
        # ... existing CSV-load body ...
```

✅ **Expect:** No syntax errors. The BigQuery and Cloud Storage clients auto-emit their own spans — they'll attach as children of yours.

### Step 3 — Flip on `OTEL_ENABLED` in the Deployment

`k8s/deployment.yaml` already has the env var pre-written but commented out. Find the `pothole-laureate` container's `env:` block (around line 25-35), uncomment these two lines:

```yaml
- name: OTEL_ENABLED
  value: "true"
```

Or with sed:

```bash
sed -i 's|# - name: OTEL_ENABLED|- name: OTEL_ENABLED|; s|#   value: "true"|  value: "true"|' k8s/deployment.yaml
```

Verify:

```bash
grep -A1 OTEL_ENABLED k8s/deployment.yaml
```

✅ **Expect:**
```
- name: OTEL_ENABLED
  value: "true"
```

### Step 4 — Build the new image and roll it out

Build from the `pothole-poet/` parent directory (where the Dockerfile lives — see Q2D-2 Concept for why). The previous Step 3 sed ran inside `streamlit/`; `cd` up one level for the build:

```bash
cd ~/quest/pothole-poet

gcloud builds submit \
  --tag="europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel" \
  --region=$REGION
```

✅ **Expect** (after ~3 min): `SUCCESS` + the digest.

```bash
kubectl apply -f streamlit/k8s/deployment.yaml
kubectl set image deployment/pothole-laureate \
  pothole-laureate=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel \
  -n laureate
kubectl rollout status deployment/pothole-laureate -n laureate
```

✅ **Expect:** `deployment "pothole-laureate" successfully rolled out`.

### Step 5 — While the build runs (~3 min): build a Guardian dashboard

Cloud Monitoring → Dashboards → Create. Add three charts:

- `monitoring.googleapis.com/uptime_check/check_passed` filtered to your Q2E-1 check
- `cloudtrace.googleapis.com/billing/spans_ingested` (Cloud Trace span count)
- `kubernetes.io/container/cpu/core_usage_time` filtered to namespace `laureate` (Pod CPU)

Save as `Pothole Laureate · Guardian view`. Keep it open in a tab during Q3+ — this becomes your "is anything weird happening right now?" surface.

### Step 6 — Generate traffic and verify spans land

```bash
# Hit the page a few times
for i in 1 2 3 4 5; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 1; done

# Wait ~30-60s for the first traces to land
sleep 60

# List recent traces
gcloud trace traces list --limit=5 --format="value(traceId)"
```

✅ **Expect:** 5 trace IDs printed.

In the Console: **Trace → Trace explorer** → filter `service.name = pothole-laureate`. Click a `load_silver` trace. The span tree shows:

```
load_silver                              ── 240 ms
  └─ google.cloud.bigquery.Client.query    ── 180 ms
      └─ POST /bigquery/v2/queries         ── 150 ms
read_broadcast                           ──  35 ms
  └─ google.cloud.storage.Bucket.get       ──  30 ms
```

That's the moment you can answer *"why is the page slow today?"* without guessing.

<Screenshot caption="Trace explorer: filtered to pothole-laureate, showing recent traces with load_silver / load_bronze / read_broadcast as root spans." />

<Gotchas>
- <strong>No traces appear, ever.</strong> Most likely: <code>cloudtrace.googleapis.com</code> isn&rsquo;t enabled on the project. <code>telemetry.googleapis.com</code> silently discards trace data when Cloud Trace API is disabled. Check: <code>gcloud services list --enabled | grep cloudtrace</code>. Fix: <code>gcloud services enable cloudtrace.googleapis.com</code>. (Per-Garage Terraform pre-enables it; flag your Garage owner if it&rsquo;s missing.)
- <strong>"Permission denied" in Pod logs from OTel exporter.</strong> The Pod&rsquo;s WIF principal needs <code>roles/cloudtrace.agent</code> and <code>roles/monitoring.metricWriter</code>. Both are bound in Step 0 above; if the Pod logs show <code>permission denied</code>, re-run Step 0 and wait ~7 min for IAM propagation (per Google&rsquo;s WIF docs). Verify: <code>gcloud projects get-iam-policy $PROJECT_ID --flatten='bindings[].members' --filter='bindings.members:principal*pothole-laureate AND bindings.role:cloudtrace.agent' --format='value(bindings.role)'</code>.
- <strong>Streamlit reloader keeps recreating the TracerProvider.</strong> Streamlit&rsquo;s file-watch reloader can re-import the app on file changes, which calls <code>setup_otel()</code> again. The OTel SDK warns about double initialisation but keeps working. Safe to ignore in dev.
- <strong>Custom spans show up but BigQuery spans don&rsquo;t.</strong> The <code>google-cloud-bigquery</code> Python client has OpenTelemetry instrumentation built in &mdash; it auto-emits spans when a TracerProvider is configured before the client is constructed. There is <strong>no separate</strong> <code>opentelemetry-instrumentation-google-cloud-bigquery</code> package on PyPI; don&rsquo;t add one. If BQ child spans are missing, confirm <code>setup_otel()</code> runs before <code>bigquery.Client()</code> is first imported/called. (In <code>app.py</code> the setup block is at the top, above <code>load_silver</code>, so this works by construction.)
- <strong>gRPC connection errors in Pod logs.</strong> The Pod&rsquo;s outbound gRPC needs to reach <code>telemetry.googleapis.com:443</code>. GKE Autopilot reaches it via Private Google Access (auto-enabled on private-node subnets) &mdash; no Cloud NAT required. If you see connection refused, confirm <code>cloudtrace.googleapis.com</code> is enabled on the project (per-Garage Terraform pre-enables it).
</Gotchas>

<Shipped>
Silver tier, Guardian piece. <strong>Your Streamlit Pod is observable.</strong> Every page render produces a trace; every BigQuery query you make from the app is a child span; every Cloud Storage broadcast read is a child span. Your team's dashboards now have a real signal feed.
</Shipped>

🛡 Move to **Q2E-3** — set up the alert + broadcast + snooze loop, the full Guardian-of-the-day rhythm.
