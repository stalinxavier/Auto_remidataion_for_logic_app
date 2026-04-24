# Azure Logic App Auto-Remediation System

A LangGraph + FastAPI application that automatically detects, classifies, analyses, and fixes Azure Logic App failures — with full traceability via JSON snapshots at every step.

```
Observer → Classifier → Root Cause Analysis → Fixer
```

---

## Table of Contents

1. [How the Pipeline Works](#how-the-pipeline-works)
2. [Project Structure](#project-structure)
3. [Setup: Step by Step](#setup-step-by-step)
   - [Step 1 — Prerequisites](#step-1--prerequisites)
   - [Step 2 — Clone the Repository](#step-2--clone-the-repository)
   - [Step 3 — Create a Virtual Environment](#step-3--create-a-virtual-environment)
   - [Step 4 — Activate the Virtual Environment](#step-4--activate-the-virtual-environment)
   - [Step 5 — Install Dependencies](#step-5--install-dependencies)
   - [Step 6 — Configure Environment Variables](#step-6--configure-environment-variables)
   - [Step 7 — Start the Server](#step-7--start-the-server)
   - [Step 8 — Verify the Server is Running](#step-8--verify-the-server-is-running)
4. [Running the Application](#running-the-application)
5. [All API Endpoints](#all-api-endpoints)
6. [Output Files](#output-files)
7. [Safety Rules](#safety-rules)
8. [Troubleshooting](#troubleshooting)
9. [Environment Variables Reference](#environment-variables-reference)

---

## How the Pipeline Works

When you call `POST /run`, the following four steps run automatically in sequence:

```
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1 — Observer                                               │
│                                                                  │
│  Authenticates against Azure ARM using your Service Principal.   │
│  Downloads two things in one session:                            │
│    1. The current Logic App workflow definition JSON             │
│    2. The last 50 failed runs with action-level error details    │
│                                                                  │
│  Saves: _temp/observer_output_<timestamp>.json                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │ passes: errors + workflow definition
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2 — Classifier (LLM)                                       │
│                                                                  │
│  Sends each error to the LLM.                                    │
│  Classifies into one of five types:                              │
│    Authentication | Timeout | Connector Failure |                │
│    Payload Issue | Unknown                                       │
│  Assigns severity: Low | Medium | High | Critical                │
│                                                                  │
│  Saves: _temp/classifier_output_<timestamp>.json                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │ passes: classified errors
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3 — Root Cause Analysis (LLM)                              │
│                                                                  │
│  LLM receives error details + compact workflow action summary.   │
│  For each error it identifies:                                   │
│    - The exact workflow action that failed (affected_action)     │
│    - Root cause (specific, not generic)                          │
│    - A concrete fix plan                                         │
│    - Action type: update_workflow | retry | config_change        │
│    - A confidence score (0.0 – 1.0)                              │
│                                                                  │
│  Saves: _temp/rca_output_<timestamp>.json                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │ passes: RCA results
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4 — Fixer                                                  │
│                                                                  │
│  Uses the workflow definition already in state (no extra GET).   │
│                                                                  │
│  For update_workflow:                                            │
│    - LLM returns surgical patches:                               │
│      (action_name + property_path + new_value)                   │
│    - Patches applied programmatically — never rewrites the whole │
│      workflow JSON                                               │
│    - All patches accumulated → single PUT to Azure ARM           │
│                                                                  │
│  For retry:                                                      │
│    - POST to Azure ARM resubmit endpoint                         │
│                                                                  │
│  For config_change:                                              │
│    - Logged for human review — never automated                   │
│                                                                  │
│  Saves: _temp/fixer_output_<timestamp>.json                      │
│         _temp/patched_workflow_<timestamp>.json (if patched)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Auto_remidataion_for_logic_app/
├── _config/
│   └── config.py               ← Loads all env vars via Settings class
├── _llm/
│   ├── factory_llm.py          ← AICoreLLMClient + call_llm_structured()
│   └── models_llm.py           ← Pydantic schemas for all LLM outputs
├── _nodes/
│   ├── observer_node.py        ← Step 1: ARM GET (workflow + failed runs)
│   ├── classifier_node.py      ← Step 2: LLM error classification
│   ├── root_cause_analysis.py  ← Step 3: LLM root cause + fix planning
│   └── fixer_node.py           ← Step 4: LLM patches → PUT to ARM
├── _util/
│   └── file_ops.py             ← save_json() / load_latest_json()
├── _temp/                      ← Auto-written JSON snapshots (git-ignored)
├── graph.py                    ← LangGraph StateGraph builder
├── main.py                     ← FastAPI app with 5 endpoints
├── requirements.txt
├── .env                        ← Your credentials (never commit this)
└── README.md
```

---

## Setup: Step by Step

### Step 1 — Prerequisites

Before starting, confirm you have:

- **Python 3.11 or later**
  Check with: `python --version`
- **An Azure Logic App** that has failed runs in the last 24 hours
- **An Azure Service Principal** with `Contributor` role on the Logic App's resource group
- **A SAP AI Core deployment** (or any OpenAI-compatible LLM endpoint)

If you need to create a Service Principal:

```powershell
az ad sp create-for-rbac --name "logic-app-remediator" --role Contributor `
  --scopes /subscriptions/<subscription-id>/resourceGroups/<resource-group>
```

This command outputs the `appId` (client ID), `password` (client secret), and `tenant` values you will need in Step 6.

---

### Step 2 — Clone the Repository

PowerShell or Command Prompt:

```powershell
cd C:\Users\StalinEdwinPrakash\Documents
git clone <repo-url> Auto_remidataion_for_logic_app
cd Auto_remidataion_for_logic_app
```

---

### Step 3 — Create a Virtual Environment

Run this inside the project folder:

```powershell
python -m venv .venv
```

This creates a `.venv` folder. Your global Python installation is not affected.

If `python` is not found, try:

```powershell
py -3.11 -m venv .venv
```

---

### Step 4 — Activate the Virtual Environment

You must activate the virtual environment **every time you open a new terminal** for this project.

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Command Prompt:**

```cmd
.venv\Scripts\activate.bat
```

When activation succeeds, your prompt will show `(.venv)`:

```
(.venv) PS C:\Users\StalinEdwinPrakash\Documents\Auto_remidataion_for_logic_app>
```

> If PowerShell blocks the activation script, run this once and then try again:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

---

### Step 5 — Install Dependencies

After activating the virtual environment:

```powershell
pip install -r requirements.txt
```

This installs FastAPI, LangGraph, the Azure SDK, Pydantic, and all other required packages.

---

### Step 6 — Configure Environment Variables

Open the `.env` file in the project root and fill in every value:

```env
# ── Azure Service Principal ─────────────────────────────────────
# From: az ad sp create-for-rbac output
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=your-client-secret-here

# ── Azure Resources ─────────────────────────────────────────────
AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_RESOURCE_GROUP=my-resource-group
LOGIC_APP_NAME=my-logic-app-name

# ── Log Analytics (optional) ────────────────────────────────────
LOG_ANALYTICS_WORKSPACE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# ── SAP AI Core (LLM) ───────────────────────────────────────────
AICORE_BASE_URL=https://api.ai.xxx.hana.ondemand.com
AICORE_CLIENT_ID=your-aicore-client-id
AICORE_CLIENT_SECRET=your-aicore-client-secret
AICORE_AUTH_URL=https://your-subaccount.authentication.hana.ondemand.com
LLM_DEPLOYMENT_ID=your-deployment-id
AICORE_RESOURCE_GROUP=default
```

Key notes:

- `LOGIC_APP_NAME` is used automatically when you call `/run` without a request body.
- All five `AZURE_*` values are required for the Observer and Fixer nodes.
- All `AICORE_*` values are required for the Classifier, RCA, and Fixer nodes.
- Do **not** add quotes around values.
- Do **not** commit `.env` to git — it is already in `.gitignore`.

---

### Step 7 — Start the Server

In **Terminal 1**, with the virtual environment active:

```powershell
uvicorn main:app --reload --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> Keep Terminal 1 open while you use the application.
> The `--reload` flag automatically restarts the server when you edit any `.py` file.

---

### Step 8 — Verify the Server is Running

Open **Terminal 2** (a new terminal), activate the virtual environment, then run:

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
curl.exe http://localhost:8000/health
```

**Command Prompt:**

```cmd
.venv\Scripts\activate.bat
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "missing_env_vars": [],
  "logic_app": "my-logic-app-name"
}
```

If `missing_env_vars` lists any names, add those values to `.env`, then press `Ctrl+C` in Terminal 1 and restart the server.

---

## Running the Application

Use **Terminal 2** for all commands below. Terminal 1 must stay running.

### Run the full remediation pipeline

This is the main command. It runs all four steps in order.

**PowerShell:**

```powershell
curl.exe -X POST http://localhost:8000/run
```

**Command Prompt:**

```cmd
curl -X POST http://localhost:8000/run
```

**With a specific Logic App name** (overrides `.env`):

```powershell
curl.exe -X POST http://localhost:8000/run `
  -H "Content-Type: application/json" `
  -d "{\"workflow_name\":\"my-logic-app\"}"
```

```cmd
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d "{\"workflow_name\":\"my-logic-app\"}"
```

What happens after this call:

1. Observer downloads the workflow definition and failed run logs from Azure
2. Classifier sends each error to the LLM and classifies it
3. RCA identifies the root cause and proposes a fix plan for each error
4. Fixer applies patches to the workflow definition and PUTs it back to Azure ARM
5. JSON snapshots of each step are saved to `_temp/`
6. The combined result of all four steps is returned in the API response

---

## All API Endpoints

### `GET /health` — Check configuration

```powershell
curl.exe http://localhost:8000/health
```

Returns which required env vars are set and the configured Logic App name.

---

### `POST /run` — Run the full pipeline

```powershell
# Uses LOGIC_APP_NAME from .env
curl.exe -X POST http://localhost:8000/run

# Override the Logic App name at runtime
curl.exe -X POST http://localhost:8000/run `
  -H "Content-Type: application/json" `
  -d "{\"workflow_name\":\"my-logic-app\"}"
```

Returns the combined JSON output from all four nodes.

---

### `GET /observer` — Fetch logs only (no LLM)

```powershell
curl.exe "http://localhost:8000/observer?workflow_name=my-logic-app"
```

Runs only the Observer node. Useful for:
- Verifying Azure credentials work before running the full pipeline
- Inspecting what failed runs exist without triggering any LLM calls

---

### `GET /workflow/{name}` — Fetch a workflow definition

```powershell
curl.exe http://localhost:8000/workflow/my-logic-app
```

Returns the current workflow definition JSON from Azure ARM.

---

### `PUT /workflow/{name}` — Update a workflow definition manually

```powershell
curl.exe -X PUT http://localhost:8000/workflow/my-logic-app `
  -H "Content-Type: application/json" `
  -d @_temp/patched_workflow_20240422_120000.json
```

The request body must follow this structure:

```json
{
  "definition": {
    "...full workflow JSON here..."
  }
}
```

---

### Interactive API Documentation

When the server is running, open either of these in a browser:

| URL | What it provides |
|-----|-----------------|
| `http://localhost:8000/docs` | Swagger UI — fill in parameters and run endpoints directly from the browser |
| `http://localhost:8000/redoc` | ReDoc — clean, readable reference documentation |

Using `/docs` is the easiest way to test the API without dealing with `curl` formatting.

---

## Output Files

Every pipeline run writes these files to `_temp/`:

| File | Written by | Contents |
|------|-----------|----------|
| `observer_output_<ts>.json` | Observer | Workflow action names + all failed runs with action-level errors |
| `classifier_output_<ts>.json` | Classifier | Each run: error type + severity assigned by LLM |
| `rca_output_<ts>.json` | RCA | Per-run: affected action, root cause, fix plan, confidence score |
| `fixer_output_<ts>.json` | Fixer | Per-run fix result: success / failed / skipped + patches applied |
| `patched_workflow_<ts>.json` | Fixer | Full workflow JSON as it was sent to Azure ARM (only if patches were applied) |

These files are written even if a later step fails, so you can inspect any step independently.

---

## Safety Rules

| Rule | Detail |
|------|--------|
| Confidence gate | Any item with LLM confidence below `0.6` is skipped and flagged for manual review — no action taken |
| Surgical patches | The LLM returns `(action_name, property_path, new_value)` tuples. Patches are applied programmatically, not by rewriting the whole workflow |
| Single PUT | All patches across a pipeline run are accumulated and sent in one PUT call to Azure ARM |
| Structure validation | Before every PUT, the node confirms that no top-level ARM keys were removed by any patch |
| Config changes | Items with `action_type: config_change` are never automated — always logged for human action |
| Patched file | The full patched workflow is saved to `_temp/patched_workflow_<ts>.json` before the PUT so you have a record of exactly what was sent |

---

## Troubleshooting

### `python` is not recognized

Try:

```powershell
py -3.11 -m venv .venv
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn main:app --reload --port 8000
```

---

### PowerShell blocks the activation script

Run this once per PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### `curl` behaves unexpectedly in PowerShell

In PowerShell, `curl` is an alias for `Invoke-WebRequest`, not the real curl binary.

Use one of these instead:

```powershell
# Option 1 — real curl binary
curl.exe http://localhost:8000/health

# Option 2 — PowerShell native
Invoke-RestMethod http://localhost:8000/health
```

---

### Server starts but `/run` fails immediately

1. Call the observer endpoint first to isolate the problem:

```powershell
curl.exe "http://localhost:8000/observer?workflow_name=my-logic-app"
```

- If observer fails → Azure credentials or Logic App name is wrong. Check `.env`.
- If observer succeeds but classifier fails → AI Core credentials are wrong. Check `AICORE_*` values in `.env`.

2. Check the server terminal (Terminal 1) for the full error traceback.

---

### `/health` shows `missing_env_vars`

Open `.env`, add the missing values, then restart the server:

```powershell
# Press Ctrl+C in Terminal 1, then:
uvicorn main:app --reload --port 8000
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes | Azure Active Directory tenant ID |
| `AZURE_CLIENT_ID` | Yes | Service principal application (client) ID |
| `AZURE_CLIENT_SECRET` | Yes | Service principal client secret |
| `AZURE_SUBSCRIPTION_ID` | Yes | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Yes | Resource group that contains the Logic App |
| `LOGIC_APP_NAME` | Recommended | Default Logic App name used by `/run` and `/observer` |
| `LOG_ANALYTICS_WORKSPACE_ID` | No | Log Analytics workspace ID (optional query source) |
| `AICORE_BASE_URL` | Yes (LLM steps) | SAP AI Core API base URL |
| `AICORE_CLIENT_ID` | Yes (LLM steps) | AI Core OAuth client ID |
| `AICORE_CLIENT_SECRET` | Yes (LLM steps) | AI Core OAuth client secret |
| `AICORE_AUTH_URL` | Yes (LLM steps) | AI Core OAuth token endpoint |
| `LLM_DEPLOYMENT_ID` | Yes (LLM steps) | Deployed model ID in AI Core |
| `AICORE_RESOURCE_GROUP` | No | AI Core resource group (default: `default`) |

---

## Quick Start (Shortest Version)

If you have already set up `.env`, this is the full sequence from a fresh terminal:

**Terminal 1 — server:**

```powershell
cd C:\Users\StalinEdwinPrakash\Documents\Auto_remidataion_for_logic_app
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

**Terminal 2 — test:**

```powershell
cd C:\Users\StalinEdwinPrakash\Documents\Auto_remidataion_for_logic_app
.\.venv\Scripts\Activate.ps1
curl.exe http://localhost:8000/health
curl.exe -X POST http://localhost:8000/run
```
