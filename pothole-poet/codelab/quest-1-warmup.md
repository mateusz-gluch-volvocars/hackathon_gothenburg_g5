# 🛠 Quest 1-4 — Workstation warm-up

<Objective lane="all">

**🎯 What you'll do.** Open your Cloud Workstation, clone the Quest repo into `~/quest`, run a few sanity checks, and pick which **Persona** (Data Engineer / Pipeline-author / Infra-Admin / App Dev / Guardian) you'll own for the build sprint. ~10 minutes, all four of you doing the same thing in parallel.

**🤝 Why it matters.** Every codelab from Q2 onward assumes you're sitting in a Workstation terminal with the repo at `~/quest` and `gcloud` pointed at your Garage's project. Persona assignment locks in here too — once Q2 starts you're working *solo* for ~30 minutes, so pick now while the team's still in the same room.

</Objective>

> ~10 minutes. Everyone in the Garage.

You're signed in (Q1-1), you know how to navigate the Console (Q1-2), and you've seen your VPC (Q1-3). Last orientation step before the build sprint: open your Cloud Workstation, clone the Quest repo, run a few sanity checks, and pick a lane.

---

## 🌐 Open these tabs (all in your laptop's browser — the workstation has no browser)

Sign in with **Volvo Cars SSO** — the same identity you used in Q1-1. Your Garage's GCP project is one of the projects your identity has access to; the Project Selector in the Console (top-left) is how you switched into it.

1. **Cloud Workstation IDE** — link on your workbench card. Looks like:
   `https://<workstation>.cloudworkstations.dev`
2. **GCP Console** — `https://console.cloud.google.com/?project=<your-project-id>`

Your **garage_id** and **project_id** are on the workbench card your Foreman handed you at check-in — both values are unique to your Garage. If your card is missing or unreadable, flag a Sherpa before anything else; nothing in this Quest will work without them.

---

## 1. The two-tab model

You'll always have at least two tabs open in your **laptop's** browser:

- **Tab 1: Cloud Workstation IDE** — Code-OSS + integrated Linux terminal running on a VM inside *your* GCP project. This is where you edit files and run `gcloud`, `psql`, `gsutil`, `bq`, `kubectl`.
- **Tab 2..N: GCP Console** — one tab per product (AlloyDB / Apache Airflow / BigQuery / Kubernetes Engine) for the Console click-paths.

**The Workstation has no browser inside it.** Whenever a codelab says "open the GCP Console" or "open a URL", that happens in *another tab* on your laptop — never inside the Workstation IDE.

<Concept title="A few Workstation quirks worth knowing up front">

- Your home directory (`/home/user`) lives on a **persistent disk** that survives Workstation stops. If you step away and it idles out, your edits and the cloned repo are still there on restart.
- Workstations **idle out** after ~2 hours without interaction. Clicking around in the IDE counts; the long Composer wait won't. If you walk away to lunch, just click the Workstation URL again to relaunch.
- The Workstation URL on your workbench card looks like `<workstation>.<cluster>.cloudworkstations.dev`. If it asks "Start workstation?", click yes.

</Concept>

The Quest content lives in a public GitHub repo. Your first job is to clone it onto the Workstation so every command in the upcoming codelabs has the files it needs.

## 2. What it looks like when done

A VS Code window in your laptop's browser tab, with the Quest repo file tree on the left and a terminal at the bottom. Like this:

```
~/quest$ ls
LICENSE  pothole-poet  README.md
~/quest$ gcloud config get-value project
<your-garage-project-id>
```

<Screenshot src="/quest/pothole-poet/img/workstation_ide.png" caption="Cloud Workstation IDE on first load — file tree on the left, terminal on the bottom." />

## 3. Open the IDE and a terminal

There are two ways to open your Cloud Workstation:

- **Option A (Direct link):** Click the workstation link on your workbench card.
- **Option B (GCP Console):** Search for `Cloud Workstations` in the Console search bar. You will land on the Workstations page showing the 4 workstations pre-provisioned for your Garage — named `garage-<garage_id>-dev-1` through `dev-4` (e.g. `garage-g01-dev-1`, `garage-g01-dev-2`, …). Find the one with your name / slot number on the workbench card. If its status is **Stopped**, click the **Start** (play) button next to it and wait ~20 seconds. Once its status changes to **Running**, click **Launch** to open the IDE in a new tab.

<Screenshot src="/quest/pothole-poet/img/console_workstations_list.png" caption="The Cloud Workstations page in the Google Cloud Console — showing cards for your workstations, their statuses (Stopped / Running), and buttons to Start and Launch them." />

Once the VS Code window loads in your browser, open the integrated terminal: **Terminal → New Terminal**, or press <kbd>Ctrl</kbd>+<kbd>`</kbd>.

## 4. Clone the Quest repo into `~/quest`

The workstation comes up empty. Every later codelab references files at `~/quest/pothole-poet/...`, so the first thing you do in the terminal is clone the **public Iron & Cloud Quest repo** into that path.

**The repo:** `https://github.com/larsers/hackathon_gothenburg.git`
**Clone target:** `~/quest`
**Auth:** none — the repo is public.

Copy this whole block into your Workstation terminal:

```bash
git clone https://github.com/larsers/hackathon_gothenburg.git ~/quest
cd ~/quest
ls
```

**Expected output of `ls`:**

```
LICENSE  pothole-poet  README.md
```

If you see those three entries, you're good. If `git clone` reports "Repository not found", double-check the URL — it's case-sensitive. If `ls` shows `quests/` instead of `pothole-poet/`, you cloned an older snapshot; run `cd ~ && rm -rf quest` and re-clone.

## 5. Verify your environment is sane

Run a few commands in the terminal to confirm the workstation is wired to your Garage's GCP project and has the tools the codelabs assume.

*What to check:*
- Active gcloud account (likely the workstation runner SA).
- Default project matches your `project_id`.
- `bq`, `gsutil`, `kubectl`, `python3`, `psql`, `jq` are all on PATH (pre-installed in the Iron & Cloud workstation image).

Two paths to do this — pick whichever fits your style.

### ✨ Path A — Agentic verification with **Antigravity CLI** (recommended)

Google's **Antigravity CLI** (launched with the command `agy`) is pre-installed on the Workstation image. It's a terminal-based AI agent that reads workspace skills committed to the Quest repo (`~/quest/.agents/plugins/iron-and-cloud/`) and can drive the whole verification with one prompt — read-only, no system changes.

The first time you run `agy` on a fresh Workstation, it walks you through a 4-step onboarding: login method → OAuth → project ID → location. Read the steps below before you start; it's quicker if you know what's coming.

**Step 1 — Launch `agy` from inside the repo.**

```bash
cd ~/quest
agy
```

**Step 2 — Pick "Use a Google Cloud project" as the login method.**

You'll see a welcome banner with two options. Use the arrow keys to highlight **`2. Use a Google Cloud project`**, then press <kbd>Enter</kbd>. **Do NOT pick option 1 (Google OAuth)** — that's the consumer flow and won't work with Volvo Cars Cloud Identity in the Garage's project.

<Screenshot src="/quest/pothole-poet/img/agy_login_select.png" caption="Antigravity CLI welcome screen — two login methods. Pick option 2 'Use a Google Cloud project'." />

**Step 3 — Authenticate via your laptop's browser.**

Antigravity CLI prints a long Google OAuth URL and waits. The Workstation has no browser, so:

1. **Select the entire URL** (starts with `https://accounts.google.com/o/oauth2/auth?...`) and copy it to your clipboard.
2. **Paste the URL into a new tab** in your laptop's browser — the same browser session you used in Q1-1, where you're already signed in with your **Volvo Cars work account**.
3. **Approve the OAuth consent screen**. Google hands you back an **authorization code** — a short string.
4. **Copy the authorization code** and paste it back into the Workstation terminal at the `authorization code...` prompt. Press <kbd>Enter</kbd>.

<Screenshot src="/quest/pothole-poet/img/agy_oauth_url.png" caption="After picking 'Use a Google Cloud project', Antigravity CLI prints the OAuth URL and a clickable 'Click here to authenticate' link, with an input field for the authorization code at the bottom." />

**Step 4 — Enter your Garage's Google Cloud Project ID.**

At the `Enter Google Cloud Project ID:` prompt, type your **Garage's `project_id`** from the workbench card (something like `vcc-ic-g03`) and press <kbd>Enter</kbd>.

<Screenshot src="/quest/pothole-poet/img/agy_project_id.png" caption="The 'Enter Google Cloud Project ID' prompt. Paste your Garage's project_id from the workbench card, e.g. `vcc-ic-g03`." />

**Step 5 — Select `global` as the Google Cloud Location.**

The prompt offers three options: `global`, `us`, `eu`. Use the arrow keys to highlight **`global`** and press <kbd>Enter</kbd>. **Do NOT pick `eu` or `us`** — the Iron & Cloud Quest uses Gemini 3 which is only hosted on the global endpoint. Picking a regional endpoint will silently break the AI lanes later.

<Screenshot src="/quest/pothole-poet/img/agy_location.png" caption="The Google Cloud Location picker. Always pick `global` — Gemini 3 is global-endpoint only." />

**Step 6 — Run the verification prompt.**

Antigravity CLI drops you into its interactive prompt. Type and press <kbd>Enter</kbd>:

> *Verify my environment and make sure I'm ready for the Iron & Cloud hackathon.*

Antigravity CLI runs the read-only checks (`gcloud auth list`, tool versions, repo layout) on its own — no permission prompts, because no system changes happen during verification. You'll see a green summary like:

```
✅ gcloud signed in as workstation-runner-<garage_id>@<project>.iam.gserviceaccount.com
✅ Project: <your-project-id>
✅ Tools on PATH: bq, gsutil, kubectl, python3, psql 16, jq, agy
✅ Repo at ~/quest with pothole-poet/ present
You're ready.
```

**Step 7 — Exit Antigravity CLI.**

Type `/exit` and press <kbd>Enter</kbd>. You're back in your Workstation shell. (Antigravity CLI remembers your login, project, and location — next time you run `agy`, you go straight to the interactive prompt; no re-authentication.)

<Concept title="What just happened — the agentic loop in 30 seconds">

Antigravity CLI read the `workstation-check` **skill** committed in the Quest repo, planned its checks, and ran read-only discovery commands on its own. It would have paused for your `y`/`N` confirmation before running anything that *changes* the system — but for this verification there's nothing to change; every tool the Quest needs is already baked into the workstation image.

You'll see the human-in-the-loop pattern properly in **Q2A-3**, **Q2C-2** and **Q2D-3** where dedicated skills walk lane-specific tasks (AlloyDB seed, BigQuery federation, Workload Identity binding) and each one stops before any write to ask for your `y`. All driven by the same Antigravity CLI session and the same workspace rule (`~/quest/.agents/plugins/iron-and-cloud/rules/context.md`) that teaches it our region, project conventions, and the Quest's hard constraints.

</Concept>

### Path B — Manual verification

If `agy login` stalls, the agent is unresponsive, or you'd just rather see the raw commands — run them yourself. Both paths confirm the same thing: every tool is on PATH and gcloud is wired to your Garage's project.

<Cheat title="Show the verify commands">

```bash
gcloud auth list
gcloud config get-value project
bq --version | head -1
gsutil --version | head -1
kubectl version --client 2>/dev/null | head -1
python3 --version
psql --version
jq --version
agy --version 2>/dev/null || echo 'agy installed'
```

✅ You should see an active SA, your `project_id`, and version strings for every tool. `psql` should report PostgreSQL 16. If anything is missing, flag a Sherpa.

</Cheat>

## 6. Skim the Quest README

Open `pothole-poet/README.md` in the IDE (left-side file tree → click). Skim the story, the lane table, and the tier ladder. Two minutes.

<Cheat title="Show two power-tips for the IDE">

These aren't required, but they make life nicer:

- **Multiple terminals.** Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>5</kbd> (or click the **Split** icon in the terminal tab list) to split into two side-by-side terminals. Useful when one is running `psql` interactively and you want a free shell for `gsutil`.
- **Drag files in.** You can drag files from your laptop's Finder/Explorer onto the Code-OSS file tree to upload them to `/home/user/`. Right-click a file in the tree → **Download** to pull it back.
- **Install the PWA** for better keyboard shortcuts. The browser eats some shortcuts (<kbd>Cmd</kbd>+<kbd>W</kbd>, <kbd>Cmd</kbd>+<kbd>T</kbd>) that the IDE wants. Click the install icon in your laptop browser's address bar; the workstation reopens as a desktop-style app where the IDE owns those keys.

</Cheat>

## 7. Decide your lanes (~3 min, all together)

Look at your team. Pick one role each — then open that lane's codelab page from the sidebar on the left.

| Lane | Role | What they own | Sidebar page |
|---|---|---|---|
| A | **Airflow Lead** | Managed Service for Apache Airflow + the DAG | Q2B · Airflow Lead |
| B | **AlloyDB Lead** | AlloyDB cluster + schema + seed | Q2A · AlloyDB Lead |
| C | **BigQuery Lead** | BigQuery dataset + AlloyDB federation | Q2C · BigQuery Lead |
| D | **GKE / App Lead** | Streamlit app + GKE Autopilot + Gateway | Q2D-1 → Q2D-5 · GKE / App Lead (5 pages) |

**Smaller Garage?**
- **3 people:** collapse C + D. BigQuery Lead finishes BQ work, then drops into Streamlit.
- **2 people:** you're a **Bronze Garage**. One person provisions; the other ships Streamlit on the bundled CSV. Skip the rest. The Foreman will confirm.

## 8. Final check before you split

Each person should now have:
- Cloud Workstation IDE open in their laptop's browser
- The Quest repo cloned at `~/quest`
- A lane (write it on a sticky note if helpful)
- Their next codelab page open in another tab on the **hub**

When the room confirms — **the build sprint begins.**

🚦 Go to your lane.

<Gotchas>
- <strong>Workstation won&rsquo;t start / spins forever.</strong> Refresh the workbench card and click <strong>Start workstation</strong> again. If still stuck after 60 seconds, flag a Sherpa &mdash; they&rsquo;ll re-issue your card.
- <strong><code>gcloud config get-value project</code> shows the wrong project.</strong> Run <code>gcloud config set project &lt;your-project-id&gt;</code> using the project_id on your workbench card.
- <strong><code>git clone</code> says &ldquo;Repository not found&rdquo;.</strong> Double-check the URL spelling. The repo is public &mdash; no auth is needed.
- <strong>You see <code>quests/</code> instead of <code>pothole-poet/</code> at the repo root.</strong> You may have cloned an older snapshot &mdash; <code>cd ~ &amp;&amp; rm -rf quest &amp;&amp; git clone &hellip; ~/quest</code> to start fresh.
- <strong>Trying to open a URL from the workstation terminal does nothing.</strong> Expected &mdash; the workstation has no browser. Copy the URL and paste it into a fresh tab in your laptop&rsquo;s browser.
</Gotchas>

<Shipped>
Every Garage member has their Cloud Workstation open in their laptop&rsquo;s browser, the Quest repo cloned at <code>~/quest</code>, and a chosen Lane on a sticky note. <strong>You&rsquo;re ready for the build sprint.</strong>
</Shipped>
