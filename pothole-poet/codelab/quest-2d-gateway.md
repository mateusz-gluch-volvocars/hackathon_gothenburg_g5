# ☸ Quest 2D-5 — Configure the Gateway (your URL goes live)

<Objective lane="infra">

**🎯 What you'll do.** `kubectl apply` three manifests: Gateway, HTTPRoute, and HealthCheckPolicy. The Gateway binds to the pre-provisioned global static IP `pothole-gateway-ip` and uses GatewayClass `gke-l7-global-external-managed` (Google's global external Application Load Balancer). Wait ~3-5 minutes for the LB to provision, then `curl` the IP. **That URL is your Garage's public endpoint.**

**🤝 Why it matters.** This is the moment **your work goes public**. The whole Garage will be watching when this `curl` returns 200; the Foundation URL is live. After this page, the App Dev / Guardian can switch `MODE=live` (Q3) the moment the DAG finishes, and the same URL starts serving real Gemini poems instead of bundled CSV. **Your URL is what the room sees at demo time.**

</Objective>

> Lane D · 5 of 5. ~15 minutes wall-clock (~3 min hands-on).

<QuickPath>

```bash
cd ~/quest/pothole-poet/streamlit

# 1. Apply Gateway + HTTPRoute + HealthCheckPolicy
kubectl apply \
  -f k8s/gateway.yaml \
  -f k8s/httproute.yaml \
  -f k8s/healthcheckpolicy.yaml

# 2. Wait until Programmed=True (~3-5 min on a fresh cluster)
until [ "$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.conditions[?(@.type=="Programmed")].status}')" = "True" ]; do
  echo "$(date +%H:%M) still provisioning..."; sleep 30
done

# 3. Get the public IP
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.addresses[0].value}')
echo "Public URL: http://$GATEWAY_IP/"

# 4. Smoke-test the health endpoint
curl -s "http://$GATEWAY_IP/_stcore/health"
# ✅ Expect: ok

# 5. Open http://$GATEWAY_IP/ in your laptop's browser (Workstation has no browser)
```

</QuickPath>

A Pod is reachable inside the cluster but not from the internet. The **Gateway API** is Kubernetes' standard for HTTP routing in front of Pods: a **Gateway** owns the public IP and listener config, an **HTTPRoute** tells it where to send traffic, and a **HealthCheckPolicy** tells the load balancer how to probe your Pods. Apply three YAMLs, wait for the LB, get a public IP, see your app.

---

<Callout type="critical" title="Use these exact names — later steps depend on them">

The cluster name `laureate-cluster` is referenced by kubectl commands across Q2D-3 through Q6. **We strongly recommend using the defaults.** If you chose a different name in Q2D-1, click any highlighted name in the code blocks (look for the gold underline); your change propagates across all pages automatically.

</Callout>

### Step 1 — Apply Gateway + HTTPRoute + HealthCheckPolicy

```bash
cd ~/quest/pothole-poet/streamlit

kubectl apply \
  -f k8s/gateway.yaml \
  -f k8s/httproute.yaml \
  -f k8s/healthcheckpolicy.yaml
```

✅ **Expect:**
- `gateway.gateway.networking.k8s.io/pothole-gateway created`
- `httproute.gateway.networking.k8s.io/pothole-route created`
- `healthcheckpolicy.networking.gke.io/pothole-laureate-hc created`

<Concept title="Why do we need a HealthCheckPolicy?">

GKE Gateway does **not** infer health check parameters from your Pod's readiness probe (unlike the older GKE Ingress). By default the load balancer probes `GET /` and expects HTTP 200. For Streamlit, `GET /` triggers a full page render that can take 5+ seconds on a cold Pod; the LB times out, marks the endpoint unhealthy, and you get 503s right when you're trying to demo.

The `healthcheckpolicy.yaml` tells the LB to probe `/_stcore/health` (Streamlit's built-in liveness endpoint, returns `ok` in under 50 ms) every 15 sec. Endpoints stay healthy through cold starts, and your demo does not 503.

</Concept>

### Step 2 — Wait for the load balancer to be Programmed (~3-5 min)

Check the Gateway status with `describe`:

```bash
kubectl describe gateway pothole-gateway -n laureate
```

Scroll to the **Status > Conditions** section. Look for `Programmed` with `Status: True`. That means the GKE Gateway controller has created all the GCP Compute resources (forwarding rule, target proxy, URL map, backend service, health check) and the load balancer is serving traffic.

If `Programmed` is not yet `True`, wait 30 seconds and re-run.

<Cheat title="Poll programmatically instead of re-running describe">

```bash
until [ "$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.conditions[?(@.type=="Programmed")].status}')" = "True" ]; do
  echo "$(date +%H:%M) still provisioning..."; sleep 30
done
echo "✅ PROGRAMMED"
```

If the wait drags past 8 min, re-run `kubectl describe gateway pothole-gateway -n laureate` and read the **Events** section; it usually shows the actual error.

</Cheat>

### Step 3 — Get the public IP

```bash
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')

echo "Public URL: http://$GATEWAY_IP/"
```

✅ **Expect:** A real public IPv4 like `34.117.42.183`.

### Step 4 — Smoke-test the health endpoint

```bash
curl -s "http://$GATEWAY_IP/_stcore/health"
```

✅ **Expect:** `ok`

> If you get `404 default backend - 404`: the Gateway is up but the HTTPRoute hasn't attached yet. Run `kubectl describe httproute pothole-route -n laureate` and check the **Parents > Conditions** section for `Accepted: True`. Wait 30 sec and re-curl.

### Step 5 — Open it in your laptop's browser

In your **laptop's** browser (the Workstation has no browser), open:

```
http://<your-gateway-ip>/
```

✅ **Expect:** The Office page loads: header, 12 neighbourhoods, placeholder poems, dataframe.

**Your Garage's public URL is live.**

<Screenshot src="/quest/pothole-poet/img/streamlit_bronze.png" caption="Streamlit page served via GKE Gateway: header, 12 neighbourhoods, dataframe view (seed data)." />

### Step 6 — While you wait for the rest of the Garage

Pair with the Data Engineer and Pipeline-author: when they finish, the DAG triggers and `pothole_laureate.neighbourhood_odes` populates. Then Quest 3 swaps your `MODE` env var from `seed` to `live` (one `kubectl set env`) and the same Pods read live data instead of the bundled CSV.

<Gotchas>
- <strong>Gateway stays <code>Programmed=False</code> for &gt;7 min.</strong> Run <code>kubectl describe gateway pothole-gateway -n laureate</code>. The Events section usually shows the actual error (firewall, missing NEG, IAM).
- <strong>External IP empty.</strong> The pre-provisioned static IP <code>pothole-gateway-ip</code> may not exist. Check <code>gcloud compute addresses list --global --filter="name=pothole-gateway-ip"</code>. If missing, flag a Sherpa; it is in the per-Garage Terraform.
- <strong><code>404 default backend - 404</code> on the LB IP.</strong> The Gateway is up but the HTTPRoute has not attached yet. <code>kubectl describe httproute pothole-route -n laureate</code>: look for <code>Accepted: True</code> in the Parents section. If <code>False</code>, the reason is shown there (usually the parentRef name does not match the Gateway). Wait 30 sec and refresh.
- <strong><code>no healthy upstream</code> / 503s once traffic arrives.</strong> The LB health check is probing the wrong path or your Pods are slow to respond. Confirm the HealthCheckPolicy applied: <code>kubectl get healthcheckpolicy -n laureate</code> should list <code>pothole-laureate-hc</code>. If missing, <code>kubectl apply -f k8s/healthcheckpolicy.yaml</code>.
- <strong>Do not edit the <code>cloud.google.com/neg</code> annotation on the Service.</strong> Per the official Gateway API docs: you cannot modify the NEG annotation for a Service that is part of the Gateway. If you need to change exposed ports, delete and recreate the Service.
- <strong>Page loads but the dataframe is empty.</strong> The image was built from <code>streamlit/</code> instead of <code>pothole-poet/</code>. Re-do Q2D-2 with the correct <code>cd</code>.
- <strong>You opened the URL in the Workstation IDE preview pane.</strong> The Workstation has no browser; the preview pane does not reach external IPs. Open the URL in your <em>laptop's</em> browser.
- <strong>Issues you cannot diagnose from <code>kubectl describe</code> alone.</strong> Open the Logs Explorer (Q1-6) and filter: Resource Type = <code>k8s_cluster</code> for LB events, or <code>k8s_container</code> with namespace = <code>laureate</code> for Pod-level errors.
</Gotchas>

<Shipped>
The URL is on the board. <strong>A public URL on a Google Cloud global load balancer serves the Office page with all 12 neighbourhoods, health-checked against Streamlit's real liveness endpoint.</strong> The Garage now has a guaranteed demo; even if the DAG or AlloyDB fall over, this URL is your safety net.
</Shipped>

---

☸ **Q2D-5 done.** Your public URL is live. While you wait for the other lanes to finish, continue with the Guardian observability pages (Q2E) to set up monitoring on the URL you just shipped.

➡️ Next: **Q2E-1 — Uptime Check** (sidebar on the left).
