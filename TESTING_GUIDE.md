# Testing Your Auto-Remediation Pipeline: Complete Guide

## 🚀 Quick Start Testing (5 minutes)

### **Terminal 1 — Start Server**
```powershell
cd C:\Users\StalinEdwinPrakash\Documents\Auto_remidataion_for_logic_app
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

Expected:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

### **Terminal 2 — Run Tests**
```powershell
cd C:\Users\StalinEdwinPrakash\Documents\Auto_remidataion_for_logic_app
.\.venv\Scripts\Activate.ps1
pytest tests/test_complete.py -v -s
```

---

## 📊 Testing Flow (What Gets Tested)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣  HEALTH CHECK                                                │
│    curl.exe http://localhost:8000/health                       │
│    ✓ All env vars set? ✓ Logic App name correct?               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣  OBSERVER NODE (Azure Connection)                            │
│    curl.exe http://localhost:8000/observer?workflow_name=...   │
│    ✓ Connects to Azure? ✓ Fetches failed runs?                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣  FULL PIPELINE (All 4 Nodes)                                 │
│    curl.exe -X POST http://localhost:8000/run                  │
│    ✓ Classifier works? ✓ RCA works? ✓ Fixer works?             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4️⃣  OUTPUT VALIDATION                                            │
│    Check _temp/ folder for JSON files                          │
│    ✓ Valid JSON? ✓ Correct structure?                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5️⃣  AZURE LOGIC APP VERIFICATION                               │
│    Check changes in Azure Portal & test execution             │
│    ✓ Patches applied? ✓ Errors fixed?                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Manual API Testing Commands

### **1. Check Configuration**
```powershell
curl.exe http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "missing_env_vars": [],
  "logic_app": "my-logic-app"
}
```

---

### **2. Test Azure Connection (Observer Only)**
```powershell
curl.exe "http://localhost:8000/observer?workflow_name=my-logic-app"
```

Look for:
- ✓ `workflow_definition` field
- ✓ `failed_runs` array with errors
- ✓ Error details for each failed run

---

### **3. Run Full Pipeline**
```powershell
curl.exe -X POST http://localhost:8000/run `
  -H "Content-Type: application/json" `
  -d "{`"workflow_name`":`"my-logic-app`"}"

curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d "{\"workflow_name\": \"RUNTIME_ERRORS\"}"  
```

Check response contains:
- ✓ `observer` - workflow + errors
- ✓ `classifier` - error types & severity
- ✓ `rca` - root causes & fixes
- ✓ `fixer` - patches applied

---

### **4. Check Output Files**
```powershell
ls -la _temp/*_output_*.json | tail -4
```

You should see (in order of execution):
1. `observer_output_<timestamp>.json` - 1-2 KB
2. `classifier_output_<timestamp>.json` - 2-5 KB
3. `rca_output_<timestamp>.json` - 3-8 KB
4. `fixer_output_<timestamp>.json` - 2-5 KB
5. `patched_workflow_<timestamp>.json` - 10-50 KB (if patches applied)

---

## 🔍 Inspect JSON Outputs

### **View Latest Classifier Output**
```powershell
Get-Content (ls _temp/classifier_output_*.json | tail -1) | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Look for:
```json
{
  "results": [
    {
      "run_id": "...",
      "error_type": "Authentication|Timeout|Connector Failure|Payload Issue|Unknown",
      "severity": "Low|Medium|High|Critical",
      "error_message": "..."
    }
  ]
}
```

---

### **View Latest RCA Output**
```powershell
Get-Content (ls _temp/rca_output_*.json | tail -1) | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Look for:
```json
{
  "results": [
    {
      "run_id": "...",
      "affected_action": "action_name",
      "root_cause": "specific description",
      "fix_plan": "what will be fixed",
      "action_type": "update_workflow|retry|config_change",
      "confidence_score": 0.85
    }
  ]
}
```

---

### **View Latest Fixer Output**
```powershell
Get-Content (ls _temp/fixer_output_*.json | tail -1) | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Look for:
```json
{
  "results": [
    {
      "run_id": "...",
      "status": "success|failed|skipped",
      "patches_applied": [
        {
          "action": "action_name",
          "property": "$.inputs.authentication",
          "old_value": "Basic",
          "new_value": "OAuth"
        }
      ]
    }
  ]
}
```

---

## ✅ Azure Logic App Verification

### **Step 1: Compare Workflow Definitions**

**Before fix:**
```powershell
curl.exe http://localhost:8000/workflow/my-logic-app | ConvertFrom-Json | ConvertTo-Json -Depth 10 > before.json
```

**After fix (in Azure Portal):**
- Go to: **Logic Apps** → **Your App** → **Logic app designer**
- Look for green checkmarks (✓) on all actions
- Check **Code view** for changes in authentication/retry logic
- Compare with `_temp/patched_workflow_<timestamp>.json`

---

### **Step 2: Test the Logic App**

1. **Manual Trigger:**
   - Click "Run trigger" or "Run" in Azure Portal
   - Watch it execute in real-time

2. **Monitor Execution:**
   - Check each action's outputs (click each action)
   - Verify no red error indicators
   - Compare with previous failed runs

3. **Check Logs:**
   - Go to **Monitoring** → **Runs**
   - Filter by status: "Succeeded"
   - Verify recent runs all show green (✓)

---

### **Step 3: Validate Fixes**

| Check | How | Expected |
|-------|-----|----------|
| **Auth Fixed** | Check connector authentication | "Connected" status (green) |
| **Timeouts Fixed** | Increase timeout in retry policies | Check Run History → No timeout errors |
| **Payload Fixed** | Review action inputs/outputs | Valid JSON, correct field types |
| **Connector Fixed** | Test individual connector | No 40x or 50x errors |

---

## 🐛 Debugging Issues

### **Issue: All tests pass but Azure says workflow unchanged**

**Check:**
```powershell
# Compare timestamps
ls _temp/patched_workflow_*.json | select Name, LastWriteTime
```

**Solution:**
- Manually push the patched workflow:
  ```powershell
  curl.exe -X PUT "http://localhost:8000/update-workflow?workflow_name=my-logic-app"
  ```

---

### **Issue: Fixer output shows "skipped"**

**Check confidence score:**
```powershell
Get-Content (ls _temp/rca_output_*.json | tail -1) | ConvertFrom-Json | % {$_.results | ? {$_.confidence_score -lt 0.6}}
```

**Action:**
- Items with confidence < 0.6 are skipped for safety
- Review in Azure Portal and apply manually

---

### **Issue: Tests fail on "No failed runs found"**

**Reason:** Logic App hasn't had any recent failures

**Solution:**
1. Intentionally break the Logic App (bad auth, invalid URL)
2. Trigger a few failed runs
3. Wait 2-3 minutes for them to appear
4. Run tests again

---

## 📈 Success Criteria: "Application Working Perfectly"

✅ **All tests pass:**
```
test_health_check PASSED
test_observer_fetches_workflow PASSED
test_full_pipeline_execution PASSED
test_output_files_exist PASSED
test_json_validity PASSED
test_output_structure PASSED
```

✅ **Azure changes verified:**
- Workflow definition updated
- No errors in recent runs
- Actions execute successfully
- Patches match what was applied

✅ **Performance acceptable:**
- Full pipeline < 60 seconds
- Observer < 10 seconds
- No timeouts

✅ **Safety checks passed:**
- No top-level ARM properties deleted
- All confidence scores reviewed
- Patches applied only to intended actions

---

## 🚀 Production Testing Workflow

```
1. Deploy → test_complete.py passes ✓
2. Run pipeline → Check _temp/ folder ✓
3. Validate Azure → Manual verification checklist ✓
4. Monitor runs → 24 hours, 0 new errors ✓
5. Production ready ✅
```

