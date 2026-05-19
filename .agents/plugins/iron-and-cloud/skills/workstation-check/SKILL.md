---
name: workstation-check
description: Verifies the Cloud Workstation environment is ready for the Iron & Cloud hackathon. Checks gcloud auth and active project, confirms required CLI tools (bq, gsutil, kubectl, python3, git) are on PATH, captures PROJECT_ID and PROJECT_NUMBER for later lanes, and installs postgresql-client if missing. Use when the participant asks to verify, set up, prepare, sanity-check, or check their workstation, or asks whether they are ready to start the hackathon.
---

# Workstation check (Q1 — Section 5)

**Codelab counterpart:** Q1 — `~/quest/pothole-poet/codelab/quest-1-warmup.md`, Section 5 (Path A).

Use this skill to verify a participant's Cloud Workstation is fully primed for the Iron & Cloud hackathon. Run the checks in order; report a clean summary checklist at the end.

## Checks (run in order)

### 1. gcloud authentication + active project
- Run `gcloud auth list --format=json` and confirm at least one active account.
- Run `gcloud config get-value project` and capture as `PROJECT_ID`.
- Run `gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)'` and capture as `PROJECT_NUMBER`.
- **Surface both to the participant.** They will need `PROJECT_NUMBER` in Q2D-3 for the WIF principal URI.

### 2. Core CLI tools on PATH
Verify each of these resolves and runs without error:
- `gcloud --version` (Google Cloud SDK)
- `bq version | head -1`
- `gsutil version | head -1`
- `kubectl version --client 2>/dev/null | head -1`
- `python3 --version`
- `git --version`

For each tool, report `OK <version>` or `MISSING`. **Do not propose installs for these** — they ship with the Workstation image and a missing entry indicates an image-level problem the participant should flag to a Sherpa.

### 3. PostgreSQL client (`psql`)
The Workstation image deliberately does not ship `psql`. The AlloyDB Lead (Lane B) needs it in Q2A-3 to seed `pothole_reports` via `\copy`.

- Check with `command -v psql`.
- If MISSING:
  1. Explain to the participant: *"Lane B (AlloyDB) needs `psql` to seed the database in Q2A-3. I can install the PostgreSQL client now — it will persist on your home directory's persistent disk."*
  2. Propose this exact command for HITL approval:
     ```bash
     sudo apt-get update -qq && sudo apt-get install -y postgresql-client
     ```
  3. Mention that the sandbox confirmation prompt will offer *"Yes, and run without sandbox restrictions"* — that's the correct choice for `sudo apt` since elevation needs unsandboxed access.
  4. After install, verify with `psql --version`. Expect PostgreSQL 16.x.

### 4. Quest repo at `~/quest`
- Confirm `~/quest` exists and contains `pothole-poet/`, `README.md`, `LICENSE`.
- If `~/quest` is empty or missing, propose:
  ```bash
  git clone https://github.com/larsers/hackathon_gothenburg.git ~/quest
  ```
- If `~/quest` exists but has a stale layout (e.g. a nested `quests/` directory), propose:
  ```bash
  cd ~ && rm -rf quest && git clone https://github.com/larsers/hackathon_gothenburg.git ~/quest
  ```

## Final summary

Render a clean checklist with status icons. Example shape:

```
✅ gcloud authenticated as <account@example.com>
✅ Active project: <PROJECT_ID> (number: <PROJECT_NUMBER>)
✅ Core tools: gcloud, bq, gsutil, kubectl, python3, git
✅ psql installed (PostgreSQL 16.4)
✅ Repo at ~/quest

🎉 Your Cloud Workstation is primed and ready for the Iron & Cloud hackathon.
```

End with a reminder: *"You can exit Antigravity CLI with `Ctrl+D` and proceed to Section 6 of Q1 (Find your way around the GCP Console)."*

## What not to do

- Don't install or update `gcloud`, `bq`, `gsutil`, `kubectl`, `python3`, or `git`. If any are missing, that's an image-level problem — escalate to a Sherpa.
- Don't reconfigure the active gcloud project unless the participant explicitly says theirs is wrong. The Workstation comes pre-pointed at the Garage's project.
- Don't propose `gcloud auth application-default login` here — ADC isn't needed for the warm-up. (Q2A-3's `bq_seed` Terraform local-exec needs it, but that's not run by participants.)
