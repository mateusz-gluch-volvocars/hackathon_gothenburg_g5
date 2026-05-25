# 🌐 Quest 1-3 — Your Garage's VPC

<Objective lane="all">

**🎯 What you'll do.** Open the VPC Networks page, look at the `garage-vpc` VPC and its single regional subnet in `europe-west1`, note the subnet's CIDR range, and understand the **no public IPs** Volvo Cars org policy that shapes everything you'll build today. ~5 minutes, all four of you, on your own laptop.

**🤝 Why it matters.** Every resource you create today. AlloyDB cluster, GKE nodes, Composer workers, lives inside this VPC. Half the day's *"why can't X talk to Y?"* puzzles dissolve once you've seen the runway. This page is **look-don't-touch**: your VPC is pre-provisioned and the rest of the Quest depends on its exact shape.

</Objective>

> ~5 minutes. Everyone in the Garage, on your own laptop browser. **No clicking on Create / Edit / Delete buttons.**

This is the only page in Quest 1 where you're not setting something up; you're orienting yourself to the runway your work will land on.

---

## 1. Why

Every cloud resource lives somewhere on a network. In Google Cloud, that "somewhere" is a **VPC**. a Virtual Private Cloud, which is your project's own private slice of the internet. Inside the VPC you have **subnets** (one per region), private IP ranges, firewall rules, and routes.

One thing worth knowing about how Volvo Cars uses VPCs: **public IPs are not given out without cause** and are handled with exceptions. For today's hackathon, all your infrastructure runs on private IPs inside the VPC. That's why we use **Cloud Workstations** to reach private infrastructure; your Workstation is already inside the VPC, so it has direct access to things like AlloyDB's private IP.

**Private Google Access** is enabled on the subnet, which means private resources can still reach `*.googleapis.com` (Artifact Registry, BigQuery, Cloud Build, etc.) over Google's private backbone, no public IP needed.

## 2. What it looks like when done

The VPC Networks page in the Console, showing your project's `garage-vpc` (custom-mode), a single regional subnet in `europe-west1` named `garage-vpc` with CIDR `10.0.0.0/16` and Private Google Access on, and one firewall rule (`allow-internal`).

<Screenshot src="/quest/pothole-poet/img/console_vpc_detail.png" caption="VPC Network detail page for `garage-vpc`. the Subnets tab open, showing one regional subnet in europe-west1 with CIDR 10.0.0.0/16, Private Google Access ON, and the allow-internal firewall rule listed beneath." />

## 3. Find your VPC

1. Press <kbd>/</kbd> to open the search bar and type `VPC network`. Click **VPC networks** in the results. (You can pin it if you want, but you'll only visit it once or twice today.)

2. You see one VPC in your project: **`garage-vpc`**. Click its name.

*(If you also see a `default` VPC sitting alongside, that's a leftover from GCP's auto-provisioning. The Quest uses `garage-vpc` exclusively, ignore the default one.)*

## 4. Look at the two things that matter

The VPC detail page has two things to look at. Don't change either of them.

**Subnets.** One subnet named `garage-vpc`, in region `europe-west1`, with a CIDR range of `10.0.0.0/16`. You'll see IPs from this range on every resource that lives directly in the VPC today, the Workstation VMs you're sitting in, the AlloyDB Service Networking peering allocation. (The AlloyDB cluster itself and the GKE nodes use peered or alias IP ranges rather than this subnet directly, more on that in the lane codelabs.)

**Firewall rules** (tab in the left rail or the "Firewalls" sub-page). One rule:

- `allow-internal`. ingress on tcp/udp/icmp from `10.0.0.0/8`. Anything inside the VPC can talk to anything else in the VPC, on any port. This is why the Workstation can `psql` into AlloyDB's private IP, why the GKE Pod can hit AlloyDB later, why Composer's DAG can reach BigQuery's regional endpoint.

That's the only firewall rule we ship. Volvo Cars' `compute.vmExternalIpAccess` policy means no VM in this VPC has a public IP, so the usual GCP `allow-ssh` / `allow-rdp` / `allow-icmp` rules from-anywhere would be dead weight, we don't create them.

## 5. While you wait

*Nothing waits.* If a teammate is still scrolling, point them at the CIDR (`10.0.0.0/16`) and the `allow-internal` firewall rule; that's the whole story of this page.

## 6. Verify

- You can name your VPC (`garage-vpc`) and its subnet CIDR (`10.0.0.0/16`).
- You did *not* click any Create / Edit / Delete buttons.

That's it. Verification for Q1-3 is conceptual; you understand where things will live.

<Concept title="What is a VPC, in one paragraph?">

A **VPC** is a project-scoped private network. Resources inside the same VPC can reach each other on **private IPs**. addresses from the subnet's CIDR range, like `10.0.0.5`. Resources in different VPCs can't talk by default (you'd need VPC peering, a Cloud VPN, or a public IP and the open internet). VPCs span a whole project, but **subnets are regional**. each subnet covers one GCP region. Today you have one subnet, `garage-vpc` in `europe-west1`. Everything you build lives there.

Your Garage's VPC was pre-created by the platform team, with one regional subnet in `europe-west1`, Private Google Access on, an `allow-internal` firewall rule, and a Service Networking peering already configured so AlloyDB's managed network can hand you a private IP in Q2A.

</Concept>

<Concept title="What's a CIDR range, in 30 seconds?">

A CIDR like `10.0.0.0/16` is shorthand for "a block of IP addresses starting at `10.0.0.0` and extending across the first 16 bits of the address." In practice that means **65,536 addresses** in the range `10.0.0.0` to `10.0.255.255`. The `/16` is the prefix length; smaller numbers mean bigger blocks (a `/8` is 16M addresses, a `/24` is 256).

Workstation VMs and the AlloyDB peering allocation today come out of this block. You don't have to do anything with the number; it's just useful to know your IPs are private and what private range they're in.

</Concept>

<Gotchas>
- <strong>You see a <code>default</code> VPC alongside <code>garage-vpc</code>.</strong> Ignore the default one; it's a GCP auto-create artifact and isn't wired up for the Quest. All later codelabs use <code>garage-vpc</code> exclusively.
- <strong>You see "Activate this API" on the VPC Networks page.</strong> Shouldn't happen (the Compute Engine API is pre-enabled); flag a Sherpa if you do.
- <strong>You accidentally clicked Edit on the <code>allow-internal</code> firewall rule.</strong> Click <strong>Cancel</strong>, not Save. The rule is load-bearing, changing or deleting it silently breaks later codelabs.
</Gotchas>

<Shipped>
You can name your Garage's VPC (<code>garage-vpc</code>) and its subnet CIDR (<code>10.0.0.0/16</code>). You know why Volvo Cars VMs have no public IPs, and how Private Google Access plus Google's managed front doors fill the gap. <strong>The runway is clear, on to Q1-4, your Workstation.</strong>
</Shipped>
