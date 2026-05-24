# 🎨 Quest 4 — Render the Poems

<Objective lane="all">

**🎯 What you'll do.** As a team, decide what your Streamlit Office should *look* like. Map of Göteborg with neighbourhood pins? Long scroll of poems on parchment? Severity dashboard with charts? An Excel-like grid? An opera libretto? You have ~25 minutes, the four of you, to make it yours. Edit happens below the `# TEAM CANVAS` marker in `streamlit/app.py`.

**🤝 Why it matters.** The platform refused to pick this for you on purpose. **Every Garage's Office looks different** — that's what makes the demo train interesting. The judges have already seen the Streamlit defaults; they want to see what *your* Office decided. This is the page where the Quest stops being a tutorial and starts being a project.

</Objective>

> The whole team. ~25 minutes.

You shipped Silver. Twelve poems are live on a generic dataframe page. Now decide: **how does the Göteborg Pothole Poet Laureate Office want to present its work to the world?**

The platform refuses to pick the look for you. That's the team's job. Surprise everyone at demo.

---

## Where to edit

`pothole-poet/streamlit/app.py` — scroll to the **`# TEAM CANVAS`** block near the bottom. Everything above it is plumbing. Everything below it is yours.

<Screenshot src="/quest/pothole-poet/img/team_canvas.png" caption="The TEAM CANVAS marker in app.py — everything below this line is the team's playground." />

The dataframe `df` available to you contains:

| column | type | what it holds |
|---|---|---|
| `neighbourhood` | string | one of 12 |
| `pothole_count` | int | total reports |
| `avg_severity` | float | 1.0 to 5.0 |
| `dominant_weather` | string | snö / regn / sol / slask / dimma |
| `dominant_mood` | string | frustrated / philosophical / amused / resigned / vengeful / lagom |
| `centroid_lat` / `centroid_lng` | float | for plotting on a map |
| `ode` | string | the Laureate's three-line poem |
| `composed_at` | timestamp | when the Laureate composed it |

---

## Three inspiration cards (you can ignore them all)

### Map mode

Use `pydeck` (already in `requirements.txt`) to render Gothenburg as a choropleth. Each neighbourhood gets a marker scaled by `pothole_count`. Hovering shows the ode in a tooltip.

```python
import pydeck as pdk

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(latitude=57.71, longitude=11.97, zoom=11),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["centroid_lng", "centroid_lat"],
            get_radius="pothole_count * 0.5",
            get_fill_color=[176, 125, 98, 180],  # copper, with alpha
            pickable=True,
        ),
    ],
    tooltip={"text": "{neighbourhood}\n{ode}"},
))
```

### Wall mode

A scrollable parchment of all twelve poems with a severity bar next to each.

```python
for _, row in df.iterrows():
    with st.container(border=True):
        st.markdown(f"### {row['neighbourhood']}")
        st.markdown(f"<div class='laureate-poem'>{row['ode']}</div>", unsafe_allow_html=True)
        st.progress(row['avg_severity'] / 5.0, text=f"{row['avg_severity']:.1f} / 5 iron marks")
```

### Dashboard mode

A Volvo-style instrument cluster — each neighbourhood is a gauge, the central console shows the active ode.

```python
import plotly.graph_objects as go

cols = st.columns(4)
for i, (_, row) in enumerate(df.iterrows()):
    with cols[i % 4]:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row['avg_severity'],
            title={'text': row['neighbourhood']},
            gauge={'axis': {'range': [0, 5]},
                   'bar': {'color': "#b07d62"},
                   'threshold': {'line': {'color': "#1a1a2e", 'width': 4},
                                 'thickness': 0.75, 'value': 4}},
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
```

---

## Or: do something nobody else thought of

- A news ticker scrolling all twelve poems across the bottom
- An "Office hours" page that picks a different poem each minute
- A pothole confessional booth (text-to-speech reads the poem aloud)
- An animated cracked-asphalt background
- A leaderboard of neighbourhoods by "drama level"
- An opera libretto layout with stage directions
- A retro 1970s government bulletin design
- A Volvo dashboard warning-light interface
- ...whatever fits your Office's personality

The platform doesn't care. The judges will.

---

## Iterate

Edit `app.py`. Save. Rebuild + roll out:

```bash
cd ~/quest/pothole-poet/streamlit

gcloud builds submit \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v2 \
  --region=europe-west1

kubectl set image deployment/pothole-laureate \
  pothole-laureate=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v2 \
  -n laureate

kubectl rollout status deployment/pothole-laureate -n laureate
```

Each rebuild is ~1-2 min (cached layers). The Gateway URL stays the same. Iterate fast — bump the tag (`:v3`, `:v4`, …) each time so the rolling restart picks up the change.

## Done

<Gotchas>
- <strong>pydeck map renders blank.</strong> Lat/lng are easy to swap. The dataframe column is <code>centroid_lng</code>, <code>centroid_lat</code> &mdash; pydeck wants <code>[longitude, latitude]</code> in <code>get_position</code>.
- <strong>Rollout succeeds but the page didn&rsquo;t change.</strong> Browser cache. Hard-refresh (<kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>). If still stale, confirm the new tag is rolled out: <code>kubectl describe deployment pothole-laureate -n laureate | grep Image</code>.
- <strong>Plotly gauge is too tall / overflows.</strong> Set <code>fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))</code> &mdash; the inspiration card has it; don&rsquo;t drop it.
- <strong>Page renders, but no data.</strong> The <code>load_silver()</code> function couldn&rsquo;t reach BigQuery &mdash; check that <code>TIER=SILVER</code> and <code>PROJECT_ID</code> are both set on the Deployment (<code>kubectl describe deployment pothole-laureate -n laureate | grep -A2 Environment</code>).
</Gotchas>

<Shipped>
The Office has a face. <strong>Your Streamlit app reflects your Garage&rsquo;s taste &mdash; map, dashboard, parchment, opera libretto, or whatever you cooked up.</strong> No two Garages will demo the same page; that&rsquo;s the point.
</Shipped>

When the team is happy: high-five. Move to Quest 5 to polish the Laureate's voice (or skip ahead to Quest 6 for the Gold-tier audience-input loop).

➡️ Optional next: **Quest 5 — Theme It** or **Quest 6 — The Gold Loop** (both in the sidebar).
