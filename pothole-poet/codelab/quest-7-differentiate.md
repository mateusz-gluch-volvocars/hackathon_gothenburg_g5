# 🏆 Quest 7 — Differentiate to Win

<Objective lane="all">

**🎯 What you'll do.** Use **Antigravity CLI** to push your Garage's demo past the core pipeline. Pick one direction (persona deepening, leaderboard, translation, roast mode, mood theming, citizen spotlight) or describe a freeform feature; agentic implementation does the heavy lifting with HITL approval on every write. ~15–45 minutes depending on the direction.

**🤝 Why it matters.** Every Garage that reaches this page has a pipeline that looks identical underneath. AlloyDB → Airflow → BigQuery → GKE. and a demo (form + HTTPS + alert) of the same shape. **The hackathon prize goes to the most creative, most differentiated demo on the stage.** This is the Quest that wins it.

</Objective>

> All hands. ~15–45 min depending on direction picked. Requires Foundation + Q6A + Q6B + Q2E-4 already shipped.

<QuickPath>

```bash
cd ~/quest
agy
```

Then ask:

> *"We've finished the core pipeline + polish. We have ~30 minutes before demo. What can we build to make our demo stand out?"*

Antigravity CLI will check your pipeline state, ask what your team is good at + what kind of "wow" you want, and walk you through one direction with HITL on every write. The `build-helper` skill in `~/quest/.agents/plugins/iron-and-cloud/skills/` is what powers the flow; same pattern as the other lane skills, just open-ended at the end.

</QuickPath>

You've shipped the core pipeline + polish: form (Q6A) + HTTPS (Q6B) + alert/broadcast (Q2E-4). Your demo will work. **But every other Garage's demo will work too**, with the same shape, and the demo train is what the judges remember. Identical pipelines tell identical stories; the Garage that breaks away with something the judges haven't seen the previous fifteen times is the one that takes the prize.

<Screenshot src="/quest/pothole-poet/img/streamlit_full.png" caption="The baseline: MODE=full with live odes, report form, Guardian banner, and pirate captain voice. Every Garage has this. What makes yours different?" />

---

## How it works

The Quest repo ships a workspace plugin at `~/quest/.agents/plugins/iron-and-cloud/`. Antigravity CLI auto-loads it whenever you launch `agy` inside the repo. Inside the plugin is the `build-helper` skill: it knows the pipeline's invariants (data spine, naming conventions, GCP service constraints), carries a small inspiration menu, and steers Antigravity CLI through a structured flow with HITL approval on every write.

The flow:

1. **Frame the window.** Antigravity CLI asks how much time you have, what your team's strength is (data viz, prompt engineering, UI polish, backend, demo storytelling), and what kind of "wow" you want: visual surprise, narrative depth, an interactive moment with the judge, or a measurable insight.
2. **Propose a plan, NO writes yet.** For the chosen direction, Antigravity CLI states what will ship, lists the files it'll touch, estimates the time budget, and surfaces any invariants the change stresses. Waits for your explicit *"go"*.
3. **Implement with HITL.** Every write paused, diff in plain English first, code second, then `y`/`n`. Read-only discovery happens freely.
4. **Verify.** After the build, runs sanity probes against the pipeline invariants (page still serves, env still wired, BQ tables still queryable).
5. **Demo prep.** Helps you write the 60-second framing. *"In the next minute, you'll watch our Pothole Laureate roast Hisingen against Vasastan in the voice of an IKEA assembly manual…"*

## The inspiration menu

These are **starting points**, not cookie-cutters. Mix and match welcomed. None of them needs a new GCP API enabled.

- **Deepen your Q5 persona across the whole app.** The Q5 prompt voice extends to the page title, header copy, sidebar form labels, Streamlit theme color, and the analyst-bench `AI.GENERATE` prompts. Whole app reads as one coherent voice instead of a generic shell wrapping a stylized ode. ~20–30 min.

- **Neighbourhood Laureate leaderboard.** A new Streamlit tab/section ranks the 12 neighbourhoods by an `AI.GENERATE`-scored property: most dramatic, most repetitive, most beloved, most exasperated. Judge clicks a ranking, sees the ode + the score. ~25–35 min.

- **Translate-and-compare.** Each ode displayed in Swedish + English side-by-side via `AI.GENERATE` (Gemini handles translation directly, no Cloud Translation API needed). Optional toggle for German or any other language your team picks. ~20–30 min.

- **Laureate Roast mode.** A new sidebar control picks any two neighbourhoods and asks Gemini to compose a *comparative* ode. *"Hisingen vs Vasastan: whose roads are worse?"* The verse renders in your chosen persona's voice. ~20–30 min.

- **Severity-driven UI mood theming.** The Streamlit page's color scheme shifts based on the day's dominant mood across neighbourhoods. Frustrated → red palette. Resigned → grey. Vengeful → orange. Lagom → muted blue. A small mood indicator next to the header. ~15–25 min, shortest direction; good for teams running low on time.

- **Citizen spotlight.** A new page listing the loudest, most-frequent, and most-eloquent citizens per neighbourhood, using the `citizens` and `social_sentiment` reference tables already loaded in Q2C-3. Click a citizen → see their reports + Gemini-generated profile blurb. ~25–40 min.

- **Freeform.** Describe what your team wants. Antigravity CLI proposes 2–3 implementations sized to your remaining time, maps each against the invariants, and tells you honestly if your idea needs a new GCP API (it'll suggest the closest variant that doesn't).

## Hard invariants — never break these

These are the load-bearing pieces of the pipeline. The `build-helper` skill enforces them, but it helps to know what they are so you can sanity-check Antigravity CLI's proposed changes:

- **The data spine.** AlloyDB `pothole_reports` schema, BigQuery dataset `pothole_laureate`, connection IDs `alloydb_archive` and `gemini`, the DAG producing `pothole_reports_raw` and `neighbourhood_odes`.
- **12 neighbourhoods.** Any new view must keep showing all 12 (or explicitly filter from the full 12 in a way the demo can revert).
- **Gemini 3 global endpoint.** Never accept a proposal that switches to a regional Gemini endpoint or an older model.
- **GKE shape.** Pod runs in namespace `laureate` as ServiceAccount `pothole-laureate`. Gateway + HTTPRoute + HealthCheckPolicy stay attached.
- **`MODE`, `BROADCAST_BUCKET`, `ALLOYDB_*` env vars.** `kubectl set env` merges, but if Antigravity CLI proposes a fresh `set env` call, the existing env vars must be listed alongside the new ones.
- **No new GCP APIs.** Curated list is already enabled. Don't approve a direction that needs Cloud TTS, Cloud Translation, Vision, Maps, etc.. it adds Foreman-touch steps you don't have time for.

If Antigravity CLI proposes something that would break one of these, it'll flag it before any write. Read the warning before pressing `y`.

## Time discipline

The skill time-boxes the chosen direction against your stated budget. Two rules worth remembering:

- **If you're past 70% of your time budget and < 50% complete, stop and ship a degraded version.** Judges prefer a working smaller thing over a half-finished bigger thing.
- **Demo framing is itself a deliverable.** Save the last 5 minutes for rehearsing your 60-second framing out loud. The Garage with a working feature *and* a sharp one-sentence pitch wins over the Garage with a slightly fancier feature *and* a rambling pitch.

## What "done" looks like

A direction is done when:

1. The new feature renders in the page at the public Gateway URL (not just locally).
2. The five invariant probes from the skill all still pass.
3. The team has rehearsed the 60-second demo framing out loud once.

Then surface the demo train clock and let them go.

<Shipped>
🏆 Your Garage's demo is now <strong>different</strong> from every other Garage in the room. Same pipeline underneath, your story on stage. The most creative implementation takes the hackathon prize at <strong>T+3:10</strong>.
</Shipped>
