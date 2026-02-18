# Deploy Continuous Polling to Google Cloud

This guide walks you through deploying a **polling script** to Google Cloud so it runs automatically on a schedule. It is written for beginners: every step is explained, and you will learn what each part does.

---

## Table of Contents

1. [Ultra-Quick Start (All Steps, All Commands)](#ultra-quick-start-all-steps-all-commands)
2. [What You Are Building](#what-you-are-building)
3. [Key Terms (Glossary)](#key-terms-glossary)
4. [Prerequisites](#prerequisites)
5. [Architecture Overview](#architecture-overview)
6. [Step-by-Step Deployment](#step-by-step-deployment)
7. [Environment Variables and Secrets](#environment-variables-and-secrets)
8. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
9. [Troubleshooting](#troubleshooting)
10. [Quick Checklist](#quick-checklist)
11. [Optional: Cloud Run Jobs](#optional-cloud-run-jobs)

---

## Ultra-Quick Start (All Steps, All Commands)

This section is a **copy–paste friendly checklist** using **this exact project** (`google-cloud-ex`) as the example.  
Follow it **from top to bottom once**, then use later sections for deeper explanations.

> Wherever you see `YOUR_PROJECT_ID`, replace it with your real GCP Project ID  
> (for example: `my-gcp-project-123456`).

### 1. Install and verify gcloud

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **OS** | Windows 10+, macOS 10.14+, or Linux (x86_64 / ARM). |
| **Disk** | ~500 MB for SDK; more if using optional components. |
| **Permissions** | User account with write access to install directory (e.g. no need for admin if using user install). |
| **Network** | Internet to download installer and components. |

1. Install the Google Cloud SDK from: `https://cloud.google.com/sdk/docs/install`.
2. Close and reopen your terminal (or open a new one).
3. Check installation:

```bash
gcloud version
```

You should see version info instead of "command not found".

**Possible errors and solutions (Step 1):**

| Error | Cause | Solution |
|-------|--------|----------|
| `gcloud: command not found` (Windows) | Installer didn't add to PATH, or terminal not restarted. | Restart terminal. If still missing: add install path (e.g. `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin`) to system PATH. |
| `gcloud: command not found` (macOS/Linux) | Same as above. | Run the installer's `install.sh` again or add the SDK `bin` directory to your `PATH` in `~/.bashrc` or `~/.zshrc`. |
| Installer fails with "Access denied" | No write permission to install folder. | Run as admin (Windows) or choose a user directory; or use `curl \| bash` install to home directory. |
| `gcloud version` shows old version | Cached or old install. | Run `gcloud components update` to get latest. |

### 2. Log in and set your project

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Browser** | Default browser for OAuth; must be able to open `https://accounts.google.com`. |
| **Google account** | Personal Gmail or Google Workspace with access to the GCP project. |
| **Project** | Project must already exist; you need its **Project ID** (not project name or number). |

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config get-value project
```

The last command must print **exactly** the Project ID you want to use.

**Possible errors and solutions (Step 2):**

| Error | Cause | Solution |
|-------|--------|----------|
| `ERROR: (gcloud.auth.login) ... Unable to open browser` | Headless or SSH environment. | Run `gcloud auth login --no-launch-browser`, then open the printed URL in a machine with a browser and paste the code back. |
| `ERROR: (gcloud.config.set project) ... Project ID ... not found` | Wrong ID, project deleted, or no access. | Check ID: `gcloud projects list`. Ensure project exists and your account has access. Use the **PROJECT_ID** column value. |
| `You do not currently have an active account selected` | Not logged in or session expired. | Run `gcloud auth login` again. |
| Browser opens but "Access blocked" or "Invalid client" | Org policy or app not trusted. | Use a personal Google account, or ask org admin to allow Google Cloud SDK. |

### 3. Enable required APIs (once per project)

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **IAM** | Your account needs `serviceusage.services.enable` (e.g. Owner, Editor, or "Service Usage Admin"). |
| **Billing** | Project must have a billing account linked (APIs can still be free tier). |
| **Network** | Internet access for API calls. |

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

All three must finish with a success message.

**Possible errors and solutions (Step 3):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Permission denied` or `403` on enable | Account lacks permission. | Use an account with Owner/Editor on the project, or add role "Service Usage Admin". |
| `Billing account not found` / billing error | Project has no billing account. | In Console: Billing → Link a billing account to this project. |
| `API [run.googleapis.com] not enabled` (later steps) | Enable didn't complete or wrong project. | Re-run the three `gcloud services enable` commands; wait 1–2 minutes and retry. |
| Operation hangs or times out | Propagation delay. | Wait 30–60 seconds and run the same command again; check [Console → APIs & Services](https://console.cloud.google.com/apis/library). |

### 4. Build the container image from this folder

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Working directory** | Must be the folder containing `Dockerfile`, `requirements.txt`, `app.py`, `main.py`. |
| **APIs** | Cloud Build API enabled (Step 3). |
| **IAM** | Account needs `cloudbuild.builds.create` and Storage (e.g. "Cloud Build Editor" or Owner). |
| **Network** | Stable internet; build uploads context and pulls base image. |
| **Quota** | Cloud Build has a free tier; first builds usually stay within it. |

Make sure you are inside the project folder that has the `Dockerfile`:

```bash
cd "C:\git\my project\google-cloud-ex"
ls Dockerfile
```

Then build the image:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/poller
```

Wait until you see `SUCCESS` and the image name (`gcr.io/YOUR_PROJECT_ID/poller`).

**Possible errors and solutions (Step 4):**

| Error | Cause | Solution |
|-------|--------|----------|
| `ERROR: (gcloud.builds.submit) ... Dockerfile not found` | Wrong directory or no Dockerfile. | `cd` to the project root and run `ls Dockerfile` (or `dir Dockerfile` on Windows). |
| `ERROR: ... Permission denied` / 403 | Missing IAM or APIs. | Enable Cloud Build API; ensure account has Cloud Build Editor (or Owner). |
| `ERROR: failed to solve: ... pull access denied` | Base image `python:3.11-slim` not pullable. | Check network/proxy; retry. If on restricted network, use a mirror or allow Docker Hub. |
| `ERROR: ... requirements.txt ... No such file` | File missing or wrong case. | Ensure `requirements.txt` exists in same folder as Dockerfile; check spelling/case. |
| Build runs but fails at `pip install` | Invalid or private package in `requirements.txt`. | Fix package names/versions in `requirements.txt`; run `pip install -r requirements.txt` locally to reproduce. |
| Upload very slow or timeout | Large context (e.g. `node_modules`, `.git`). | Add a `.dockerignore` (e.g. `__pycache__`, `.git`, `*.pyc`) to shrink upload. |

### 5. Deploy the Cloud Run service

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Image** | Image from Step 4 must exist: `gcr.io/YOUR_PROJECT_ID/poller`. |
| **APIs** | Cloud Run API enabled (Step 3). |
| **IAM** | Account needs `run.services.create` / `run.services.update` (e.g. "Cloud Run Admin" or Owner). |
| **Region** | Use a region where Cloud Run is available (e.g. `us-central1`, `europe-west1`). |

```bash
gcloud run deploy poller-service ^
  --image gcr.io/YOUR_PROJECT_ID/poller ^
  --platform managed ^
  --region us-central1 ^
  --no-allow-unauthenticated ^
  --timeout=300 ^
  --concurrency=1
```

> On macOS / Linux, use `\` line continuations instead of `^`:

```bash
gcloud run deploy poller-service \
  --image gcr.io/YOUR_PROJECT_ID/poller \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --timeout=300 \
  --concurrency=1
```

At the end, note the **Service URL** (looks like `https://poller-service-xxxxx-uc.a.run.app`).  
We call this `YOUR_CLOUD_RUN_URL`.

You can always re-print it later:

```bash
gcloud run services describe poller-service --region us-central1 --format="value(status.url)"
```

**Possible errors and solutions (Step 5):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Image ... not found` or `Failed to pull image` | Image not built or wrong project/tag. | Run Step 4 again; use exact tag `gcr.io/YOUR_PROJECT_ID/poller`. List images: `gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID`. |
| `Permission denied` / 403 on deploy | Missing Cloud Run or IAM. | Enable Cloud Run API; grant "Cloud Run Admin" (or Owner) to your account. |
| `ResourceExhausted` or quota | Project/region quota exceeded. | Use another region or request quota increase in Console. |
| Deploy succeeds but service won't start (CrashLoopBackOff in logs) | App crashes on boot (e.g. missing env, wrong port). | Check Cloud Run logs; ensure app listens on `PORT` (default 8080) and has no required env vars missing. |
| `Do you want to continue (Y/n)?` | Confirmation prompt. | Type `Y` and Enter to proceed. |

### 6. Create a service account for Scheduler

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **IAM** | Account needs `iam.serviceAccounts.create` (e.g. Owner or "Service Account Admin"). |
| **Name** | Service account ID must be unique in project; only lowercase, numbers, hyphens (e.g. `scheduler-invoker`). |

```bash
gcloud iam service-accounts create scheduler-invoker ^
  --display-name="Scheduler Invoker"
```

If it already exists, you can reuse it.

**Possible errors and solutions (Step 6):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Already exists` | Service account with that ID already in project. | Safe to ignore; use the existing account for Step 7 and 8. Or use a different ID (e.g. `scheduler-invoker-2`). |
| `Invalid argument` / name rejected | Invalid characters or length. | Use only lowercase letters, numbers, hyphens; 6–30 chars. |
| `Permission denied` | Cannot create service accounts. | Use Owner or add "Service Account Admin" role. |

### 7. Allow that service account to call Cloud Run

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Service** | `poller-service` must be deployed (Step 5). |
| **Region** | Must match the region used in Step 5 (e.g. `us-central1`). |
| **IAM** | Your account needs `run.services.setIamPolicy` (e.g. Owner or "Cloud Run Admin"). |
| **Service account** | `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com` must exist (Step 6). |

```bash
gcloud run services add-iam-policy-binding poller-service ^
  --region us-central1 ^
  --member="serviceAccount:scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com" ^
  --role="roles/run.invoker"
```

This is what lets Cloud Scheduler call your service securely.

**Possible errors and solutions (Step 7):**

| Error | Cause | Solution |
|-------|--------|----------|
| `403 Forbidden` when Scheduler runs (later) | Binding not applied or wrong account/region. | Re-run this command with exact service account email and `--region us-central1`. In Console: Cloud Run → poller-service → Permissions → confirm "Cloud Run Invoker" for `scheduler-invoker@...`. |
| `Service [poller-service] not found` | Wrong region or name. | Use same region as deploy: `--region us-central1`. List: `gcloud run services list --region us-central1`. |
| `Service account ... does not exist` | Wrong PROJECT_ID or typo. | Use exact email: `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`. List: `gcloud iam service-accounts list`. |
| `Permission denied` on add-iam-policy-binding | Your user lacks permission. | Use Owner or "Cloud Run Admin" to set IAM. |

### 8. Create the Cloud Scheduler job (runs every minute)

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Cloud Scheduler API** | Enabled in Step 3. |
| **URI** | Full Cloud Run URL from Step 5, including `https://` and trailing `/` (e.g. `https://poller-service-xxxxx-uc.a.run.app/`). |
| **Service account** | Same as Step 7: `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`. |
| **Location** | Use a region that has Cloud Scheduler (e.g. `us-central1`); often same as Cloud Run. |
| **IAM** | Account needs `cloudscheduler.jobs.create`. |

Replace `YOUR_CLOUD_RUN_URL` with the URL from step 5 (include the trailing `/`):

```bash
gcloud scheduler jobs create http poller-every-minute ^
  --location us-central1 ^
  --schedule "* * * * *" ^
  --uri "YOUR_CLOUD_RUN_URL/" ^
  --http-method GET ^
  --oidc-service-account-email "scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

Example with fake values:

```bash
gcloud scheduler jobs create http poller-every-minute ^
  --location us-central1 ^
  --schedule "* * * * *" ^
  --uri "https://poller-service-xxxxx-uc.a.run.app/" ^
  --http-method GET ^
  --oidc-service-account-email "scheduler-invoker@my-gcp-project-123456.iam.gserviceaccount.com"
```

**Possible errors and solutions (Step 8):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Job [poller-every-minute] already exists` | Job with that name already in location. | Use a new name (e.g. `poller-every-minute-2`) or delete first: `gcloud scheduler jobs delete poller-every-minute --location us-central1`. |
| `Invalid URI` or job runs but 404 | Missing `https://` or path. | Use full URL: `https://poller-service-xxxxx-uc.a.run.app/` (root path). |
| Scheduler runs but Cloud Run returns **403** | Invoker role not bound or wrong service account. | Re-do Step 7; ensure `--oidc-service-account-email` matches the account that has Invoker. |
| `Permission denied` creating job | Missing Scheduler permissions. | Grant "Cloud Scheduler Admin" (or Owner) to your account; ensure Cloud Scheduler API is enabled. |
| Cron expression rejected | Invalid cron syntax. | Use 5 fields: `* * * * *` (every minute). See [Cloud Scheduler cron](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules). |

### 9. Trigger one run manually

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Job** | Job created in Step 8; location must match (`us-central1`). |
| **IAM** | Account needs `cloudscheduler.jobs.run` (e.g. "Cloud Scheduler Admin" or Owner). |

```bash
gcloud scheduler jobs run poller-every-minute --location us-central1
```

You should see: `Job [poller-every-minute] has been run.`

**Possible errors and solutions (Step 9):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Job [poller-every-minute] not found` | Wrong name or location. | Use exact name and `--location us-central1`. List: `gcloud scheduler jobs list --location us-central1`. |
| `Permission denied` | Cannot trigger jobs. | Grant "Cloud Scheduler Admin" or Owner. |
| Job "has been run" but no logs in Cloud Run | 403 from Cloud Run or wrong URL. | Fix Step 7 (Invoker role); confirm Step 8 URI is correct and service is deployed. |

### 10. Confirm Cloud Run actually ran your code

**Environment / requirements:**

| Requirement | Details |
|-------------|--------|
| **Logging** | Cloud Run uses Cloud Logging; no extra API beyond Run. |
| **IAM** | To read logs: "Logs Viewer" or "Project Viewer" (or Owner). |

From the command line:

```bash
gcloud run services logs read poller-service --region us-central1 --limit 50
```

Look for log messages from `main.py` like:

- `Polled X record(s)`
- `Run finished. Processed X record(s).`

If you see those, **the full flow using this project is working**.  
Now you can read the rest of this guide for deeper explanations and customization.

**Possible errors and solutions (Step 10):**

| Error | Cause | Solution |
|-------|--------|----------|
| `No logs found` or empty output | No requests yet, or wrong service/region. | Trigger job (Step 9) and wait ~30 seconds; use correct `--region us-central1` and service name. |
| `Permission denied` reading logs | Missing logging permissions. | Grant "Logs Viewer" role on the project. |
| Logs show 4xx/5xx or container crash | App error or misconfiguration. | Open Cloud Run → poller-service → Logs; check stack traces and fix code or env (e.g. PORT, required env vars). |

---

## What You Are Building

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

## Key Terms (Glossary)

| Term | Meaning |
|------|--------|
| **gcloud** | Google Cloud command-line tool. You use it to create and manage resources (projects, Cloud Run, Scheduler, etc.). |
| **Project / Project ID** | A Google Cloud project is a container for all your resources (services, billing, etc.). The **Project ID** is a unique ID like `my-app-12345`. You need it in many commands. |
| **Cloud Run** | A service that runs your code in a **container** when it receives an HTTP request. You don't manage servers; Google runs and scales them for you. |
| **Container / Docker image** | A packaged version of your app (code + runtime). Cloud Run runs this image. |
| **Cloud Scheduler** | A cron-like service. It can send HTTP requests (or publish to Pub/Sub) on a schedule (e.g. every 1 minute). |
| **Service account** | An identity used by applications (not a human). Here we use one so that **Cloud Scheduler** is allowed to call **Cloud Run**. |
| **Region** | The geographic location where your service runs (e.g. `us-central1`). We use `us-central1` in this guide; you can change it. |

---

## Prerequisites

Before you start, make sure you have the following. Each item is explained in detail below.

1. **A Google account** (Gmail or Google Workspace).
2. **A Google Cloud project** (with billing enabled) — see [Creating a Google Cloud project](#creating-a-google-cloud-project).
3. **Your Project ID** — see [Finding your Project ID](#finding-your-project-id).
4. **Google Cloud CLI (gcloud) installed** — see [Installing gcloud](#installing-gcloud).

### Prerequisites — Environment summary

| Item | What you need |
|------|----------------|
| **Machine** | Windows 10+, macOS 10.14+, or Linux with terminal and internet. |
| **Browser** | For `gcloud auth login` and Cloud Console (OAuth and billing). |
| **Network** | Internet for gcloud, Cloud Build, and Cloud Run. |
| **Permissions** | Google account with Owner or Editor on the GCP project (or equivalent roles per step). |
| **Billing** | Project linked to a billing account (free tier is enough to start). |

### Prerequisites — Common errors and solutions

| Error | When it happens | Solution |
|-------|------------------|----------|
| "Billing account required" when enabling APIs | Creating project or enabling APIs. | In Console: Billing → Link a billing account to the project. |
| "You do not have permission" on project | Setting project or listing projects. | Use an account that has at least Viewer on the project; Owner/Editor for full deployment. |
| Project ID vs project number confusion | Commands expect Project ID. | Use the **Project ID** (e.g. `my-app-12345`), not the numeric project number. Find it in Console project selector or `gcloud projects list`. |

---

### Creating a Google Cloud project

A **Google Cloud project** is like a folder for everything you will create: your Cloud Run service, the Scheduler job, and billing. All resources belong to one project, and you use a **Project ID** (a unique name) to refer to it in commands and the console.

**If you already have a project** you want to use, skip to [Finding your Project ID](#finding-your-project-id). Otherwise, follow these steps to create a new one.

#### Step A — Open Google Cloud Console

1. In your browser, go to **[https://console.cloud.google.com/](https://console.cloud.google.com/)**.
2. Sign in with your Google account (Gmail or Google Workspace) if you are not already signed in.

You will see the Cloud Console home. At the top of the page there is a **project selector** (it may say "Select a project" or show the name of a current project).

#### Step B — Create a new project

1. Click the **project selector** at the top (next to "Google Cloud" or the Google Cloud logo).
2. In the window that opens, click **"NEW PROJECT"** (or "Create Project").
3. Fill in:
   - **Project name** — A friendly name only you see (e.g. "My Poller App"). You can change it later. This is **not** the Project ID.
   - **Organization** — If you have a Google Workspace organization, you can choose it. Otherwise leave as "No organization."
   - **Location** — Optional; leave default if you are not in an organization.
4. Click **"CREATE"** (or "Create").
5. Wait a few seconds. When the project is ready, it will be selected automatically and the console will switch to that project.

**Important:** The console also generates a **Project ID** for you. It is usually based on the project name but made unique (e.g. "my-poller-app" or "my-poller-app-123456"). You **must** use this Project ID (not the project name) in all `gcloud` commands and in this guide.

#### Step C — Enable billing on the project

Google Cloud requires a **billing account** to be linked to the project before you can use Cloud Run and Cloud Scheduler. You will not be charged just for linking billing; many services have a free tier, and you only pay when you go beyond free usage.

1. In the Cloud Console, open the **navigation menu** (☰) at the top left.
2. Go to **"Billing"** (under "Google Cloud" or search for "Billing" in the menu).
3. If you see **"Link a billing account"** or **"Create account"**:
   - Click it and follow the steps to create or link a billing account (you will need a payment method; free tier usage often stays within no-charge limits).
4. If you already have a billing account, make sure your **new project** is linked to it:
   - On the Billing page, click **"My projects"** or **"Manage billing accounts"** as needed.
   - Select your project and link it to the correct billing account.

When billing is linked, you can proceed. Keep the project selected; you will need its **Project ID** in the next section.

---

### Finding your Project ID

The **Project ID** is a unique identifier (e.g. `my-poller-app-123456`). You will paste it everywhere this guide says `YOUR_PROJECT_ID`.

**Option 1 — From the Cloud Console (browser)**

1. Click the **project selector** at the top of the page (it shows the current project name).
2. In the list, find your project. The **Project ID** is shown under or next to the project name (often in gray or smaller text).
3. Click the Project ID to copy it, or select and copy it manually. Save it somewhere handy (e.g. a text file).

**Option 2 — From the command line (after installing gcloud)**

If you have already installed the Google Cloud CLI and logged in (see Step 4 in the deployment steps), you can list your projects:

```bash
gcloud projects list
```

The output is a table. Use the value in the **PROJECT_ID** column (not the NAME column) as `YOUR_PROJECT_ID`.

**Check:** Project IDs are usually lowercase letters, numbers, and hyphens (e.g. `my-app-12345`). If you see a long number, that is the project number; the guide uses the **Project ID** (the text name), not the number.

---

### Installing gcloud

The **gcloud** CLI is the command-line tool for creating and managing resources (projects, Cloud Run, Scheduler, etc.). You need it to build and deploy from your terminal.

1. **Install:**  
   Follow the official install guide for your operating system:  
   **[https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)**  
   (Choose Windows, macOS, or Linux and follow the steps.)
2. **Restart your terminal** after installation (or open a new terminal window).
3. **Check that it works:**  
   Run:
   ```bash
   gcloud version
   ```
   You should see version numbers for `Google Cloud SDK` and related components. If the command is not found, the installer may not have added `gcloud` to your PATH; check the install guide for your OS.

You will use `gcloud` to log in and set your project in **Step 4** of the deployment section.

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Scheduler (runs on a schedule, e.g. every 1 minute)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │  HTTP GET request
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Run service (your container)                              │
│  • Receives GET /                                                │
│  • Calls run_poll() once:                                        │
│      - poll service (get new records)                            │
│      - map data (transform)                                      │
│      - call destination API                                      │
│      - acknowledge record                                        │
│  • Returns "OK" and exits                                        │
└─────────────────────────────────────────────────────────────────┘
```

So: **Scheduler sends GET → Cloud Run runs one poll cycle → response → done.** No infinite loop.

---

## Step-by-Step Deployment

### Step 1 — Prepare Your Python Code (Single Execution)

**Environment for this step:** Python 3.11+ recommended (to match the Dockerfile); no GCP resources needed yet.

Your code must **run once per request** and then exit. This project already does that.

**Location:** `main.py` defines `run_poll()`, which:

1. Fetches records from your poll source (e.g. mock in the sample).
2. For each record: maps data, sends to API, acknowledges.
3. Exits when done.

**Requirements:**

- No `while True` in the code that runs on Cloud Run.
- One invocation of `run_poll()` = one poll cycle.

The pattern in `main.py` is correct:

```python
def run_poll() -> None:
    records = poll_service()
    for r in records:
        mapped = map_data(r)
        send_api(mapped)
        acknowledge(r)
    logger.info("Run finished. Processed %d record(s).", len(records))
```

You will later replace `poll_service()`, `send_api()`, and `acknowledge()` with your real logic (e.g. Pub/Sub, your API, your DB).

---

### Step 2 — HTTP Endpoint for Cloud Run

**Environment for this step:** Flask and dependencies from `requirements.txt`; app must listen on `PORT` (default 8080) for Cloud Run.

Cloud Run needs an **HTTP endpoint** to trigger your logic. That is in `app.py`:

- **GET /** — runs `run_poll()` once and returns `"OK"`. This is the URL Cloud Scheduler will call.
- **GET /health** — returns `"OK"`. Used for health/liveness checks.

No changes are required here for the basic deployment.

---

### Step 3 — Project Structure

**Environment for this step:** All files in one folder; no extra tools required. Commands in later steps assume you run them from this folder.

Your project folder should look like this:

```text
google-cloud-ex/
  main.py           # Poll logic (run_poll, poll_service, map_data, etc.)
  app.py            # Flask app: GET / and GET /health
  requirements.txt  # Python dependencies (flask, requests, ...)
  Dockerfile        # Builds the container image for Cloud Run
  DEPLOYMENT_GUIDE.md
```

All of these should be in the same folder. You will run the following commands from this folder (e.g. `google-cloud-ex`).

---

### Step 4 — Install gcloud and Log In

1. **Install gcloud**  
   - Follow: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)  
   - Restart your terminal after installation.

2. **Log in** (opens a browser to sign in with your Google account):

   ```bash
   gcloud auth login
   ```

3. **Set the project** (replace `YOUR_PROJECT_ID` with your real Project ID from Prerequisites):

   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

   Example: `gcloud config set project my-app-123456`

4. **Check that it worked:**

   ```bash
   gcloud config get-value project
   ```

   You should see your Project ID printed.

---

### Step 5 — Enable Required APIs

**Environment for this step:**

| Requirement | Details |
|-------------|--------|
| **APIs** | None needed in advance; this step enables them. |
| **IAM** | Your account needs `serviceusage.services.enable` (included in Owner, Editor, or "Service Usage Admin"). |
| **Billing** | Project must have billing linked; otherwise enable may fail. |

Google Cloud requires you to **enable** APIs for each project. We need:

- **Cloud Run** — to run your service.
- **Cloud Build** — to build your container image.
- **Cloud Scheduler** — to trigger your service on a schedule.

Run these three commands (one at a time is fine):

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

**What you might see:**  
Each command may take 10–30 seconds and print something like "Operation finished successfully." If you get a permission error, make sure you are logged in and your account has "Owner" or "Editor" on the project.

**Possible errors and solutions (Step 5):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Permission denied` or `403` | Account cannot enable APIs. | Use Owner/Editor or add "Service Usage Admin" role. |
| `Billing account not found` | Project has no billing. | In Console: Billing → Link a billing account. |
| `API already enabled` | Normal if re-running. | No action; proceed to next step. |
| Operation hangs | Propagation delay. | Wait 1–2 minutes; re-run the same command if needed. |

---

### Step 6 — Build and Deploy to Google Cloud

This step has **two parts**: first you **build** a container image from your project, then you **deploy** that image to Cloud Run so it can receive HTTP requests. Both use the `gcloud` CLI.

**Overview:**

1. **Build** — Your project (code + `Dockerfile`) is sent to **Google Cloud Build**. Cloud Build runs the steps in your `Dockerfile` to create a **Docker image** and stores it in **Google Container Registry** (e.g. `gcr.io/YOUR_PROJECT_ID/poller`).
2. **Deploy** — You tell Cloud Run to run that image as a **service**. Cloud Run creates a new **revision** (a version of your service), routes traffic to it, and gives you a public URL (protected by authentication).

You must do the build first; the deploy command uses the image produced by the build.

---

#### 6.1 — Open a terminal in your project folder

**Environment for 6.1:**

| Requirement | Details |
|-------------|--------|
| **Shell** | Any terminal (PowerShell, cmd, Git Bash, WSL, macOS/Linux terminal). |
| **Working directory** | Must be the project root where `Dockerfile`, `app.py`, `main.py`, `requirements.txt` exist. |

All commands in this step must be run from the folder that contains your app and the `Dockerfile`. That folder should contain at least:

- `main.py`
- `app.py`
- `requirements.txt`
- `Dockerfile`

**Example (Windows):**

```bash
cd "C:\git\my project\google-cloud-ex"
```

**Example (Linux/macOS):**

```bash
cd /path/to/google-cloud-ex
```

Check that the `Dockerfile` is there:

```bash
# Windows (PowerShell)
dir Dockerfile

# Linux/macOS or Git Bash
ls -la Dockerfile
```

**Possible errors (6.1):** If `Dockerfile` not found, you are in the wrong directory; `cd` to the folder that contains the Dockerfile and try again.

---

#### 6.2 — Build the project (create the container image)

**What “building” means here**

- A **container image** is a snapshot of your app plus a Python runtime, so Cloud Run can run it the same way every time.
- The **Dockerfile** describes how to create that image: install dependencies from `requirements.txt`, copy your code, set the port, and define the command that starts the app (`python app.py`).
- **Cloud Build** runs that process in Google’s infrastructure and saves the result as an image in **Google Container Registry** with a tag like `gcr.io/YOUR_PROJECT_ID/poller`.

**Command to build**

Replace `YOUR_PROJECT_ID` with your actual Google Cloud Project ID (the one you set in Step 4):

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/poller
```

**What happens when you run it:**

1. `gcloud` uploads the contents of the current folder (respecting `.dockerignore` if present) to Cloud Build.
2. Cloud Build runs the `Dockerfile`:
   - Uses a base image (e.g. `python:3.11-slim`).
   - Installs packages from `requirements.txt`.
   - Copies your application code.
   - Sets the start command to `python app.py`.
3. The resulting image is stored as `gcr.io/YOUR_PROJECT_ID/poller`.
4. Build logs stream in the terminal; at the end you should see **SUCCESS** and the image name.

**Typical duration:** First build often takes 2–5 minutes. Later builds are faster thanks to caching.

**Environment for 6.2 (build):**

| Requirement | Details |
|-------------|--------|
| **Cloud Build API** | Enabled (Step 5). |
| **IAM** | `cloudbuild.builds.create`, storage for artifacts (e.g. "Cloud Build Editor" or Owner). |
| **Project** | Correct project: `gcloud config get-value project`. |
| **Network** | Upload and base image pull (Docker Hub for `python:3.11-slim`). |

**Possible errors and solutions (Step 6.2):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Dockerfile not found` | Wrong working directory. | Run from project root (6.1); `ls Dockerfile` to confirm. |
| `requirements.txt` not found / pip fails | Missing file or bad package name. | Ensure `requirements.txt` is in same dir as Dockerfile; test locally: `pip install -r requirements.txt`. |
| `pull access denied` for base image | Network or registry issue. | Check proxy/firewall; retry; ensure Docker Hub (or mirror) is reachable. |
| `Permission denied` / 403 | Cloud Build or Storage permission. | Enable Cloud Build API; grant "Cloud Build Editor" (or Owner). |
| Build context too large / timeout | Large files (e.g. `.git`, `node_modules`) uploaded. | Add `.dockerignore` with `__pycache__`, `.git`, `*.pyc`, large dirs. |
| `ERROR: ... failed to build` (generic) | Error in Dockerfile or app. | Read the build log line above the error; fix Dockerfile or dependencies. |

**Verify the build:**

- In the terminal you should see something like: `SUCCESS` and `gcr.io/YOUR_PROJECT_ID/poller`.
- Optional: list images in the registry:

  ```bash
  gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
  ```

  You should see `gcr.io/YOUR_PROJECT_ID/poller`.

**Optional: test the image locally (if you have Docker installed)**

To run the same image on your machine before deploying:

```bash
docker run --rm -p 8080:8080 gcr.io/YOUR_PROJECT_ID/poller
```

Then open `http://localhost:8080/` in a browser; you should get "OK". Press Ctrl+C to stop. This is not required for deployment but helps confirm the image works.

---

#### 6.3 — Deploy the image to Cloud Run

After the image is built and stored in Container Registry, you **deploy** it as a Cloud Run service. That creates (or updates) a service that listens for HTTP requests and runs your container.

**Command to deploy**

Replace `YOUR_PROJECT_ID` with your Project ID again:

```bash
gcloud run deploy poller-service \
  --image gcr.io/YOUR_PROJECT_ID/poller \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --timeout=300 \
  --concurrency=1
```

**What happens when you run it:**

1. Cloud Run takes the image `gcr.io/YOUR_PROJECT_ID/poller`.
2. It creates a **new revision** of the service `poller-service` (or creates the service if it does not exist).
3. It configures the service with the options you passed (region, timeout, concurrency, no public access).
4. It routes 100% of traffic to the new revision.
5. You get a **service URL** (e.g. `https://poller-service-xxxxx-uc.a.run.app`). Only callers that can authenticate (e.g. Cloud Scheduler with the right service account) can call it.

**What each option means:**

| Option | Meaning |
|--------|--------|
| `poller-service` | Name of the Cloud Run service (you can change it, e.g. `my-poller`). |
| `--image gcr.io/...` | The image built in Step 6.2. Must match the tag you used in `gcloud builds submit`. |
| `--platform managed` | Use fully managed Cloud Run (no Kubernetes cluster to manage). |
| `--region us-central1` | Region where the service runs (e.g. `us-central1`, `europe-west1`). |
| `--no-allow-unauthenticated` | Only authenticated callers can invoke the URL. Use this when only Cloud Scheduler (with a service account) should trigger the job. |
| `--timeout=300` | Maximum time one request can run (300 seconds = 5 minutes). Increase if one poll cycle might take longer. |
| `--concurrency=1` | One container instance serves one request at a time, reducing overlapping poll runs. |

**During deploy:** You may be prompted **"Do you want to continue (Y/n)?"** — type `Y` and press Enter.

**Environment for 6.3 (deploy):**

| Requirement | Details |
|-------------|--------|
| **Image** | Must exist: `gcr.io/YOUR_PROJECT_ID/poller` (from 6.2). |
| **Cloud Run API** | Enabled (Step 5). |
| **IAM** | `run.services.create` / `run.services.update` (e.g. "Cloud Run Admin" or Owner). |
| **Region** | Use supported region (e.g. `us-central1`). |

**Possible errors and solutions (Step 6.3):**

| Error | Cause | Solution |
|-------|--------|----------|
| `Image ... not found` | Image not built or wrong tag/project. | Complete 6.2; use exact tag; list: `gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID`. |
| `Permission denied` on deploy | Missing Run or IAM. | Enable Cloud Run API; grant "Cloud Run Admin" or Owner. |
| Service deploys but revision fails / CrashLoopBackOff | App exits or crashes on start. | Check Cloud Run logs; ensure app listens on `PORT` (8080), no missing required env vars, and no import errors. |
| `ResourceExhausted` | Quota (e.g. concurrent revisions). | Delete old revisions in Console or use another region. |

**Verify deployment:**

- The command prints the **Service URL** at the end (see 6.4 below).
- Optional: list services in the region:

  ```bash
  gcloud run services list --region us-central1
  ```

  You should see `poller-service` with status "Serving."

---

#### 6.4 — Get your Cloud Run URL

After a successful deploy, the last lines of output look like:

```text
Service [poller-service] revision has been deployed and is serving 100 percent of traffic.
Service URL: https://poller-service-xxxxx-uc.a.run.app
```

**Copy this URL** — you need it for the Cloud Scheduler job in Step 8. We refer to it as `YOUR_CLOUD_RUN_URL`. The path Scheduler will call is the root, e.g. `https://poller-service-xxxxx-uc.a.run.app/`.

**If you need the URL later:**

```bash
gcloud run services describe poller-service --region us-central1 --format="value(status.url)"
```

**Summary of Step 6:** Build once with `gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/poller`, then deploy with `gcloud run deploy poller-service --image gcr.io/YOUR_PROJECT_ID/poller ...`. Save the Service URL for Step 8.

---

### Step 7 — Let Cloud Scheduler Call Cloud Run (Authentication)

**Environment for Step 7:**

| Requirement | Details |
|-------------|--------|
| **Cloud Run service** | Deployed (Step 6); know its name and region. |
| **IAM** | Your account needs `iam.serviceAccounts.create` (7.1) and `run.services.setIamPolicy` (7.2). |
| **Service account** | Created in 7.1; use exact email in 7.2 and Step 8. |

Cloud Run is deployed with **no public access** (`--no-allow-unauthenticated`). So we must give **Cloud Scheduler** permission to call it. We do that by:

1. Creating a **service account** for Scheduler.
2. Granting that service account the **Cloud Run Invoker** role on your Cloud Run service.

**7.1 — Create a service account**

```bash
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Scheduler Invoker"
```

- **What this does:** Creates an identity (service account) that Scheduler will use when it sends requests to Cloud Run.
- If you see "already exists," you may have created it before; you can use the same one or pick a different name (e.g. `scheduler-invoker-2`).

**7.2 — Grant the Invoker role to that service account**

Replace `YOUR_PROJECT_ID` with your Project ID:

```bash
gcloud run services add-iam-policy-binding poller-service \
  --region us-central1 \
  --member="serviceAccount:scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

- **What this does:** Allows the `scheduler-invoker` service account to invoke (call) the `poller-service` Cloud Run service. Without this, Scheduler’s requests would get "403 Forbidden."

**Possible errors and solutions (Step 7):** See the Quick Start section above (Steps 6–7) for 403, "Service not found," "Service account does not exist," and permission errors — same causes and fixes apply.

---

### Step 8 — Create the Cloud Scheduler Job

**Environment for Step 8:**

| Requirement | Details |
|-------------|--------|
| **Cloud Scheduler API** | Enabled (Step 5). |
| **Cloud Run URL** | From Step 6.4; full URL with `https://` and trailing `/`. |
| **Service account** | Same as Step 7: `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com`. |
| **IAM** | Your account needs `cloudscheduler.jobs.create`. |

This job will send an HTTP GET request to your Cloud Run URL on a schedule (e.g. every minute).

Replace in the command below:

- `YOUR_PROJECT_ID` — your Google Cloud Project ID.
- `YOUR_CLOUD_RUN_URL` — the Cloud Run service URL from Step 6.4 (include the trailing `/` for the root path), e.g. `https://poller-service-xxxxx-uc.a.run.app/`

```bash
gcloud scheduler jobs create http poller-every-minute \
  --location us-central1 \
  --schedule "* * * * *" \
  --uri "YOUR_CLOUD_RUN_URL" \
  --http-method GET \
  --oidc-service-account-email "scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

**What each part means:**

| Part | Meaning |
|------|--------|
| `poller-every-minute` | Name of the Scheduler job (you can change it). |
| `--location us-central1` | Scheduler job lives in this region (often same as Cloud Run). |
| `--schedule "* * * * *"` | Cron expression: every minute (every hour, every day, etc.). |
| `--uri "..."` | The full URL Cloud Scheduler will call (your Cloud Run URL, e.g. `https://...run.app/`). |
| `--http-method GET` | Use GET (matches your Flask `GET /`). |
| `--oidc-service-account-email` | Scheduler uses this service account to authenticate to Cloud Run (OIDC). |

**Possible errors and solutions (Step 8):** See the Quick Start Step 8 table above (job already exists, invalid URI, 403, permission denied, cron syntax).

**Cron reminder:** Cloud Scheduler’s minimum interval is typically **1 minute**. If you need sub-minute polling, you need a different design (e.g. Pub/Sub, Cloud Tasks, or a long-running worker).

**Example with real values:**

```bash
gcloud scheduler jobs create http poller-every-minute \
  --location us-central1 \
  --schedule "* * * * *" \
  --uri "https://poller-service-xxxxx-uc.a.run.app/" \
  --http-method GET \
  --oidc-service-account-email "scheduler-invoker@my-project-123456.iam.gserviceaccount.com"
```

---

### Step 9 — Test End-to-End

**Environment for Step 9:** Job must exist (Step 8); your account needs `cloudscheduler.jobs.run`. Logs require "Logs Viewer" or equivalent.

**9.1 — Run the Scheduler job once (manual trigger)**

This runs the job immediately instead of waiting for the next minute:

```bash
gcloud scheduler jobs run poller-every-minute --location us-central1
```

You should see something like: "Job [poller-every-minute] has been run."

**9.2 — Check that Cloud Run was called**

- **Option A — Logs:** In [Google Cloud Console](https://console.cloud.google.com/) go to **Cloud Run → poller-service → Logs**. You should see a request and log lines from `main.py` (e.g. "Polled X record(s)", "Run finished. Processed X record(s).").
- **Option B — Command line:**

  ```bash
  gcloud run services logs read poller-service --region us-central1 --limit 50
  ```

**9.3 — Inspect the Scheduler job (optional)**

To see job details (schedule, URI, etc.):

```bash
gcloud scheduler jobs describe poller-every-minute --location us-central1
```

If you see recent runs and matching logs in Cloud Run, your end-to-end flow is working.

---

### Step 10 — View Logs Later

**Environment:** Cloud Logging is used automatically by Cloud Run. Your account needs "Logs Viewer" (or Owner) to read logs.

- **Console:** Cloud Run → select `poller-service` → **Logs** (or use **Logging → Logs Explorer** and filter by resource type "Cloud Run Revision" and service name `poller-service`).
- **CLI:**

  ```bash
  gcloud run services logs read poller-service --region us-central1 --limit 100
  ```

In the logs, look for:

- "Polled X record(s)"
- "API send: ..." (or your real API logic)
- "Acknowledged record id=..."
- "Run finished. Processed X record(s)."

---

## Environment Variables and Secrets

You often need configuration (API base URL, keys, etc.) in the container. Use **environment variables** for non-sensitive config and **Secret Manager** for secrets.

### Required environment (this project)

| Variable | Where used | Required? | Notes |
|----------|-------------|-----------|--------|
| `PORT` | `app.py` | No (default 8080) | Cloud Run sets this automatically; app uses `os.environ.get("PORT", 8080)`. |
| Custom (e.g. `API_BASE_URL`) | Your code in `main.py` | Only if your logic needs it | Set via `--set-env-vars` or Secret Manager. |

### Setting environment variables on Cloud Run

**Set plain environment variables:**

```bash
gcloud run services update poller-service \
  --region us-central1 \
  --set-env-vars "API_BASE_URL=https://example.com,ENVIRONMENT=production"
```

**Clear or update:** Re-run with new `--set-env-vars`; to remove all, use `--clear-env-vars` (see `gcloud run services update --help`).

### Secrets (e.g. API keys)

- **Store** the secret in [Secret Manager](https://console.cloud.google.com/security/secret-manager) (create a secret, then note its name).
- **Enable** Secret Manager API if not already: `gcloud services enable secretmanager.googleapis.com`
- **Grant** Cloud Run's service account access to the secret (e.g. "Secret Manager Secret Accessor").
- **Inject** into the service as an env var or mounted file. See [Cloud Run: Using Secret Manager](https://cloud.google.com/run/docs/configuring/services/secrets).

Example (mount as env var):

```bash
gcloud run services update poller-service \
  --region us-central1 \
  --set-secrets="API_KEY=my-secret-name:latest"
```

### Possible errors (environment and secrets)

| Error | Cause | Solution |
|-------|--------|----------|
| App crashes with `KeyError` or missing config | Required env var not set. | Set the variable with `--set-env-vars` or `--set-secrets`. |
| `Permission denied` accessing secret | Run service account cannot read secret. | Grant the Cloud Run service account "Secret Manager Secret Accessor" on the secret. |
| `Secret [name] not found` | Wrong secret name or project. | Create the secret in the same project; use correct name and version (e.g. `my-secret:latest`). |
| Env var not visible in app | Cached revision still serving. | Trigger a new deployment (e.g. `gcloud run services update ... --set-env-vars`) and wait for new revision to serve traffic. |

---

## Common Mistakes to Avoid

| Mistake | Why it’s a problem |
|--------|---------------------|
| Using `while True` in Cloud Run service code | Cloud Run is request-based; the container can be stopped when idle. Use one poll per request. |
| Deploying with `--allow-unauthenticated` when only Scheduler should call the URL | Anyone on the internet could trigger your poll and potentially abuse or overload your backend. |
| Forgetting to grant `roles/run.invoker` to the Scheduler service account | Scheduler’s requests get 403 and your job never runs. |
| Poll cycle longer than Cloud Run timeout | Request is cut off. Increase `--timeout` or process fewer records per run. |
| Non-idempotent processing | The same record might be processed more than once (retries, duplicate triggers). Design your API/DB updates so that processing the same record twice is safe. |

---

## Troubleshooting

Use this section when something fails; each step in the guide also has a **Possible errors and solutions** table for that step.

### Build fails (Step 6.2)

| Check | Action |
|-------|--------|
| **Working directory** | Ensure you are in the project folder that contains `Dockerfile`, `requirements.txt`, `app.py`, `main.py`. Run `ls Dockerfile` (or `dir Dockerfile` on Windows). |
| **requirements.txt** | Check for typos; ensure `flask` and `requests` (or your deps) are valid. Test locally: `pip install -r requirements.txt`. |
| **Dockerfile** | Ensure base image is pullable (e.g. `python:3.11-slim`). If behind a proxy, configure Docker/Cloud Build for it. |
| **Context size** | If upload is very slow or times out, add a `.dockerignore` (e.g. `__pycache__`, `.git`, `*.pyc`). |
| **Reproduce locally** | If you have Docker: `docker build -t test .` to see the same errors. |

### Deploy fails (Step 6.3)

| Check | Action |
|-------|--------|
| **APIs** | Confirm Cloud Run API is enabled (Step 5): `gcloud services list --enabled --filter="name:run.googleapis.com"`. |
| **Project** | Confirm project: `gcloud config get-value project`. Must match the project where you built the image. |
| **Image** | Image must exist: `gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID`. Re-run Step 6.2 if missing. |
| **IAM** | Your account needs Cloud Run Admin (or Owner). In Console: IAM & Admin → check your role. |

### 403 when Scheduler runs

| Check | Action |
|-------|--------|
| **Step 7.2** | Ensure you ran the IAM binding: `gcloud run services add-iam-policy-binding poller-service --region us-central1 --member="serviceAccount:scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.invoker"`. |
| **Service account** | Use the **exact** email: `scheduler-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com` (replace `YOUR_PROJECT_ID`). |
| **Region** | `--region` must match the Cloud Run service region (e.g. `us-central1`). |
| **Console** | Cloud Run → poller-service → **Permissions** → confirm the Scheduler service account has "Cloud Run Invoker." |

### Job created but no logs in Cloud Run

| Check | Action |
|-------|--------|
| **Manual run** | Run the job once: `gcloud scheduler jobs run poller-every-minute --location us-central1`. Wait ~30 seconds, then check logs. |
| **URI** | In the Scheduler job, `--uri` must be the **full** URL: `https://poller-service-xxxxx-uc.a.run.app/` (with `https://` and trailing `/`). |
| **OIDC** | `--oidc-service-account-email` must match the service account that has Invoker on the Cloud Run service. |
| **Logs** | `gcloud run services logs read poller-service --region us-central1 --limit 50`. Or Console → Cloud Run → poller-service → Logs. |

### Container starts then crashes (no successful requests)

| Check | Action |
|-------|--------|
| **Port** | App must listen on `PORT` (Cloud Run sets it; default 8080). This project uses `os.environ.get("PORT", 8080)` in `app.py`. |
| **Dependencies** | Ensure all imports in `app.py` and `main.py` are in `requirements.txt`. |
| **Logs** | Check Cloud Run revision logs for Python tracebacks (import errors, missing env vars, etc.). |

### "Permission denied" or "API not enabled"

| Check | Action |
|-------|--------|
| **APIs** | Enable all three: `run.googleapis.com`, `cloudbuild.googleapis.com`, `cloudscheduler.googleapis.com` (Step 5). |
| **Roles** | Your Google account needs Owner or Editor (or equivalent: Cloud Run Admin, Cloud Build Editor, Cloud Scheduler Admin, etc.) on the project. |
| **Billing** | Project must have a billing account linked. |

---

## Quick Checklist

Before you consider the deployment done, verify:

- [ ] `run_poll()` runs once per request and exits (no infinite loop).
- [ ] You are in the correct project: `gcloud config get-value project`.
- [ ] All three APIs enabled: Cloud Run, Cloud Build, Cloud Scheduler.
- [ ] Image built: `gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/poller` succeeded.
- [ ] Cloud Run service deployed and you saved the service URL.
- [ ] Service account `scheduler-invoker` created.
- [ ] Invoker role granted to that service account on `poller-service`.
- [ ] Cloud Scheduler HTTP job created with correct `--uri` and `--oidc-service-account-email`.
- [ ] Manual run of the job works: `gcloud scheduler jobs run poller-every-minute --location us-central1`.
- [ ] Cloud Run logs show "Polled ..." and "Run finished. Processed ...".

---

## Optional: Cloud Run Jobs

If your workload is **only** batch/polling (no need to serve HTTP to other clients), you can use **Cloud Run Jobs** instead of a **Cloud Run Service**:

- A **Job** runs the container once to completion (no Flask, no HTTP).
- **Cloud Scheduler** can trigger a **Job run** on a schedule.

So: Scheduler → start Job run → container runs `run_poll()` (or equivalent) and exits. No web server needed.

Your current setup (Cloud Run **Service** + Scheduler calling GET /) is a common and valid approach, especially when you want a simple HTTP endpoint to trigger or debug the poll. You can switch to Jobs later if you prefer.

---

*End of guide. If you follow the steps in order and replace every `YOUR_PROJECT_ID` and `YOUR_CLOUD_RUN_URL` with your real values, you should have a working scheduled poller on Google Cloud.*
