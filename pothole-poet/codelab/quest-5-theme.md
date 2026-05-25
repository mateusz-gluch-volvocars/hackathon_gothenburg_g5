# ✨ Quest 5 — Theme It

<Objective lane="all">

**🎯 What you'll do.** Polish the visual palette and swap the Laureate's voice. The voice is **one prompt change** in `airflow/sql/02_enrich.sql` — make Gemini compose as a pirate captain, IKEA assembly manual, ABBA chorus, somber Bergman narrator, anything. Re-trigger the DAG (~3 min) and watch every poem regenerate in the new voice. ~15 minutes.

**🤝 Why it matters.** This is the **second-loudest demo moment**. Generic AI poems are forgettable; pirate-captain pothole poems are unforgettable. Pick a voice that lands the joke for the room you're presenting to — judges will remember "the Garage that did the IKEA-manual potholes" three weeks after they've forgotten everything else. **The persona you pick here is also the foundation you'll deepen during the open build window (Quest 7)** — ask Antigravity CLI to apply the same voice across the whole app (page title, sidebar, theme color, analyst prompts), not just the ode.

</Objective>

> Optional. ~15 minutes. The whole team or one person.

Two ways to give the Office personality without rebuilding anything.

---

## A. Change the Laureate's voice

The Laureate's style is one prompt in one file: `pothole-poet/airflow/sql/02_enrich.sql`.

Open it. Find the `prompt =>` block. The default is *"a melancholic Swedish bureaucrat."* Swap it.

### Examples to steal

**Pirate captain:**
```
'Compose a single three-line sea shanty in the voice of a 17th-century Swedish pirate captain ',
'about the neighbourhood of ', neighbourhood, '. ',
```

**ABBA chorus writer:**
```
'Compose a single three-line ABBA-style chorus, with internal rhyme, ',
'about the potholes of ', neighbourhood, '. ',
```

**IKEA assembly manual:**
```
'Compose three terse, numbered, IKEA-assembly-style instructions ',
'for surviving the potholes of ', neighbourhood, '. No words; pictograms only described in text. ',
```

**ICA-handlare (corner-shop owner):**
```
'Compose a single three-line lament in the voice of a Gothenburg ICA-handlare ',
'whose delivery van keeps hitting potholes in ', neighbourhood, '. ',
```

### Apply it

1. Edit `02_enrich.sql`.
2. Re-upload to the Composer DAGs bucket:
   ```bash
   DAGS_BUCKET="$(gcloud composer environments describe the-laureate-bureau \
     --location=europe-west1 --format='value(config.dagGcsPrefix)')"
   gcloud storage cp ~/quest/pothole-poet/airflow/sql/02_enrich.sql "$DAGS_BUCKET/sql/"
   ```
3. Re-trigger the DAG from the Airflow UI.
4. Wait ~60 seconds. Refresh the Streamlit page.
5. The Laureate now speaks differently.

<Screenshot src="/quest/pothole-poet/img/streamlit_voiceswap.png" caption="Streamlit page after a voice swap — same neighbourhoods, different tone (e.g. pirate captain, IKEA manual, ABBA chorus)." />

## B. Polish the Office's look

`pothole-poet/streamlit/app.py` has a `PALETTE` dict near the top:

```python
PALETTE = {
    "charcoal":  "#1a1a2e",
    "warm_grey": "#f5f0eb",
    "pine":      "#2d6a4f",
    "copper":    "#b07d62",
}
```

Swap any colour. Swap the page emoji. Change the title. The header caption is one line below the title — rewrite it in your Office's voice.

If you want a logo, drop an SVG in `streamlit/` and `st.image()` it in the header.

Rebuild + roll out:

```bash
cd ~/quest/pothole-poet/streamlit

gcloud builds submit \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:theme \
  --region=europe-west1

kubectl set image deployment/pothole-laureate \
  pothole-laureate=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:theme \
  -n laureate

kubectl rollout status deployment/pothole-laureate -n laureate
```

---

## Done

<Gotchas>
- <strong>Re-triggered the DAG but odes look the same.</strong> Did you re-upload <code>02_enrich.sql</code> to <code>$DAGS_BUCKET/sql/</code>? The DAG reads from the bucket, not your local copy.
- <strong>Gemini truncates long prompts.</strong> Keep the prompt under ~600 chars. The Laureate compresses the conceit; you don&rsquo;t need to over-specify.
- <strong>Palette swap doesn&rsquo;t apply after rollout.</strong> Streamlit caches CSS aggressively &mdash; hard-refresh in the browser. If the colour <em>still</em> doesn&rsquo;t change, confirm the new image rolled out: <code>kubectl describe deployment pothole-laureate -n laureate | grep Image</code>.
- <strong>Voice change made the JSON parser brittle.</strong> If you switched to a heavily formatted style (e.g. lists, JSON), the downstream renderer may struggle. Stick to plain prose with a 3-line constraint.
</Gotchas>

<Shipped>
The Office has personality. <strong>The Laureate now speaks in your team&rsquo;s chosen voice and the page wears your team&rsquo;s palette.</strong> Two prompts, one rollout.
</Shipped>

The Office has personality. Move to Quest 6 for the audience-input loop, or stay here and iterate.

➡️ Optional next: **Quest 6 — Make it yours** (sidebar on the left).
