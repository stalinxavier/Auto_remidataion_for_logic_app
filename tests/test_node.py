import pytest
from _nodes.observer_node import run_observer
from _nodes.classifier_node import run_classifier
from _nodes.root_cause_analysis import run_rca
from _nodes.fixer_node import run_fixer

def test_observer_fetches_workflow():
    """Verify observer returns valid workflow + error logs"""
    result = run_observer(workflow_name="test-logic-app")
    assert "workflow_definition" in result
    assert "failed_runs" in result

def test_classifier_assigns_severity():
    """Check classifier categorizes errors correctly"""
    test_errors = [{"message": "timeout"}]
    result = run_classifier(test_errors)
    assert all("severity" in err for err in result)
    assert all("error_type" in err for err in result)