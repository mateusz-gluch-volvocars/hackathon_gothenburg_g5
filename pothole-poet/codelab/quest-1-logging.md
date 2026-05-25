# 📋 Quest 1-6 — Meet the Logs Explorer

<Screenshot src="/quest/pothole-poet/img/console_logs_explorer.png" caption="The Logs Explorer: Query pane at the top, Fields pane on the left, Timeline in the center, and log entries at the bottom." />

<Objective lane="all">

**🎯 What you'll do.** Open Cloud Logging's Logs Explorer, learn the four-pane layout (Query, Fields, Timeline, Results), try the one query pattern you'll use all day, and pin Logging to your Console menu. ~5 minutes, all four of you on your own laptops.

**🤝 Why it matters.** When something breaks later today (and something will), the Logs Explorer is where you find out *why*. Composer Gen 3 stores all Airflow task logs exclusively in Cloud Logging, so the Pipeline-author cannot debug a failed DAG without this. For GKE, the Fields pane drill-down (cluster, namespace, pod, container) is the fastest path from "my Pod crashed" to "here is the stack trace." Five minutes of orientation now saves thirty minutes of fumbling later.

</Objective>

> ~5 minutes. Everyone in the Garage, on your own laptop browser.

You know how to navigate the Console (Q1-2), you've seen your VPC (Q1-3), your Workstation is running (Q1-4), and your AI assistant is set up (Q1-5). One last orientation before the build sprint: the place you'll go when things break.

---

## 1. Why

Cloud Logging is the centralized log store for every GCP service in your project. Every container stdout line from GKE, every Airflow task execution from Composer, every Cloud Build step, every Kubernetes event: it all lands here automatically. You do not configure log shipping; it is on by default.

The Logs Explorer is the Console UI for searching, filtering, and reading those logs. You already have `roles/logging.viewer` on your Garage's project (granted by the platform team), so you have read-only access to everything.

Today you'll use Logging in four situations, each tied to a different **resource type**:

| When | Resource type | Who hits it |
|---|---|---|
| Airflow DAG task fails | `cloud_composer_environment` | Pipeline-author (Lane A) |
| Cloud Build image build fails | `build` | GKE / App Lead (Lane D) |
| GKE Pod crashes or won't start | `k8s_container` | GKE / App Lead (Lane D) |
| Gateway stuck, LB health check fails | `k8s_cluster` (events) | GKE / App Lead (Lane D) |

You don't need to memorize these. This page teaches the *pattern*; the later codelabs point you back here when a specific failure happens.

## 2. Open the Logs Explorer

1. Press <kbd>/</kbd> to open the search bar. Type `logs explorer`. Click **Logs Explorer** in the results (the one whose subheading says "Logging").

2. You land on the Logs Explorer page. Four panes:

   | Pane | Where | What it does |
   |---|---|---|
   | **Query pane** | Top | Where you type or paste log filters. Has a "Run query" button on the right. |
   | **Fields pane** | Left sidebar | Shows filterable dimensions: Resource Type, Severity, Log Name. Click any value to add it as a filter. |
   | **Timeline** | Center, above results | A histogram of log volume over time, color-coded by severity (blue = info, yellow = warning, red = error). |
   | **Results pane** | Below the timeline | The actual log entries. Click any row to expand it and see the full payload. |

   If the Fields pane is not visible, click the toggle labeled **Log fields** in the toolbar above the results.

## 3. The one query pattern you need

Every debugging session today follows three steps:

1. **Pick the resource type** in the Fields pane. Click "Resource Type" to expand it. You'll see the resource types that have emitted logs in your project. Click the one that matches your problem (see the table in Section 1).

2. **Filter by severity.** In the Fields pane, click "Severity" and select **Error** (or Warning if you want more context). The Results pane now shows only those entries.

3. **Read the error.** Click a log entry in the Results pane to expand it. The `textPayload` or `jsonPayload.message` field contains the actual error message, stack trace, or status.

That is the whole pattern. Resource type, severity, read.

<Concept title="How GKE logs drill down in the Fields pane">

When you select `k8s_container` as the resource type, the Fields pane shows additional labels you can filter on: **cluster_name**, **namespace_name**, **pod_name**, **container_name**. This hierarchy is your fastest debugging path on GKE.

For today's Quest, the drill-down is: cluster `laureate-cluster`, namespace `laureate`, then the specific pod. You rarely need to go deeper than namespace for a hackathon; the container-level filter becomes valuable in production when a Pod runs sidecars alongside your app container.

</Concept>

<Concept title="Why Composer Gen 3 logs are only in Cloud Logging">

Composer Gen 2 wrote task logs to both a GCS bucket and Cloud Logging. Gen 3 simplified this: task logs go exclusively to Cloud Logging. There is no `logs/` folder in the environment's GCS bucket.

This means the Logs Explorer is the *only* place to read Airflow task output, error messages, and scheduling decisions. The Airflow UI also shows task logs (it pulls them from Cloud Logging behind the scenes), but the Logs Explorer gives you better search and filtering across multiple tasks at once.

The resource type is `cloud_composer_environment`. Filter by `labels.workflow` to narrow to a specific DAG, or by `labels.task_id` for a specific task.

</Concept>

## 4. Try it: look at what's already here

Your project already has logs, even though you haven't built anything yet. GCP emits audit logs for every API call.

1. In the Logs Explorer, clear any existing query (click the **Clear query** button, or select all text in the Query pane and delete).

2. In the Fields pane, click **Resource Type**. You should see `audited_resource` (and possibly others if your Workstation is running).

3. Click `audited_resource`. The Results pane fills with Admin Activity audit logs: project creation, API enablement, IAM bindings, resource provisioning. This is the Terraform work that set up your Garage.

4. Click any log entry to expand it. Note the structure: `resource.type`, `resource.labels`, `severity`, `timestamp`, and the payload.

You've just run your first Logs Explorer query. The exact same flow works when a DAG fails or a Pod crashes; only the resource type changes.

## 5. Star Logging in your menu

1. Click the **hamburger menu** (top-left).
2. Find **Logging** (under the Observability category, or type "logging" in the menu's filter box at the top).
3. Click the **⭐ star icon** next to Logging. Starred products float to the top of your menu.
4. Your starred section should now show five products: AlloyDB, Composer, BigQuery, Kubernetes Engine, and Logging.

## 6. While you wait

*Nothing waits.* If you finished early, try one more thing: in the Fields pane under Severity, select **Error**. If there are zero errors, your Garage's pre-provisioning was clean. If there *are* errors, skim one. You'll recognize the pattern when you need it later.

## 7. Verify

- The Logs Explorer is open and you can see the four-pane layout.
- You ran at least one query by clicking a resource type in the Fields pane.
- Logging is starred in your hamburger menu alongside the four products from Q1-2.

## Expected result

The Logs Explorer open in your browser, showing the four-pane layout (see the screenshot at the top of this page). Logging is pinned in your hamburger menu alongside the four products from Q1-2.

<Gotchas>
- <strong>The Fields pane is missing or hidden.</strong> Click the <strong>Log fields</strong> toggle in the toolbar above the Results pane.
- <strong>No resource types appear in the Fields pane.</strong> You may be in the wrong project. Glance at the project picker (top-left). New projects can also take a few minutes for the first audit logs to index.
- <strong>You see "Permission denied" on the Logging page.</strong> Your Garage role should include <code>roles/logging.viewer</code>. Flag a Sherpa; the IAM binding may be incomplete.
- <strong>You don't see <code>k8s_container</code> or <code>cloud_composer_environment</code>.</strong> Those resource types only appear after the corresponding service is provisioned: GKE in Q2D-1, Composer in Q2B-1. If you don't see them yet, that is expected.
</Gotchas>

<Shipped>
You know where to go when things break. The Logs Explorer is open, you can pick a resource type, filter by severity, and read the error. Logging is pinned alongside your four build products. <strong>Orientation complete. Go to your lane and start building.</strong>
</Shipped>
