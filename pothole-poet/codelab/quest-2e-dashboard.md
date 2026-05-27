# 🛡 Quest 2E-3 — Guardian Dashboard: your PromQL command center

<Objective lane="guardian">

**🎯 What you'll do.** Build a **5-widget Cloud Monitoring dashboard** using **PromQL** queries across three metric layers: GCP platform, Kubernetes infrastructure, and your OTel application metrics. One screen, one query language, every signal your Garage produces. ~12 min.

**🤝 Why it matters.** Data without a view is data nobody looks at. Your uptime check (Q2E-1) and OTel instrumentation (Q2E-2) are producing signals right now. GKE Autopilot adds infrastructure metrics automatically. This dashboard puts all of it on one screen; it is where the Guardian lives for the rest of the day.

</Objective>

> Guardian lane · ~12 min · follows Q2E-2 (you need OTel metrics flowing).

<QuickPath>

Open **Console → Monitoring → Dashboards → Create Custom Dashboard**. Name it `Pothole Laureate · Guardian`.

For each widget: **Add widget** → **Line chart** → click **`< > PromQL`** → paste the query → **Run query** → **Apply**.

```promql
# Widget 1 — Uptime (GCP platform metric)
{"monitoring.googleapis.com/uptime_check/check_passed", monitored_resource="uptime_url"}

# Widget 2 — Request rate (your OTel counter)
rate({"prometheus.googleapis.com/pothole_laureate_requests/counter", job="pothole-laureate"}[5m])

# Widget 3 — Pod CPU (Kubernetes infrastructure metric)
rate({"kubernetes.io/container/cpu/core_usage_time", namespace="laureate"}[5m])

# Widget 4 — Latency p95 (your OTel histogram)
histogram_quantile(0.95, sum(rate({"prometheus.googleapis.com/pothole_laureate_request_duration_seconds/histogram", job="pothole-laureate"}[5m])) by (le))

# Widget 5 — Pod memory (Kubernetes gauge)
{"kubernetes.io/container/memory/used_bytes", namespace="laureate"}
```

Generate traffic, then save:

```bash
for i in 1 2 3 4 5 6 7 8; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 2; done
```

✅ All 5 widgets show data within 1-2 min. Save the dashboard.

Import the full pipeline dashboard (one command):

```bash
cd ~/quest/pothole-poet
gcloud monitoring dashboards create --config-from-file=dashboards/pipeline-overview.json
```

✅ "Pothole Laureate · Pipeline Overview" appears in Dashboards with 11 PromQL widgets covering Streamlit, Composer, and AlloyDB.

</QuickPath>

You have three metric sources producing data right now. The uptime check from Q2E-1 pings every 60 seconds. The OTel instrumentation from Q2E-2 exports counters and histograms every 15 seconds. GKE Autopilot collects Pod CPU and memory continuously. None of that is useful until you can see it in one place.

---

<Concept title="🤖 Or drive this with Antigravity CLI">

**Antigravity CLI** has a **`dashboard-helper`** skill that covers this entire page: builds the 5-widget Guardian dashboard, imports the pipeline overview JSON, helps write custom PromQL queries, and debugs widgets showing "No data." Make sure you're in the Quest repo so the workspace plugin loads:

```bash
cd ~/quest
agy
```

Then ask:

> *"Help me build the Guardian dashboard with PromQL widgets for uptime, request rate, latency, Pod CPU, and Pod memory."*

Or skip straight to the import:

> *"Import the pipeline overview dashboard from the dashboards folder."*

</Concept>

### Step 1 — Create the dashboard

Open **Console → Monitoring → Dashboards → Create Custom Dashboard**.

Name it `Pothole Laureate · Guardian`.

For every widget below: click **Add widget** → select **Line chart** → in the query pane, click the **`< > PromQL`** button to switch to the code editor. Paste the query, click **Run query**, then **Apply**.

<Screenshot src="/quest/pothole-poet/img/monitoring_dashboard.png" caption="Cloud Monitoring custom dashboard with PromQL widgets. Your Guardian dashboard will have five widgets covering uptime, request rate, latency, Pod CPU, and Pod memory." />

### Step 2 — Widget 1: Uptime (GCP platform metric)

```promql
{"monitoring.googleapis.com/uptime_check/check_passed", monitored_resource="uptime_url"}
```

This metric exists because you ran `gcloud monitoring uptime create` in Q2E-1. Cloud Monitoring created it for you; you did not instrument anything. The value is `1` (up) or `0` (down), one data point per minute per probe region.

The curly-brace syntax `{"metric.type", label="value"}` is a **PromQL selector**. It picks time series by metric name and label values. Cloud Monitoring metric names are fully qualified (`monitoring.googleapis.com/...`), so they are longer than bare Prometheus metric names, but the selector mechanics are identical. This is the modern **UTF-8 PromQL** syntax; if you find examples online using an underscore+colon form like `kubernetes_io:container_cpu_core_usage_time`, that is the legacy encoding of the same metric. Both work, but the quoted form is current and what Cloud Monitoring generates.

✅ **Expect:** A line at `1.0` across all regions. If any region shows `0`, your Gateway is down for that probe.

### Step 3 — Widget 2: Request rate (your OTel counter)

```promql
rate({"prometheus.googleapis.com/pothole_laureate_requests/counter", job="pothole-laureate"}[5m])
```

This is YOUR metric. The `request_counter.add(1, {"function": "read_broadcast"})` you wrote in Q2E-2 Step 2 produces a Prometheus counter named `pothole_laureate_requests`. Every time a user loads the page, the counter increments.

A counter only goes up, so the raw value is a staircase. **`rate()`** converts it into requests per second over a 5-minute window. The `function` label you set in Q2E-2 lets you break down by code path: `load_live` vs `read_broadcast` vs `load_seed`.

✅ **Expect:** A low line (your curl traffic from Q2E-2). Will climb when real users arrive on event day.

### Step 4 — Widget 3: Pod CPU (Kubernetes infrastructure metric)

```promql
rate({"kubernetes.io/container/cpu/core_usage_time", namespace="laureate"}[5m])
```

Same `rate()` pattern as Widget 2, different metric source. GKE Autopilot collects `kubernetes.io/container/cpu/core_usage_time` automatically for every Pod. You did not instrument anything; the platform did it for you. The value is CPU cores used (0.05 = 5% of one core).

Notice: the PromQL is structurally identical to Widget 2. Selector, `rate()`, time window. Three different metric prefixes (`monitoring.googleapis.com`, `prometheus.googleapis.com`, `kubernetes.io`), same query language.

✅ **Expect:** A line between 0.01 and 0.10 for the Streamlit Pod.

<Concept title="Three metric layers, one query language">

Your first three widgets each draw from a different metric source:

| Layer | Prefix | Who collects it |
|---|---|---|
| **GCP platform** | `monitoring.googleapis.com/...` | Cloud Monitoring, automatically. Uptime checks, load balancer latency, API error rates. |
| **Your application** | `prometheus.googleapis.com/...` | Your OTel code from Q2E-2. Counters, histograms, anything you instrument. |
| **Kubernetes infra** | `kubernetes.io/...` | GKE Autopilot, automatically. Pod CPU, memory, restart count, network. |

All three land in Cloud Monitoring as Prometheus-format time series. All three are queryable with the same PromQL syntax. That is why one dashboard can show platform health, app behavior, and infrastructure utilization side by side with the same query language across every widget.

Cloud Monitoring also exposes a **Prometheus-compatible read API** at:

```
https://monitoring.googleapis.com/v1/projects/PROJECT_ID/location/global/prometheus/api/v1/
```

Any tool that speaks the standard Prometheus query API can read all three metric layers from this single endpoint.

</Concept>

### Step 5 — Widget 4: Request latency p95 (your OTel histogram)

```promql
histogram_quantile(0.95, sum(rate({"prometheus.googleapis.com/pothole_laureate_request_duration_seconds/histogram", job="pothole-laureate"}[5m])) by (le))
```

This is the `request_duration.record(time.time() - _start, ...)` histogram from Q2E-2 Step 2. It captures how long each function takes, not just how often it runs.

**`histogram_quantile(0.95, ...)`** computes the 95th percentile latency: "95% of requests completed faster than this." The `by (le)` clause is standard Prometheus histogram syntax; `le` (less-than-or-equal) is the bucket boundary label that every Prometheus histogram emits. Under the hood, Cloud Monitoring stores your OTel histogram as a distribution-valued metric and exposes it with the standard `_bucket`, `_count`, and `_sum` suffixes so `histogram_quantile()` works exactly as it does on a native Prometheus histogram.

With Widgets 2 and 4 together you have two of the three **RED signals**: **R**ate (Widget 2) and **D**uration (Widget 4). The uptime check (Widget 1) covers **E**rrors. That is a production-grade observability surface from three PromQL queries.

✅ **Expect:** A line showing p95 latency in seconds. Typically 0.2-0.5 s for `load_live` (the BigQuery round-trip dominates).

### Step 6 — Widget 5: Pod memory (Kubernetes gauge)

```promql
{"kubernetes.io/container/memory/used_bytes", namespace="laureate"}
```

No `rate()` this time. Memory is a **gauge**: it goes up and down as the process allocates and frees. You query the raw value, not the rate of change. Compare this to the CPU widget (Step 4), which uses a counter and needs `rate()`.

The difference matters whenever you write PromQL: counters get `rate()` or `increase()`; gauges get raw values or `avg_over_time()`. Cloud Monitoring is **strongly typed**, so choosing wrong does not just give meaningless results; the query fails outright. Running `rate()` on a gauge or `histogram_quantile()` on a counter returns an error, not silent garbage. That is stricter than upstream Prometheus, and it catches mistakes early.

✅ **Expect:** A line around 100-200 MB (Streamlit + Python runtime + cached DataFrames).

### Step 7 — Generate traffic and verify

Send a batch of requests so all widgets have fresh data:

```bash
for i in 1 2 3 4 5 6 7 8; do curl -s "http://$GATEWAY_IP/" >/dev/null; sleep 2; done
```

Wait 1-2 minutes (OTel metrics export every 15 seconds; Cloud Monitoring needs a couple of export cycles to render new data points). Then check each widget:

| Widget | What to see |
|---|---|
| Uptime | Flat line at 1.0 |
| Request rate | Non-zero, reflects your curl traffic |
| Pod CPU | Small bump during request processing |
| Latency p95 | 0.2-0.5 s range |
| Pod memory | Stable around 100-200 MB |

Click **Save** in the dashboard toolbar.

✅ **All 5 widgets show data.** Leave this tab open; this is your "is anything weird right now?" surface for the rest of the day.

### Step 8 — Import the full pipeline dashboard (one command)

You built your Guardian dashboard by hand to learn the PromQL patterns. In production you would not start from scratch: you define dashboards as JSON and import them with a single command. Your quest repo includes a pre-built dashboard that covers the entire Pothole Laureate pipeline:

```bash
cd ~/quest/pothole-poet

gcloud monitoring dashboards create \
  --config-from-file=dashboards/pipeline-overview.json
```

✅ **Expect:** `Created dashboard [projects/<id>/dashboards/<id>].`

Open **Console → Monitoring → Dashboards** → click **Pothole Laureate · Pipeline Overview**.

The dashboard has three sections:

| Section | Widgets | What they show |
|---|---|---|
| **Top row** | 3 scorecards with sparklines | App uptime (Q2E-1), Composer health, AlloyDB CPU. Green = healthy; red = investigate. |
| **Streamlit App** | Request rate by function, latency p95, Pod CPU, Pod memory | Your OTel metrics from Q2E-2 + GKE infrastructure. Same queries you hand-built in Steps 2-6. |
| **Data Pipeline** | Composer task throughput, AlloyDB CPU utilization | The upstream pipeline: are DAG tasks finishing? Is the database under load? |

Use the **Namespace** filter at the top to scope the GKE widgets to `laureate`.

<Concept title="Dashboards as code">

The JSON file you just imported is the same format the Cloud Monitoring API uses. That means you can round-trip any dashboard between projects:

1. Build or customize a dashboard in the Console UI.
2. Find its ID: `gcloud monitoring dashboards list --format="table(name, displayName)"`
3. Export it: `gcloud monitoring dashboards describe DASHBOARD_ID --format=json > my-dashboard.json`
4. Check it into version control.
5. Import it into any other project: `gcloud monitoring dashboards create --config-from-file=my-dashboard.json`

The JSON structure uses `prometheusQuery` fields for PromQL widgets. Open `dashboards/pipeline-overview.json` in your Workstation IDE and search for that key to see all 11 queries. The `dashboardFilters` array at the top defines the **Namespace** dropdown; it resolves automatically at render time and scopes the GKE widgets without touching the Composer or AlloyDB queries.

Your quest repo also includes two Google-published sample dashboards (`dashboards/k8s-pod-prometheus.json` and `dashboards/k8s-cluster-prometheus.json`) with generic Kubernetes PromQL widgets. Import them the same way if you want broader cluster-level visibility.

</Concept>

<Gotchas>
- <strong>Widget shows "No data" after pasting the query.</strong> Click <strong>Run query</strong> before clicking Apply. The editor does not auto-run.
- <strong>Request rate and latency widgets are empty.</strong> OTel metrics need traffic to exist. Run the curl loop in Step 7, wait 1-2 minutes, then refresh the widget. If still empty after 3 minutes, check that <code>OTEL_ENABLED</code> is <code>"true"</code> in the Pod: <code>kubectl exec deploy/pothole-laureate -n laureate -- env | grep OTEL</code>.
- <strong>Pod CPU/memory show multiple lines.</strong> If the Deployment has more than one replica, each Pod reports independently. That is correct; the lines diverge slightly. To see the total, wrap the query in <code>sum()</code>.
- <strong>"Could not find requested metric" on kubernetes.io metrics.</strong> GKE system metrics take 5-10 minutes to appear after the first Pod starts. If your GKE cluster is brand new, wait and retry.
- <strong>The PromQL button is missing.</strong> Look for the <strong>&lt; &gt; PromQL</strong> toggle in the query pane toolbar. If you don&rsquo;t see it, scroll down or widen the panel.
</Gotchas>

<Shipped>
<strong>Your Guardian dashboard is live.</strong> Five widgets, three metric layers, one query language. Platform health, app behavior, and infrastructure utilization on one screen. Keep this tab open for the rest of the day; the next page (Q2E-4) adds the alert that pages you when something on this dashboard goes red.
</Shipped>

➡️ Next: **Q2E-4 — Alert · Broadcast · Snooze** (sidebar on the left).
