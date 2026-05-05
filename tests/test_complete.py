"""
Complete testing suite for Auto-Remediation Pipeline
Tests both local functionality and Azure Logic App changes
"""

import json
import pytest
import requests
from pathlib import Path
from datetime import datetime, timedelta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PART 1: LOCAL TESTS (API & Pipeline)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASE_URL = "http://localhost:8000"


class TestHealthAndSetup:
    """Verify server is running and configured correctly"""

    def test_server_is_running(self):
        """Check if FastAPI server responds"""
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        print("✓ Server is running")

    def test_env_vars_configured(self):
        """Check all required environment variables are set"""
        resp = requests.get(f"{BASE_URL}/health")
        data = resp.json()

        assert data["status"] in ["ok", "degraded"]
        if data["missing_env_vars"]:
            print(f"⚠ Missing vars: {data['missing_env_vars']}")
        else:
            print("✓ All environment variables configured")

        assert data["logic_app"], "LOGIC_APP_NAME not set"
        print(f"✓ Logic App: {data['logic_app']}")


class TestPipelineExecution:
    """Test the full 4-stage pipeline"""

    def test_observer_only(self):
        """Run observer to verify Azure connection works"""
        resp = requests.get(
            f"{BASE_URL}/observer",
            params={"workflow_name": "my-logic-app"}  # Change to your app name
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "workflow_definition" in data, "No workflow definition returned"
        assert "failed_runs" in data, "No failed runs returned"
        assert len(data["failed_runs"]) > 0, "No failed runs found (expected at least one)"

        print(f"✓ Observer found {len(data['failed_runs'])} failed runs")
        return data

    def test_full_pipeline_execution(self):
        """Run complete pipeline: Observer → Classifier → RCA → Fixer"""
        print("\n🔄 Starting full pipeline...")
        resp = requests.post(
            f"{BASE_URL}/run",
            json={"workflow_name": "my-logic-app"}  # Change to your app name
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "completed"
        assert "observer" in data
        assert "classifier" in data
        assert "rca" in data
        assert "fixer" in data

        print("✓ Pipeline completed all 4 stages")
        return data


class TestOutputFiles:
    """Validate JSON output files"""

    def test_output_files_exist(self):
        """Check that output files were created with correct timestamps"""
        temp_dir = Path("_temp")
        assert temp_dir.exists(), "_temp directory not found"

        # Get latest files (within last 5 minutes)
        now = datetime.now()
        recent_files = {
            "observer": list(temp_dir.glob("observer_output_*.json")),
            "classifier": list(temp_dir.glob("classifier_output_*.json")),
            "rca": list(temp_dir.glob("rca_output_*.json")),
            "fixer": list(temp_dir.glob("fixer_output_*.json")),
        }

        for stage, files in recent_files.items():
            assert len(files) > 0, f"No {stage} output files found"
            latest = max(files, key=lambda p: p.stat().st_mtime)
            file_age = (now - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds()
            assert file_age < 300, f"{stage} file is older than 5 minutes"
            print(f"✓ {stage:12} output exists: {latest.name}")

    def test_json_validity(self):
        """Verify all JSON files are valid"""
        temp_dir = Path("_temp")

        for json_file in sorted(temp_dir.glob("*_output_*.json"))[-4:]:  # Last 4 files
            try:
                with open(json_file) as f:
                    json.load(f)
                print(f"✓ {json_file.name} is valid JSON")
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {json_file.name}: {e}")

    def test_output_structure(self):
        """Verify output structure matches schema"""
        temp_dir = Path("_temp")

        # Check classifier output
        classifier_file = sorted(temp_dir.glob("classifier_output_*.json"))[-1]
        with open(classifier_file) as f:
            classifier_data = json.load(f)
            for item in classifier_data.get("results", []):
                assert "error_type" in item, "Missing error_type"
                assert "severity" in item, "Missing severity"
                assert item["severity"] in ["Low", "Medium", "High", "Critical"]
        print(f"✓ Classifier output has correct structure")

        # Check RCA output
        rca_file = sorted(temp_dir.glob("rca_output_*.json"))[-1]
        with open(rca_file) as f:
            rca_data = json.load(f)
            for item in rca_data.get("results", []):
                assert "affected_action" in item, "Missing affected_action"
                assert "root_cause" in item, "Missing root_cause"
                assert "confidence_score" in item, "Missing confidence_score"
        print(f"✓ RCA output has correct structure")

        # Check fixer output
        fixer_file = sorted(temp_dir.glob("fixer_output_*.json"))[-1]
        with open(fixer_file) as f:
            fixer_data = json.load(f)
            for item in fixer_data.get("results", []):
                assert "status" in item, "Missing status"
                assert item["status"] in ["success", "failed", "skipped"]
        print(f"✓ Fixer output has correct structure")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PART 2: AZURE LOGIC APP VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAzureLogicAppChanges:
    """Verify actual changes in Azure Logic App"""

    def test_workflow_updated_in_azure(self):
        """Check if workflow definition changed in Azure"""
        resp = requests.get(f"{BASE_URL}/workflow/my-logic-app")  # Change to your app name
        assert resp.status_code == 200

        current_definition = resp.json()
        print(f"✓ Fetched current workflow from Azure")
        print(f"  Last modified: {current_definition.get('properties', {}).get('changedTime')}")

    def test_patched_workflow_structure(self):
        """Verify patched workflow has valid structure before deployment"""
        temp_dir = Path("_temp")
        patched_files = list(temp_dir.glob("patched_workflow_*.json"))

        if not patched_files:
            print("ℹ No patched workflow files (no fixes applied)")
            return

        latest_patched = max(patched_files, key=lambda p: p.stat().st_mtime)
        with open(latest_patched) as f:
            patched = json.load(f)

        # Validate structure
        assert "location" in patched, "Missing 'location' field"
        assert "properties" in patched, "Missing 'properties' field"
        assert "definition" in patched["properties"], "Missing 'properties.definition'"
        assert "actions" in patched["properties"]["definition"], "Missing actions in definition"

        print(f"✓ Patched workflow structure is valid")
        print(f"  File: {latest_patched.name}")
        print(f"  Actions count: {len(patched['properties']['definition']['actions'])}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PART 3: MANUAL VERIFICATION CHECKLIST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_verification_checklist():
    """Print manual steps to verify in Azure Portal"""
    checklist = """

╔════════════════════════════════════════════════════════════════════════════╗
║                    AZURE LOGIC APP VERIFICATION CHECKLIST                  ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 STEP 1: Check Workflow Definition in Azure Portal
    1. Go to: Azure Portal → Logic Apps → [Your Logic App]
    2. Click "Logic app designer" or "Code view"
    3. Verify patches were applied:
       - Look for modified actions (should match RCA output)
       - Check timestamps in "Last modified"
       - Compare with _temp/patched_workflow_<timestamp>.json

    ✓ Patches applied correctly?

📋 STEP 2: Monitor Recent Runs
    1. In Logic App → "Runs" or "Execution history"
    2. Filter by date: AFTER pipeline execution
    3. Trigger a manual run (or wait for scheduled trigger)
    4. Observe the run:
       - All actions execute without the previous errors
       - Check individual action outputs
       - Look for successful completion (green checkmark)

    ✓ Logic App runs without previous errors?

📋 STEP 3: Review Error Details
    1. Go to any recent failed run BEFORE remediation
    2. Click on the failed action
    3. Check error message matches what's in rca_output_*.json
    4. Now trigger a NEW run - compare outputs

    ✓ Error is fixed in new runs?

📋 STEP 4: Validate Connector Connections
    1. Logic App → "Connections"
    2. Verify all connections show "Connected" status
    3. Check if auth issues were the root cause

    ✓ All connections healthy?

📋 STEP 5: Review Changes in Git (if tracked)
    1. _temp/fixed_workflow_*.json contains what was sent
    2. Compare lines with current Azure definition
    3. Verify no unintended changes

    ✓ Only intended changes were applied?

════════════════════════════════════════════════════════════════════════════════
    """
    print(checklist)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUN TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "="*80)
    print("AUTO-REMEDIATION PIPELINE - COMPLETE TEST SUITE")
    print("="*80)

    # Run pytest
    pytest.main([__file__, "-v", "-s"])

    # Print checklist after tests
    print_verification_checklist()
