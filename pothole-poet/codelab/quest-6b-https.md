# ✨ Quest 6B — Real HTTPS via Certificate Manager + nip.io

<Objective lane="infra">

**🎯 What you'll do.** Add **real HTTPS** to your Gateway via Certificate Manager **load-balancer authorization** on a `<your-ip>.nip.io` hostname. ~15 min of work + ~10–30 min cert provisioning wait you can spend on something else.

**🤝 Why it matters.** The Foundation URL was plain HTTP. For demo polish the URL needs a green padlock; judges notice. TLS termination is platform substrate, not feature work, which is why this page belongs to **Infra-Admin**, not the App Dev / Guardian who's busy with the Q6A form.

</Objective>

> Make it yours · ~15 min hands-on + ~10–30 min cert provisioning wait · independent of Q6A.

<QuickPath>

```bash
# 1. Get Gateway IP and derive the nip.io hostname
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')
NIP_HOST="${GATEWAY_IP}.nip.io"
echo "Hostname: $NIP_HOST"

# 2. Create the managed cert + cert map (cert provisions async ~10-30 min)
gcloud certificate-manager certificates create pothole-laureate-cert \
  --domains="$NIP_HOST" --location=global

gcloud certificate-manager maps create pothole-laureate-map --location=global

gcloud certificate-manager maps entries create pothole-laureate-entry \
  --map=pothole-laureate-map \
  --certificates=pothole-laureate-cert \
  --hostname="$NIP_HOST" --location=global

# 3. Switch Gateway to the HTTPS overlay
cd ~/quest/pothole-poet/streamlit
sed -i "s/REPLACE_CERTMAP_NAME/pothole-laureate-map/g" k8s/gold/gateway-https.yaml
grep -q REPLACE_CERTMAP_NAME k8s/gold/gateway-https.yaml \
  && echo "WARN: substitution failed" || echo "✅ substitution clean"
kubectl apply -f k8s/gold/gateway-https.yaml

# 4. Poll cert state until ACTIVE (~10-30 min, async)
until [ "$(gcloud certificate-manager certificates describe pothole-laureate-cert --location=global --format='value(managed.state)')" = "ACTIVE" ]; do
  echo "$(date +%H:%M) cert state: PROVISIONING..."; sleep 60
done

# 5. Visit https://$NIP_HOST/ in laptop's browser → green padlock
```

</QuickPath>

The Foundation URL served over plain HTTP. For demo polish, add HTTPS using **Certificate Manager** with **load balancer authorization** and a **nip.io** hostname derived from your Gateway IP.

---

### Step 1 — Get your Gateway IP and derive the nip.io hostname

```bash
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')

NIP_HOST="${GATEWAY_IP}.nip.io"
echo "Hostname: $NIP_HOST"
```

✅ **Expect:** `Hostname: 34.117.42.183.nip.io` (with your real IP)

<Concept title="Why nip.io and load balancer authorization?">

Google-managed certs need to prove you own the domain. The usual mechanism is **DNS authorization**. you add a CNAME record to the parent domain. That requires you to *own* the parent domain, which we don't (no hackathon-owned DNS zone).

**nip.io** is a free wildcard DNS service: `35.190.42.17.nip.io` automatically resolves to `35.190.42.17`. So if your Gateway IP is `35.190.42.17`, the hostname `35.190.42.17.nip.io` already points at your Gateway, no DNS work needed.

**Load balancer authorization** uses **HTTP-01 validation**. Certificate Manager hits port 80 on the LB IP to verify control. It's automatic, requires no DNS changes. Since `<ip>.nip.io` resolves to the IP, the challenge succeeds. No DNS authorization, no parent-zone control, no shared DNS infra.

</Concept>

### Step 2 — Create the managed cert + cert map

```bash
# Managed cert. Default authorization = load balancer (HTTP-01 to port 80).
gcloud certificate-manager certificates create pothole-laureate-cert \
  --domains="$NIP_HOST" \
  --location=global

# Cert map (the Gateway controller's annotation references this).
gcloud certificate-manager maps create pothole-laureate-map \
  --location=global

# Bind the cert to the hostname inside the map.
gcloud certificate-manager maps entries create pothole-laureate-entry \
  --map=pothole-laureate-map \
  --certificates=pothole-laureate-cert \
  --hostname="$NIP_HOST" \
  --location=global
```

✅ **Expect** (three times): `Created [...].`

### Step 3 — Switch the Gateway to the HTTPS overlay

The repo has an HTTPS-overlay manifest at `k8s/gold/gateway-https.yaml` that adds a `:443` HTTPS listener and the `networking.gke.io/certmap` annotation. Substitute your map name and apply.

```bash
cd ~/quest/pothole-poet/streamlit

sed -i "s/REPLACE_CERTMAP_NAME/pothole-laureate-map/g" k8s/gold/gateway-https.yaml
```

✅ **Verify the substitution worked:**

```bash
grep -q REPLACE_CERTMAP_NAME k8s/gold/gateway-https.yaml \
  && echo "WARN: substitution failed" || echo "✅ substitution clean"
```

> If "WARN" appears, the placeholder wasn't found; check `cat k8s/gold/gateway-https.yaml | grep certmap` to see what's there. A silent sed failure here means HTTPS will load with the wrong cert (browser warning).

Apply:

```bash
kubectl apply -f k8s/gold/gateway-https.yaml
```

✅ **Expect:** `gateway.gateway.networking.k8s.io/pothole-gateway configured`

### Step 4 — Wait for the cert to PROVISION (~10-30 min)

The Gateway will keep serving HTTP on :80 the whole time (the HTTP-01 challenge needs that). Cert provisioning is asynchronous.

```bash
until [ "$(gcloud certificate-manager certificates describe pothole-laureate-cert --location=global --format='value(managed.state)')" = "ACTIVE" ]; do
  echo "$(date +%H:%M) cert state: PROVISIONING..."; sleep 60
done
echo "✅ cert ACTIVE"
```

✅ **Expect** (eventually): `✅ cert ACTIVE`

While you wait, help your team, the Guardian may have alerts firing, the App Dev may be wrestling with a Q6A form bug, the Pipeline-author may be tuning DAG cadence.

### Step 5 — Visit the HTTPS URL

Open `https://<your-nip-host>/` in your **laptop's** browser (replace with the value from Step 1, e.g. `https://35.190.42.17.nip.io/`).

✅ **Expect:** Page loads with a valid certificate. No browser warning. Green padlock in the address bar.

**Real HTTPS is live.** No domain registration required.

<Gotchas>
- <strong>Cert stuck on PROVISIONING for &gt;30 min.</strong> Either the Gateway isn&rsquo;t serving HTTP on :80 (the HTTP-01 challenge fails) or the IP doesn&rsquo;t actually resolve to your Gateway. Test: <code>curl http://$NIP_HOST/_stcore/health</code> should return <code>ok</code>; if not, fix that first.
- <strong>Browser warning: cert is for the wrong domain.</strong> The <code>sed</code> didn&rsquo;t substitute the map name, the Gateway is using a different (or no) cert. Re-run Step 3 and verify with the grep check.
- <strong>Confused about which authorization type.</strong> Don&rsquo;t use <code>--dns-authorizations</code> on the cert; that requires owning the parent zone. Omitting it (as in Step 2 above) defaults to load balancer authorization, which is what works for nip.io.
- <strong>Guardian's uptime check now failing on HTTP.</strong> If your Q2E-1 uptime check was set to follow the Gateway IP on HTTP, the HTTPS-only redirect (if you added one) may make it fail. Either keep both listeners open, or re-point the uptime check at <code>https://$NIP_HOST/</code>.
</Gotchas>

<Shipped>
HTTPS is live. <strong>The Pothole Poet now serves over a real HTTPS URL with a Google-managed certificate, with no domain ownership required.</strong> The green padlock costs nothing on judging day. nip.io + LB authorization is a pattern worth keeping in your back pocket for any internal demo.
</Shipped>

**HTTPS is live.** Pair this with Q6A and your demo URL is `https://<ip>.nip.io/` with a fresh ode for whichever neighbourhood the judge picked.

➡️ Next: **Q7 — Differentiate to Win** (sidebar on the left). Your core pipeline is shipped — now use **Antigravity CLI** to push past the tutorial and make your demo the one the judges remember.
