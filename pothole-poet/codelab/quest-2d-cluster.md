# ☸ Quest 2D-1 — Stand Up the GKE Autopilot Cluster

<Objective lane="infra">

**🎯 What you'll do.** Run a single `gcloud container clusters create-auto` command to spin up a regional GKE Autopilot cluster called `laureate-cluster` with `--enable-private-nodes`. ~6-8 minutes of waiting. While it provisions, capture `PROJECT_ID` + `PROJECT_NUMBER` (you'll need both for Q2D-3).

**🤝 Why it matters.** This cluster is **the runtime your Streamlit app will live on for the rest of the day**. Every other Q2D page (image build, identity binding, deploy, gateway) targets this cluster. The `--enable-private-nodes` flag is non-negotiable in your Garage's project — the Volvo Cars org policy blocks public-IP nodes — and forgetting it costs you 8 minutes when the create fails halfway. Get the click right the first time.

</Objective>

> Lane D · 1 of 5. ~10 minutes wall-clock (~2 min hands-on).

<QuickPath>

```bash
# 1. Capture project identifiers (you'll need PROJECT_NUMBER for Q2D-3)
export PROJECT_ID="$(gcloud config get-value project)"
export PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
export REGION="europe-west1"
echo "PROJECT_ID=$PROJECT_ID  PROJECT_NUMBER=$PROJECT_NUMBER"

# 2. Create the Autopilot cluster (~6-8 min)
gcloud container clusters create-auto laureate-cluster \
  --region=$REGION \
  --enable-private-nodes \
  --release-channel=regular

# 3. Verify cluster is RUNNING
gcloud container clusters describe laureate-cluster \
  --region=$REGION --format='value(status)'
# ✅ Expect: RUNNING
```

</QuickPath>

Your Streamlit app needs a **runtime** — somewhere a container can run, reachable from the public internet, with the ability to call other GCP services on the Garage's behalf. **GKE Autopilot** is Google's managed Kubernetes mode: production-grade orchestration with the operational overhead stripped out.

---

### Step 1 — Capture project identifiers

In your Workstation terminal, set the variables you'll reuse across all five Q2D pages:

```bash
export PROJECT_ID="$(gcloud config get-value project)"
export PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
export REGION="europe-west1"

echo "PROJECT_ID=$PROJECT_ID  PROJECT_NUMBER=$PROJECT_NUMBER"
```

✅ **Expect:** Both values printed. `PROJECT_NUMBER` is all digits (12 digits, looks like `624958632298`); `PROJECT_ID` is human-readable (lowercase + digits + hyphens, matches the value on your workbench card).

> Both values are needed for the Workload Identity binding in Q2D-3. **They are different identifiers for the same project** — mixing them up in Q2D-3 is the single most expensive mistake in the day. Capture them both now and never substitute one for the other.

### Step 2 — Create the cluster

The single command below creates a regional Autopilot cluster with private nodes (the project's org policy forbids public-IP nodes — outbound to Google APIs goes via Private Google Access, no NAT involved).

```bash
gcloud container clusters create-auto laureate-cluster \
  --region=$REGION \
  --enable-private-nodes \
  --release-channel=regular
```

✅ **Expect** (after ~6-8 min): `Created [https://container.googleapis.com/v1/projects/<id>/locations/europe-west1/clusters/laureate-cluster]`

> **Don't sit and watch it.** Read Step 3 while it provisions.

<Concept title="What does Autopilot do for me that Standard GKE doesn't?">

A Standard GKE cluster gives you Kubernetes plus a pile of operational chores: sizing nodes, patching them, configuring autoscalers, hardening images, deciding bin-packing strategies. **Autopilot** removes all of that. You write Pod specs; Google provisions the right node shapes on demand and bills you per-pod (CPU/memory/storage you actually requested), not per-node.

The trade is some flexibility — no SSH to nodes, no privileged Pods, no kernel modules, a fixed set of allowed images. For typical web workloads (including this one) those constraints don't matter and the operational savings are large. Autopilot is Google's recommended default for new clusters.

</Concept>

<Concept title="What does --enable-private-nodes actually do?">

By default, GKE nodes get a public IP and become directly reachable from the internet. **Private nodes** keep them on internal-only IPs — no public surface to scan, no risk of a misconfigured Pod accidentally accepting outside traffic. This Quest enforces it (the project's `compute.vmExternalIpAccess` org policy refuses to provision public-IP nodes at all).

Private nodes still need a way to reach Google APIs — pulling images from Artifact Registry, talking to BigQuery, fetching tokens from the metadata server. **Private Google Access** handles that: it's auto-enabled on Autopilot's private-node subnet, and routes traffic to any `*.googleapis.com` endpoint over Google's internal network without a public IP. No NAT, no firewall plumbing.

**There is no general-purpose internet egress.** The per-Garage Terraform module deliberately omits Cloud NAT to mimic a secure corporate environment — your Pods can reach Google APIs and that's it. If your app needs to call a third-party webhook or a non-Google public API, it won't work; route that traffic via a Google service (e.g. Cloud Functions / Workflows with their own egress) instead.

</Concept>

### Step 3 — While you wait (~6-8 min): be useful

a) **Skim the Streamlit code.** In your Workstation IDE, open `pothole-poet/streamlit/app.py`. Note:
- The `TIER` env var at the top — controls Bronze / Silver / Gold mode.
- The `# TEAM CANVAS` block near the bottom — that's where Quest 4 lives. **Don't edit it now.**
- `pothole-poet/Dockerfile` — vanilla Python + Streamlit, listens on 8080. It lives one directory up from `streamlit/` so the Bronze seed CSV is in the build context.

b) **Look at the manifests.** In `pothole-poet/streamlit/k8s/`, you'll see five YAMLs you'll apply across Q2D-3 to Q2D-5: `namespace-and-sa.yaml`, `deployment.yaml`, `service.yaml`, `gateway.yaml`, `httproute.yaml`. We'll explain each as you apply it.

c) **Pair with the Data Engineer.** They're standing up AlloyDB + the BigQuery dataset (`pothole_laureate`) + the AlloyDB federation. Once both work, your data path is ready end-to-end — your Pod will read `pothole_laureate.neighbourhood_odes` once the Pipeline-author's DAG populates it.

### Step 4 — Verify cluster is RUNNING

```bash
gcloud container clusters describe laureate-cluster \
  --region=$REGION --format='value(status)'
```

✅ **Expect:** `RUNNING`

In the Console (`https://console.cloud.google.com/kubernetes/list/overview?project=$PROJECT_ID`), the cluster shows green health.

<Gotchas>
- <strong>Create command fails with <code>org policy compute.vmExternalIpAccess</code>.</strong> You forgot <code>--enable-private-nodes</code>. Re-run with the flag.
- <strong>Stuck on PROVISIONING for &gt;12 min.</strong> Check the Console's <strong>Kubernetes Engine &rarr; Operations</strong> tab for an error. Past 15 min, flag a Sherpa.
- <strong><code>command not found: gcloud</code>.</strong> You&rsquo;re in a Cloud Shell, not the Workstation. Open the Workstation terminal instead &mdash; <code>gcloud</code> is preinstalled there.
- <strong><code>Insufficient quota</code> errors.</strong> Autopilot uses E2 nodes from the project&rsquo;s default quota. If hit, flag a Sherpa &mdash; the platform pre-allocates enough but a stale Garage may still be holding nodes.
- <strong><code>PROJECT_NUMBER</code> empty in Step 1.</strong> Make sure <code>gcloud config get-value project</code> returns your Garage&rsquo;s project_id (from your workbench card). If it&rsquo;s blank or a different project, run <code>gcloud config set project &lt;your-project-id&gt;</code> first.
</Gotchas>

<Shipped>
The runtime is up. <strong>GKE Autopilot cluster <code>laureate-cluster</code> is RUNNING in <code>europe-west1</code>, ready to host workloads.</strong> No nodes for you to manage; Google handles that.
</Shipped>

☸ **Q2D-1 done.** Cluster live but empty.

➡️ Next: **Q2D-2 — Build the Container Image** (sidebar on the left).
