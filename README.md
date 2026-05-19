# Iron & Cloud — Quest content

This repo is what your **Cloud Workstation** clones at the start of the day. Everything you need to write, edit, and deploy lives in here.

The instructions for what to do — codelab pages, day flow, lane choreography — are on the hub:

> **(Placeholder for Cloud Run Hub URL)**

Open that, pick your **Garage**, and your assigned Quest opens.

---

## What's in here

Each top-level folder is one **Quest**. A Quest is a themed lab where a 4-person Garage builds an end-to-end data application on Google Cloud (AlloyDB → Managed Airflow → BigQuery → Streamlit on GKE Autopilot, fronted by a Gateway-API global load balancer).

| Folder | Quest | Status |
|---|---|---|
| [`pothole-poet/`](./pothole-poet/) | **The Pothole Poet** — compose municipal verse from synthetic citizen pothole reports across twelve real Göteborg neighbourhoods. | 🟢 Ready |

More Quests will be added as siblings of this folder. Your facilitator will tell you which one your Garage is assigned to.

---

## How to use this repo on the day

You don't *need* to read this README cold — the hub walks you through everything. But the short version is:

1. **Open your Cloud Workstation** (link on your workbench card).
2. **Clone this repo** into the workstation:
   ```bash
   git clone https://github.com/larsers/hackathon_gothenburg.git ~/quest
   cd ~/quest
   ```
3. **Open the hub**, pick your Garage, and follow the codelab. Every command and click path the codelab references lives in the right `pothole-poet/` (or other-Quest) subfolder.

---

## Licensing

See [`LICENSE`](./LICENSE).
