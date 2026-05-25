# 🚦 Quest 1-1 — Sign in & take a first look

<Objective lane="all">

**🎯 What you'll do.** Sign in to your Garage's GCP project with Volvo Cars SSO, land on the Cloud Console, and identify the four landmarks of the top bar: project picker, search, Cloud Shell, account avatar. ~4 minutes, all four of you on your own laptops at the same time.

**🤝 Why it matters.** GCP Console is your second window all day. Before you can do anything useful, you need to be signed in as the right person, looking at the right project. This page is two clicks and a glance. Q1-2 is where you actually start learning the navigation muscle memory.

**🏆 How the day is judged.** Up to 30 Garages are running this same Quest in parallel. Everyone's Foundation pipeline will look identical. **The prize goes to the Garage whose demo is most creative and most differentiated from the rest**. and the leverage for that comes from **Antigravity CLI** (`agy`), which you'll meet in Q1-4. Start thinking about what your team's "voice" might be from the start of the day, not just at the end.

</Objective>

> ~4 minutes. Everyone in the Garage, on your own laptop.

You don't need a personal Google account to do this Quest; your **Volvo Cars SSO** identity has been granted access to a GCP project that was pre-provisioned for your Garage. The Console doesn't drop you directly into that project, though. Volvo Cars developers typically have access to many projects, so after signing in you'll use the **Project Selector** (top-left of the Console) to navigate to your Garage's specific project.

---

## 1. Why

Every interaction with Google Cloud: clicking in the Console, running `gcloud`, calling an API from code; it all boils down to *"call API X in project Y as identity Z."* This page sets up two of those three: **your identity** (Volvo Cars SSO) and **your project** (the one printed on your workbench card). The third (an API call) happens for the first time in Q2.

GCP has hundreds of products, and the Console is the UI on top of them. The shape has been stable since 2018: a top bar with global tools (project, search, terminal, profile), a hamburger menu on the left for the product catalog, and the page body in the middle.

## 2. Sign in and select your Garage's project

1. Open `https://console.cloud.google.com` in your laptop's browser (not the workstation; it has no browser).

2. If a sign-in screen pops up, pick your **Volvo Cars work account**. Some of you will see two Google identities (a personal `@gmail.com` plus the Volvo one), always pick the work one. Same identity you use for any other Google service at work.

3. The Console loads on a default landing page, likely scoped to a project you have access to from your day job, or showing "Select a project" if none is sticky. Either way, you're not yet in your Garage's project.

4. Click the **Project Selector** in the top-left, next to the Google Cloud logo. A dialog opens listing every project your identity has access to.

5. Type your `project_id` from the workbench card into the dialog's search box to filter the list, then click your Garage's project to switch into it. The Console reloads scoped to that project.

**Shortcut:** you can skip the Project Selector clicks by opening `https://console.cloud.google.com/?project=<your-project-id>` directly. The `?project=` parameter pre-selects the project. Useful if your workbench card is already in your hand.

## 3. Spot the four landmarks of the top bar

You should land on the Cloud overview page. Look at the top bar, left-to-right:

| Landmark | Where | What it's for |
|---|---|---|
| 🟦 **Project picker** | Top-left, next to the Google Cloud logo | Switch projects · confirm you're in the right one |
| 🔍 **Search bar** | Top-center | Jump to any product or resource (Q1-2 walks this) |
| `>_` **Cloud Shell** | Top-right | A browser-drawer Linux terminal · we won't use it today |
| 👤 **Account avatar** | Far top-right | Confirms which identity you're signed in as |

<Screenshot src="/quest/pothole-poet/img/console_top_landmarks.png" caption="The four landmarks of the Console top bar, project picker (left, next to the Google Cloud logo), search bar (center), Cloud Shell `>_` icon (right), and account avatar (far right). Highlight each with a coloured callout so it's obvious which is which." />

Glance at each. You don't have to click them yet. Q1-2 walks you through the project picker and search bar properly.

## 4. While you wait

*Nothing waits.* **Sherpa moment**. if sign-in stalled, popped a strange consent screen, or landed you in someone else's project, flag a Sherpa now. Almost every Day-1 sign-in issue is a workbench-card SSO binding fix and takes 30 seconds.

## 5. Verify

Both of these are true:

- The **account avatar** (top-right) shows your Volvo Cars email.
- The **project picker** (top-left) shows the exact `project_id` from your workbench card.

If either is wrong, **don't navigate further**. fix it first, or every later command writes to the wrong place.

<Concept title="What is a GCP project, really?">

A **project** is the basic unit of isolation in Google Cloud. Resources (databases, buckets, services), API quotas, IAM policies, and billing all live inside exactly one project. Anyone with the right role on the project can do things to its resources; anyone without that role can't see them at all.

Each Garage = its own separate project today. Yours is yours alone; you can't accidentally see or break another Garage's work, and they can't see or break yours.

The `project_id` (lowercase, dashes, like `iron-cloud-g3-a7f1`) is the permanent name. There's also a `project_number` (a long integer) you'll occasionally see in resource paths. Both refer to the same project; either works in most places, but a few APIs require one or the other, the codelabs say which when it matters.

</Concept>

<Concept title="Why don't I need a personal Google account?">

Your Garage's project is bound to **Volvo Cars Cloud Identity**. the same SSO that signs you into every other Google service at work. From Google Cloud's perspective, your Volvo Cars email *is* a Google identity (specifically a "Workspace" or "Cloud Identity" account). No separate `@gmail.com` account needed.

This is how every enterprise GCP customer works. Volvo Cars-the-organisation owns the identity, you're a member of it, and the IAM bindings on your Garage's project list your work email as a principal.

</Concept>

## Expected result

A browser tab on your laptop showing the Cloud overview page. Top-right: your Volvo Cars work email next to the avatar. Top-left: the project picker, showing your Garage's `project_id` from the workbench card.

<Screenshot src="/quest/pothole-poet/img/console_overview_login.png" caption="The Cloud overview page on first sign-in; your Garage's project_id visible in the top-left project picker, your Volvo Cars work email visible in the top-right account avatar." />

<Gotchas>
- <strong>Sign-in lands you on a "Select an account" screen.</strong> Pick your Volvo Cars work account. If only a personal account shows up, your browser session is signed into the wrong Google account, open an incognito tab and try again.
- <strong>Your Garage's project doesn't appear in the Project Selector.</strong> Your SSO identity hasn't been granted access yet; flag a Sherpa with your <code>garage_id</code>.
- <strong>You land on a different project after selecting (one of your day-job projects sticky from a previous session).</strong> Click the Project Selector again and re-pick your Garage's <code>project_id</code> from the workbench card. The Console remembers the last project per browser session.
- <strong>The <code>?project=</code> shortcut URL drops you on "Select a project" instead.</strong> Either the project_id was mistyped or your identity doesn't yet have access. Fall back to the Project Selector flow in Section 3; if the project still doesn't show, flag a Sherpa.
</Gotchas>

<Shipped>
You're signed in with Volvo Cars SSO, sitting on the Cloud overview page for your Garage's GCP project, and you can name the four landmarks of the top bar. <strong>Onwards to Q1-2. where you actually start using them.</strong>
</Shipped>
