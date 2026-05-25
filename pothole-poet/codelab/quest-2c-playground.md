# 📊 Quest 2C-3 — The Analyst's Bench

<Objective lane="data">

**🎯 What you'll do.** Two phases of analyst work. **Phase A (~30 min)** runs against the 6 pre-loaded reference tables and starts immediately: crew leaderboards, freeze-thaw correlation, citizen power-user ranking, `AI.GENERATE` straight from SQL on the social-sentiment corpus, per-capita SLA analysis. **Phase B (~15 min)** unlocks once Q3 finishes and the DAG has landed today's `pothole_reports_raw` + `neighbourhood_odes`. you join today's data into the historical baseline.

**🤝 Why it matters.** The other lanes deliver a demo (the live odes); this page delivers analytical insight. By the end the BigQuery Lead has answered the question their day-job warehouse can't trivially answer. *call an LLM directly from a SELECT, classify free text against ground truth, and join three years of historical context to today's events in one query*. backed by data they wrote queries against. Phase A in particular **never blocks on the Pipeline lane**, so you have ~30 minutes of real work the moment Q2C-1 ends.

</Objective>

> Lane C · 3 of 3. ~45 minutes total. Phase A starts now (parallel to Q2C-2); Phase B unlocks when Q3 completes.

<QuickPath>

```sql
-- A1: crew leaderboard — fastest crew at the top, SLA breach % surfaced.
SELECT c.crew_name, c.base_neighbourhood,
       COUNT(*) AS jobs, ROUND(AVG(w.fix_minutes),1) AS avg_min,
       ROUND(100*COUNTIF(w.sla_breached)/COUNT(*),1) AS sla_breach_pct
FROM `pothole_laureate.work_orders` w
JOIN `pothole_laureate.crews` c USING (crew_id)
GROUP BY c.crew_name, c.base_neighbourhood
ORDER BY sla_breach_pct ASC;
-- ✅ Expect: 12 rows, breach pct ranges across crews

-- A4: AI.GENERATE in SQL — Gemini summarises 30 days of Hisingen discourse.
-- Replace <your-project-id> first (Ctrl+H in Studio).
SELECT AI.GENERATE(
  prompt => (
    'You are a Göteborg city-council media analyst. In three sentences, summarise ',
    'the citizen mood about road conditions in Hisingen based on these recent posts: ',
    STRING_AGG(text, ' || ' LIMIT 30)
  ),
  endpoint      => 'https://aiplatform.googleapis.com/v1/projects/<your-project-id>/locations/global/publishers/google/models/gemini-3-flash-preview',
  connection_id => '<your-project-id>.europe-west1.gemini',
  model_params  => JSON '{"generation_config":{"thinking_config":{"thinking_level":"LOW"}}}'
).result AS council_summary
FROM `pothole_laureate.social_sentiment`
WHERE neighbourhood = 'Hisingen'
  AND posted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);
-- ✅ Expect: a 3-sentence council brief in plain English

-- B1 (Phase B, after Q3): today's severity distribution vs. 3-year baseline.
WITH live AS (
  SELECT severity_iron_marks AS severity,
         COUNT(*)*100.0/SUM(COUNT(*)) OVER () AS pct
  FROM `pothole_laureate.pothole_reports_raw` GROUP BY severity_iron_marks
), hist AS (
  SELECT severity_at_fix AS severity,
         COUNT(*)*100.0/SUM(COUNT(*)) OVER () AS pct
  FROM `pothole_laureate.work_orders` GROUP BY severity_at_fix
)
SELECT severity, ROUND(live.pct,1) AS today_pct, ROUND(hist.pct,1) AS hist_pct,
       ROUND(live.pct - hist.pct, 1) AS delta_pct
FROM live FULL OUTER JOIN hist USING (severity) ORDER BY severity;
-- ✅ Expect: 5 rows; delta_pct shows whether today skews milder or harsher
```

</QuickPath>

🛠 **For the daily analyst.** The 6 pre-loaded tables (`neighbourhoods`, `crews`, `citizens`, `weather_daily`, `work_orders`, `social_sentiment`) are queryable **right now**, no waiting on AlloyDB or the DAG. Five Phase-A queries below, then three Phase-B queries that join today's pipeline data into the historical context. Each one shows a muscle BigQuery flexes that PowerBI/Snowflake don't trivially match: AI in SQL, `QUALIFY`, native window functions, AI ground-truth comparison, `APPROX_TOP_COUNT`.

---

## Phase A — While the pipeline builds (~30 min)

### Step 1 — Crew leaderboard (work_orders × crews)

Fastest crew up top, slowest at the bottom, SLA breach percentage surfaced. The shape any test-engineer dashboard recognises: facts joined to a crew/team dimension, ranked.

```sql
SELECT
  c.crew_name,
  c.base_neighbourhood,
  COUNT(*)                                              AS jobs_completed,
  ROUND(AVG(w.fix_minutes), 1)                          AS avg_fix_minutes,
  ROUND(100 * COUNTIF(w.sla_breached) / COUNT(*), 1)    AS sla_breach_pct,
  c.motto
FROM `pothole_laureate.work_orders` w
JOIN `pothole_laureate.crews` c USING (crew_id)
GROUP BY c.crew_name, c.base_neighbourhood, c.motto
ORDER BY sla_breach_pct ASC;
```

✅ **Expect:** 12 rows. The motto column is gratuitous but earns its place. "Botany is our cover story" is more memorable than `crew-linnaeus-tools`.

<Concept title="Why COUNTIF instead of SUM(CASE WHEN ...)">

`COUNTIF(condition)` is BigQuery shorthand for `COUNT(CASE WHEN condition THEN 1 END)`. Half the keystrokes, same plan. Shows up in `APPROX_COUNT_DISTINCT`, `APPROX_QUANTILES`, `APPROX_TOP_COUNT`. BQ's "approximation family" that's much faster than exact aggregation when you only need a leaderboard, not an audit. Worth knowing exists.

</Concept>

### Step 2 — Freeze-thaw correlation (weather_daily × work_orders)

The classic "does X cause Y" question. Aggregate work-order count by day, group by whether that day was a freeze-thaw event, compare averages.

```sql
WITH daily_work AS (
  SELECT DATE(reported_at) AS d, COUNT(*) AS jobs
  FROM `pothole_laureate.work_orders`
  GROUP BY d
)
SELECT
  w.freeze_thaw_event,
  COUNT(DISTINCT w.date)                AS days,
  ROUND(AVG(COALESCE(dw.jobs, 0)), 2)   AS avg_jobs_per_day
FROM `pothole_laureate.weather_daily` w
LEFT JOIN daily_work dw ON dw.d = w.date
WHERE w.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
GROUP BY w.freeze_thaw_event;
```

✅ **Expect:** 2 rows. The analyst's job here is to *measure* whether freeze-thaw days actually correlate with more pothole work, and to be honest about the answer. In the current seed, `work_orders.severity` and the daily job rate are not modelled against `freeze_thaw_event`, so the two `avg_jobs_per_day` values typically come out within ±0.1 of each other. The query mechanics are sound; the result is "no detectable effect in this dataset", and saying that out loud is itself the muscle to build.

### Step 3 — Citizen power-users by tone (citizens, QUALIFY)

Find the top-1 power user (by `propensity_score`, tie-break by `citizen_id`) for each `(neighbourhood, tone)` cell. The kind of "row-per-bucket" question that classically requires a self-join or a CTE-with-rank wrapper. BigQuery's `QUALIFY` collapses it to a single statement.

```sql
SELECT
  home_neighbourhood,
  tone,
  full_name,
  occupation,
  propensity_score
FROM `pothole_laureate.citizens`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY home_neighbourhood, tone
  ORDER BY propensity_score DESC, citizen_id
) = 1
ORDER BY home_neighbourhood, tone;
```

✅ **Expect:** Up to 144 rows (12 neighbourhoods × 12 tones). Each row is the "loudest voice in this corner of the city".

<Concept title="QUALIFY. the WHERE for window functions">

Standard SQL forces you to wrap window functions in a subquery before you can filter on them. `QUALIFY` lets you filter on a window function in the same SELECT. same way `HAVING` filters on aggregates. Snowflake has it, BigQuery has it; PowerBI's M layer doesn't expose anything equivalent. If you only learn one BQ-specific thing today, learn this.

</Concept>

### Step 4 — Call Gemini from SQL on social_sentiment ⭐

The headline flex. `AI.GENERATE` is a regular scalar function; call it inside a `SELECT`, pipe in any string from any column or aggregate, get text back. No Python, no API client, no orchestration. The analyst writes the prompt, BQ handles auth and dispatch through the pre-provisioned `gemini` connection.

Replace `<your-project-id>` (Ctrl+H in Studio):

```sql
SELECT
  AI.GENERATE(
    prompt => (
      'You are a Göteborg city-council media analyst. In three sentences, ',
      'summarise the citizen mood about road conditions in Hisingen based on ',
      'these recent posts: ',
      STRING_AGG(text, ' || ' LIMIT 30)
    ),
    endpoint      => 'https://aiplatform.googleapis.com/v1/projects/<your-project-id>/locations/global/publishers/google/models/gemini-3-flash-preview',
    connection_id => '<your-project-id>.europe-west1.gemini',
    model_params  => JSON '{"generation_config":{"thinking_config":{"thinking_level":"LOW"}}}'
  ).result AS council_summary
FROM `pothole_laureate.social_sentiment`
WHERE neighbourhood = 'Hisingen'
  AND posted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);
```

✅ **Expect:** A three-sentence council brief in English, written by Gemini, sourced from ~30 actual posts in your dataset. Swap `'Hisingen'` for any neighbourhood and re-run.

<Concept title="The sentiment_seed column is your answer key">

`social_sentiment.sentiment_seed` is ground truth, when the row was generated, it was tagged `frustrated`, `resigned`, `hopeful`, or `sarcastic`. That makes this dataset suitable for evaluating Gemini, not just calling it: have the model classify each post, compare to the seed, compute accuracy. The pattern (LLM as classifier with held-out labels) is one of the few reliable ways to put an LLM in production without flying blind.

</Concept>

<Cheat title="Show the classifier-vs-ground-truth variant">

```sql
WITH sample AS (
  SELECT post_id, text, sentiment_seed
  FROM `pothole_laureate.social_sentiment`
  WHERE RAND() < 0.01  -- ~30 posts; bump if you want more
)
SELECT
  s.text,
  s.sentiment_seed AS ground_truth,
  LOWER(TRIM(AI.GENERATE(
    prompt => CONCAT(
      'Classify the sentiment of this Göteborg road-condition post into ',
      'exactly one of: frustrated, resigned, hopeful, sarcastic. Reply with ',
      'one word only, lowercase. Post: ', s.text
    ),
    endpoint      => 'https://aiplatform.googleapis.com/v1/projects/<your-project-id>/locations/global/publishers/google/models/gemini-3-flash-preview',
    connection_id => '<your-project-id>.europe-west1.gemini',
    model_params  => JSON '{"generation_config":{"thinking_config":{"thinking_level":"LOW"}}}'
  ).result)) AS gemini_classification
FROM sample s;
```

Then wrap that in another query computing `AVG(CASE WHEN gemini_classification = ground_truth THEN 1.0 ELSE 0.0 END)` to get accuracy. ~70-90% is normal; disagreements are often genuinely ambiguous posts, which is its own finding.

</Cheat>

### Step 5 — Per-capita SLA breach (neighbourhoods × work_orders)

The dim-table flex; same fact table as Step 1, but normalised by neighbourhood attributes instead of by crew.

```sql
SELECT
  n.neighbourhood,
  n.population,
  n.road_km,
  COUNTIF(w.sla_breached)                               AS breaches,
  ROUND(COUNTIF(w.sla_breached) * 1000.0 / n.road_km,    2) AS breaches_per_road_km,
  ROUND(COUNTIF(w.sla_breached) * 1000.0 / n.population, 2) AS breaches_per_1k_residents
FROM `pothole_laureate.neighbourhoods` n
LEFT JOIN `pothole_laureate.work_orders` w USING (neighbourhood)
GROUP BY n.neighbourhood, n.population, n.road_km
ORDER BY breaches_per_road_km DESC;
```

✅ **Expect:** 12 rows. Hisingen has the most absolute breaches (it's huge); Haga or Centrum has the highest per-km (small dense districts). The two rankings disagree; that's the point.

### Step 6 — (optional, ~10 min) Plot it in a Studio Notebook

Studio's **Notebook** surface combines SQL cells, Python cells, and inline output. The `%%bigquery df --project=<your-project-id>` cell magic drops query results straight into a pandas DataFrame.

In Studio, **+** dropdown → **Notebook** → pick `europe-west1`.

```python
%%bigquery df --project=<your-project-id>
SELECT n.neighbourhood, n.cobblestone_pct,
       ROUND(100*COUNTIF(w.sla_breached)/COUNT(*),1) AS sla_breach_pct
FROM `pothole_laureate.work_orders` w
JOIN `pothole_laureate.neighbourhoods` n USING (neighbourhood)
GROUP BY n.neighbourhood, n.cobblestone_pct;
```

```python
import matplotlib.pyplot as plt
ax = df.plot.scatter(x='cobblestone_pct', y='sla_breach_pct',
                     figsize=(8,5), color='#b07d62')
ax.set_title('Cobblestone density vs. crew SLA breach rate')
ax.set_xlabel('Cobblestone (%)'); ax.set_ylabel('SLA breach (%)')
for _, r in df.iterrows():
    ax.annotate(r['neighbourhood'], (r['cobblestone_pct'], r['sla_breach_pct']))
plt.show()
```

✅ **Expect:** A scatter plot. Whether the correlation is real or a coincidence of the synthetic seed is for you to decide.

---

## Phase B — When the pipeline lands (~15 min)

The DAG creates two new tables in `pothole_laureate` when Q3 finishes: `pothole_reports_raw` (5,000 federated citizen reports) and `neighbourhood_odes` (12 Gemini-composed verses). Refresh Explorer; they appear under the same dataset as the pre-loaded tables. Now your Phase A muscle memory applies to today's data.

### Step 7 — Today's severity vs, the 3-year baseline (pothole_reports_raw × work_orders)

```sql
WITH live AS (
  SELECT severity_iron_marks AS severity,
         COUNT(*)                                AS n,
         COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct
  FROM `pothole_laureate.pothole_reports_raw`
  GROUP BY severity_iron_marks
),
hist AS (
  SELECT severity_at_fix AS severity,
         COUNT(*)                                AS n,
         COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct
  FROM `pothole_laureate.work_orders`
  GROUP BY severity_at_fix
)
SELECT
  COALESCE(live.severity, hist.severity) AS severity,
  ROUND(live.pct, 1) AS today_pct,
  ROUND(hist.pct, 1) AS historical_pct,
  ROUND(live.pct - hist.pct, 1) AS delta_pct
FROM live FULL OUTER JOIN hist USING (severity)
ORDER BY severity;
```

✅ **Expect:** 5 rows (one per severity). `delta_pct` tells you whether today's reports skew milder or harsher than the historical fix-time distribution. Either answer is interesting.

### Step 8 — Reporter-tone bias (pothole_reports_raw × citizens)

Are high-propensity citizens (chronic reporters) biasing today's severity ratings upward? Join today's reports to the citizens table on `citizen_id`, group by `tone`.

```sql
SELECT
  c.tone,
  COUNT(DISTINCT r.id)                       AS reports_today,
  ROUND(AVG(r.severity_iron_marks), 2)       AS avg_severity_today,
  ROUND(AVG(c.propensity_score), 2)          AS avg_propensity
FROM `pothole_laureate.pothole_reports_raw` r
JOIN `pothole_laureate.citizens` c ON c.citizen_id = r.citizen_id
GROUP BY c.tone
ORDER BY avg_severity_today DESC;
```

✅ **Expect:** Up to 12 rows (one per tone). The seed generator assigns citizen `tone` independently of `severity_iron_marks` (severity is picked from neighbourhood-level weights *before* a citizen is selected), so `avg_severity_today` typically lands within ~0.2 across all tones, a flat-ish leaderboard. That null result is itself the finding worth reporting: *"chronic-reporter tone does not appear to bias today's severity ratings in this dataset."* ~10% of today's reports are anonymous (`citizen_id IS NULL`) and won't be in this output; surface them with a separate `WHERE r.citizen_id IS NULL` query.

### Step 9 — Ode mood vs. social-sentiment baseline (neighbourhood_odes × social_sentiment)

The closing-the-loop query. The DAG aggregated today's `reporter_mood` per neighbourhood and asked Gemini to write a verse over it. Meanwhile, `social_sentiment` has 3 years of citizen posts about each neighbourhood with their own ground-truth sentiment. Do the two storylines agree?

```sql
WITH sentiment_dom AS (
  SELECT
    neighbourhood,
    APPROX_TOP_COUNT(sentiment_seed, 1)[OFFSET(0)].value AS dominant_social_sentiment
  FROM `pothole_laureate.social_sentiment`
  WHERE posted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
  GROUP BY neighbourhood
)
SELECT
  o.neighbourhood,
  o.dominant_mood              AS reporter_mood_today,
  s.dominant_social_sentiment  AS social_sentiment_yr,
  CASE
    WHEN o.dominant_mood IN ('frustrated','vengeful')
         AND s.dominant_social_sentiment IN ('frustrated','sarcastic')
    THEN '✓ aligned (frustrated)'
    WHEN o.dominant_mood IN ('philosophical','lagom','amused')
         AND s.dominant_social_sentiment IN ('hopeful','resigned')
    THEN '✓ aligned (calm)'
    ELSE '✗ divergent'
  END AS alignment,
  o.ode
FROM `pothole_laureate.neighbourhood_odes` o
LEFT JOIN sentiment_dom s USING (neighbourhood)
ORDER BY o.neighbourhood;
```

✅ **Expect:** 12 rows. Some neighbourhoods will be aligned; some divergent. The ode column shows you exactly what Gemini said, useful when explaining a divergent row to a stakeholder ("Hisingen citizens have been resigned for a year, but today's reporters are vengeful, what changed in the last 90 days?").

### Step 10 — (optional, ~10 min) Ask Data Canvas about today's data

**Data Canvas** is BQ Studio's NL-to-SQL surface: drop a table on a canvas, type a question in plain English, Gemini writes the SQL and renders the chart. Best on flat columns; works well on `pothole_reports_raw`.

In Studio, **+** dropdown → **Create new** → **Data canvas** → region `europe-west1` → name `pothole-poet-explore`. **Search** → drag `pothole_reports_raw`. Try:

1. *"Show today's reports broken down by weather, as a stacked bar per neighbourhood."*
2. *"Which citizens filed more than 3 reports today and what tones are they?"*. note: needs the `citizens` table dragged in as a second node.
3. *"Summarise the top 5 swallowed objects in Hisingen using one Gemini sentence."*. Data Canvas knows about `AI.GENERATE`; see if it composes a sensible call.

Inspect the SQL each step. When the chart is good, save the canvas, the App Lead can pull screenshots into Streamlit later.

---

<Gotchas>
- <strong>AI.GENERATE returns NULL or errors with <code>permission denied</code>.</strong> The <code>gemini</code> connection&rsquo;s service account is missing <code>roles/aiplatform.user</code>. Pre-provisioning binds it; if it&rsquo;s missing, flag a Sherpa rather than rebinding by hand.
- <strong>AI.GENERATE returns <code>404 model not found</code>.</strong> You used the regional endpoint name (<code>europe-west1</code>) instead of the global one. Gemini 3 is global-endpoint only, the URL <strong>must</strong> contain <code>locations/global</code>.
- <strong>QUALIFY: <code>syntax error</code>.</strong> You&rsquo;re on a SQL dialect setting that&rsquo;s not GoogleSQL. Studio defaults are right; if you set <code>--use_legacy_sql=true</code> anywhere, undo it.
- <strong>Notebook fails to start.</strong> Pick the <strong>europe-west1</strong> runtime; <code>us-central1</code> works but is slower.
- <strong>Data Canvas isn&rsquo;t available in <code>europe-west1</code>.</strong> Fall back to <code>us-central1</code> for the canvas runtime, the dataset stays in <code>europe-west1</code>.
- <strong>Phase B queries return zero rows.</strong> The DAG hasn&rsquo;t run yet, or it failed. Refresh Explorer; if <code>pothole_reports_raw</code> isn&rsquo;t there, it&rsquo;s a Pipeline-lane problem, not yours.
- <strong>STRING_AGG with LIMIT inside AI.GENERATE prompt times out.</strong> You asked Gemini to read 5,000 posts. Cap the LIMIT to ~50; the model&rsquo;s context isn&rsquo;t the bottleneck, latency is.
</Gotchas>

<Shipped>
You&rsquo;ve flexed five Phase-A muscles BigQuery makes easy that the Snowflake/PowerBI stack doesn&rsquo;t. <code>QUALIFY</code> for window-function filtering, <code>AI.GENERATE</code> as a scalar function, ground-truth evaluation of an LLM in pure SQL, <code>APPROX_TOP_COUNT</code> for cheap ranking, <code>COUNTIF</code> for terse conditional counts, and three Phase-B joins that fold today&rsquo;s pipeline data into 3 years of historical context. The Garage now has analytical answers, not just a demo.
</Shipped>

📊 **Lane C done.** Tell the Pipeline-author the federation is wired and your queries are ready, then drift over to the App Lead and pair on Streamlit; they may want screenshots of your Phase B alignment query for the demo tile.

➡️ Next: **Quest 3 — Wire the Pipeline** (sidebar on the left). The team converges.
