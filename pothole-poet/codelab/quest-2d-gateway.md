# ☸ Quest 2D-5 — Configure the Gateway (Bronze URL goes live)

<Objective lane="infra">

**🎯 What you'll do.** `kubectl apply -f` three manifests — Gateway, HTTPRoute, and a HealthCheckPolicy. Gateway uses GatewayClass `gke-l7-global-external-managed` and binds to the pre-provisioned global static IP `pothole-gateway-ip`. Wait ~5-8 minutes for `PROGRAMMED=True`, then `curl` the IP. **That URL is your Bronze tier.**

**🤝 Why it matters.** This is the moment **your work goes public**. The whole Garage will be watching when this `curl` returns 200 — Bronze is locked in. After this page, the App Dev / Guardian can flip `TIER=SILVER` (Q3) the moment the DAG finishes, and the same URL starts serving live Gemini poems instead of bundled CSV. **Your URL is what the room sees at demo time.**

</Objective>

> Lane D · 5 of 5. ~15 minutes wall-clock (~3 min hands-on).

<QuickPath>

```bash
cd ~/quest/pothole-poet/streamlit

# 1. Apply Gateway + HTTPRoute + HealthCheckPolicy (no substitutions needed)
kubectl apply \
  -f k8s/gateway.yaml \
  -f k8s/httproute.yaml \
  -f k8s/healthcheckpolicy.yaml

# 2. Wait until PROGRAMMED=True (~3-5 min on a fresh cluster)
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

A Pod is reachable inside the cluster but not from the internet. The **Gateway API** is Kubernetes' modern successor to Ingress — same idea (HTTP routing in front of Pods) with cleaner separation of concerns. Apply three YAMLs (Gateway + HTTPRoute + HealthCheckPolicy), wait for the LB to provision, get a public IP, see your app.

---

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

<Concept title="Why these manifests need no substitution">

All three files in `k8s/` ship ready to apply. Three design choices that keep them substitution-free:

- **`gateway.yaml`** uses `addresses: [{type: NamedAddress, value: pothole-gateway-ip}]` — the per-Garage Terraform module pre-provisions a global static IP with that exact name, so the Gateway resolves to a determinate IP on first apply (and the same IP across re-deploys). No env-var substitution.
- **`httproute.yaml`** has no `hostnames` field, which the Gateway API spec interprets as "match all hosts." That's correct for a hackathon where you don't own a domain — you route on IP. When Q6B introduces `<ip>.nip.io`, the same route still works because the cert binding handles host validation at the Cert Manager layer.
- **`httproute.yaml`** also has no `sectionName` on its `parentRefs`, so it attaches to every listener on the Gateway. Bronze has one listener (`http`); Q6B's overlay adds `https` and the same route renders identically on both. No re-apply needed for Gold.

The only file in this lane that needs `sed` is `deployment.yaml` (`REPLACE_PROJECT_ID` for the image path), and Q2D-4 handles that.

</Concept>

<Concept title="Gateway API in three layers + why this GatewayClass">

The Gateway API splits routing into three resources:

1. **GatewayClass** — defines the implementation. We use `gke-l7-global-external-managed`, which means "GCP global external Application Load Balancer" — Anycast IP advertised in every Google region, Premium Network Tier. Pre-installed on every Autopilot cluster.

2. **Gateway** — the actual entry point. It owns the public IP, the listener config (port 80 here), and the TLS settings (none in Bronze/Silver — Q6B adds HTTPS).

3. **HTTPRoute** — routing rules. It says "send any request reaching this Gateway to this backend Service." You can have many HTTPRoutes per Gateway, owned by different teams. That separation is the whole point: platform team owns Gateways, app teams own HTTPRoutes.

**Why `gke-l7-global-external-managed` specifically?** GKE ships ~10 GatewayClasses (regional vs global, external vs internal, single-cluster vs multi-cluster, plus the legacy `gke-l7-gxlb`). Google explicitly recommends `gke-l7-global-external-managed(-mc)` over the legacy `gke-l7-gxlb` for new builds — it supports header rewrites, URL redirects, and the modern security/traffic-management features the legacy class doesn't. For a single-cluster hackathon Pod that needs a public IP, `-managed` is the right default. In a multi-region production deployment you'd reach for the `-mc` variant.

</Concept>

<Concept title="GKE doesn't infer health checks (Ingress did)">

A subtle but important difference between GKE Ingress and GKE Gateway:

- **Ingress** read your Pod's `readinessProbe` and used it for the load balancer health check — automatically.
- **Gateway** does NOT. By default the LB probes `GET /` and expects HTTP 200.

For Streamlit, `GET /` returns the rendered page (a 200, eventually) — but on a cold Pod doing a first BigQuery query that can take 5+ seconds. The LB times out, marks the NEG endpoint unhealthy, and you get *"no healthy upstream"* 503s right when you're trying to demo.

The fix is a **HealthCheckPolicy** — one of the four Policy types in GKE Gateway (the others are `GCPGatewayPolicy`, `GCPBackendPolicy`, and `GCPTrafficDistributionPolicy`). Our `k8s/healthcheckpolicy.yaml` targets the `pothole-laureate` Service by name and tells the LB to probe `/_stcore/health` (Streamlit's built-in liveness endpoint, returns `ok` in under 50 ms) every 15 sec with a 5-sec timeout. NEG endpoints stay healthy through cold starts, and your demo doesn't 503.

</Concept>

### Step 2 — Wait for the load balancer to be PROGRAMMED (~3-5 min)

Watch the Gateway's Programmed condition flip to True:

```bash
kubectl get gateway pothole-gateway -n laureate -w
```

Look for the `PROGRAMMED` column to show `True`. Press Ctrl-C to exit the watch.

✅ **Expect:** `PROGRAMMED True` (3-5 min on first deploy).

<Cheat title="Or poll programmatically (works on all kubectl versions)">

Some older kubectl versions don't show the `PROGRAMMED` column. Use this instead:

```bash
until [ "$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.conditions[?(@.type=="Programmed")].status}')" = "True" ]; do
  echo "$(date +%H:%M) still provisioning..."; sleep 30
done
echo "✅ PROGRAMMED"
```

If the wait drags past 8 min, drop into `kubectl describe gateway pothole-gateway -n laureate` and read the **Conditions** + **Events** sections — they usually show the actual error.

</Cheat>

<Concept title="Programmed vs Ready conditions — which do I trust?">

If you `kubectl describe gateway` you'll see both a `Programmed` condition AND a `Ready` condition, both showing `Status: True`. Why two?

`Ready` is **deprecated** in the OSS Gateway API spec ("The OSS Gateway API has altered the 'Ready' condition semantics and reserved it for future use. GKE Gateway will stop emitting it in a future update"). It's still emitted today for backward compatibility but will go away. **Always check `Programmed`.**

`Programmed: True` means the GKE Gateway controller has reconciled the manifest into actual GCP Compute resources (forwarding rule, target proxy, URL map, backend service, health check) and the load balancer is serving traffic. That's the only signal that matters for "is my Gateway live?"

</Concept>

> *What's happening behind the scenes:* the Gateway controller is creating a forwarding rule, target proxy, URL map, backend service, and health check pointing at the NEGs your Service annotation registered.

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

> If you get `404 default backend - 404`: the Gateway is up but the HTTPRoute hasn't attached yet. Run `kubectl describe httproute pothole-route -n laureate` and check the **Parents** → **Conditions** section for `Accepted: True`. Wait 30 sec and re-curl.

### Step 5 — Open it in your laptop's browser

In your **laptop's** browser (the Workstation has no browser), open:

```
http://<your-gateway-ip>/
```

✅ **Expect:** The Bronze Office page loads — header, 12 neighbourhoods, placeholder poems, dataframe.

🥉 **You just shipped Bronze.**

<Screenshot caption="Bronze Streamlit page served via GKE Gateway: header, 12 neighbourhoods, dataframe view." />

### Step 6 — While you wait for the rest of the Garage

The HTTPRoute has no hostname match — any request to the IP routes to your Streamlit Service. That's fine for Bronze/Silver. In Q6B you'll add HTTPS and use `<ip>.nip.io` as the hostname.

Pair with the Data Engineer and Pipeline-author: when they finish, the DAG triggers and `pothole_laureate.neighbourhood_odes` populates. Then Quest 3 swaps your `TIER` env var from BRONZE to SILVER (one `kubectl set env`) and the same Pods read live data instead of the bundled CSV.

<Gotchas>
- <strong>Gateway stays <code>PROGRAMMED=False</code> for &gt;7 min.</strong> Run <code>kubectl describe gateway pothole-gateway -n laureate</code> &mdash; the Events section usually shows the actual error (firewall, missing NEG, IAM).
- <strong>External IP empty.</strong> The pre-provisioned static IP <code>pothole-gateway-ip</code> may not exist. Check <code>gcloud compute addresses list --global --filter="name=pothole-gateway-ip"</code>. If missing, flag a Sherpa &mdash; it&rsquo;s in the per-Garage Terraform.
- <strong><code>404 default backend - 404</code> on the LB IP.</strong> The Gateway is up but the HTTPRoute hasn&rsquo;t attached yet. <code>kubectl describe httproute pothole-route -n laureate</code> &mdash; look for <code>Accepted: True</code> in the Parents section. If <code>False</code>, the reason is shown there (usually the parentRef name doesn&rsquo;t match the Gateway). Wait 30 sec and refresh.
- <strong><code>no healthy upstream</code> / 503s once traffic arrives.</strong> The LB&rsquo;s health check is probing the wrong path or your Pods are slow to respond. Confirm the HealthCheckPolicy applied: <code>kubectl get healthcheckpolicy -n laureate</code> &mdash; should list <code>pothole-laureate-hc</code>. If it&rsquo;s missing, <code>kubectl apply -f k8s/healthcheckpolicy.yaml</code>. Without it the LB defaults to <code>GET /</code> which on Streamlit triggers a full page render and can flap on cold Pods.
- <strong>Tried to edit the <code>cloud.google.com/neg</code> annotation on the Service.</strong> Don&rsquo;t. Per the official Gateway API docs: <em>"you cannot modify the cloud.google.com/neg annotation for a Service that is part of the Gateway."</em> If you need to change exposed ports, delete + recreate the Service (and the Gateway controller will re-attach).
- <strong>HTTPRoute has no effect.</strong> <code>kubectl describe httproute pothole-route -n laureate</code> shows attachment status. Look for <code>Accepted: True</code> in the parents conditions. If <code>Reason: NoMatchingParent</code>, the parentRef name (or namespace) is wrong.
- <strong>Page loads in your browser but the dataframe is empty, or the Pod crashes with <code>FileNotFoundError: '/seed/pothole_reports.csv'</code>.</strong> The image was built from <code>streamlit/</code> instead of <code>pothole-poet/</code>, so the sibling <code>seed/</code> directory wasn&rsquo;t in the build context. Re-do Q2D-2 with the correct <code>cd</code>.
- <strong>You opened the URL in the Workstation IDE preview pane.</strong> The Workstation has no browser &mdash; the preview pane doesn&rsquo;t reach external IPs. Open the URL in your <em>laptop&rsquo;s</em> browser.
</Gotchas>

<Shipped>
Bronze is on the board. <strong>A public URL on a Google Cloud global load balancer serves the Office page with all 12 neighbourhoods, with NEG endpoints health-checked against Streamlit&rsquo;s real liveness endpoint.</strong> The Garage now has a guaranteed demo &mdash; even if the DAG, federation, or AlloyDB fall over, this URL is your safety net.
</Shipped>

---

## Going further (after Bronze)

Six things you'd reach for in production but we don't need today. Pointers, not prescriptions:

- **HealthCheckPolicy tuning** — adjust `checkIntervalSec`, `timeoutSec`, `healthyThreshold`, `unhealthyThreshold` for your traffic profile. [HealthCheckPolicy API ref](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources#configure_gateway_resources_using_policies).
- **GCPBackendPolicy** — advanced traffic distribution: session affinity, locality-aware load balancing, custom request headers per backend, the `CUSTOM_METRICS` balancing mode driven by ORCA load reports from your app. [GCPBackendPolicy docs](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources#configure_traffic_management).
- **GCPGatewayPolicy** — frontend tuning: SSL profiles, request/response timeouts, connection draining. [GCPGatewayPolicy docs](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources#configure_load_balancers).
- **HTTP→HTTPS redirect** — once Q6B gives you HTTPS, add a `RequestRedirect` filter on the HTTPRoute so port-80 traffic auto-bounces to port 443. [Configuring HTTP-to-HTTPS redirects](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/deploying-gateways#configure_http-to-https_redirects).
- **URL rewrites + path redirects** — `URLRewrite` and `RequestRedirect` filters on HTTPRoute let you do `/old/*` → `/new/*` at the LB without app changes. [Path redirects and URL rewrites](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/deploying-gateways#configure_path_redirects_and_url_rewrites).
- **Multi-cluster Gateways** (`gke-l7-global-external-managed-mc`) — one Gateway, many GKE clusters across regions, traffic routed to the closest healthy backend. [Deploying multi-cluster Gateways](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/deploying-multi-cluster-gateways).
- **ReferenceGrant for cross-namespace routing** — when an HTTPRoute in namespace `frontend` needs to point at a Service in namespace `backend`, you create a `ReferenceGrant` in `backend` permitting the cross-namespace reference. [ReferenceGrant docs](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/gateway-api#referencegrant).

The full GKE Gateway API guide: [docs.cloud.google.com/kubernetes-engine/docs/concepts/gateway-api](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/gateway-api).

---

☸ **Lane D done (Bronze tier).** Five pages, one cluster, one image, one identity, four manifests, one global LB, one health-checked NEG. Now wait for the Pipeline-author + Data Engineer to finish. When the DAG is green, head to Quest 3 to swap the data source from CSV to BigQuery (one env var change + one rolling restart).

➡️ Next: **Quest 3 — Wire the Pipeline** (sidebar on the left).
