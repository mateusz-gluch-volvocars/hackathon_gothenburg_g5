---
name: build-helper
description: Drives Quest 7 (Differentiate to Win) — the open-ended build window after the team has shipped the Foundation pipeline + Make it yours polish (Q6A form, Q6B HTTPS, Q2E-4 alert + broadcast). Helps the team pick a direction (small inspiration menu or freeform), preserves the pipeline's hard invariants, walks through agentic implementation with HITL on every write, time-boxes against the demo train clock, and verifies the end state. Use when the participant lands on Q7, asks to differentiate their demo, asks how to win the hackathon, says they want to build something beyond the core pipeline, or asks what to do with their remaining time before T+3:00.
---

# Build helper — Differentiate to Win

**Codelab counterpart:** Q7 — `~/quest/pothole-poet/codelab/quest-7-differentiate.md` (the participant-facing version of this skill — same menu, same invariants, narrative tone).

This skill is the agentic side of **Quest 7 — Differentiate to Win**. Every Garage builds the same pipeline today; every Garage's core demo (form + HTTPS + alert) follows the same shape. The hackathon prize goes to the Garage that uses this skill to push past the tutorial. Twenty-one Garages, twenty-one different demos — your job is to make this Garage's the one the judges remember.

## When to use this skill

Trigger this skill ONLY when the participant has already shipped:

1. **Foundation** — public URL serving live Gemini-composed odes (Q1 → Q3 complete).
2. **Q6A** — Submit-a-Pothole form writing back to AlloyDB.
3. **Q6B** — HTTPS via Cert Manager on `<ip>.nip.io`.
4. **Q2E-4** — Guardian alert + broadcast banner.

If any of these is incomplete, do NOT start a differentiation direction — point them at the missing codelab page instead. A Garage that ships a fancy capability on top of an incomplete pipeline won't survive demo questions.

If the team is unsure where they are, run this discovery (read-only, no permission needed):

```bash
# Foundation: page reachable + odes table populated
curl -s "http://$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.addresses[0].value}')/_stcore/health"
PROJECT_ID="$(gcloud config get-value project)"
bq query --use_legacy_sql=false "SELECT COUNT(*) AS odes FROM \`$PROJECT_ID.pothole_laureate.neighbourhood_odes\`"

# Q6A: AlloyDB writable from Pod (form would land rows here)
kubectl describe deployment pothole-laureate -n laureate | grep -A1 ALLOYDB_HOST || echo "Q6A NOT DONE"

# Q6B: HTTPS listener attached
kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.listeners[*].name}' | grep -q https && echo "Q6B DONE" || echo "Q6B NOT DONE"

# Q2E-4: broadcast bucket env wired
kubectl describe deployment pothole-laureate -n laureate | grep BROADCAST_BUCKET || echo "Q2E-4 NOT DONE"
```

Surface any gaps to the team before proposing a direction.

## Hard invariants — never break these

These are the load-bearing pieces of the pipeline. Any direction must leave them working at the end. If a proposed change risks breaking one, surface it before any write:

- **The data spine.** AlloyDB `pothole_reports` table keeps its current schema. BigQuery dataset stays `pothole_laureate`. The DAG keeps producing `pothole_reports_raw` and `neighbourhood_odes`. Federation connection ID stays `alloydb_archive`. Gemini connection ID stays `gemini`.
- **12 neighbourhoods.** Every Streamlit view must continue to show all 12 — or explicitly filter from the full 12 in a way the demo can revert. Hardcoding to fewer than 12 silently is a regression.
- **Gemini model + endpoint.** `gemini-3-flash-preview` on the global endpoint (`locations/global`). Never propose a regional endpoint or an older model.
- **GKE shape.** Pod runs in namespace `laureate` as ServiceAccount `pothole-laureate`. The WIF principal binding for BigQuery dataViewer + jobUser stays in place. The Gateway + HTTPRoute + HealthCheckPolicy stay attached.
- **MODE env contract.** `MODE=full` already drives Q6A's sidebar form rendering. A new direction adding UI should respect the same env-flag gating pattern rather than ripping it out.
- **`BROADCAST_BUCKET` env.** Q2E-4 wired this and the Streamlit app reads it for the Guardian banner. Don't clobber it in any new `kubectl set env` call — list it explicitly when re-running `set env`.
- **No extra Google Cloud APIs.** The Garage project has a curated API list (AlloyDB, BigQuery, Composer, Vertex AI, Cloud Build, Cloud Run, GKE, etc.). Don't propose a direction that needs a new API (Cloud Text-to-Speech, Cloud Translation, Cloud Vision, Maps Platform, etc.) — it adds a Foreman-touch step and time the team doesn't have. Stick to capabilities reachable via what's already enabled.
- **Don't pre-clone or re-clone.** The team is in `~/quest/`. Edit in place.

## The flow

### Step 1 — Frame the build window (~3 min)

Before proposing anything, ask the team three short questions:

1. **How much time** do you have before the demo train? (Typical answers: 15 / 30 / 45 / 60 min.) Use the answer to budget.
2. **What's your team's strength** today — data viz, prompt engineering, UI polish, backend wiring, demo storytelling? Use this to weight the menu.
3. **What kind of "wow"** do you want in the demo — visual surprise, narrative depth, an interactive moment with the judge, or a measurable insight? Use this to filter the menu.

Then surface the menu below, ranked by fit to those answers. Always include the freeform option.

### Step 2 — Propose, then confirm (NO writes yet)

For the chosen direction, write a one-screen plan that includes:

- **What ships:** one sentence describing the end-state the judge will see.
- **Files to touch:** explicit paths under `~/quest/pothole-poet/`.
- **Time budget:** estimated minutes, broken into discovery / implementation / verification / demo-prep.
- **Invariants stressed:** which of the invariants above this direction puts pressure on (e.g. "rebuilds the container image — we'll need `gcloud builds submit` + `kubectl rollout restart`, ~5 min").
- **Risk if running long:** what to drop to ship a smaller version. ("If we hit minute 25 and the chart isn't rendering, we drop the AI scoring and ship a count-based ranking instead.")

Wait for the team's explicit **"go"** before any tool call that writes.

### Step 3 — Implement with HITL

Standard Antigravity CLI practice — every proposed write:
- Diff in plain English first ("we're adding a sidebar selectbox that picks the neighbourhood comparison").
- Literal code or command second.
- Wait for `y`.
- Probe after each meaningful change (the page renders, the BQ query returns, the new env var lands on the Pod).

If a step takes longer than estimated, stop and resurface to the team before continuing.

### Step 4 — Verify against the invariants

After the build, run a sanity sweep before declaring done:

```bash
# Page still serves
GATEWAY_IP=$(kubectl get gateway pothole-gateway -n laureate -o jsonpath='{.status.addresses[0].value}')
curl -fs "http://$GATEWAY_IP/_stcore/health" && echo "page healthy"

# Pod env still has full mode + broadcast + AlloyDB
kubectl describe deployment pothole-laureate -n laureate | grep -E "MODE|BROADCAST_BUCKET|ALLOYDB_HOST"

# BQ tables still queryable
PROJECT_ID="$(gcloud config get-value project)"
bq query --use_legacy_sql=false "SELECT COUNT(*) AS n FROM \`$PROJECT_ID.pothole_laureate.neighbourhood_odes\`"
```

If any check fails, walk back with the team rather than calling it done.

### Step 5 — Demo prep

Help the team write a one-sentence demo framing — what the judge will see in 60 seconds, and what makes their Garage's demo different from the one before. Example:

> *"In the next minute, you'll watch our Pothole Laureate roast Hisingen against Vasastan in the voice of an IKEA assembly manual, scored on dramatic intensity by Gemini itself — pothole reports as flatpack instructions."*

The framing is itself a deliverable; teams that have one win demos.

## The inspiration menu

These are **starting points**, not cookie-cutters. Each direction is sketched lightly so the team + Antigravity CLI can decide the specifics together. The participant-facing version of this menu is in Q7; treat the two as one — if the team has read Q7 they already know the high-level shape, your job is to ground it in their specifics. Mix and match welcomed.

### Direction A — Deepen the Laureate's persona across the whole app

**What ships.** The Q5 prompt voice (pirate, IKEA, Volvo press, ABBA, freeform) extends consistently to the page title, header copy, sidebar form labels, Streamlit theme color, and (optionally) the analyst-bench `AI.GENERATE` prompts. The whole app reads as one coherent voice instead of a generic shell wrapping a stylized ode.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — `st.set_page_config`, header, sidebar, color theme
- `pothole-poet/airflow/sql/02_enrich.sql` — verify the Q5 prompt is aligned
- Optionally `pothole-poet/bigquery/*.sql` for analyst-bench prompts

**Outline.** Read `app.py` first to discover the current titles/headers/copy. Propose a per-line shift that keeps the voice consistent. Apply, rebuild the image (`gcloud builds submit`), roll the deployment (`kubectl rollout restart`), confirm the new page renders.

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 20–30 min. (~10 discovery + edit, ~5 rebuild, ~10 verify + demo-prep.)

---

### Direction B — Neighbourhood Laureate leaderboard

**What ships.** A new Streamlit tab/section that ranks the 12 neighbourhoods by an `AI.GENERATE`-scored property — most dramatic Laureate, most repetitive, most beloved, most exasperated. The judge clicks into a ranking and sees the Laureate's verse + the score.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — new tab + ranking display
- Optionally a new `pothole-poet/bigquery/leaderboard.sql` or inline query in `app.py`

**Outline.** Compose a BigQuery query that joins `neighbourhood_odes` with an inline `AI.GENERATE` call that scores each ode 1–10 on the chosen dimension. Cache the result in Streamlit (the scoring costs Gemini calls; cache for the session). Render as a ranked list with the ode body underneath.

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 25–35 min.

---

### Direction C — Translate-and-compare (Swedish ↔ English) via AI.GENERATE

**What ships.** Each ode displayed in both languages side-by-side, with a small "translated by Gemini" caption. Optionally a toggle for German or any other language the team picks.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — side-by-side column layout + a translation call per ode
- Optionally cache the translation in BigQuery via an extra DAG step

**No extra API needed.** Gemini does translation directly via `AI.GENERATE` — *not* Cloud Translation API. Stay inside `aiplatform.googleapis.com`.

**Outline.** Wrap each ode display in two `st.columns()`. Left column shows the original; right column calls `AI.GENERATE` with a "translate this Göteborg verse to Swedish, preserving the rhythm" prompt. Streamlit's `@st.cache_data` keeps the translation stable for the demo.

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 20–30 min.

---

### Direction D — "Laureate Roast" comparative mode

**What ships.** A new sidebar control that picks any two neighbourhoods and asks Gemini to compose a *comparative* ode — "Hisingen vs. Vasastan: whose roads are worse?" The verse is rendered in the chosen persona's voice.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — two `st.selectbox()` controls + a button that triggers a fresh `AI.GENERATE` call
- Optionally `pothole-poet/airflow/sql/03_roast.sql` if the team wants the roast generation in the DAG instead of live

**Outline.** Add the comparison UI. On button click, query BigQuery with an `AI.GENERATE` that takes the two neighbourhoods' aggregated mood + severity + sample quotes and produces a 6-line comparative verse. Render below.

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 20–30 min.

---

### Direction E — Severity-driven UI mood theming

**What ships.** The Streamlit page's color scheme shifts based on the day's dominant mood across the 12 neighbourhoods. Frustrated → red palette. Resigned → grey. Vengeful → orange. Lagom → muted blue. A small mood indicator + count next to the header.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — read `neighbourhood_odes.dominant_mood`, compute the top mood, theme accordingly via `st.markdown` + inline CSS

**Outline.** Add a one-query lookup at page load. Switch the Streamlit theme via a `st.markdown('<style>...</style>')` injection (Streamlit doesn't natively support runtime theme switching, but CSS injection works). Add a small caption: *"Today Göteborg feels: vengeful (8 of 12 neighbourhoods)."*

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 15–25 min. Shortest direction; good for teams running low on time.

---

### Direction F — Citizen spotlight

**What ships.** A new page listing the loudest, the most-frequent, and the most-eloquent citizens per neighbourhood — using the existing `citizens` and `social_sentiment` reference tables that were pre-loaded in Q2C-3. Click a citizen, see their reports + their Gemini-generated profile blurb.

**Files likely touched.**
- `pothole-poet/streamlit/app.py` — a new `st.page` or expander section
- Optional: a new BQ query in `pothole-poet/bigquery/` (or inline)

**Outline.** Query `citizens` joined with `pothole_reports_raw` (today) and `social_sentiment` (historical) to rank reporters per neighbourhood. For each top reporter, generate a one-paragraph profile via `AI.GENERATE` with the persona voice.

**Container rebuild required.** Yes — `streamlit/app.py` changed.

**Time budget.** 25–40 min. Heaviest direction by data complexity.

---

### Direction Z — Freeform

The team describes something not on the menu. Listen, then:

1. **Restate** what they want in your own words and get them to confirm you heard it right.
2. **Map it to the invariants.** If their idea needs a new API, a new GCP service, or breaks the data spine — say so before pretending it's possible. Suggest the closest variant that fits the budget.
3. **Propose 2–3 implementations**, varying in scope (small / medium / ambitious) and time (15 / 30 / 45 min). Be honest about which is realistic given their answers in Step 1.
4. **Pick one with the team**, then go to Step 2 of the flow above.

If their idea is genuinely outside what the pipeline + enabled APIs support: tell them. Don't fake it. Offer the closest Direction A–F as a fallback.

## Common pitfalls

- **Container image cache.** A `kubectl rollout restart` only re-pulls the image if the digest changed. After `gcloud builds submit --tag …:latest`, the digest IS new even though the tag is the same — so the rollout does pick up the change. But if you used a pinned tag (e.g. `:2026-05-19`), bump it before re-deploying.
- **`kubectl set env` and `BROADCAST_BUCKET`.** If a direction adds new env vars and you re-issue `set env`, list `BROADCAST_BUCKET` and `MODE` and `ALLOYDB_*` explicitly. `set env` merges, but verifying with `kubectl describe deployment ... | grep -A6 Environment` after every env change is cheap insurance.
- **BigQuery costs.** `AI.GENERATE` calls in the page-load path cost Gemini tokens per ode per render. Wrap them in `@st.cache_data` or move them into a DAG step so the demo doesn't burn through quota.
- **Streamlit re-runs on every interaction.** If a direction adds a "click to generate" button, gate the generation behind the button — not at top of script — or every selectbox change triggers a fresh Gemini call.
- **Demo runs out before build.** If you're past 70% of the time budget and < 50% complete, stop and ship a degraded version. The judge prefers a working smaller thing over a half-finished bigger thing.

## What "done" looks like

A direction is done when:

1. The new feature renders in the page at the public Gateway URL (not just locally).
2. The five invariant probes (Step 4) all still pass.
3. The team has rehearsed the 60-second demo framing out loud once.

Then surface the demo train clock and let them go.
