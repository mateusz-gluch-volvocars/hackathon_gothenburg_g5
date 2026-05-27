---
name: dashboard-helper
description: Builds and imports Cloud Monitoring dashboards with PromQL for Q2E-3 of the Iron & Cloud Pothole Poet quest. Creates the 5-widget hand-built Guardian dashboard, imports the pre-built pipeline-overview.json, lists and exports existing dashboards, and helps write or debug PromQL queries against any of the three metric layers (GCP platform, OTel app, Kubernetes infra). Use when the Guardian asks to create a dashboard, import a dashboard, write a PromQL query, debug a dashboard widget, export a dashboard, or asks about Cloud Monitoring metrics.
---

# Dashboard helper (Q2E-3)

**Codelab counterpart:** Q2E-3 — `~/quest/pothole-poet/codelab/quest-2e-dashboard.md`.

Use this skill when the Guardian is building, importing, or debugging Cloud Monitoring dashboards. Drive each step interactively; do not auto-run writes without HITL approval.

## What you can rely on

- The participant has completed Q2E-1 (uptime check exists) and Q2E-2 (OTel instrumentation deployed, `OTEL_ENABLED=true`).
- OTel metrics are flowing: `pothole_laureate_requests` (counter) and `pothole_laureate_request_duration_seconds` (histogram), both under `prometheus.googleapis.com/`.
- GKE Autopilot collects `kubernetes.io/container/cpu/core_usage_time` and `kubernetes.io/container/memory/used_bytes` automatically.
- The uptime check is named `pothole-laureate-uptime`.
- Pre-built dashboard JSON lives at `~/quest/pothole-poet/dashboards/pipeline-overview.json`.
- Two additional Google-published sample dashboards: `dashboards/k8s-pod-prometheus.json` and `dashboards/k8s-cluster-prometheus.json`.

## The three metric layers

All three are PromQL-queryable in Cloud Monitoring:

| Layer | Prefix | Source |
|---|---|---|
| GCP platform | `monitoring.googleapis.com/...` | Automatic (uptime checks, LB latency, API errors) |
| Application | `prometheus.googleapis.com/...` | Your OTel code from Q2E-2 |
| Kubernetes | `kubernetes.io/...` | GKE Autopilot, automatic |

## PromQL syntax for Cloud Monitoring

Cloud Monitoring uses **UTF-8 PromQL**. Metric names go inside braces, quoted:

```promql
{"monitoring.googleapis.com/uptime_check/check_passed", monitored_resource="uptime_url"}
```

Key rules:
- **Counters** need `rate()` or `increase()`: `rate({"prometheus.googleapis.com/pothole_laureate_requests/counter"}[5m])`
- **Gauges** are queried raw (no `rate()`): `{"kubernetes.io/container/memory/used_bytes", namespace="laureate"}`
- **Histograms** use `histogram_quantile()` with `by (le)`: `histogram_quantile(0.95, sum(rate({"prometheus.googleapis.com/pothole_laureate_request_duration_seconds/histogram"}[5m])) by (le))`
- Cloud Monitoring is **strongly typed**: `rate()` on a gauge or `histogram_quantile()` on a counter returns an error, not silent garbage.
- Legacy underscore+colon syntax (`kubernetes_io:container_cpu_core_usage_time`) also works but the quoted UTF-8 form is current.

## Steps

### 1. Build the hand-built Guardian dashboard (if not already done)

Check if the participant has already created the dashboard in the Console:

```bash
gcloud monitoring dashboards list --format="table(name, displayName)" | grep -i guardian
```

If not found, walk them through creating it in **Console -> Monitoring -> Dashboards -> Create Custom Dashboard**, named `Pothole Laureate · Guardian`.

Five widgets, each as a Line chart with PromQL:

**Widget 1 — Uptime (GCP platform metric):**
```promql
{"monitoring.googleapis.com/uptime_check/check_passed", monitored_resource="uptime_url"}
```

**Widget 2 — Request rate (OTel counter):**
```promql
rate({"prometheus.googleapis.com/pothole_laureate_requests/counter", job="pothole-laureate"}[5m])
```

**Widget 3 — Pod CPU (Kubernetes metric):**
```promql
rate({"kubernetes.io/container/cpu/core_usage_time", namespace="laureate"}[5m])
```

**Widget 4 — Latency p95 (OTel histogram):**
```promql
histogram_quantile(0.95, sum(rate({"prometheus.googleapis.com/pothole_laureate_request_duration_seconds/histogram", job="pothole-laureate"}[5m])) by (le))
```

**Widget 5 — Pod memory (Kubernetes gauge):**
```promql
{"kubernetes.io/container/memory/used_bytes", namespace="laureate"}
```

### 2. Import the pipeline overview dashboard

```bash
cd ~/quest/pothole-poet
gcloud monitoring dashboards create --config-from-file=dashboards/pipeline-overview.json
```

Verify it appeared:

```bash
gcloud monitoring dashboards list --format="table(name, displayName)" | grep -i pipeline
```

The imported dashboard has 11 widgets: 3 health scorecards (uptime, Composer, AlloyDB), 4 Streamlit app charts (request rate, latency, Pod CPU, Pod memory), 2 section headers, and 2 pipeline charts (Composer task throughput, AlloyDB CPU).

### 3. Import Google-published sample dashboards (optional)

```bash
gcloud monitoring dashboards create --config-from-file=dashboards/k8s-pod-prometheus.json
gcloud monitoring dashboards create --config-from-file=dashboards/k8s-cluster-prometheus.json
```

### 4. Export a dashboard (dashboards as code)

If the participant wants to export their hand-built dashboard:

```bash
# Find the dashboard ID
gcloud monitoring dashboards list --format="table(name, displayName)"

# Export it
gcloud monitoring dashboards describe DASHBOARD_ID --format=json > my-dashboard.json
```

The exported JSON uses `prometheusQuery` fields for PromQL widgets. It can be imported into any other project with `gcloud monitoring dashboards create --config-from-file=my-dashboard.json`.

### 5. Debug a widget showing "No data"

Common causes, in order:

1. **No traffic.** OTel metrics only exist after requests hit the app. Run: `curl -s "http://$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.addresses[0].value}')/"` a few times.
2. **OTEL_ENABLED not set.** Check: `kubectl exec deploy/pothole-laureate -n laureate -- env | grep OTEL`. Should show `OTEL_ENABLED=true`.
3. **Metric export lag.** OTel exports every 15 s; Cloud Monitoring needs 1-2 export cycles. Wait 1-2 minutes.
4. **Wrong metric type.** If they used `rate()` on a gauge or raw query on a counter, Cloud Monitoring returns an error (strongly typed). Check the metric type.
5. **GKE metrics not yet available.** `kubernetes.io` metrics take 5-10 minutes to appear after the first Pod starts on a new cluster.
6. **Composer/AlloyDB widgets empty.** These show data only if the participant has already created the Composer environment (Q2B) and AlloyDB cluster (Q2A). If those resources don't exist yet, the widgets are expected to be empty.

### 6. Help write custom PromQL queries

If the participant wants to add widgets beyond the standard five, help them:

1. Identify which metric layer the data comes from.
2. Look up the metric name: `gcloud monitoring metrics list --filter="metric.type:KEYWORD" --format="value(type)" | head -10`
3. Check if it's a counter (needs `rate()`) or gauge (raw value).
4. Compose the PromQL using the UTF-8 quoted syntax.
5. Test it in **Metrics Explorer -> PromQL** before adding to a dashboard.
