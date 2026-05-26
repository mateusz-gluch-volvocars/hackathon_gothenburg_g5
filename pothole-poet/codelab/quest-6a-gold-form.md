# ✨ Quest 6A — Make it yours: Submit a Pothole

<Objective lane="guardian">

**🎯 What you'll do.** Add a **"Submit a Pothole" sidebar form** to your Streamlit app that writes back to AlloyDB, then re-trigger the DAG and watch the next ode reference the new submission. ~20 minutes.

**🤝 Why it matters.** This is the **demo punchline**. A judge submits *"my pothole has political opinions"* through your form, sits through one DAG re-run, refreshes, and watches their words baked into a freshly-composed Vasastan ode. **That moment** is the difference between "nice tutorial" and "we built a real thing today". This is also the page where every persona's lane participates: you (App Dev / Guardian) ship the form, your Data Engineer's AlloyDB takes the write, your Pipeline-author's DAG re-composes, your Infra-Admin's Gateway serves the result.

</Objective>

> Make it yours · ~20 minutes · pairs naturally with Q6B (HTTPS) which any order works.

<QuickPath>

```bash
# 1. Get AlloyDB private IP (set fresh — env var won't survive across shells)
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
[ -z "$ALLOYDB_HOST" ] && { echo "ERROR: empty IP — check AlloyDB cluster"; exit 1; }
echo "AlloyDB private IP: $ALLOYDB_HOST"

# 2. Patch deployment with MODE=full + AlloyDB env vars (also re-asserts BROADCAST_BUCKET)
kubectl set env deployment/pothole-laureate -n laureate \
  MODE=full \
  ALLOYDB_HOST="$ALLOYDB_HOST" \
  ALLOYDB_USER=postgres \
  ALLOYDB_PASSWORD=buildwithgemini2026 \
  ALLOYDB_DBNAME=postgres \
  BROADCAST_BUCKET="$(gcloud config get-value project)-broadcast"

kubectl rollout status deployment/pothole-laureate -n laureate

# 3. Submit a quote through the form (in laptop browser), then ask Pipeline-author
# to re-trigger the DAG, then refresh and read the new ode.
```

</QuickPath>

The best demo moment in the whole Quest. A judge submits an absurd pothole quote through your Streamlit app. The Pipeline-author re-triggers the DAG. Three minutes later the page refreshes; that quote is baked into the freshly-composed poem about whichever neighbourhood the judge picked.

The form structure (added to the Streamlit sidebar in `full` mode):

- Neighbourhood (dropdown)
- Severity (slider 1-5)
- Weather (dropdown)
- Your mood (dropdown)
- Your quote (text input)
- **Report it** button

The form `INSERT`s into AlloyDB via `psycopg2`. The next DAG run picks it up.

---

### Step 1 — Get the AlloyDB private IP

You need the cluster's primary-instance private IP for the Deployment env var. Don't trust whatever shell variable you had earlier; re-fetch it fresh:

```bash
ALLOYDB_HOST="$(gcloud alloydb instances describe pothole-archive-primary \
  --cluster=pothole-archive --region=europe-west1 \
  --format='value(ipAddress)')"
[ -z "$ALLOYDB_HOST" ] && { echo "ERROR: empty IP — check AlloyDB cluster"; exit 1; }
echo "AlloyDB private IP: $ALLOYDB_HOST"
```

✅ **Expect:** `AlloyDB private IP: 10.x.x.x`

<Concept title="How does the Pod reach AlloyDB on a private IP?">

AlloyDB only listens on a **private IP** (a `10.x.x.x` address inside your VPC). For your Streamlit container to write to it, the container has to be on the same network, anything outside the VPC has no route to that IP at all.

GKE Pods get an IP from your VPC's pod range when they schedule, so they're already inside the network. From a Pod, `psycopg2.connect(host="10.x.x.x", ...)` just works; same as if you were running `psql` from a VM in the same VPC. This is one of the reasons GKE is a good fit for workloads that need to talk to private GCP databases: zero extra plumbing for the network hop.

</Concept>

### Step 2 — Patch the Deployment with `MODE=full` + AlloyDB env vars

Add the env vars to the running Deployment in one command. Kubernetes does a rolling restart automatically.

> **Important:** `kubectl set env` *merges* into the existing env list; it updates or appends the vars you name and leaves the rest alone. We list all six here anyway so the env contract is explicit on one line; if you already set `BROADCAST_BUCKET` in Q2E-3 it would survive a narrower command too.

```bash
kubectl set env deployment/pothole-laureate -n laureate \
  MODE=full \
  ALLOYDB_HOST="$ALLOYDB_HOST" \
  ALLOYDB_USER=postgres \
  ALLOYDB_PASSWORD=buildwithgemini2026 \
  ALLOYDB_DBNAME=postgres \
  BROADCAST_BUCKET="$(gcloud config get-value project)-broadcast"

kubectl rollout status deployment/pothole-laureate -n laureate
```

✅ **Expect:** `deployment.apps/pothole-laureate env updated` then `deployment "pothole-laureate" successfully rolled out`.

> The Gateway URL doesn't change; same IP, same image, new env, two new Pods.

### Step 3 — Submit a quote through the form

Open the Gateway URL (or `<ip>.nip.io` if you also did Q6B) in your **laptop's** browser.

✅ **Expect:** The sidebar now has the **🚧 Report a pothole** form.

<Screenshot src="/quest/pothole-poet/img/streamlit_form_sidebar.png" caption="Streamlit sidebar showing the Report a pothole form: neighbourhood, severity, weather, mood, quote." />

1. Pick any neighbourhood. Pick something funny.
2. Click **Report it**.

✅ **Expect:** Green success banner. "Reported. The Laureate composes hourly..."

### Step 4 — Confirm the row landed in AlloyDB

In AlloyDB Studio:

```sql
SELECT *
FROM pothole_reports
WHERE reporter_quote LIKE '%<part of your quote>%'
ORDER BY reported_at DESC;
```

✅ **Expect:** One row with your quote.

### Step 5 — Re-trigger the DAG

Ask your Pipeline-author to re-trigger `compose_the_odes` from the Airflow UI. Or fire it yourself:

```bash
gcloud composer environments run the-laureate-bureau \
  --location=europe-west1 \
  dags trigger -- compose_the_odes
```

✅ **Expect:** DAG run kicked off; ~1-2 min to complete.

### Step 6 — Refresh Streamlit and read the new ode

1. Wait ~60 sec for the DAG to complete.
2. Refresh the Streamlit page in your laptop's browser.
3. Pick the neighbourhood you reported in.

✅ **Expect:** The new poem references your quote phrasing.

<Screenshot src="/quest/pothole-poet/img/streamlit_form_ode.png" caption="Same neighbourhood, freshly composed ode after the audience submission, quote phrasing visible in the verse." />

🎩 **The room understands what just happened.** The interactive loop is live.

### Demo time

Have a judge submit a quote on the live URL. Frame it for the room: *"This will cycle in three minutes. Watch the poem change."* If your Garage timed it right, the new poem appears live during your demo. If not, you re-trigger the DAG offstage and bring it back at the end.

If you're also doing **Q6B** (HTTPS), demo on the `https://<ip>.nip.io/` URL. the green padlock makes the moment land harder.

<Gotchas>
- <strong>Form submits without error but no row in AlloyDB.</strong> The Streamlit code is silently swallowing the exception; check Pod logs (<code>kubectl logs -n laureate -l app=pothole-laureate --tail=100</code>).
- <strong>Form 500s with <code>connection refused</code>.</strong> The <code>ALLOYDB_HOST</code> env var didn&rsquo;t make it onto the Pod. Re-check with <code>kubectl describe deployment pothole-laureate -n laureate | grep -A6 Environment</code>.
- <strong>DAG re-ran but the new ode doesn&rsquo;t mention your quote.</strong> The aggregation may have averaged your quote out. Submit 2&ndash;3 quotes to the same neighbourhood to dominate the dominant-mood / dominant-weather bucket the prompt sees.
- <strong>Form works but the Guardian's broadcast banner disappeared.</strong> Only possible if someone explicitly removed it. <code>kubectl set env</code> merges, so it can&rsquo;t have happened from Step 2 alone. Check Pod env (<code>kubectl describe deployment pothole-laureate -n laureate | grep -A6 Environment</code>) and re-assert with <code>kubectl set env deployment/pothole-laureate -n laureate BROADCAST_BUCKET=&quot;$(gcloud config get-value project)-broadcast&quot;</code>.
- <strong>Form errors or silent failures you can&rsquo;t reproduce.</strong> Open the Logs Explorer (Q1-5) and filter: Resource Type = <code>k8s_container</code>, namespace = <code>laureate</code>, Severity = Error. Look for <code>psycopg2</code> connection or authentication errors pointing to the AlloyDB host or password.
</Gotchas>

<Shipped>
The interactive loop is live. <strong>The Office accepts public pothole submissions, the DAG re-runs, and the next composition cycle weaves audience input into the Laureate's verse.</strong> A judge submits a quote, three minutes later the room watches the page change. That's the moment.
</Shipped>

**The interactive loop is live.** The Office now accepts public submissions, composes verse from them, and publishes results on the same page.

If you have time, head to **Q6B** for HTTPS polish, or back to Quest 4 (Render) for visual polish.
