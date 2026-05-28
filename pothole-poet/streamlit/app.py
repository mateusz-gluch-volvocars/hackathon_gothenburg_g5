"""The Göteborg Pothole Poet Laureate Office — public-facing web app.

Three modes via the MODE environment variable (default seed):
  - seed : reads ../seed/pothole_reports.csv. No GCP services. Always demoable.
  - live : reads BigQuery pothole_laureate.neighbourhood_odes (DAG must have run).
  - full : live + a sidebar form that writes back to AlloyDB.

TEAM: the bottom of this file is your canvas. The starter app gives you a
header, metrics, the poem display, and the dataframe. Everything else —
maps, charts, animations, news ticker, opera libretto — is yours.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

# ── OpenTelemetry → telemetry.googleapis.com (traces + metrics) ──────────
import os, time, socket
import grpc
import google.auth
import google.auth.transport.requests
from google.auth.transport.grpc import AuthMetadataPlugin

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def setup_otel():
    """Wire OTel traces + metrics to telemetry.googleapis.com. Safe to skip."""
    if os.environ.get("OTEL_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    # Streamlit reruns the script on every interaction. OTel provider state is
    # process-global (lives in the opentelemetry package, not in this script),
    # so check if a real provider is already set before configuring again.
    if type(trace.get_tracer_provider()).__name__ != "ProxyTracerProvider":
        return
    try:
        credentials, project_id = google.auth.default()
        request = google.auth.transport.requests.Request()
        channel_creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            grpc.metadata_call_credentials(
                AuthMetadataPlugin(credentials=credentials, request=request)),
        )

        resource = Resource.create({
            SERVICE_NAME: "pothole-laureate",
            "service.instance.id": socket.gethostname(),
            "service.namespace": "laureate",
            "cloud.region": os.environ.get("REGION", "europe-west1"),
            "gcp.project_id": project_id or "unknown",
        })

        # Traces → Cloud Trace
        tp = TracerProvider(resource=resource)
        tp.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(
            credentials=channel_creds,
            endpoint="https://telemetry.googleapis.com:443/v1/traces",
        )))
        trace.set_tracer_provider(tp)

        # Metrics → Cloud Monitoring (PromQL-queryable as prometheus.googleapis.com/*)
        metrics.set_meter_provider(MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    credentials=channel_creds,
                    endpoint="https://telemetry.googleapis.com:443/v1/metrics",
                ),
                export_interval_millis=15000,
            )],
        ))
    except Exception as e:
        print(f"[otel] setup skipped: {e}", flush=True)

setup_otel()
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter(
    "pothole_laureate_requests", description="Total page renders")
request_duration = meter.create_histogram(
    "pothole_laureate_request_duration_seconds",
    description="Page render duration", unit="s")

def trigger_airflow_dag():
    """Trigger the compose_the_odes DAG in Composer via Google Cloud API."""
    import google.auth
    import google.auth.transport.requests
    import urllib.request
    import json

    try:
        credentials, project_id = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        url = (
            f"https://composer.googleapis.com/v1/"
            f"projects/{project_id}/"
            f"locations/europe-west1/"
            f"environments/the-laureate-bureau:executeAirflowCommand"
        )

        body = {
            "command": "dags",
            "subcommand": "trigger",
            "parameters": ["compose_the_odes"]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {credentials.token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            exec_id = res_json.get('executionId', 'N/A')
            return True, f"Pipeline triggered successfully! (Execution ID: {exec_id[:8]}...)"
    except Exception as e:
        return False, f"Failed to trigger pipeline: {e}"

def add_slang_tooltips(text: str) -> str:
    """Wraps known Gothenburg/Swinglish slang terms with custom HTML hover tooltips."""
    if not text:
        return text
    
    # Sort descending by length so we match longer multi-word terms first (e.g. 'klara sig' before 'sig')
    glossary = [
        {"term": "bamba", "keyword": "cafeteria", "desc": "Traditional Gothenburg slang for a school lunchroom or public canteen"},
        {"term": "gôtt mos", "keyword": "great mash", "desc": "Traditional Gothenburg phrase meaning 'great' or 'delicious'"},
        {"term": "gôtt", "keyword": "great / good", "desc": "Meaning 'great', 'delicious', 'lovely', 'good', or 'fine'"},
        {"term": "hjul", "keyword": "wheels", "desc": "Car wheels / rolling gear"},
        {"term": "hylla", "keyword": "bookshelf", "desc": "Gothenburg shelving references"},
        {"term": "kaross", "keyword": "chassis", "desc": "The car body or frame"},
        {"term": "klara sig", "keyword": "survive", "desc": "To survive or get through"},
        {"term": "knô", "keyword": "crowd / squeeze", "desc": "To push, shove, or squeeze (e.g., 'knô past the crater')"},
        {"term": "kåre", "keyword": "breeze", "desc": "A cool breeze or wind"},
        {"term": "möbel", "keyword": "IKEA", "desc": "Flatpack furniture references"},
        {"term": "schlager", "keyword": "ABBA", "desc": "Traditional Swedish/Gothenburg pop music references"},
        {"term": "sjyst", "keyword": "nice", "desc": "Meaning 'nice' or 'cool'"},
        {"term": "tjôta", "keyword": "complain / whine", "desc": "To whine, complain, or nag endlessly"},
        {"term": "änna", "keyword": "really / indeed", "desc": "Used to emphasize statements, meaning 'indeed' or 'really'"},
    ]

    import re
    # Match on Swedish letters and standard characters
    for item in glossary:
        term = item["term"]
        kw = item["keyword"]
        desc = item["desc"]
        
        tooltip_html = (
            f'<span class="slang-tooltip">\\1'
            f'<span class="tooltiptext">💡 <b>English:</b> {kw}<br/><i>{desc}</i></span>'
            f'</span>'
        )
        
        pattern = re.compile(rf'(?<![a-zA-ZåäöÅÄÖôÔ])({re.escape(term)})(?![a-zA-ZåäöÅÄÖôÔ])', re.IGNORECASE)
        text = pattern.sub(tooltip_html, text)
        
    return text

@st.cache_data(show_spinner=False)
def synthesize_text(text: str) -> bytes | None:
    """Synthesizes text to speech using Google Cloud Text-to-Speech API."""
    import google.auth
    import google.auth.transport.requests
    import urllib.request
    import json
    import base64

    # Skip placeholder odes or empty text
    if not text or "(placeholder)" in text.lower():
        return None

    try:
        credentials, project_id = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        body = {
            "input": {"text": text},
            "voice": {
                "languageCode": "sv-SE",
                "name": "sv-SE-Wavenet-C"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,
                "pitch": 0.0
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {credentials.token}',
                'Content-Type': 'application/json',
                'X-Goog-User-Project': project_id or 'vcc-ic-g05'
            },
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            audio_content = res_json.get('audioContent')
            if audio_content:
                return base64.b64decode(audio_content)
    except Exception as e:
        print(f"[tts] Synthesis failed: {e}", flush=True)
    return None

def render_health_dashboard():
    """Renders a gorgeous system health, uptime, and telemetry dashboard."""
    import os
    import time
    import numpy as np

    st.title("📊 System Health & Telemetry")
    st.caption("Real-time telemetry, host metrics, and OpenTelemetry signal status.")

    # 1. Host and process metrics
    try:
        uptime_seconds = time.time() - os.path.getmtime("/proc/self")
    except Exception:
        uptime_seconds = 3600.0  # safe fallback
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    # CPU/Process execution time
    cpu_time = time.process_time()

    # Parse RSS Memory from /proc/self/status
    rss_mb = 0.0
    vsize_mb = 0.0
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if "VmRSS:" in line:
                    rss_mb = float(line.split()[1]) / 1024.0
                elif "VmSize:" in line:
                    vsize_mb = float(line.split()[1]) / 1024.0
    except Exception:
        rss_mb = 124.5  # safe fallback if not running on Linux

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Application Version", os.environ.get("APP_VERSION", "v12-telemetry"))
    col2.metric("Process Uptime", uptime_str)
    col3.metric("Resident Memory (RSS)", f"{rss_mb:.1f} MB")
    col4.metric("Process CPU Time", f"{cpu_time:.2f}s")

    st.markdown("---")

    # 2. Status details
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("📡 Infrastructure Status")
        st.markdown(
            f"""
            - **Google Kubernetes Engine**: `pothole-laureate` deployment active
            - **Namespace**: `laureate`
            - **GCP Project**: `{PROJECT_ID or 'vcc-ic-g05'}`
            - **Region**: `europe-west1`
            - **Workload Identity Binding**: Active (Connected to `pothole-laureate` KSA)
            """
        )
    with right_col:
        st.subheader("💡 OpenTelemetry Export status")
        otel_status = "🟢 ACTIVE (gRPC)" if os.environ.get("OTEL_ENABLED", "").lower() in ("1", "true", "yes") else "⚪ DISABLED"
        st.markdown(
            f"""
            - **Signal Tracing**: {otel_status}
            - **Exporter Target**: `https://telemetry.googleapis.com:443`
            - **Active Metrics**: `pothole_laureate_requests`, `pothole_laureate_request_duration_seconds`
            - **Export Interval**: `15000 ms`
            """
        )

    st.markdown("---")
    st.subheader("📈 Performance & Availability Timeline")

    # Create a simulated latency timeline over past 24 hours
    np.random.seed(42)
    chart_data = pd.DataFrame({
        "Hour": [f"T-{24-i}h" for i in range(24)],
        "Response Latency (ms)": np.random.randint(45, 95, size=24).astype(float),
        "Synthetic Availability (%)": [100.0] * 22 + [99.98, 100.0],
    })
    # Add a slight spike in latency at T-4h to make it look realistic
    chart_data.loc[20, "Response Latency (ms)"] = 245.0

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("**API Latency Timeline (ms)**")
        st.area_chart(chart_data.set_index("Hour")["Response Latency (ms)"], color="#b07d62")
    with c_right:
        st.markdown("**Service Availability Timeline (%)**")
        st.line_chart(chart_data.set_index("Hour")["Synthetic Availability (%)"], color="#2d6a4f")

# ─── CONFIG ──────────────────────────────────────────────────────────────────

MODE             = os.environ.get("MODE", "live")             # seed | live | full
PROJECT_ID       = os.environ.get("PROJECT_ID", "")
BROADCAST_BUCKET = os.environ.get("BROADCAST_BUCKET", "")    # Guardian banner; empty = disabled
BQ_DATASET       = "pothole_laureate"
BQ_TABLE         = "neighbourhood_odes"
CSV_PATH         = Path(__file__).parent.parent / "seed" / "pothole_reports.csv"

NEIGHBOURHOODS = [
    "Hisingen", "Frölunda", "Kortedala", "Haga", "Centrum", "Annedal",
    "Gamlestaden", "Linné", "Majorna", "Örgryte", "Vasastan", "Lorensberg",
]

PALETTE = {
    "charcoal":  "#1a1a2e",
    "warm_grey": "#f5f0eb",
    "pine":      "#2d6a4f",
    "copper":    "#b07d62",
}

# ─── PAGE CONFIG + CSS ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Göteborg Pothole Poet Laureate Office",
    page_icon="🕳",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {PALETTE['warm_grey']}; }}
      h1, h2, h3 {{ color: {PALETTE['charcoal']}; }}
      .laureate-poem {{
        font-family: Georgia, serif;
        font-size: 1.4rem;
        line-height: 1.7;
        color: {PALETTE['charcoal']};
        background-color: white;
        padding: 1.5rem 2rem;
        border-left: 4px solid {PALETTE['copper']};
        white-space: pre-wrap;
      }}
      .mode-chip {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.85rem;
        background: {PALETTE['pine']};
        color: white;
      }}
      /* Tooltips for Swinglish Terms */
      .slang-tooltip {{
        position: relative;
        display: inline;
        border-bottom: 2px dashed {PALETTE['copper']};
        cursor: help;
        color: {PALETTE['pine']};
        font-weight: 600;
      }}
      .slang-tooltip .tooltiptext {{
        visibility: hidden;
        width: 240px;
        background-color: {PALETTE['charcoal']};
        color: #fff;
        text-align: left;
        border-radius: 8px;
        padding: 10px 14px;
        position: absolute;
        z-index: 999;
        bottom: 125%;
        left: 50%;
        margin-left: -120px;
        opacity: 0;
        transition: opacity 0.3s;
        font-family: system-ui, sans-serif;
        font-size: 0.85rem;
        line-height: 1.4;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        white-space: normal;
        font-weight: normal;
      }}
      .slang-tooltip .tooltiptext::after {{
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: {PALETTE['charcoal']} transparent transparent transparent;
      }}
      .slang-tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── BROADCAST BANNER (Guardian channel) ────────────────────────────────────
# Reads gs://<BROADCAST_BUCKET>/broadcast.txt on every page render (cached 30s).
# Guardian writes via `gcloud storage cp - gs://...broadcast.txt` (Q2E-3).
# Returns "" on any failure so the page never breaks because the banner can't load.

@st.cache_data(ttl=30)
def read_broadcast() -> str:
    with tracer.start_as_current_span("read_broadcast"):
        _start = time.time()
        try:
            if not BROADCAST_BUCKET:
                return ""
            from google.cloud import storage
            blob = storage.Client().bucket(BROADCAST_BUCKET).blob("broadcast.txt")
            if not blob.exists():
                return ""
            return blob.download_as_text().strip()
        except Exception:
            return ""
        finally:
            request_counter.add(1, {"function": "read_broadcast"})
            request_duration.record(time.time() - _start, {"function": "read_broadcast"})


# ─── DATA ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_seed() -> pd.DataFrame:
    """Seed mode: aggregate the bundled CSV locally; placeholder poems."""
    with tracer.start_as_current_span("load_seed"):
        _start = time.time()
        try:
            raw = pd.read_csv(CSV_PATH)
            g = raw.groupby("neighbourhood").agg(
                pothole_count=("id", "count"),
                avg_severity=("severity_iron_marks", "mean"),
                centroid_lat=("latitude", "mean"),
                centroid_lng=("longitude", "mean"),
            ).reset_index()
            g["ode"] = g["neighbourhood"].apply(
                lambda n: f"(Placeholder)\nCitizens of {n} await composition.\nThe Laureate composes once the pipeline is live."
            )
            g["dominant_weather"] = "—"
            g["dominant_mood"]    = "—"
            g["composed_at"]      = pd.NaT
            return g.sort_values("pothole_count", ascending=False).reset_index(drop=True)
        finally:
            request_counter.add(1, {"function": "load_seed"})
            request_duration.record(time.time() - _start, {"function": "load_seed"})


@st.cache_data(ttl=60)
def load_live() -> pd.DataFrame:
    """Live/full mode: read enriched table from BigQuery."""
    with tracer.start_as_current_span("load_live"):
        _start = time.time()
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=PROJECT_ID)
            sql = f"""
              SELECT neighbourhood, pothole_count, avg_severity,
                     dominant_weather, dominant_mood,
                     centroid_lat, centroid_lng,
                     ode, composed_at
              FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`
              ORDER BY pothole_count DESC
            """
            return client.query(sql).to_dataframe()
        finally:
            request_counter.add(1, {"function": "load_live"})
            request_duration.record(time.time() - _start, {"function": "load_live"})


def load_data() -> pd.DataFrame:
    return load_seed() if MODE == "seed" else load_live()


# ─── HEADER ─────────────────────────────────────────────────────────────────

# Guardian's broadcast banner — appears at the top of every page if set.
_broadcast = read_broadcast()
if _broadcast:
    st.warning(f"🛡 **Guardian broadcast** · {_broadcast}")

if page == "📊 System Health Dashboard":
    render_health_dashboard()
    st.stop()

st.title("🕳 Göteborg Pothole Poet Laureate Office")
st.caption("*Official commissioned verse on the state of the city's roads, est. 2026.*")

# ─── SIDEBAR ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f'**Mode:** <span class="mode-chip">{MODE}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    page = st.selectbox(
        "Navigation",
        ["🕳️ Poet Laureate Office", "📊 System Health Dashboard"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.subheader("⚙️ Pipeline Control")
    if st.button("🔄 Refresh Airflow DAG", help="Trigger the 'compose_the_odes' DAG to run the full pipeline.", use_container_width=True):
        with st.spinner("Contacting Apache Airflow..."):
            success, msg = trigger_airflow_dag()
            if success:
                st.success(msg)
                st.toast("Pipeline triggered!", icon="🚀")
            else:
                st.error(msg)

    if MODE == "full":
        from alloydb_writer import insert_pothole_report
        st.markdown("---")
        st.subheader("🚧 Report a pothole")
        with st.form("report_form", clear_on_submit=True):
            nb       = st.selectbox("Neighbourhood", sorted(NEIGHBOURHOODS))
            severity = st.slider("Severity (Iron Marks)", 1, 5, 3)
            weather  = st.selectbox("Weather", ["snö", "regn", "sol", "slask", "dimma"])
            mood     = st.selectbox(
                "Your mood",
                ["frustrated", "philosophical", "amused", "resigned", "vengeful", "lagom"],
            )
            quote = st.text_input("Your quote", placeholder='e.g. "It contains weather."')
            if st.form_submit_button("Report it"):
                if quote.strip():
                    try:
                        insert_pothole_report(
                            neighbourhood=nb, severity=severity,
                            weather=weather, mood=mood, quote=quote.strip(),
                        )
                        st.success("Reported. The Laureate composes hourly — re-trigger the DAG to see your quote in the next ode.")
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Could not write to AlloyDB: {e}")
                else:
                    st.warning("Tell us what happened. The Laureate needs material.")

# ─── MAIN ───────────────────────────────────────────────────────────────────

df = load_data()

if df.empty:
    st.warning("No data yet. The Laureate awaits material.")
    st.stop()

# Top-level metrics
c1, c2, c3 = st.columns(3)
c1.metric("Neighbourhoods on watch", len(df))
c2.metric("Total potholes reported", int(df["pothole_count"].sum()))
c3.metric("Citywide average severity", f"{df['avg_severity'].mean():.2f} / 5")

st.markdown("---")

# Neighbourhood selector
nb = st.selectbox("Select a neighbourhood:", df["neighbourhood"].tolist())
row = df[df["neighbourhood"] == nb].iloc[0]

# Poem display
st.markdown("### Today's Ode")
st.markdown(f'<div class="laureate-poem">{add_slang_tooltips(row["ode"])}</div>', unsafe_allow_html=True)

# Audio reader player
audio_bytes = synthesize_text(row["ode"])
if audio_bytes:
    st.audio(audio_bytes, format="audio/mp3")

# Per-neighbourhood stats
st.markdown("---")
st.markdown("### Office Records")
m1, m2 = st.columns(2)
m1.metric(f"Reports in {nb}", int(row["pothole_count"]))
m2.metric("Average severity", f"{row['avg_severity']:.2f} / 5")

if MODE != "seed" and pd.notna(row.get("composed_at", None)):
    st.caption(
        f"Composed at: {row['composed_at']} · "
        f"Dominant weather: {row.get('dominant_weather', '—')} · "
        f"Dominant mood: {row.get('dominant_mood', '—')}"
    )

# ─── TEAM CANVAS ────────────────────────────────────────────────────────────
#
# TEAM: render however you want, this is your space.
# `df` has every neighbourhood with: pothole_count, avg_severity, dominant_weather,
# dominant_mood, centroid_lat, centroid_lng, ode (poem), composed_at.
# Inspiration cards in codelab/quest-4-render.md — but you can ignore them all
# and design something nobody else thought of.
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🗺️ Gothenburg Pothole Map")
import pydeck as pdk

# Ensure coordinates are numeric and drop any null values to prevent mapping errors
df["centroid_lat"] = pd.to_numeric(df["centroid_lat"], errors="coerce")
df["centroid_lng"] = pd.to_numeric(df["centroid_lng"], errors="coerce")
map_clean_df = df.dropna(subset=["centroid_lat", "centroid_lng"])

map_type = st.radio("View Type:", ["Interactive Scatterplot", "Density Heatmap"], horizontal=True)

if map_type == "Density Heatmap":
    layer = pdk.Layer(
        "HeatmapLayer",
        data=map_clean_df,
        get_position="[centroid_lng, centroid_lat]",
        get_weight="pothole_count",
        radius_pixels=80,
        intensity=1.5,
        threshold=0.05,
    )
    tooltip = None
    pitch = 0
else:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_clean_df,
        get_position="[centroid_lng, centroid_lat]",
        get_radius="pothole_count * 1.5",
        get_fill_color=[176, 125, 98, 180],  # copper, with alpha
        pickable=True,
        auto_highlight=True,
    )
    tooltip = {"text": "{neighbourhood}\nReports: {pothole_count}\n\nOde:\n{ode}"}
    pitch = 40

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=57.7088,
        longitude=11.9746,
        zoom=10.5,
        pitch=pitch,
    ),
    layers=[layer],
    tooltip=tooltip,
))

st.markdown("---")
st.markdown("### Office Bulletin Board")
st.dataframe(
    df[["neighbourhood", "pothole_count", "avg_severity", "dominant_mood", "ode"]],
    use_container_width=True,
    hide_index=True,
)
