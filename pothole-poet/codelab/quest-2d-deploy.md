# ☸ Quest 2D-4 — Deploy the Workload

<Objective lane="guardian">

**🎯 What you'll do.** `kubectl apply -f` the Deployment + Service manifests from `streamlit/k8s/`. Wait for two Pods to reach `Running`. The Service is `ClusterIP` with a NEG annotation, internal-only for now, no public URL yet. ~5 minutes including the image pull from Artifact Registry.

**🤝 Why it matters.** This is the **first time your code actually runs on real infrastructure**. The two Pods need to be Running before the next page (Gateway) can route traffic to them. The NEG annotation on the Service is what lets Google's global load balancer plug straight into your Pods; it's not magic, but it does have to be set right *now*, not later.

</Objective>

> Lane D · 4 of 5. ~5 minutes hands-on.

<QuickPath>

```bash
cd ~/quest/pothole-poet/streamlit

# 1. Substitute project ID into deployment.yaml (idempotent — safe to re-run)
sed -i "s/REPLACE_PROJECT_ID/$PROJECT_ID/g" k8s/deployment.yaml
grep -q REPLACE_PROJECT_ID k8s/deployment.yaml && echo "WARN: substitution failed" || echo "✅ substitution clean"

# 2. Apply Deployment + Service
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
# ✅ Expect: deployment.apps/pothole-laureate created  +  service/pothole-laureate created

# 3. Wait for Pods Ready (~1-3 min on a fresh Autopilot)
kubectl wait --for=condition=Ready pod -l app=pothole-laureate -n laureate --timeout=300s
# ✅ Expect: 2 pods condition met

# 4. Confirm Streamlit started
kubectl logs -n laureate -l app=pothole-laureate --tail=10
# ✅ Expect: "You can now view your Streamlit app in your browser." + "URL: http://0.0.0.0:8080"
```

</QuickPath>

In Kubernetes, a **Deployment** describes "I want N copies of this container running, and please keep them running." A **Service** gives those Pods a stable in-cluster DNS name (so the Gateway in Q2D-5 can reach them by name instead of by ever-changing Pod IPs).

---

### Step 1 — Substitute your project ID into deployment.yaml

The `deployment.yaml` ships with `REPLACE_PROJECT_ID` placeholders for the image path and the `PROJECT_ID` env var. `sed` does both in one command.

```bash
cd ~/quest/pothole-poet/streamlit

sed -i "s/REPLACE_PROJECT_ID/$PROJECT_ID/g" k8s/deployment.yaml
```

✅ **Verify the substitution worked:**

```bash
grep -q REPLACE_PROJECT_ID k8s/deployment.yaml && echo "WARN: substitution failed" || echo "✅ substitution clean"
```

> Re-running `sed` is harmless, once the placeholder is gone there's nothing left to substitute. If you see "WARN: substitution failed", check that `$PROJECT_ID` is set (`echo $PROJECT_ID`).

### Step 2 — Apply Deployment + Service

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
```

✅ **Expect:**
- `deployment.apps/pothole-laureate created`
- `service/pothole-laureate created`

<Concept title="Deployment vs Pod vs Service: what's what?">

A **Pod** is the unit of execution: one or more containers sharing a network namespace. You almost never create Pods directly.

A **Deployment** is a controller that says "keep N Pods of this template alive." If a Pod crashes, the Deployment replaces it. If you change the Deployment's image, it does a rolling update.

A **Service** is a stable network endpoint. It selects Pods by label and load-balances traffic across them. ClusterIP (which we use) means "reachable only from inside the cluster"; that's fine because the Gateway will be the public entry point.

</Concept>

<Concept title="The NEG annotation in service.yaml">

You'll see this annotation on the Service:

```
cloud.google.com/neg: '{"exposed_ports": {"8080":{}}}'
```

**NEG** = Network Endpoint Group. It tells the GKE Gateway controller to use **container-native load balancing**. the Google LB sends traffic directly to Pod IPs, skipping the kube-proxy hop. Faster, fewer moving parts. Required for the Gateway in Q2D-5 to work properly.

</Concept>

### Step 3 — Wait for Pods Ready

On a fresh Autopilot cluster the FIRST Pod takes 30-90 sec because Autopilot has to provision a node first. Subsequent Pods come up in seconds.

```bash
kubectl wait --for=condition=Ready pod -l app=pothole-laureate -n laureate --timeout=300s
```

✅ **Expect:** `pod/pothole-laureate-<hash> condition met` (twice, once per Pod)

If you'd rather watch the progression:

```bash
kubectl get pods -n laureate -w
# Press Ctrl-C once both show 1/1 Running.
```

### Step 4 — Confirm Streamlit started

```bash
kubectl logs -n laureate -l app=pothole-laureate --tail=10
```

✅ **Expect** (in the log output):
- `You can now view your Streamlit app in your browser.`
- `URL: http://0.0.0.0:8080`

<Gotchas>
- <strong>Pods stuck <code>Pending</code> for &gt;3 min.</strong> Autopilot is provisioning a node; first Pod on a fresh cluster takes 30-90 sec extra. Past 3 min: <code>kubectl describe pod &lt;pod-name&gt; -n laureate | grep -A20 Events</code>. the bottom of the output shows the actual scheduling failure.
- <strong><code>ImagePullBackOff</code>.</strong> Either you forgot to push the image (Q2D-2) or the <code>sed</code> didn&rsquo;t substitute. Re-check with: <code>grep REPLACE_PROJECT_ID k8s/deployment.yaml</code> (should be empty) and <code>gcloud artifacts docker images list europe-west1-docker.pkg.dev/$PROJECT_ID/laureate</code>.
- <strong>Pods <code>CrashLoopBackOff</code>, logs say <code>permission denied</code> on BigQuery.</strong> Q2D-3 IAM binding has the wrong principal, usually <code>PROJECT_ID</code>/<code>PROJECT_NUMBER</code> mixed up. Re-run the Q2D-3 sanity check.
- <strong>Pods Ready but only one of two.</strong> Autopilot may take longer for the second Pod if it needs a new node. Wait 1-2 min more.
- <strong>Pods Ready but logs are empty.</strong> First-time Streamlit logs can take ~10 sec to flush. Re-run <code>kubectl logs</code> with <code>--tail=50</code>.
- <strong>Pod keeps crashing and <code>kubectl logs</code> only shows the last restart.</strong> Open the Logs Explorer (Q1-5) and filter: Resource Type = <code>k8s_container</code>, then namespace = <code>laureate</code> in the Fields pane. Cloud Logging retains logs from previous Pod restarts that <code>kubectl logs</code> does not.
</Gotchas>

<Shipped>
The workload is live. <strong>Two Streamlit Pods are running in the cluster, serving the Office page with seed data, ready to take traffic.</strong> Reachable from inside the cluster via DNS <code>pothole-laureate.laureate.svc.cluster.local:8080</code>. Not yet reachable from the internet; that&rsquo;s the next page.
</Shipped>

☸ **Q2D-4 done.** Pods running, but the world can't see them yet.

➡️ Next: **Q2D-5 — Configure the Gateway** (sidebar on the left).
