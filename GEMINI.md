# Iron & Cloud hackathon

You are helping a developer at the Iron & Cloud hackathon (Volvo Cars and Google Cloud, Gothenburg 2026). They are working on Quest 1: The Pothole Poet, a data pipeline that turns synthetic citizen pothole reports into poetry using Gemini.

## The quest instructions

All step-by-step instructions live in `pothole-poet/codelab/`. Read these files before answering questions about a step. The codelab is the source of truth, not your training data.

The pages are numbered and ordered:

- Q1 (quest-1-*): Setup, sign-in, navigation, VPC check, workstation warmup, Antigravity CLI login, logging
- Q2A (quest-2a-*): AlloyDB cluster, schema, seed data
- Q2B (quest-2b-*): Managed Airflow environment, DAG upload, trigger
- Q2C (quest-2c-*): BigQuery tour, federation, AI.GENERATE playground
- Q2D (quest-2d-*): GKE Autopilot cluster, container image, WIF identity, deploy, Gateway
- Q2E (quest-2e-*): Uptime check, OpenTelemetry, dashboard, alert and broadcast
- Q3 (quest-3-wire): Wire the full pipeline end-to-end
- Q4 (quest-4-render): Switch Streamlit to live BigQuery data
- Q5 (quest-5-theme): Theme and polish
- Q6A (quest-6a-gold-form): Interactive form with AlloyDB writeback
- Q6B (quest-6b-https): HTTPS via Certificate Manager
- Q7 (quest-7-differentiate): Open-ended build window, differentiate to win

When a participant asks about a specific step, read the matching codelab file first and base your answer on what it says.

## Project safety

Every garage (team) has its own GCP project. All your work must stay inside that project.

- At the start of any session, ask the participant which GCP project their garage belongs to if you do not already know. Run `gcloud config get-value project` to confirm.
- Never create, modify, or delete resources in any other project.
- Never run commands without a `--project` flag or a confirmed `gcloud config set project`.
- If a command would affect resources outside the garage project, stop and ask.

## Four lanes

Each garage has four developers working in parallel on different lanes:

- AlloyDB Lead: Q2A (cluster, schema, seed)
- Airflow Lead: Q2B (environment, DAG upload, trigger)
- BigQuery Lead: Q2C (federation, AI.GENERATE)
- GKE / App Lead: Q2D (cluster, image, WIF, deploy, Gateway)

Respect lane ownership. If someone asks about another lane's work, point them at the codelab page instead of doing it for them. After Q2, all four lanes converge in Q3.

## Region and naming

- Region is always `europe-west1`. Never propose a different region.
- The Garage VPC is called `garage-vpc`. There is no default network.
- Read PROJECT_ID and PROJECT_NUMBER dynamically, never hard-code them.

## Things to never do

- Never propose resources outside `europe-west1`.
- Never delete the GKE cluster, AlloyDB cluster, Managed Airflow environment, or any infrastructure the team spent time creating.
- Never run `gcloud projects delete` or any project-level destructive command.
- Never guess project IDs, project numbers, or IP addresses. Always read them from the live environment.
- Never skip the codelab steps or take shortcuts that bypass the learning objectives.
- Never use Gemini models older than `gemini-3-flash-preview`. The regional endpoint does not work, use the global endpoint URL.
- Never use Cloud Composer Gen 1 or Gen 2. The product is now Managed Service for Apache Airflow Gen 3.
- Never use the legacy `--connection_type=CLOUD_SQL` flag for BigQuery connections to AlloyDB.
- Never grant `roles/run.invoker` to `allUsers` via gcloud (org policy blocks it).

## Code and config files

The repo contains starter code that participants use during the quest:

- `pothole-poet/streamlit/`: The Streamlit app (app.py, requirements.txt)
- `pothole-poet/Dockerfile`: Container image definition
- `pothole-poet/airflow/`: The Airflow DAG
- `pothole-poet/alloydb/`: Schema SQL files
- `pothole-poet/bigquery/`: BigQuery SQL files
- `pothole-poet/seed/`: Seed data (pothole_reports.csv)
- `pothole-poet/dashboards/`: Monitoring dashboard JSON

When helping with code changes, edit these files in place. Do not create new directories or restructure the project.

## Asking for help

If you are unsure about something, read the relevant codelab page. If the answer is not there, tell the participant to ask a Sherpa (a floating leader/helper in the room) rather than guessing.
