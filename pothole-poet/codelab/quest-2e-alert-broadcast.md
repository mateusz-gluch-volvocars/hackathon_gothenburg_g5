# 🛡 Quest 2E-4 — Alert · Broadcast · Snooze: the full Guardian loop

<Objective lane="guardian">

**🎯 What you'll do.** Wire the **alert policy** on top of your Q2E-1 uptime check, post a **broadcast banner** that Streamlit renders to citizens, then **snooze the alert** when you claim a failure. ~15 min.

**🤝 Why it matters.** This is the **complete** Guardian loop: alert fires → you claim it (snooze) → broadcast "known issue" → fix → clear. The same on-call pattern production teams run daily.

</Objective>

> Guardian lane · ~15 min · uses `gcloud` throughout (no Console clicking) so the API surface is visible, what tooling could automate next.

<QuickPath>

```bash
PROJECT_ID="$(gcloud config get-value project)"
PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
EMAIL="$(gcloud config get-value account)"

# 0. Let the Pod read the broadcast bucket. Bind storage.objectViewer to the
#    WIF principal — same principal URI as the BQ + OTel bindings (Q2D-3, Q2E-2).
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="$PRINCIPAL" --role="roles/storage.objectViewer"

# 1. Email notification channel
gcloud beta monitoring channels create \
  --display-name="Guardian email · $EMAIL" \
  --type=email \
  --channel-labels="email_address=$EMAIL"

CHANNEL_ID="$(gcloud beta monitoring channels list \
  --filter='displayName:"Guardian"' --format='value(name)' | head -1)"

# 2. Alert policy on the Q2E-1 uptime check
UPTIME_CHECK_ID="$(gcloud monitoring uptime list-configs \
  --filter="displayName=pothole-laureate-uptime" \
  --format='value(name)' | head -1 | awk -F/ '{print $NF}')"

cat > /tmp/uptime-alert.json <<EOF
{
  "displayName": "pothole-laureate-uptime-alert",
  "combiner": "OR",
  "conditions": [{
    "displayName": "Uptime check failing",
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.\"check_id\"=\"${UPTIME_CHECK_ID}\" AND resource.type=\"uptime_url\"",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_NEXT_OLDER",
        "crossSeriesReducer": "REDUCE_COUNT_FALSE",
        "groupByFields": ["resource.label.\"host\""]
      }],
      "comparison": "COMPARISON_GT", "thresholdValue": 1, "duration": "60s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["${CHANNEL_ID}"]
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/uptime-alert.json

# 3. Broadcast a healthy banner
echo "Pipeline healthy — Guardian: @your-handle" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"

# 4. Trigger failure → claim → snooze → restore loop
kubectl delete pod -l app=pothole-laureate -n laureate
sleep 90  # email arrives, incident appears
echo "🛠 Known issue: Pod restart in progress · Guardian: @your-handle" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"

POLICY_ID="$(gcloud alpha monitoring policies list \
  --filter="displayName=pothole-laureate-uptime-alert" --format='value(name)' | head -1)"
gcloud alpha monitoring snoozes create \
  --display-name="Investigating Pod restart · @your-handle" \
  --criteria-policies="$POLICY_ID" \
  --start-time="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time="$(date -u -d '+30 minutes' +%Y-%m-%dT%H:%M:%SZ)"

echo "Pipeline healthy · restored at $(date -u +%H:%MZ)" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"
```

</QuickPath>

Q2E-1 tells you something's down. Q2E-2 shows what users experienced. This page is what you *do* about it: claim the failure (snooze), broadcast to your team, fix, clear.

---

### Step 0 — Let the Pod read the broadcast bucket

The Streamlit Pod reads `gs://<project>-broadcast/broadcast.txt` on every page render (cached 30 s). Until the Pod's WIF principal has read access, the banner never appears. Bind it now, same pattern as Q2D-3 and Q2E-2.

```bash
PROJECT_ID="$(gcloud config get-value project)"
PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/laureate/sa/pothole-laureate"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="$PRINCIPAL" \
  --role="roles/storage.objectViewer"
```

✅ **Expect:** `Updated IAM policy for project [<project>].` with the new principal + role listed.

> IAM propagation takes 2–7 minutes per Google's WIF docs. If the first banner you write in Step 3 doesn't show up immediately, wait and refresh.

### Step 1 — Create the email notification channel

```bash
EMAIL="$(gcloud config get-value account)"

gcloud beta monitoring channels create \
  --display-name="Guardian email · $EMAIL" \
  --type=email \
  --channel-labels="email_address=$EMAIL"
```

✅ **Expect:** `Created notification channel [projects/.../notificationChannels/<id>].`

Capture the channel ID for the next step:

```bash
CHANNEL_ID="$(gcloud beta monitoring channels list \
  --filter='displayName:"Guardian"' \
  --format='value(name)' | head -1)"
echo "Channel: $CHANNEL_ID"
```

✅ **Expect:** Full channel resource path like `projects/<id>/notificationChannels/123456789`.

### Step 2 — Create the alert policy on the Q2E-1 uptime check

Find the uptime check ID and write a policy file:

```bash
PROJECT_ID="$(gcloud config get-value project)"
UPTIME_CHECK_ID="$(gcloud monitoring uptime list-configs \
  --filter="displayName=pothole-laureate-uptime" \
  --format='value(name)' | head -1 | awk -F/ '{print $NF}')"

cat > /tmp/uptime-alert.json <<EOF
{
  "displayName": "pothole-laureate-uptime-alert",
  "combiner": "OR",
  "conditions": [{
    "displayName": "Uptime check failing",
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.\"check_id\"=\"${UPTIME_CHECK_ID}\" AND resource.type=\"uptime_url\"",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_NEXT_OLDER",
        "crossSeriesReducer": "REDUCE_COUNT_FALSE",
        "groupByFields": ["resource.label.\"host\""]
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 1,
      "duration": "60s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["${CHANNEL_ID}"]
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/uptime-alert.json
```

✅ **Expect:** `Created alert policy [projects/<id>/alertPolicies/<id>].`

<Concept title="Could this alert use PromQL instead?">

Yes. Cloud Monitoring supports PromQL-based alerting policies. We use the JSON filter format here because it is the verified pattern for uptime-check alerts. For production, consider PromQL-based policies: they use the same query language as your dashboard widgets and are portable to any Prometheus-compatible alerting backend.

</Concept>

Verify it registered:

```bash
gcloud alpha monitoring policies list \
  --filter="displayName=pothole-laureate-uptime-alert" \
  --format="value(displayName,enabled)"
```

✅ **Expect:** `pothole-laureate-uptime-alert  True`

### Step 3 — Wire the broadcast banner

The bucket `<project>-broadcast` is pre-provisioned. Broadcasting = writing one object to it:

```bash
echo "Pipeline healthy — Guardian: @your-handle" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"
```

✅ **Expect** (in the Streamlit UI within 30 sec): A yellow banner at the top reading `🛡 Guardian broadcast · Pipeline healthy. Guardian: @your-handle`.

### Step 4 — Run the failure → snooze loop

Trigger a failure: kill the Streamlit Pod:

```bash
kubectl delete pod -l app=pothole-laureate -n laureate
```

✅ **Expect:** `pod "pothole-laureate-<hash>" deleted` (twice, one per Pod).

Wait 1-2 min. Email arrives. Cloud Monitoring → Alerting shows an incident.

Claim it via broadcast:

```bash
echo "🛠 Known issue: Pod restart in progress · Guardian: @your-handle" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"
```

✅ **Expect** (Streamlit banner if still up): `🛡 Guardian broadcast · 🛠 Known issue...`

Snooze the alert for 30 min so the team isn't paged twice for the same thing:

```bash
POLICY_ID="$(gcloud alpha monitoring policies list \
  --filter="displayName=pothole-laureate-uptime-alert" \
  --format='value(name)' | head -1)"

gcloud alpha monitoring snoozes create \
  --display-name="Investigating Pod restart · @your-handle" \
  --criteria-policies="$POLICY_ID" \
  --start-time="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time="$(date -u -d '+30 minutes' +%Y-%m-%dT%H:%M:%SZ)"
```

✅ **Expect:** `Created snooze [projects/<id>/snoozes/<id>].`

Watch the Pod come back (the Deployment auto-restarted it):

```bash
kubectl get pods -n laureate -l app=pothole-laureate
```

✅ **Expect:** `Running` with `1/1` ready (within 1-2 min).

Clear the broadcast:

```bash
echo "Pipeline healthy · restored at $(date -u +%H:%MZ)" \
  | gcloud storage cp - "gs://${PROJECT_ID}-broadcast/broadcast.txt"
```

The uptime check turns green on its next probe. The snooze expires on its own; leave it or terminate early by setting `end-time` to now.

### Step 5 — Verify everything is wired

```bash
gcloud monitoring uptime list-configs                 --filter="displayName=pothole-laureate-uptime"        --format="value(displayName)"
gcloud beta monitoring channels list          --filter="displayName~Guardian"                      --format="value(displayName)"
gcloud alpha monitoring policies list         --filter="displayName=pothole-laureate-uptime-alert" --format="value(displayName)"
gcloud storage cat "gs://${PROJECT_ID}-broadcast/broadcast.txt"
```

✅ **Expect:** Each command prints one line.

<Gotchas>
- <strong>Alert policy creation returns "permission denied" on <code>monitoring.alertPolicies.create</code>.</strong> Workstation runner SA needs <code>roles/monitoring.editor</code>. Should be there via <code>roles/editor</code>. Confirm with <code>gcloud auth list</code>. you may be authed as your personal user, not the SA.
- <strong>Email notification never arrives.</strong> Check the channel was actually selected on the policy: <code>gcloud alpha monitoring policies describe $POLICY_ID --format='value(notificationChannels)'</code>. Should not be empty.
- <strong>Snooze list is empty after creating one.</strong> The <code>gcloud alpha monitoring snoozes list</code> defaults to listing snoozes ending within 14 days. Should be fine for our 30-min test, but if your snooze ended already it won&rsquo;t appear. Re-create with a longer end-time.
- <strong>Broadcast doesn&rsquo;t appear in Streamlit.</strong> The Pod&rsquo;s <code>BROADCAST_BUCKET</code> env var must be set (Terraform-provisioned, but check after any <code>kubectl set env</code> in Q3/Q4 since Kubernetes <em>replaces</em> the env list rather than merging). Restore with: <code>kubectl set env deployment/pothole-laureate BROADCAST_BUCKET="$(gcloud config get-value project)-broadcast" -n laureate</code>.
- <strong>"Snoozes don&rsquo;t have a delete operation."</strong> Correct; you terminate a snooze by updating its end-time to now. Snoozes auto-clean after their end-time passes.
</Gotchas>

<Shipped>
<strong>Your Garage has a complete Guardian loop.</strong> Alerts fire, you claim via snooze, broadcast to the team, fix, and clear.
</Shipped>

🛡 **Guardian lane done.** Head to Q3 if your team is waiting, or join wherever they are.

➡️ Next: **Quest 3 — Wire the Pipeline** (sidebar on the left).
