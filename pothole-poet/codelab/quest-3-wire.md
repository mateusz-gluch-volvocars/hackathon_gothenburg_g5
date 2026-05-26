# 🔌 Quest 3 — Wire the Pipeline

<Objective lane="all">

**🎯 What you'll do.** As a team: confirm Lane A's DAG has run successfully (BigQuery has 12 rows in `neighbourhood_odes`), then Lane D runs `kubectl set env deployment/pothole-laureate MODE=live -n laureate`. Pods restart in ~60 seconds. Refresh the URL. it now serves real Gemini poems from BigQuery instead of bundled CSV. **Foundation complete.**

**🤝 Why it matters.** This is the **convergence moment**. four parallel lanes finally meet. There's no new infrastructure here, just one env var that switches Streamlit's data source. If anyone's lane isn't done, they finish *while the team waits and watches*. Foundation isn't complete until BigQuery has poems and Streamlit reads them. Take a breath after this page; the rest of the day is about making the demo yours.

</Objective>

> All four lanes converge. ~10 minutes.

The pipeline goes live. Three short steps, one per lane.

---

## Choreography

<div style="max-width: 340px; margin: 0 auto;">

<Screenshot src="/quest/pothole-poet/img/quest_3_choreography.svg" caption="Quest 3 choreography: three handoffs, then Foundation is complete." />

</div>

---

## Step 1 — Airflow Lead: trigger the DAG (~3 min)

In the Composer environment's **DAGs** tab, click `compose_the_odes` → **Trigger DAG** (top-right play icon).

Both tasks should go green:
- `federate_pothole_reports` (~30 sec)
- `ask_the_laureate` (~30–60 sec. Gemini composes 12 odes)

If `ask_the_laureate` fails, click into it and read the logs. Most common: `gemini` connection is missing the `roles/aiplatform.user` binding (should be pre-bound by the platform; flag a Sherpa).

<Cheat title="Show how to trigger from the CLI instead">

```bash
gcloud composer environments run the-laureate-bureau \
  --location=europe-west1 \
  dags trigger -- compose_the_odes
```

</Cheat>

## Step 2 — BigQuery Lead: confirm the enriched table

In BigQuery Studio, count the odes and read a few. There should be exactly 12 rows (one per neighbourhood) and each `ode` should be a real three-line poem.

Read at least one poem out loud. Then tell the GKE / App Lead: *"Twelve odes are live. Swap your data source."*

<Cheat title="Show the verification queries">

```sql
SELECT count(*) FROM `pothole_laureate.neighbourhood_odes`;
-- Expected: 12

SELECT neighbourhood, ode
FROM `pothole_laureate.neighbourhood_odes`
ORDER BY pothole_count DESC
LIMIT 3;
-- Expected: Hisingen first, then Frölunda, then Kortedala. Each ode is real verse.
```

</Cheat>

## Step 3 — GKE / App Lead: switch `MODE` to live (~1 min)

No rebuild, no redeploy. The container code is unchanged. `app.py` reads `MODE` at runtime and switches data sources. We just patch the Deployment's env var and Kubernetes does a rolling restart.

<Cheat title="Show the env-flip command">

```bash
kubectl set env deployment/pothole-laureate MODE=live -n laureate

kubectl rollout status deployment/pothole-laureate -n laureate
```

The same two Pods bounce one at a time (rolling restart, zero downtime). The public URL doesn't change; same Gateway, same IP, same image, just new env.

</Cheat>

Open the Gateway IP in your **laptop's** browser tab (the workstation has no browser). The page now shows **real Gemini-composed poems** read live from BigQuery.

<Screenshot src="/quest/pothole-poet/img/streamlit_live.png" caption="Pipeline live: Streamlit page rendering real Gemini odes per neighbourhood, pulled from BigQuery." />

**Foundation complete.** The Office is now fully operational.

## Verify

Confirm the live page actually rendered (and isn't cached seed data).

<Cheat title="Show the smoke check">

```bash
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate \
  -o jsonpath='{.status.addresses[0].value}')

curl -s "http://$GATEWAY_IP/" | grep -o "Today's Ode" | head -1
# ✅ Returns: Today's Ode
```

In your laptop's browser tab, switch neighbourhoods in the dropdown, each shows a different real poem.

</Cheat>

## Done

<Gotchas>
- <strong>DAG is green but <code>neighbourhood_odes</code> shows 0 rows.</strong> Check the BigQuery <code>Job History</code>. the <code>ask_the_laureate</code> task may have skipped due to a stale federation cache. Re-trigger the DAG.
- <strong>Streamlit still shows the CSV after the env switch.</strong> Confirm the rollout completed (<code>kubectl rollout status deployment/pothole-laureate -n laureate</code>). If pods bounced but the page still shows seed data, hard-refresh the browser. Streamlit caches aggressively.
- <strong>Odes appear as raw JSON instead of poetry.</strong> The <code>AI.GENERATE</code> response wasn&rsquo;t unwrapped; check that <code>02_enrich.sql</code> reads <code>.result</code> off the AI.GENERATE call.
- <strong>Page loads but shows errors or stale data after switching to <code>MODE=live</code>.</strong> Open the Logs Explorer (Q1-5) and filter: Resource Type = <code>k8s_container</code>, namespace = <code>laureate</code>, Severity = Error. Common causes: BigQuery client exceptions (WIF binding from Q2D-3 is wrong) or the <code>pothole_laureate</code> dataset is not populated yet.
</Gotchas>

<Shipped>
Foundation is complete. <strong>The pipeline is end-to-end live: AlloyDB &rarr; Airflow &rarr; BigQuery (with Gemini odes) &rarr; Streamlit on GKE Autopilot via Gateway API.</strong> Every neighbourhood has a real composed poem on the page. From here, you make it yours.
</Shipped>

The whole team gathers around the Gateway URL. The Foreman comes to confirm the Foundation is live.

➡️ Next: **Quest 4 — Render the Poems** (sidebar on the left). Now you make it *yours*.
