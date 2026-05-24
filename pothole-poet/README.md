# Quest #1 — The Pothole Poet

> *"The road to Göteborg is paved with potholes. The road to insight is paved with SQL."*
> — A future Foreman, probably

A 3-hour collaborative build for a 4-person team. You will stand up an end-to-end data application on Google Cloud — operational database, orchestrated pipeline, AI-enriched analytics, and a public-facing web app — themed around a fictional **Göteborg Pothole Poet Laureate Office**.

## The story

The City of Göteborg has commissioned a **Pothole Poet Laureate** to chronicle road decay in officially-stamped verse. Citizens report potholes; the Office aggregates them per neighbourhood; the Laureate (Gemini) composes a three-line poem about each neighbourhood's pothole condition; the Office publishes it through a web app the team designs.

It is *exactly* as serious as it sounds.

## What the team builds

| Layer | Service | What it does |
|---|---|---|
| Operational store | **AlloyDB** | Holds 5,000 synthetic pothole reports across 12 real Gothenburg neighbourhoods |
| Orchestration | **Managed Service for Apache Airflow** (Composer Gen 3) | Runs the `compose_the_odes` DAG hourly |
| Analytical store | **BigQuery** | Receives federated reports, aggregates per neighbourhood, calls `AI.GENERATE` to compose poems |
| Demo surface | **Streamlit on GKE Autopilot** (Gateway API global LB) | Reads the enriched table; the team designs the look |
| Editor | **Cloud Workstations** | Browser-based IDE + terminal for all four lane builders |

The full architecture diagram + the platform's split between "pre-provisioned"
and "participant clicks" lives on the **hub**:
[https://nordic-agents-hub-624958632298.europe-west1.run.app/](https://nordic-agents-hub-624958632298.europe-west1.run.app/) →
*About the platform*.

## The four lanes

When the build sprint starts, the team splits four ways:

| Lane | Role | Owns | First codelab page |
|---|---|---|---|
| A | **Airflow Lead** | Managed Airflow + the DAG (3 pages) | [`codelab/quest-2b-environment.md`](./codelab/quest-2b-environment.md) |
| B | **AlloyDB Lead** | AlloyDB cluster + schema + seed (3 pages) | [`codelab/quest-2a-cluster.md`](./codelab/quest-2a-cluster.md) |
| C | **BigQuery Lead** | BigQuery dataset + AlloyDB federation (3 pages, +1 optional) | [`codelab/quest-2c-tour.md`](./codelab/quest-2c-tour.md) |
| D | **GKE / App Lead** | Streamlit app + GKE Autopilot + Gateway API (5 pages) | [`codelab/quest-2d-cluster.md`](./codelab/quest-2d-cluster.md) |

All four lanes start at the same moment. They converge at [`codelab/quest-3-wire.md`](./codelab/quest-3-wire.md).

## Tier mapping

| Tier | What ships | Time | Demo punch |
|---|---|---|---|
| 🥉 **Bronze** | Streamlit on GKE Autopilot reading bundled `seed.csv`, exposed via a Gateway-API global LB on plain HTTP. Twelve neighbourhoods, twelve placeholder poems. | ~45 min | A page exists. Always demoable. |
| 🥈 **Silver** | Full pipeline. Streamlit reads `pothole_laureate.neighbourhood_odes` from BigQuery. Real Gemini-composed poems per neighbourhood. | ~85 min | Live AI poems from real (synthetic) citizen quotes. |
| 🥇 **Gold** | Silver + a "Report a Pothole" form in Streamlit that writes to AlloyDB + real HTTPS via Certificate Manager (load balancer authorization, `<ip>.nip.io` hostname). Re-trigger the DAG; watch the poems regenerate. | ~100 min | Audience submits an absurd quote at demo time and watches it land in a freshly-composed poem 3 minutes later, on a properly-certificated URL. |

## What's in this directory

```
pothole-poet/
├── README.md                          # this file
├── alloydb/
│   ├── schema.sql                     # CREATE TABLE pothole_reports + indexes
│   └── seed.sql                       # COPY from gs://{project_id}-seed/pothole_reports.csv
├── airflow/
│   ├── compose_the_odes.py            # the DAG (Airflow 3.1, two BigQuery tasks)
│   └── sql/
│       ├── 01_federate.sql            # AlloyDB → BQ via Lakehouse federation
│       └── 02_enrich.sql              # GROUP BY neighbourhood + AI.GENERATE poems
├── bigquery/
│   ├── setup_alloydb_connection.sh    # Lane C runs this to create the BQ→AlloyDB connection
│   └── test_federation.sql            # Lane C smoke check
├── Dockerfile                         # built from pothole-poet/ so seed CSV is in context (see Q2D-2)
├── streamlit/
│   ├── app.py                         # Bronze | Silver | Gold modes via CONFIG switch
│   ├── alloydb_writer.py              # Gold-tier write-back helper
│   ├── requirements.txt
│   ├── .streamlit/config.toml         # pinned light theme + Office palette
│   └── k8s/                           # Kubernetes manifests
│       ├── namespace-and-sa.yaml      # namespace + ServiceAccount
│       ├── deployment.yaml            # 2 replicas of pothole-laureate
│       ├── service.yaml               # ClusterIP + NEG annotation
│       ├── gateway.yaml               # gke-l7-global-external-managed, HTTP :80
│       ├── httproute.yaml             # routes traffic to the Service
│       └── gold/
│           └── gateway-https.yaml     # Q6 Gold overlay — adds HTTPS :443
├── seed/
│   ├── generator.py                   # synthetic data generator
│   ├── citizen_quotes.txt             # 120 Volvo-coded one-liners
│   └── pothole_reports.csv            # generated; uploaded to seed bucket
└── codelab/
    ├── quest-1-signin.md              # All · 1/4 — Volvo SSO sign-in, name the four Console landmarks
    ├── quest-1-navigation.md          # All · 2/4 — Project picker, search bar, pin the four lab products
    ├── quest-1-vpc.md                 # All · 3/4 — Look at your Garage's VPC + no-public-IP policy
    ├── quest-1-warmup.md              # All · 4/4 — Open Workstation, clone repo, agentic check, lane pick
    ├── quest-2a-cluster.md            # Lane B · 1/3 — Create AlloyDB cluster + instance
    ├── quest-2a-schema.md             # Lane B · 2/3 — Run schema in AlloyDB Studio
    ├── quest-2a-seed.md               # Lane B · 3/3 — psql \copy 5,000 reports from terminal
    ├── quest-2b-environment.md        # Lane A · 1/3 — Create Managed Airflow environment
    ├── quest-2b-upload.md             # Lane A · 2/3 — Upload DAG + sql/ to GCS bucket
    ├── quest-2b-trigger.md            # Lane A · 3/3 — Trigger DAG, watch Gemini compose
    ├── quest-2c-tour.md               # Lane C · 1/3 — Tour BQ Studio + warm-up query
    ├── quest-2c-federation.md         # Lane C · 2/3 — Wire + test AlloyDB federation
    ├── quest-2c-playground.md         # Lane C · 3/3 — The Analyst's Bench (Phase A pre-loaded data + Phase B joins)
    ├── quest-2d-cluster.md            # Lane D · 1/5 — Stand up GKE Autopilot cluster
    ├── quest-2d-image.md              # Lane D · 2/5 — Build container with Cloud Build
    ├── quest-2d-identity.md           # Lane D · 3/5 — Workload Identity Federation to BigQuery
    ├── quest-2d-deploy.md             # Lane D · 4/5 — Apply Deployment + Service
    ├── quest-2d-gateway.md            # Lane D · 5/5 — Apply Gateway + HTTPRoute (Bronze HTTP)
    ├── quest-3-wire.md                # Convergence — trigger DAG, kubectl set env to SILVER
    ├── quest-4-render.md              # Team huddle — design the visual
    ├── quest-5-theme.md               # Polish — palette + AI prompt voice
    └── quest-6-gold-loop.md           # Stretch — Submit-a-Pothole writeback + real HTTPS
```

## The demo punchline

For Gold tier, at demo time, a judge submits an absurd citizen quote — *"My pothole has political opinions"* — through the team's Streamlit form. Three minutes later the page refreshes; that quote is baked into the freshly-composed poem about whichever neighbourhood the judge picked. That's the moment the room *gets it.*

## Citizen quotes — the secret ingredient

The synthetic data generator pulls from [`seed/citizen_quotes.txt`](./seed/citizen_quotes.txt) — 120 Volvo-coded one-liners that give Gemini real material to riff on. Examples:

- *"My V90 said 'good morning' and then 'goodbye'."*
- *"The pothole had its own postcode."*
- *"I have driven this road for 27 years. The pothole has driven it for 28."*

This is what keeps the poems from being generic AI mush. Edit them. Add your own. The DAG picks them up next run.

## Make it yours

There's no template for the Streamlit page. [`codelab/quest-4-render.md`](./codelab/quest-4-render.md) has inspiration cards — map of Göteborg, wall of poems on parchment, severity dashboard, opera libretto — but designing something none of them suggested is equally encouraged. Every Garage's Office looks different. **The Office is yours to staff.**
