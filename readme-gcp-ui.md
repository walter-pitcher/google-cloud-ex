## Deploy Continuous Polling to Google Cloud (GCP Console Only)

This guide is a **UI-only** version of `readme.md`.  
It shows how to deploy the same polling service using **Google Cloud Console (web UI only)** — no `gcloud` commands.

The architecture and code are **exactly the same** as in `readme.md`:

- A **Cloud Run** service that runs one poll cycle per HTTP request.
- A **Cloud Scheduler** job that calls the Cloud Run URL on a schedule.
- A **service account** that lets Scheduler call Cloud Run securely.

If you prefer the CLI version, use `readme.md`.  
If you want to click everything in the browser, use **this file**.

---

## Table of Contents

1. [What You Are Building](#what-you-are-building)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Select or Create Your Project](#step-1--select-or-create-your-project)
4. [Step 2 — Enable Required APIs](#step-2--enable-required-apis)
5. [Step 3 — Build and Store the Container Image](#step-3--build-and-store-the-container-image)
6. [Step 4 — Deploy the Cloud Run Service](#step-4--deploy-the-cloud-run-service)
7. [Step 5 — Create a Service Account for Scheduler](#step-5--create-a-service-account-for-scheduler)
8. [Step 6 — Allow That Service Account to Call Cloud Run](#step-6--allow-that-service-account-to-call-cloud-run)
9. [Step 7 — Create the Cloud Scheduler Job](#step-7--create-the-cloud-scheduler-job)
10. [Step 8 — Trigger One Run Manually](#step-8--trigger-one-run-manually)
11. [Step 9 — Confirm Cloud Run Ran Your Code](#step-9--confirm-cloud-run-ran-your-code)
12. [Common Mistakes (UI Version)](#common-mistakes-ui-version)

---

## What You Are Building

This UI guide deploys the **same app and pattern** described in `readme.md`:

### What your script does today (locally)

On your computer, the script might look like this: it runs **forever** in a loop:

```python
while True:
    poll_publication_service()   # Check for new data
    if new_record:
        map_data()               # Transform the data
        call_api()               # Send to another system
        acknowledge()            # Mark as done
```

### Why we change it for Google Cloud

**Cloud Run is request-driven.** It is **not** meant for a process that runs forever in the background. If you put an infinite loop in Cloud Run:

- The container may be stopped when "idle."
- You pay for and manage long-running processes in a way Cloud Run is not designed for.

So we change the pattern to:

1. **One request = one poll cycle.** Each time Cloud Run receives an HTTP request, it runs your poll logic **once** and then exits.
2. **Cloud Scheduler** sends that HTTP request on a schedule (e.g. every minute).
3. Result: from the outside it **looks** like continuous polling, but inside Cloud Run we only "run once per request."

### What we build

- A **Cloud Run service**: a small web app that exposes an HTTP endpoint. When someone (or Cloud Scheduler) calls that URL, your `run_poll()` runs once.
- A **Cloud Scheduler job**: a cron-like job that calls your Cloud Run URL every minute (or whatever schedule you set).

So the flow is: **Scheduler → HTTP request → Cloud Run → run_poll() once → response → done.**

---

## Prerequisites

- You have a **Google account** (Gmail or Workspace).
- You can sign in to **Google Cloud Console**: `https://console.cloud.google.com`.
- You have a **Google Cloud project** with **billing enabled** (you can also create one in Step 1).
- You have this repository’s code available in **some Git repo** (e.g. GitHub) or can upload a ZIP if needed.

> You do **not** need to install the Google Cloud SDK or use the terminal for this guide.

---

## Step 1 — Select or Create Your Project

1. In your browser, open `https://console.cloud.google.com`.
2. At the top of the page, click the **project selector** (it might say "Select a project").
3. Do one of:
   - **Use existing project**: choose the project you want to deploy into and click **Open**.
   - **Create new project**:
     - Click **NEW PROJECT** (or **Create Project**).
     - Fill in a **Project name** (e.g. "poller-app").
     - Click **CREATE** and wait until it is ready.
4. Make sure the **correct project** is selected (you will see its name at the top of the console).

![New Project form](image/Screenshot%202026-02-18%20104042.png)

You will use this same project for Cloud Run, Cloud Scheduler, and IAM.

---

## Step 2 — Enable Required APIs

You need these APIs:

- **Cloud Run Admin API**
- **Cloud Build API**
- **Cloud Scheduler API**

To enable them:

1. In the left navigation, go to **APIs & Services → Library**.
2. Search for **"Cloud Run Admin API"**.
3. Click it, then click **Enable**.
4. Repeat for:
   - **Cloud Build API**
   - **Cloud Scheduler API**

![API Library — Cloud Run Admin API](image/Screenshot%202026-02-18%20104651.png)

If you see "API enabled" already, you can leave it as is.

---

## Step 3 — Build and Store the Container Image

Your goal in this step is to get a container image. You may see one of these formats:

| Format | Meaning | When you see it |
|--------|--------|------------------|
| **`gcr.io/YOUR_PROJECT_ID/poller`** | **Google Container Registry (GCR)** — legacy registry. Replace `YOUR_PROJECT_ID` with your GCP project ID. The image name is `poller`. | Option B (Cloud Build trigger) when you set **Image** to something like `gcr.io/YOUR_PROJECT_ID/poller`. |
| **`LOCATION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY/poller`** | **Artifact Registry** — Google’s current recommended registry. Replace: `LOCATION` (e.g. `us-central1`), `YOUR_PROJECT_ID`, and `REPOSITORY` (the Artifact Registry repo name, e.g. `cloud-run-source-deploy`). | Option A (Cloud Run “deploy from repo”) often uses Artifact Registry by default. |

**In short:** Both are valid. Use the **same** image URL when deploying the Cloud Run service in Step 4. If the UI shows an Artifact Registry URL, use that; if you built with a trigger and used `gcr.io/...`, use that.

There are two common UI paths.

### Option A — Let Cloud Run Build from Your Git Repo (Recommended)

1. Push this project (including `Dockerfile`, `requirements.txt`, `app.py`, `main.py`) to a Git provider (e.g. GitHub).
2. In Cloud Console, go to **Cloud Run**.

![Navigate to Cloud Run](image/Screenshot%202026-02-18%20104904.png)

3. Click **Create service**.
4. Under **Deployment platform**, keep **Cloud Run (fully managed)**.
5. Under **Source**, choose something like:
   - **Continuously deploy from a repository**, or
   - **Source repository** (wording can vary).
6. If prompted, click **Set up with Cloud Build** and then:
   - Connect your **GitHub** account.
   - Select the repository and branch where this code lives.
7. In the build configuration:
   - Choose **Dockerfile** as the build type (if asked).
   - Point to the `Dockerfile` path (usually just `Dockerfile` in the repo root).
8. Continue to the next steps (you will finish service config in [Step 4](#step-4--deploy-the-cloud-run-service)).

Cloud Run will call **Cloud Build** behind the scenes, build the image, and store it in a registry for you.

### Option B — Create a Cloud Build Trigger (More Explicit)

Use this if you want to see the build as a separate step.

1. In Cloud Console, go to **Cloud Build → Triggers**.
2. Click **Create Trigger**.
3. Connect your repository (GitHub, Cloud Source Repositories, etc.).
4. Configure:
   - **Event**: push to a branch (e.g. `main`).
   - **Build configuration**: choose **Dockerfile** or equivalent.
   - **Dockerfile location**: path to your `Dockerfile` (often just `Dockerfile`).
   - **Image**: set to something like `gcr.io/YOUR_PROJECT_ID/poller`.
5. Save the trigger.
6. On the Triggers list, click the trigger and choose **Run** to start a manual build.
7. Wait until the build shows **Succeeded**.

You now have a container image you can select in Cloud Run.

---

## Step 4 — Deploy the Cloud Run Service

1. In Cloud Console, go to **Cloud Run**.
2. Click **Create service**.

![Cloud Run overview — deploy options](image/Screenshot%202026-02-18%20105120.png)

![Create service — continuous deploy from repository](image/Screenshot%202026-02-18%20110802.png)

3. Make sure **Cloud Run (fully managed)** is selected.
4. **Service name**: enter `poller-service`.
5. **Region**: choose a region that supports Cloud Run (e.g. `us-central1`).
6. **Deployment** (image/source):
   - If you used **Option A** above, pick the connected **repo/branch** and keep the defaults for image storage.
   - If you used **Option B**, choose **Deploy one revision from an existing container image** and select/paste the image (e.g. `gcr.io/YOUR_PROJECT_ID/poller`).
7. **Authentication**:
   - Select **Require authentication** (this is the UI equivalent of `--no-allow-unauthenticated`).
8. **Container settings** (often under **Container, connections, security** → **Container** tab):
   - **Request timeout**: set to `300` seconds.
   - **Maximum requests per container (concurrency)**: set to `1`.
9. Click **Create** (or **Deploy**).

When deployment finishes:

- Open the `poller-service` details page.
- Copy the **URL** shown at the top (e.g. `https://poller-service-xxxxx-uc.a.run.app`).
- This is your **Cloud Run URL**; you will need it in Step 7.

---

## Step 5 — Create a Service Account for Scheduler

This service account will be used by **Cloud Scheduler** to call your Cloud Run service.

1. In Cloud Console, go to **IAM & Admin → Service accounts**.
2. Click **+ CREATE SERVICE ACCOUNT**.
3. Enter:
   - **Service account name**: `Scheduler Invoker`
   - **Service account ID**: `scheduler-invoker`

![Create service account — Scheduler Invoker](image/Screenshot%202026-02-18%20111001.png)

4. Click **Create and continue**.
5. You can **skip** role assignment here (you will grant the specific role in the next step).
6. Click **Done**.

You should now see a service account like:

- `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`

![Service accounts list — scheduler-invoker](image/Screenshot%202026-02-18%20111036.png)

---

## Step 6 — Allow That Service Account to Call Cloud Run

Now give the `scheduler-invoker` service account permission to invoke your Cloud Run service.

1. In Cloud Console, go to **Cloud Run → Services → poller-service**.
2. Open the **Permissions** tab.
3. Click **Grant access** (or **Add principal**).
4. In **New principals**, enter:
   - `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`
5. In **Role**, choose:
   - **Cloud Run Invoker**.
6. Click **Save**.

This is equivalent to adding an IAM policy binding with role `roles/run.invoker`.

---

## Step 7 — Create the Cloud Scheduler Job

You will now create a Scheduler job that sends an authenticated HTTP request to your Cloud Run URL on a schedule (for example, every minute).

1. In Cloud Console, go to **Cloud Scheduler**.
2. Make sure the **location/region** is what you want (e.g. `us-central1`).
3. Click **Create job**.
4. Fill in:
   - **Name**: `poller-every-minute`
   - **Region**: `us-central1` (or your chosen Scheduler region)
   - **Description**: optional (e.g. "Call poller-service every minute").
5. Under **Frequency**, enter:
   - `* * * * *` (every minute)
6. Choose a **Time zone**.
7. Under **Target**:
   - **Target type**: `HTTP`.
   - **URL**: paste your Cloud Run URL from Step 4, including the trailing `/` if you want root path, for example:
     - `https://poller-service-xxxxx-uc.a.run.app/`
   - **HTTP method**: `GET`.
8. Under **Authentication**:
   - Choose **OIDC**.
   - **Service account**: select `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`.
   - **Audience**: usually paste the same Cloud Run URL you used in **URL**.
9. Click **Create**.

Cloud Scheduler will now be set to call your Cloud Run service according to the cron schedule you provided.

---

## Step 8 — Trigger One Run Manually

To test your setup immediately:

1. In Cloud Console, go to **Cloud Scheduler → Jobs**.
2. Click on the job `poller-every-minute`.
3. Click **Run now**.
4. Confirm the action if prompted.

You should see a small notification that the job was triggered successfully.

---

## Step 9 — Confirm Cloud Run Ran Your Code

To check that Cloud Run actually received and ran the request:

1. In Cloud Console, go to **Cloud Run**.
2. Click on **poller-service**.
3. Open the **Logs** tab.
4. Look at recent logs around the time you clicked **Run now**.

You should see log entries produced by your app (from `main.py`), such as messages indicating that it has polled and processed records.

If you do not see logs:

- Make sure you are in the **correct project** and **region**.
- Check that the Scheduler job points to the **exact** Cloud Run URL.
- Confirm that the `scheduler-invoker` service account has the **Cloud Run Invoker** role on `poller-service`.

---

## Common Mistakes (UI Version)

- **Wrong project selected**:
  - Symptoms: services, jobs, or logs "missing".
  - Fix: check the project name/ID at the top of the console; switch if needed.

- **APIs not enabled**:
  - Symptoms: error banners mentioning disabled APIs when using Cloud Run, Cloud Build, or Cloud Scheduler pages.
  - Fix: go to **APIs & Services → Library** and ensure Cloud Run Admin API, Cloud Build API, and Cloud Scheduler API are enabled.

- **Scheduler job returns 403 / unauthorized**:
  - Symptoms: Scheduler job details show HTTP 403; Cloud Run logs show unauthorized.
  - Fix:
    - Verify that `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com` has **Cloud Run Invoker** on `poller-service` (Cloud Run → `poller-service` → Permissions).
    - Confirm Scheduler job’s **Authentication** is set to **OIDC** with that same service account, and that the **Audience** matches the Cloud Run URL.

- **Wrong Cloud Run URL in Scheduler**:
  - Symptoms: Scheduler logs show 404 or hitting the wrong service.
  - Fix: copy the URL again from **Cloud Run → poller-service** and paste it into the Scheduler job **URL** field; redeploy or update the job.

- **Build or deployment using outdated source**:
  - Symptoms: code changes not reflected when Cloud Run runs.
  - Fix: push your latest code to the branch connected to Cloud Run / Cloud Build, then trigger a new deployment (rebuild) from Cloud Run or Cloud Build UI.

Once all of the above works, your polling script will be running on **Cloud Run**, triggered on a **schedule** by **Cloud Scheduler**, all configured via the **GCP Console UI only**.

