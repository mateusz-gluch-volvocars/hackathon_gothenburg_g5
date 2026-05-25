# Build context: pothole-poet/ (this directory), NOT pothole-poet/streamlit/.
#
# Why: app.py reads the seed CSV via
#   Path(__file__).parent.parent / "seed" / "pothole_reports.csv"
# which mirrors the source layout where streamlit/ and seed/ are siblings.
# Building from the parent keeps that layout inside the container, so seed
# mode renders the bundled CSV without any GCP services attached.

FROM python:3.12-slim

WORKDIR /app

# psycopg2 needs libpq + a build toolchain on slim base.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

COPY streamlit/requirements.txt streamlit/requirements.txt
RUN pip install --no-cache-dir -r streamlit/requirements.txt

COPY streamlit/ streamlit/
COPY seed/pothole_reports.csv seed/pothole_reports.csv

WORKDIR /app/streamlit

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD streamlit run app.py \
      --server.port=$PORT \
      --server.address=0.0.0.0 \
      --server.headless=true \
      --browser.gatherUsageStats=false
