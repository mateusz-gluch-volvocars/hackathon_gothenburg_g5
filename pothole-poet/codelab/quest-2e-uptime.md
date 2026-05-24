# 🛡 Quest 2E-1 — The Guardian's First Light: an Uptime Check

<Objective lane="guardian">

**🎯 What you'll do.** Stand up a **Cloud Monitoring uptime check** on the Streamlit Gateway in ~10 min. One gcloud command (or Console click-through, your choice). This is the first piece of the **App Dev / Guardian** lane: until something is being watched, nobody on your Garage knows whether the Bronze URL is actually staying alive.

**🤝 Why it matters.** Every operational dashboard worth running starts with the question "is the thing up?". A green uptime check is your team's heartbeat — your Pipeline-author can see it; your Data Engineer can see it; your Infra-Admin can see it. The Guardian lane exists so somebody on the team owns the answer.

</Objective>

> Bronze tier · ~10 min hands-on · runs in parallel with your Infra-Admin's Q2D-5 Gateway provisioning.

<QuickPath>

```bash
# 1. Wait for Infra-Admin's Gateway to have an IP (Q2D-5 Step 3)
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')
[ -z "$GATEWAY_IP" ] && { echo "Gateway IP not ready yet — wait for Q2D-5"; exit 1; }
echo "Gateway IP: $GATEWAY_IP"

# 2. Create the uptime check
gcloud monitoring uptime create pothole-laureate-uptime \
  --resource-type=uptime-url \
  --resource-labels="host=${GATEWAY_IP},project_id=$(gcloud config get-value project)" \
  --protocol=http \
  --path="/_stcore/health" \
  --period=1m \
  --timeout=10s \
  --status-codes=200

# 3. Verify it exists
gcloud monitoring uptime list-configs \
  --filter="displayName=pothole-laureate-uptime" \
  --format="value(name,httpCheck.path)"
# ✅ Expect: one line — uptime check name + /_stcore/health
```

Within 1-2 min the check turns green across all 6 probe regions. Open `Console → Monitoring → Uptime checks` to watch.

</QuickPath>

Healthy operational systems have a person whose job is to claim failures, snooze noisy alerts, and broadcast "yes, I see it" to the team. **Your team can't have any of that without an uptime check first.** This page builds the smallest possible version: one HTTP probe against the Gateway, every minute, from multiple regions.

---

### Step 1 — Confirm the Gateway has an IP

Until the Gateway is up, there's nothing to probe.

```bash
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')
echo "Gateway IP: $GATEWAY_IP"
```

✅ **Expect:** A real IPv4 address (e.g. `34.117.42.183`).

If blank, your Infra-Admin hasn't finished Q2D-5 yet (the Gateway takes 5-15 min to PROGRAM on a fresh Autopilot). Pre-position by reading the Volvo Flow-Guardian role definition in `help.mdx`, then come back when they have an IP.

### Step 2 — Create the uptime check

```bash
gcloud monitoring uptime create pothole-laureate-uptime \
  --resource-type=uptime-url \
  --resource-labels="host=${GATEWAY_IP},project_id=$(gcloud config get-value project)" \
  --protocol=http \
  --path="/_stcore/health" \
  --period=1m \
  --timeout=10s \
  --status-codes=200
```

✅ **Expect:** `Created uptime check [projects/<id>/uptimeCheckConfigs/pothole-laureate-uptime].`

<Cheat title="Or use the GKE-native UX in the Console">

The 2026 GKE Console added a "Create uptime check" button on the Service detail page that auto-fills the IP:

1. Console → **Kubernetes Engine** → **Services & Ingress** → click `pothole-laureate` (in the `laureate` namespace).
2. Scroll to the **Endpoints** card → click **Create uptime check**.
3. Fill in the form — the IP and path are pre-populated. Click **Test** before saving (one-shot probe). Click **Create**.

Note the Console says "URL" where gcloud says `uptime-url` — same resource type.

</Cheat>

<Concept title="Why does the Guardian start before the Gateway is ready?">

Pure pacing. Your Infra-Admin's Q2D-5 (Gateway provisioning + PROGRAMMED state) takes 5–15 min on a fresh Autopilot cluster. If you wait until that's done, you've burned 15 min idle. Instead, set the uptime check up *now* — the moment the Gateway flips to PROGRAMMED, your check goes green, and you've already saved your team 10 minutes.

This is the Guardian rhythm: **be ready before things break, be available before things go live.**

</Concept>

### Step 3 — Verify the check exists

```bash
gcloud monitoring uptime list-configs \
  --filter="displayName=pothole-laureate-uptime" \
  --format="value(name,httpCheck.path)"
```

✅ **Expect:** One line — the check's full name + `/_stcore/health`.

### Step 4 — Watch it go green

Open **Console → Monitoring → Uptime checks** → click `pothole-laureate-uptime`.

✅ **Expect** (within 1-2 min): Green checkmarks across all 6 probe regions. Last latency: 100-400 ms.

<Screenshot src="/quest/pothole-poet/img/monitoring_uptime.png" caption="Cloud Monitoring uptime check overview: pothole-laureate-uptime, green across 6 regions, 1-minute frequency." />

### Step 5 — While you wait: be useful

The check fires every minute, but it can take a few min for all 6 regions to converge. While you wait:

1. **Read the Guardian role description** in `help.mdx` (the help link at the top of this page). Skim the "Flow-Guardian" glossary entry so you know what rhythm Q2E-3 is going to make you do.
2. **Decide a Guardian-of-the-day handle** — pick something short (`@anna`, `@karl`). You'll use it in the broadcast banner in Q2E-3.
3. **Pre-position for Q2E-2** — open `streamlit/app.py` in your Workstation IDE. You'll be pasting an OpenTelemetry init block at the top.

<Gotchas>
- <strong>"Connection refused" on every region.</strong> The Gateway exists but isn&rsquo;t PROGRAMMED yet. <code>kubectl describe gateway pothole-gateway -n laureate</code> &mdash; look for <code>PROGRAMMED: False</code> in the Conditions block. Wait, or ask your Infra-Admin to check Q2D-5.
- <strong>Some regions green, others red, in the first 3 min.</strong> Cloud Monitoring rolls out checks region-by-region; give it 3-5 minutes for the global edge to converge before assuming something is broken.
- <strong>Path returns 404 instead of 200.</strong> The Streamlit health endpoint is <code>/_stcore/health</code> not <code>/health</code>. Edit the check, change the path, save.
- <strong>"You don&rsquo;t have permission to create uptime checks".</strong> Workstation runner SA needs <code>roles/monitoring.editor</code> &mdash; should be there via <code>roles/editor</code>. <code>gcloud auth list</code> to confirm you&rsquo;re authed correctly.
</Gotchas>

<Shipped>
Bronze tier, Guardian piece. <strong>Your team's first heartbeat is live.</strong> The Gateway has a watcher; if it goes down, the next two pages (Q2E-2 OTel + Q2E-3 alert) build on this signal so your Garage knows about failures before anyone refreshes the page.
</Shipped>

🛡 Move to **Q2E-2** — wire OpenTelemetry into the Streamlit Pod so you see what users actually do, not just whether the door is open.
