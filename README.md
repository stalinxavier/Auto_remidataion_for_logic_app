# Azure Logic App Auto-Remediation System

LangGraph-based pipeline that automatically detects, classifies, analyses, and fixes Azure Logic App failures.

```
Observer → Classifier → Root Cause Analysis → Fixer
```

---

## Folder Structure

```
├── _config/
│   └── config.py              # Env-var loader (Settings class)
├── _llm/
│   ├── factory_llm.py         # LLM client + structured output helper
│   └── models_llm.py          # Pydantic schemas for all LLM responses
├── _nodes/
│   ├── observer_node.py       # Step 1 — fetch failed Logic App runs
│   ├── classifier_node.py     # Step 2 — LLM classifies each error
│   ├── root_cause_analysis.py # Step 3 — LLM identifies root cause + fix plan
│   └── fixer_node.py          # Step 4 — applies fixes via ARM API
├── _util/
│   └── file_ops.py            # save_json / load_latest_json helpers
├── _temp/                     # Auto-generated node output JSON files
├── graph.py                   # LangGraph StateGraph builder
├── main.py                    # FastAPI app + all endpoints
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd Auto_remidataion_for_logic_app
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual Azure and AI Core credentials
```

### 4. Start the API server

```bash
uvicorn main:app --reload --port 8000
```

---

## API Endpoints & Commands

### Health Check

```bash
curl http://localhost:8000/health
```

Verifies all required env vars are set and returns the configured Logic App name.

---

### Run Full Pipeline (Observer → Classifier → RCA → Fixer)

```bash
# Uses LOGIC_APP_NAME from .env
curl -X POST http://localhost:8000/run

# Override workflow name at runtime
curl -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"workflow_name": "my-logic-app"}'
```

Returns the combined output of all four nodes. Each node also saves its JSON to `_temp/`.

---

### Run Observer Only (Fetch Failed Logs)

```bash
curl "http://localhost:8000/observer?workflow_name=my-logic-app"
```

Returns raw failed run data without running the LLM nodes.

---

### Get Workflow Definition

```bash
curl http://localhost:8000/workflow/my-logic-app
```

Fetches the current workflow JSON definition from Azure ARM.

---

### Update Workflow Definition

```bash
curl -X PUT http://localhost:8000/workflow/my-logic-app \
     -H "Content-Type: application/json" \
     -d @updated_definition.json
```

Pushes an updated workflow definition to Azure ARM.

---

## Pipeline Node Details

| Node | Input | Output | Saved to |
|------|-------|--------|----------|
| Observer | — | `observer_output` | `_temp/observer_output_<ts>.json` |
| Classifier | `observer_output` | `classifier_output` | `_temp/classifier_output_<ts>.json` |
| RCA | `classifier_output` | `rca_output` | `_temp/rca_output_<ts>.json` |
| Fixer | `rca_output` | `fixer_output` | `_temp/fixer_output_<ts>.json` |

### Error Categories (Classifier)

| Category | Description |
|----------|-------------|
| Authentication | Expired tokens, missing credentials |
| Timeout | HTTP/connector timeout exceeded |
| Connector Failure | API connector returned an error |
| Payload Issue | Malformed request/response body |
| Unknown | Unclassifiable error |

### Fix Actions (Fixer)

| Action | Behaviour |
|--------|-----------|
| `retry` | Resubmits the failed run via ARM API |
| `update_workflow` | Patches the workflow JSON definition and PUTs it back |
| `config_change` | Logs the required change for human review (not automated) |

> **Safety:** Items with LLM confidence < 0.6 are skipped and flagged for manual review. The fixer validates that no top-level definition keys are removed before PUT.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes | Azure AD tenant |
| `AZURE_CLIENT_ID` | Yes | Service principal app ID |
| `AZURE_CLIENT_SECRET` | Yes | Service principal secret |
| `AZURE_SUBSCRIPTION_ID` | Yes | Target subscription |
| `AZURE_RESOURCE_GROUP` | Yes | Resource group containing Logic App |
| `LOGIC_APP_NAME` | Yes | Logic App workflow name |
| `LOG_ANALYTICS_WORKSPACE_ID` | No | Workspace for log queries |
| `AICORE_BASE_URL` | Yes | SAP AI Core API base URL |
| `AICORE_CLIENT_ID` | Yes | AI Core OAuth client ID |
| `AICORE_CLIENT_SECRET` | Yes | AI Core OAuth client secret |
| `AICORE_AUTH_URL` | Yes | AI Core OAuth token URL |
| `LLM_DEPLOYMENT_ID` | Yes | Deployed model ID in AI Core |
| `AICORE_RESOURCE_GROUP` | No | AI Core resource group (default: `default`) |

---

## Interactive API Docs

Once the server is running:

```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```
