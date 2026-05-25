# ✨ Quest 1-5 — Set up Antigravity CLI

<Objective lane="all">

**🎯 What you'll do.** Launch Google's **Antigravity CLI** (`agy`), authenticate it against your Garage's GCP project, and run a one-prompt environment verification that confirms everything from Q1-4 is wired correctly. ~7 minutes, all four of you in parallel.

**🤝 Why it matters.** Antigravity CLI is your AI coding assistant for the rest of the day. It reads the Quest-specific skills and rules committed to the repo, so it knows your pipeline architecture, naming conventions, and hard constraints. Several later codelabs (Q2A-3, Q2C-2, Q2D-3, Q7) offer an agentic path that uses these skills to handle the error-prone parts for you. Setting it up now means you can reach for it instantly when you need it.

</Objective>

> ~7 minutes. Everyone in the Garage, on your own laptop's Workstation tab.

## 1. What is Antigravity CLI?

Antigravity CLI is Google's terminal-based AI agent. You launch it with the command `agy` and interact with it through a chat-style prompt. It can read files, run shell commands, and edit code, but it pauses for your approval (`y`/`n`) before every action that changes something on your system. This is called the **human-in-the-loop (HITL)** pattern: the agent proposes, you approve.

What makes it useful for this hackathon is the **workspace plugin** system. The Quest repo includes a plugin at `~/quest/.agents/plugins/iron-and-cloud/` that contains:

- **Rules** (`rules/context.md`): teaches the agent your region (`europe-west1`), naming conventions, Gemini model pin, and the Quest's hard constraints.
- **Skills** (`skills/` directory): task-specific guides the agent follows when you ask it to do something like "seed AlloyDB" or "bind WIF identity." Each skill knows the exact commands, the expected outputs, and the gotchas.

The agent auto-discovers this plugin when you launch `agy` from inside `~/quest`. If you launch it from anywhere else, it won't find the plugin and you'll get a generic agent with no Quest context.

<Concept title="New to Antigravity CLI? Watch this 5-minute walkthrough first">

<div style="position:relative;width:100%;max-width:640px;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;">
  <iframe
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:8px;"
    src="https://www.youtube.com/embed/am0lg5-ofvQ"
    title="Google Antigravity CLI Full Walkthrough"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
  ></iframe>
</div>

</Concept>

## 2. What it looks like when done

Antigravity CLI is authenticated, your project and location are set, and the environment verification passes:

```
✅ gcloud signed in as workstation-runner-<garage_id>@<project>.iam.gserviceaccount.com
✅ Project: <your-project-id>
✅ Tools on PATH: bq, gsutil, kubectl, python3, psql 16, jq, agy
✅ Repo at ~/quest with pothole-poet/ present
You're ready.
```

## 3. First-time setup

The first time you run `agy` on a fresh Workstation, it walks you through a short onboarding: login method, OAuth, project ID, location. Read the steps below before you start; it's quicker if you know what's coming.

**Step 1. Launch `agy` from inside the Quest repo.**

You **must** be inside `~/quest` when you launch `agy`. This is where the workspace plugin lives (`.agents/plugins/iron-and-cloud/`). If you launch from your home directory or anywhere else, the agent won't find the Iron & Cloud skills.

```bash
cd ~/quest
agy
```

**Step 2. Pick "Use a Google Cloud project" as the login method.**

You'll see a welcome banner with two options. Use the arrow keys to highlight **`2. Use a Google Cloud project`**, then press <kbd>Enter</kbd>. **Do NOT pick option 1 (Google OAuth)**, that's the consumer flow and won't work with Volvo Cars Cloud Identity in the Garage's project.

<Screenshot src="/quest/pothole-poet/img/agy_login_select.png" caption="Antigravity CLI welcome screen. Pick option 2, 'Use a Google Cloud project'." />

**Step 3. Authenticate via your laptop's browser.**

Antigravity CLI prints a long Google OAuth URL and waits. The Workstation has no browser, so:

1. **Select the entire URL** (starts with `https://accounts.google.com/o/oauth2/auth?...`) and copy it to your clipboard.
2. **Paste the URL into a new tab** in your laptop's browser, the same session where you're signed in with your **Volvo Cars work account**.
3. **Approve the OAuth consent screen**. Google hands you back an **authorization code** (a short string).
4. **Copy the authorization code** and paste it back into the Workstation terminal at the prompt. Press <kbd>Enter</kbd>.

<Screenshot src="/quest/pothole-poet/img/agy_oauth_url.png" caption="Antigravity CLI prints the OAuth URL. Copy it to your laptop browser, approve, paste the auth code back." />

**Step 4. Enter your Garage's Google Cloud Project ID.**

At the `Enter Google Cloud Project ID:` prompt, type your **Garage's `project_id`** from the workbench card (something like `vcc-ic-g03`) and press <kbd>Enter</kbd>.

<Screenshot src="/quest/pothole-poet/img/agy_project_id.png" caption="The 'Enter Google Cloud Project ID' prompt. Type your Garage's project_id from the workbench card." />

**Step 5. Select `global` as the Google Cloud Location.**

The prompt offers three options: `global`, `us`, `eu`. Pick **`global`** and press <kbd>Enter</kbd>. **Do NOT pick `eu` or `us`**: the Quest uses Gemini 3 which is only hosted on the global endpoint. Picking a regional endpoint will silently break the AI lanes later.

<Screenshot src="/quest/pothole-poet/img/agy_location.png" caption="The Google Cloud Location picker. Always pick 'global' for this Quest." />

## 4. Run the environment verification

Antigravity CLI drops you into its interactive prompt. Type:

> *Verify my environment and make sure I'm ready for the Iron & Cloud hackathon.*

The agent runs the read-only checks (`gcloud auth list`, tool versions, repo layout) on its own. No permission prompts appear because nothing is being changed. You'll see a summary confirming all tools are present and your project is set correctly.

## 5. Exit (for now)

Type `/exit` and press <kbd>Enter</kbd>. You're back in your Workstation shell.

Antigravity CLI remembers your login, project, and location. Next time you run `agy` from `~/quest`, you go straight to the interactive prompt with no re-authentication.

<Concept title="Useful shortcuts to know">

| Action | How |
|---|---|
| Run a shell command without leaving agy | Start your prompt with `!` (e.g. `! kubectl get pods -n laureate`) |
| Stop a streaming response | Press `Ctrl+C` or `Esc` |
| Approve a proposed command | Press `y` |
| Reject a proposed command | Press `n` |
| Clear the conversation and start fresh | `/clear` |
| Undo the last agent action | `/undo` |
| Resume a previous session | `/resume` (lists recent conversations you can pick up where you left off) |
| See all available commands | Type `?` |
| Exit | `/exit` (agy prints a resume command you can use to continue later) |

</Concept>

<Concept title="How the workspace plugin works">

When `agy` starts, it scans the current directory for `.agents/plugins/`. Each plugin contains a `plugin.json` manifest, optional rules (always-loaded context), and optional skills (task-specific instructions the agent loads on demand).

The Iron & Cloud plugin at `~/quest/.agents/plugins/iron-and-cloud/` includes:

- **`rules/context.md`**: loaded into every conversation. Teaches the agent your region, connection naming conventions, Gemini model pin, and the list of things it should never do (wrong region, wrong model, destructive operations).
- **Five skills**: `workstation-check`, `alloydb-seed-helper`, `bq-federation-helper`, `wif-binding-helper`, `build-helper`. Each has a `SKILL.md` with a description the agent reads to decide when it's relevant. You don't need to tell the agent which skill to use; it picks the right one based on your prompt.

This is why launching from `~/quest` matters. If the plugin isn't discovered, the agent still works, but without any of the Quest-specific knowledge.

</Concept>

<Concept title="When will I use agy during the Quest?">

Several later codelabs offer an agentic path alongside the manual click-path:

- **Q2A-3 (Seed AlloyDB)**: the `alloydb-seed-helper` skill resolves the private IP, runs the `\copy`, and verifies the row count.
- **Q2C-2 (BigQuery federation)**: the `bq-federation-helper` skill handles PROJECT_ID substitution and the UUID cast.
- **Q2D-3 (WIF identity binding)**: the `wif-binding-helper` skill constructs the principal URI correctly (the single most error-prone string of the day).
- **Q7 (Differentiate to Win)**: the `build-helper` skill guides open-ended feature work with HITL on every write.

Each one is optional. You can always follow the manual steps instead. But the agentic path is particularly valuable for Q2D-3, where a single character wrong in the principal URI causes a silent failure that costs 30 minutes to debug.

</Concept>

<Gotchas>
- <strong><code>agy</code> command not found.</strong> The Workstation image should have it pre-installed. If missing, run <code>pip install antigravity-cli</code> and retry.
- <strong>OAuth URL doesn&rsquo;t work in the browser.</strong> Make sure you&rsquo;re signed into your <strong>Volvo Cars work account</strong> (not a personal Google account) in the browser tab where you paste the URL.
- <strong>After pasting the auth code, agy says &ldquo;invalid grant&rdquo;.</strong> The auth code expires within a few minutes. If you waited too long, run <code>agy</code> again to get a fresh URL.
- <strong>agy starts but doesn&rsquo;t know about the Quest skills.</strong> You launched it from the wrong directory. Type <code>/exit</code>, then <code>cd ~/quest</code> and relaunch.
- <strong>Agent proposes a command you don&rsquo;t understand.</strong> Press <code>n</code> to reject it and ask the agent to explain what it wants to do and why. You are always in control.
</Gotchas>

<Shipped>
Antigravity CLI is authenticated, your project is set, and the workspace plugin is loaded. You have an AI assistant that knows your pipeline architecture, ready to help when you need it. <strong>Next: Q1-6, the Logs Explorer.</strong>
</Shipped>
