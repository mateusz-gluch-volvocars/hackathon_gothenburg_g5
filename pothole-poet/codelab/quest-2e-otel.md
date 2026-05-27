# 🛡 Quest 2E-2 — OpenTelemetry: see what your users see

<Objective lane="guardian">

**🎯 What you'll do.** Add **OpenTelemetry tracing and metrics** to your Streamlit app, shipping both signals to `telemetry.googleapis.com`. Traces land in Cloud Trace for debugging; metrics land in Cloud Monitoring as PromQL-queryable Prometheus time series. One setup, one endpoint, one rebuild. ~20 min.

**🤝 Why it matters.** Your uptime check (Q2E-1) tells you *if* the app is up. Traces tell you *what happens inside each request*. Metrics tell you *how the app is performing over time*: request rate, latency, broken down by code path, queryable via **PromQL**.

</Objective>

<Callout type="critical" title="Needs a running Streamlit deployment">

This page instruments the app you deployed in Q2D-4. If `kubectl get deployment pothole-laureate -n laureate` returns "not found", finish Q2D-4 first.

</Callout>

> Guardian lane · ~20 min hands-on (much of it waiting for `gcloud builds submit`).

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

# 1. Edit app.py — paste setup_otel() (traces + metrics) + wrap 3 functions (Steps 1-2)
cd ~/quest/pothole-poet/streamlit

# 2. Uncomment OTEL_ENABLED in deployment.yaml
sed -i 's|# - name: OTEL_ENABLED|- name: OTEL_ENABLED|; s|#   value: "true"|  value: "true"|' k8s/deployment.yaml
grep OTEL_ENABLED k8s/deployment.yaml
# ✅ Expect: - name: OTEL_ENABLED \n   value: "true"

# 3. Build + roll out — build from pothole-poet/ (NOT streamlit/) so the
#    seed CSV is in the build context (see Q2D-2 Concept).
cd ~/quest/pothole-poet
gcloud builds submit \
  --tag="europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel" \
  --region=$REGION

kubectl apply -f streamlit/k8s/deployment.yaml
kubectl set image deployment/pothole-laureate \
  pothole-laureate=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v3-otel \
  -n laureate
kubectl rollout status deployment/pothole-laureate -n laureate

# 4. Generate traffic + verify both signals
for i in 1 2 3 4 5; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 1; done
# ✅ Traces: Console → Trace explorer → filter service.name = pothole-laureate
# ✅ Metrics: Console → Monitoring → Metrics Explorer → PromQL →
#    {"prometheus.googleapis.com/pothole_laureate_requests/counter"}
```

</QuickPath>

## Where you are right now

Your Garage has come a long way. The AlloyDB Lead seeded 5,000 pothole reports. The Pipeline-author's DAG federates them into BigQuery where Gemini composes an ode per neighbourhood. The GKE / App Lead deployed Streamlit on Autopilot, wired its identity to BigQuery (Q2D-3), and exposed it through a Gateway. You added an uptime check in Q2E-1 that pings the public URL every 60 seconds.

So you know the app is **up**. But you can't see **inside** it. When someone says "the page was slow at 2:14pm", you have no answer. Was it the BigQuery query? The broadcast bucket read? The network? The app is a black box.

## How OpenTelemetry fixes this

**OpenTelemetry** (OTel) is the industry standard for instrumenting applications. Instead of vendor-specific libraries, your app emits **traces** and **metrics** in a standard protocol called **OTLP** (OpenTelemetry Protocol). A trace is a tree of **spans**, each one a timed operation: "`load_live` took 240 ms, and inside it, the BigQuery query took 180 ms." A metric is an aggregate counter or histogram: "the app served 12 requests in the last minute, p95 latency was 310 ms."

Google Cloud's observability stack speaks OTLP natively. One endpoint, `telemetry.googleapis.com`, accepts all three signal types: traces route to **Cloud Trace**, metrics route to **Cloud Monitoring** (queryable via **PromQL**), and logs route to **Cloud Logging**. In this Quest we instrument traces and metrics; your app's logs already reach Cloud Logging via GKE's built-in stdout capture. No proprietary SDK, no vendor lock-in; the same instrumentation works with any OTLP-compatible backend.

<Concept title="What about Managed OpenTelemetry for GKE?">

GKE also offers **Managed OpenTelemetry for GKE**: a fully managed in-cluster collector that receives OTLP traces, metrics, and logs from your workloads and exports them to Cloud Trace, Cloud Monitoring, and Cloud Logging automatically. You enable it on the cluster (`gcloud beta container clusters update ... --managed-otel-scope=COLLECTION_AND_INSTRUMENTATION_COMPONENTS`), and GKE deploys a managed collector at:

```
http://opentelemetry-collector.gke-managed-otel.svc.cluster.local:4318
```

You then create an `Instrumentation` custom resource in your namespace, and GKE auto-injects the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable into your Pods. Your app sends OTLP over HTTP to the in-cluster collector instead of authenticating directly to `telemetry.googleapis.com`. The collector handles credentials, batching, retries, and export. No WIF IAM bindings for trace/metrics export, no gRPC channel credentials in your code.

For this Quest we export directly to `telemetry.googleapis.com` so you see the full auth + export path end-to-end. Your `setup_otel()` code, your span wrappers, your counters and histograms all stay identical with either approach; the only thing that changes is where the OTLP data goes first. If you take this pipeline into production, Managed OTel is the natural next step.

</Concept>

## What you're doing, concretely

Four things:

1. **Grant the Pod permission to write traces and metrics.** Same WIF principal binding pattern as Q2D-3, two IAM roles: `cloudtrace.agent` (traces) and `monitoring.metricWriter` (metrics).

2. **Add instrumentation to `app.py`.** One `setup_otel()` block that connects both a TracerProvider and a MeterProvider to `telemetry.googleapis.com`. Same endpoint, same credentials, two signal types.

3. **Wrap your load functions.** Each function gets a span (for trace debugging) and two metric recording calls: a request counter and a duration histogram. The BigQuery and Cloud Storage clients auto-emit their own child spans underneath yours.

4. **Rebuild and verify.** One `gcloud builds submit`, one rollout, then check Cloud Trace for spans and Metrics Explorer for your counter.

---

### Step 0 — Bind the Pod's WIF principal to the OTel IAM roles

Two project-level roles on the Pod's WIF identity: `roles/cloudtrace.agent` (write spans) and `roles/monitoring.metricWriter` (write metrics). Same binding pattern as Q2D-3; same reason it can't be pre-provisioned (the WIF pool only exists after Q2D-1).

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

✅ **Expect** (twice): `Updated IAM policy for project [...]` with the new principal + role.

> IAM propagation takes 2-7 minutes. The OTel exporter retries silently; first traces may take up to ~7 min to appear after rollout.

### Step 1 — Add the `setup_otel()` block to `app.py`

Open `streamlit/app.py` in your Workstation IDE. Right after the existing `import` block, paste this:

```python
# ── OpenTelemetry → telemetry.googleapis.com (traces + metrics) ──────────
import os, time, socket
import grpc
import google.auth
import google.auth.transport.requests
from google.auth.transport.grpc import AuthMetadataPlugin

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def setup_otel():
    """Wire OTel traces + metrics to telemetry.googleapis.com. Safe to skip."""
    if os.environ.get("OTEL_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    # Streamlit reruns the script on every interaction. OTel provider state is
    # process-global (lives in the opentelemetry package, not in this script),
    # so check if a real provider is already set before configuring again.
    if type(trace.get_tracer_provider()).__name__ != "ProxyTracerProvider":
        return
    try:
        credentials, project_id = google.auth.default()
        request = google.auth.transport.requests.Request()
        channel_creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            grpc.metadata_call_credentials(
                AuthMetadataPlugin(credentials=credentials, request=request)),
        )

        resource = Resource.create({
            SERVICE_NAME: "pothole-laureate",
            "service.instance.id": socket.gethostname(),
            "service.namespace": "laureate",
            "cloud.region": os.environ.get("REGION", "europe-west1"),
            "gcp.project_id": project_id or "unknown",
        })

        # Traces → Cloud Trace
        tp = TracerProvider(resource=resource)
        tp.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(
            credentials=channel_creds,
            endpoint="https://telemetry.googleapis.com:443/v1/traces",
        )))
        trace.set_tracer_provider(tp)

        # Metrics → Cloud Monitoring (PromQL-queryable as prometheus.googleapis.com/*)
        metrics.set_meter_provider(MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    credentials=channel_creds,
                    endpoint="https://telemetry.googleapis.com:443/v1/metrics",
                ),
                export_interval_millis=15000,
            )],
        ))
    except Exception as e:
        print(f"[otel] setup skipped: {e}", flush=True)

setup_otel()
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter(
    "pothole_laureate_requests", description="Total page renders")
request_duration = meter.create_histogram(
    "pothole_laureate_request_duration_seconds",
    description="Page render duration", unit="s")
```

One function, one endpoint, two signal types:

1. **Credentials + resource**: Loads WIF identity from the Pod (Step 0). The resource attributes identify your app for both Cloud Trace labels and the Cloud Monitoring `prometheus_target` mapping.
2. **`ProxyTracerProvider` guard**: Streamlit re-runs the entire script on every user interaction, but OTel provider state is process-global (it lives in the `opentelemetry` package, not in your script). If a real provider is already set, the function returns immediately. Providers are configured exactly once per process.
3. **TracerProvider with `SimpleSpanProcessor`**: Exports each span synchronously to `telemetry.googleapis.com` → Cloud Trace. We use `SimpleSpanProcessor` for simplicity; for higher-throughput production apps, switch to `BatchSpanProcessor` (the guard prevents the leaked-thread issue).
4. **MeterProvider**: Exports counters and histograms to the same endpoint → Cloud Monitoring, where they land as `prometheus.googleapis.com/*` metrics, queryable via PromQL.
5. **Module-level instruments**: `request_counter` and `request_duration` are no-ops when `OTEL_ENABLED` is off, so the recording calls in Step 2 are always safe.

✅ **Expect:** No syntax errors when you save. `tracer`, `request_counter`, and `request_duration` are module-level globals ready for Step 2.

### Step 2 — Wrap your three functions with spans + metrics

Find these three functions in `app.py`. Each one gets a span wrapper (for trace debugging) and two metric recording lines (for the PromQL dashboard):

```python
def read_broadcast() -> str:
    with tracer.start_as_current_span("read_broadcast"):
        _start = time.time()
        # ... existing body ...
        request_counter.add(1, {"function": "read_broadcast"})
        request_duration.record(time.time() - _start, {"function": "read_broadcast"})

def load_live(...):
    with tracer.start_as_current_span("load_live"):
        _start = time.time()
        # ... existing BigQuery query body ...
        request_counter.add(1, {"function": "load_live"})
        request_duration.record(time.time() - _start, {"function": "load_live"})

def load_seed(...):
    with tracer.start_as_current_span("load_seed"):
        _start = time.time()
        # ... existing CSV-load body ...
        request_counter.add(1, {"function": "load_seed"})
        request_duration.record(time.time() - _start, {"function": "load_seed"})
```

Each function now produces two signal types:

- **A span** that records when it started, when it ended, and whether it succeeded. The BigQuery and Cloud Storage clients auto-emit their own child spans underneath yours.
- **A counter increment + duration measurement** that lands in Cloud Monitoring as `prometheus.googleapis.com/pothole_laureate_requests/counter` and `.../pothole_laureate_request_duration_seconds/histogram`. Both are PromQL-queryable the moment the first data point arrives.

✅ **Expect:** No syntax errors. The `function` label on the metrics lets you break down the dashboard by code path.

### Step 3 — Flip on `OTEL_ENABLED` in the Deployment

`k8s/deployment.yaml` has the env var pre-written but commented out. Uncomment it:

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

Build from `pothole-poet/` (where the Dockerfile lives):

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

### Step 5 — Generate traffic and verify both signals

```bash
# Hit the page a few times
for i in 1 2 3 4 5; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 1; done
```

**Verify traces.** Wait 30-60 seconds, then open the Console: **Trace → Trace explorer** → filter `service.name = pothole-laureate`.

✅ **Expect:** 5+ traces listed, each with `load_live` or `load_seed` as the root span.

Click a `load_live` trace. The span tree shows:

```
load_live                                ── 240 ms
  └─ google.cloud.bigquery.Client.query    ── 180 ms
      └─ POST /bigquery/v2/queries         ── 150 ms
read_broadcast                           ──  35 ms
  └─ google.cloud.storage.Bucket.get       ──  30 ms
```

That's the moment you can answer "why was the page slow at 2:14pm?" without guessing.

**Verify metrics.** Open **Console → Monitoring → Metrics Explorer** → click the **`< > PromQL`** button and run:

```promql
{"prometheus.googleapis.com/pothole_laureate_requests/counter"}
```

Metrics export every 15 seconds, so give it a minute after the first curl batch.

✅ **Expect:** A rising counter line. If you see data here, your OTel metrics pipeline is working. The next page (Q2E-3) puts these metrics on a proper Guardian dashboard alongside infrastructure and platform signals.

<Screenshot src="/quest/pothole-poet/img/trace_otel.png" caption="Cloud Trace waterfall view: each row is a span, nested spans show parent-child relationships, and the timeline shows where time was spent. Your traces will show load_live / read_broadcast as root spans with BigQuery and Cloud Storage child spans underneath." />

<Gotchas>
- <strong>No traces appear, ever.</strong> Most likely: <code>cloudtrace.googleapis.com</code> isn&rsquo;t enabled on the project. <code>telemetry.googleapis.com</code> silently discards trace data when Cloud Trace API is disabled. Check: <code>gcloud services list --enabled | grep cloudtrace</code>. Fix: <code>gcloud services enable cloudtrace.googleapis.com</code>. (Per-Garage Terraform pre-enables it; flag your Garage owner if it&rsquo;s missing.)
- <strong>"Permission denied" in Pod logs from OTel exporter.</strong> The Pod&rsquo;s WIF principal needs <code>roles/cloudtrace.agent</code> and <code>roles/monitoring.metricWriter</code>. Both are bound in Step 0 above; if the Pod logs show <code>permission denied</code>, re-run Step 0 and wait ~7 min for IAM propagation (per Google&rsquo;s WIF docs). Verify: <code>gcloud projects get-iam-policy $PROJECT_ID --flatten='bindings[].members' --filter='bindings.members:principal*pothole-laureate AND bindings.role:cloudtrace.agent' --format='value(bindings.role)'</code>.
- <strong>Streamlit reloader keeps recreating the TracerProvider.</strong> Streamlit re-runs the entire script on every user interaction and on file changes. The <code>ProxyTracerProvider</code> check in <code>setup_otel()</code> handles this: OTel provider state is process-global (lives in the <code>opentelemetry</code> package, not in your script), so once a real provider is set, subsequent reruns skip setup automatically. If you removed that check and see &ldquo;TracerProvider already set&rdquo; warnings, add it back.
- <strong>No new traces on consecutive page refreshes.</strong> If your load functions use <code>@st.cache_data</code>, the function body (including the span wrapper) only runs on cache misses. Wait for the cache TTL to expire (30-60 s depending on your setting), then refresh. You will see a new trace.
- <strong>Custom spans show up but BigQuery spans don&rsquo;t.</strong> The <code>google-cloud-bigquery</code> Python client has OpenTelemetry instrumentation built in; it auto-emits spans when a TracerProvider is configured before the client is constructed. There is <strong>no separate</strong> <code>opentelemetry-instrumentation-google-cloud-bigquery</code> package on PyPI; don&rsquo;t add one. If BQ child spans are missing, confirm <code>setup_otel()</code> runs before <code>bigquery.Client()</code> is first imported/called. (In <code>app.py</code> the setup block is at the top, above <code>load_live</code>, so this works by construction.)
- <strong>gRPC connection errors in Pod logs.</strong> The Pod&rsquo;s outbound gRPC needs to reach <code>telemetry.googleapis.com:443</code>. GKE Autopilot reaches it via Private Google Access (auto-enabled on private-node subnets); no Cloud NAT required. If you see connection refused, confirm <code>cloudtrace.googleapis.com</code> is enabled on the project (per-Garage Terraform pre-enables it).
</Gotchas>

<Shipped>
<strong>Your Streamlit Pod is observable, two ways.</strong> Every page render produces a <strong>trace</strong> in Cloud Trace (debug individual requests) and a <strong>metric data point</strong> in Cloud Monitoring (queryable via PromQL). One endpoint, one set of credentials, two signal types. The next page puts these metrics on a proper dashboard.
</Shipped>

➡️ Next: **Q2E-3 — Guardian Dashboard** (sidebar on the left).
