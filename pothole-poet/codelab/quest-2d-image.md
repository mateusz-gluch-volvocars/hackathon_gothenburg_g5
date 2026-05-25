# ☸ Quest 2D-2 — Build the Container Image

<Objective lane="guardian">

**🎯 What you'll do.** Run `gcloud builds submit` from `quests/pothole-poet/` to build the Streamlit container with Cloud Build and push it to your Garage's pre-provisioned Artifact Registry repo (`laureate`). ~5 minutes for the build + push. **No local Docker daemon involved** — Cloud Build runs the Dockerfile in Google's infrastructure.

**🤝 Why it matters.** GKE pulls images from a registry, not from your laptop or the Workstation. Without an image sitting in Artifact Registry, the next page (deploy) has nothing to schedule onto your cluster. This is the same Cloud Build → Artifact Registry pattern most teams use to ship production containers — one command, no local Docker daemon, the registry as the source of truth.

</Objective>

> Lane D · 2 of 5. ~5 minutes wall-clock (~1 min hands-on).

<QuickPath>

```bash
# Build context is pothole-poet/ (NOT pothole-poet/streamlit/) so the
# seed CSV is alongside the Streamlit app in the image — see the Concept block
# below for the path mechanic.
cd ~/quest/pothole-poet

gcloud builds submit \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v1 \
  --region=$REGION
# ✅ Expect: SUCCESS, with the digest of the pushed image

# Verify it landed
gcloud artifacts docker images list \
  europe-west1-docker.pkg.dev/$PROJECT_ID/laureate \
  --format="table(IMAGE,TAGS,UPDATE_TIME)"
# ✅ Expect: pothole-laureate / v1 / today's timestamp
```

</QuickPath>

A Pod runs a container. A container runs from an image. We package the Streamlit code as a container image and push it where the cluster can pull from. **Cloud Build** does the packaging. **Artifact Registry** stores the image. One command does both.

---

### Step 1 — Build and push (~3 min)

`cd` into the **`pothole-poet/`** directory (the Dockerfile lives there, one level above `streamlit/`) and submit the build. Cloud Build reads the `Dockerfile`, builds the image on its infrastructure, and pushes the result to AR.

```bash
cd ~/quest/pothole-poet

gcloud builds submit \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v1 \
  --region=$REGION
```

✅ **Expect** (after ~3 min): A stream of build output ending with `SUCCESS` and the SHA digest of the pushed image.

> First build pulls the `python:3.12-slim` base, installs `libpq-dev` + `gcc`, then `pip install` the deps. ~3 min total. Re-runs are faster — cached layers from the previous build are reused.
>
> The `--region=europe-west1` keeps the build close to AR; without it Cloud Build runs in `us-central1` and uploads cross-region (slower).

<Concept title="Why is the Dockerfile in pothole-poet/ and not in streamlit/?">

Seed mode serves the bundled `seed/pothole_reports.csv` so the page works without AlloyDB or BigQuery. `app.py` reads it via `Path(__file__).parent.parent / "seed" / "pothole_reports.csv"` — i.e. a sibling of the `streamlit/` directory.

Docker can only `COPY` files that are inside the build context, so building from `streamlit/` alone would leave the seed CSV out and the app would crash on import with `FileNotFoundError: '/seed/pothole_reports.csv'`. Building from the `pothole-poet/` parent keeps `streamlit/` and `seed/` as siblings inside the image — same layout as on disk, no path math in `app.py`.

</Concept>

<Concept title="Why Cloud Build instead of running docker locally?">

**Cloud Build** runs your `docker build` on Google's infrastructure. Same outcome as local `docker build && docker push`, with three things that matter here:

1. **No Docker daemon to install.** The Workstation talks to Cloud Build via gcloud — nothing else to set up.
2. **Faster cold starts.** Cloud Build runs in the same network as Artifact Registry with cached base images, so a fresh `python:3.12-slim` pull is seconds, not minutes.
3. **Reproducible.** The build environment is fixed by Google, not by whatever happens to be on your laptop today.

</Concept>

<Concept title="What is Artifact Registry?">

**Artifact Registry** is GCP's managed container registry. One repo per project per region, addressed as `<region>-docker.pkg.dev/<project>/<repo>`. The platform pre-provisioned a repo called `laureate` in `europe-west1` for your container images.

The full image path you'll push to today: `europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v1`.

</Concept>

### Step 2 — While you wait (~2 min)

Open the **Artifact Registry** page in the Console (`https://console.cloud.google.com/artifacts?project=$PROJECT_ID`). You'll see the `laureate` repo. Once the build finishes, refresh — `pothole-laureate` appears with one tag (`v1`) and the layer breakdown.

### Step 3 — Verify the image is in AR

```bash
gcloud artifacts docker images list \
  europe-west1-docker.pkg.dev/$PROJECT_ID/laureate \
  --format="table(IMAGE,TAGS,UPDATE_TIME)"
```

✅ **Expect:**

```
IMAGE                                                                  TAGS  UPDATE_TIME
.../laureate/pothole-laureate                                          v1    2026-MM-DD...
```

<Gotchas>
- <strong><code>PERMISSION_DENIED: artifactregistry.repositories.uploadArtifacts</code>.</strong> The Workstation SA needs <code>roles/artifactregistry.writer</code>. Pre-provisioned, but if missing flag a Sherpa.
- <strong>Build fails with <code>requirements.txt</code> resolution errors.</strong> Don&rsquo;t pin newer versions than what&rsquo;s in the file. Cloud Build uses Python 3.12.
- <strong>Build hangs at <code>FETCHSOURCE</code> or fails with <code>Dockerfile not found</code>.</strong> The build context must be <code>pothole-poet/</code> (where the Dockerfile lives), not <code>pothole-poet/streamlit/</code>. <code>cd ~/quest/pothole-poet</code> before running <code>gcloud builds submit</code>.
- <strong>Pods crash on start with <code>FileNotFoundError: '/seed/pothole_reports.csv'</code>.</strong> The Dockerfile build context didn&rsquo;t include the sibling <code>seed/</code> directory. You almost certainly ran the build from <code>streamlit/</code> instead of <code>pothole-poet/</code> &mdash; re-do Step 1 from the correct directory.
- <strong><code>repository "laureate" not found</code>.</strong> The AR repo is in the per-Garage Terraform module &mdash; if missing, flag a Sherpa.
</Gotchas>

<Shipped>
The container is in the registry. <strong><code>europe-west1-docker.pkg.dev/$PROJECT_ID/laureate/pothole-laureate:v1</code> is ready to be pulled by the cluster.</strong>
</Shipped>

☸ **Q2D-2 done.** Image built and pushed.

➡️ Next: **Q2D-3 — Bind Pod Identity to BigQuery** (sidebar on the left).
