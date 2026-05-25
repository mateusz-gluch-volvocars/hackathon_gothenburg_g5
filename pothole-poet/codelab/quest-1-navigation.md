# 🧭 Quest 1-2 — Project, menu, search bar

<Objective lane="all">

**🎯 What you'll do.** Learn the three tools that get you anywhere in the GCP Console in under five seconds: the **project picker** (top-left), the **search bar** (top-center, <kbd>/</kbd> or <kbd>Ctrl</kbd>+<kbd>/</kbd>), and the **hamburger menu** (top-left, all products). Pin the four services this Quest uses so they live at the top of your menu all day. ~7 minutes, on your laptop browser.

**🤝 Why it matters.** This is muscle memory you'll use a hundred times today. Without it, every "now go to AlloyDB" instruction in a later codelab becomes a thirty-second hunt; with it, it's three keystrokes. New-to-GCP engineers consistently rate this the single highest-leverage few minutes of their first week.

</Objective>

> ~7 minutes. Everyone in the Garage, on your own laptop browser.

In Q1-1 you confirmed the right project is selected. Now you learn how to *navigate*, which is mostly about *not* using the hamburger menu's deep nesting and instead reaching for the search bar.

---

## 1. Why

GCP has hundreds of products organised into a dozen categories. The hamburger menu is a maze for newcomers. AlloyDB is under "Databases", Composer is under "Data Analytics → Cloud Composer", BigQuery is under "Analytics → BigQuery", Kubernetes Engine is its own top-level entry. You *could* hunt every time. You won't, because the search bar exists.

The Console designers put three navigation tools at the top of every page for exactly this reason. Today you learn all three, in order of how often you'll use them.

## 2. What it looks like when done

The hamburger menu, open. At the top, a "📌 Pinned" section with four entries: **AlloyDB**, **Composer**, **BigQuery**, **Kubernetes Engine**, in roughly that order. Underneath, the rest of the product catalog organised by category.

<Screenshot src="/quest/pothole-poet/img/console_pinned_menu.png" caption="Hamburger menu fully expanded, the Pinned section at the very top showing AlloyDB, Composer, BigQuery, and Kubernetes Engine (📌 icon visible next to each), with the rest of the product catalog (Compute, Databases, Storage, Networking, Data Analytics…) underneath." />

## 3. The project picker — global state, glance at it constantly

1. Click your project name in the top-left, next to the Google Cloud logo.
2. A panel slides out showing the projects you have access to. Type your `project_id` in the picker's search box to filter; click it to switch. (You're probably already on it; confirm.)
3. Close the picker.

The project picker is **global Console state**: every page you load until you change it is scoped to whatever's selected here. The #1 cause of *"I created the resource but the next page says it doesn't exist!"* is having the wrong project selected and not noticing. Glance at the picker before every Create / Apply / Run.

<Concept title="Why is the project selector such a big deal?">

Every GCP resource (database, bucket, service, dataset) lives inside exactly one **project**. Every API call you make from the Console is scoped to whichever project is currently selected. If your Console tab is on the *wrong* project, you'll get permission-denied errors, missing-resource errors, or, worse, you'll create your AlloyDB cluster in someone else's Garage and not realise it. Always glance at the project selector before clicking.

</Concept>

## 4. The search bar — your fastest tool, by far

The search bar is the single fastest tool in the Console. Get comfortable with it.

1. Press <kbd>/</kbd> (or <kbd>Ctrl</kbd>+<kbd>/</kbd> on Windows/Linux, <kbd>Cmd</kbd>+<kbd>/</kbd> on Mac). The cursor jumps to the search bar.

2. Type `alloydb` (case-insensitive). Within a second, results group into:

   - **Products & pages**: the AlloyDB product itself, sub-pages like "Clusters", and adjacent products.
   - **Resources**: none yet, because you haven't created any.
   - **Documentation**: Google's docs that match.

   <Screenshot src="/quest/pothole-poet/img/console_search_alloydb.png" caption="The search bar open with `alloydb` typed, showing the three grouped result sections. Products & pages (top), Resources (empty for an unprovisioned Garage), and Documentation (bottom). Captured before any Q2 resources exist so participants see exactly what their own search will look like at this point." aspect="16 / 8" />

3. Click "AlloyDB" in the products section. You land on the AlloyDB landing page for your project. *Don't create anything yet*; just look around. Press <kbd>Alt</kbd>+<kbd>←</kbd> (browser back) to return to the overview.

4. Press <kbd>/</kbd> again and try a few more:

   - `iam` → jumps to the IAM page.
   - `gke` → jumps to Kubernetes Engine (the abbreviation works).
   - Your `project_id` → can switch projects directly from search.

Three rules for the search bar that pay back through the day:

- **Products you don't know the menu path of**: search. Faster than clicking.
- **Resources you've already created** (clusters, datasets, buckets, IAM bindings): search. After Q2 you'll have several; the search bar finds them by name.
- **Things you forgot the exact name of**: search. It does fuzzy matching across products, resources, and documentation.

<Concept title="The search bar's superpower: resource search">

Once you've created resources later today (an AlloyDB cluster, a BigQuery dataset, a GKE cluster), the search bar finds those too. Press <kbd>/</kbd> and type `pothole-laureate` (the name of one of the resources you'll create in Q2D); after that resource exists, the result list will include "AlloyDB cluster pothole-laureate" with a direct link to it.

This works across products. Type a resource name and you don't need to remember which product owns it. It's especially useful in shared projects (yours isn't, but in your day-job Volvo Cars project it will be).

</Concept>

## 5. The hamburger menu — and pinning

The hamburger is the full product catalog. You'll use it when you're browsing rather than hunting a specific product.

1. Click the **☰** icon in the top-left. The menu slides out.

2. Scroll to find each of these four products, and click the **📌 pin** icon next to its name. Pinned products float to the top of the menu and stay there across sessions:

   | Product | Where it lives in the menu | Pin it |
   |---|---|---|
   | **AlloyDB for PostgreSQL** | Databases → AlloyDB for PostgreSQL | 📌 |
   | **Composer** | Data Analytics → Cloud Composer *(Google's name for Managed Service for Apache Airflow)* | 📌 |
   | **BigQuery** | Analytics → BigQuery | 📌 |
   | **Kubernetes Engine** | (Top-level, near the top of the menu) | 📌 |

3. Scroll the menu back to the top. The pinned section should now show all four products. You'll be tabbing between them for the next three hours.

4. Click outside the menu to close it. Reopen it; the pins persisted across the open/close.

## 6. While you wait

*Nothing waits.* If you finish early, search for a product you've never heard of (`spanner`, `vertex ai`, `cloud run`) and read its landing page for a minute. GCP has a *lot* of products; the Console is also a discovery surface. Don't click Create on anything; every resource costs money.

## 7. Verify

- 📌 The hamburger menu shows **AlloyDB**, **Composer**, **BigQuery**, **Kubernetes Engine** in the pinned section at the top.
- 🔍 You used the search bar at least twice without touching the mouse to open it.
- 🟦 The project picker still shows your `project_id` (you didn't accidentally switch).

<Concept title="Cloud Shell vs. Cloud Workstations vs. running gcloud locally">

You'll spot a **`>_` Cloud Shell** icon in the top-right of the Console. Clicking it pops out a browser-drawer Linux terminal that lets you run `gcloud` against the current project without installing anything locally.

**We don't use Cloud Shell today.** Your Garage uses **Cloud Workstations** instead, a full-fledged dev VM that lives *inside* your Garage's VPC (which Cloud Shell doesn't) and has persistent storage (which Cloud Shell only has 5 GB of). You'll meet Workstations properly in Q1-4.

The third option, running `gcloud` from your laptop, also works (install once, authenticate against the project). We don't use that either, for the same reason: it's not in the VPC, so it can't reach AlloyDB's private IP later.

</Concept>

<Gotchas>
- <strong>Search bar doesn't open when you press <kbd>/</kbd>.</strong> Your browser caught the keystroke (usually if focus is in a text field). Click anywhere outside a form and try again; <kbd>Ctrl</kbd>+<kbd>/</kbd> also works.
- <strong>Pinning didn't save.</strong> Browser is in incognito or you're signed into multiple Google accounts in the same browser. Sign out of all but the work account or stay in regular browsing mode for the day.
- <strong>You see "Activate this API" on a product's landing page.</strong> Don't click it; every API you need today is pre-enabled for your Garage's project. If you see this prompt on AlloyDB / Composer / BigQuery / Kubernetes Engine, flag a Sherpa; that's a pre-provisioning miss.
- <strong>"Permission denied" anywhere.</strong> Don't debug it yourself; flag a Sherpa with the exact error text. Your Garage role binding may be partial.
</Gotchas>

<Shipped>
You can jump anywhere in the GCP Console in three keystrokes. Your four lab products are pinned at the top of the menu. The project picker is locked on your <code>project_id</code>. <strong>Console navigation is muscle memory. On to Q1-3, your VPC.</strong>
</Shipped>
