import json
import pytest
from fastapi.testclient import TestClient

def test_database_relationships_and_kpis():
    from core.database import query
    from core.kpis import dashboard_metrics,regional_performance
    orphan=query("SELECT COUNT(*) n FROM sales_opportunities o LEFT JOIN customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL")[0]["n"]
    assert orphan==0
    metrics=dashboard_metrics("Last 12 Months")
    assert metrics["pipeline_value"]>0
    assert 0<=metrics["weighted_pipeline"]<=metrics["pipeline_value"]
    assert not regional_performance().empty

def test_allowlisted_tool_validation():
    from core.agent_tools import run_tool
    with pytest.raises(ValueError):run_tool("arbitrary_sql",{})
    with pytest.raises(Exception):run_tool("find_overdue_opportunities",{"limit":1000})

def test_gemini_errors_are_actionable_without_exposing_key():
    from core.gemini_agent import _safe_error
    message=_safe_error(Exception("403: Your API key was reported as leaked. secret-value"))
    assert "reported as leaked" in message
    assert "secret-value" not in message

def test_requirements_to_workflow_conversion():
    from core.requirements import deterministic_spec,to_workflow
    spec=deterministic_spec("Every Monday identify overdue opportunities without recent follow-up and prepare follow-up tasks.")
    workflow=to_workflow(spec)
    assert workflow=={"trigger":"weekly","data_source":"sales_database","condition":"overdue","action":"follow_up_task","approval_required":True,"parameters":{"limit":20}}

def test_workflow_execution_and_permissions(users):
    from core.workflow_engine import save_workflow,run,set_state
    cfg={"trigger":"manual","data_source":"sales_database","condition":"overdue","action":"report","approval_required":False,"parameters":{"limit":5}}
    wid=save_workflow(users["builder"],"Test workflow","data_quality",cfg)
    assert run(users["builder"],wid,True)["status"]=="succeeded"
    with pytest.raises(PermissionError):set_state(users["builder"],wid,"active")
    set_state(users["manager"],wid,"active")

def test_approval_exact_payload_and_crm_persistence(users):
    from core.approvals import approval_match,request_approval,review,assert_approved
    from legacy_crm.app import app
    oid="OPP-000001";payload={"subject":"Approved follow-up","due_date":"2026-12-01"}
    aid=request_approval(users["builder"],"create_follow_up",oid,payload)
    with pytest.raises(PermissionError):review(users["builder"],aid,"approved")
    review(users["manager"],aid,"approved")
    assert_approved(aid,"create_follow_up",oid,payload)
    assert approval_match(aid,"create_follow_up",oid,payload)["valid"]
    assert not approval_match(aid,"create_follow_up",oid,{**payload,"subject":"Modified"})["valid"]
    with pytest.raises(PermissionError):assert_approved(aid,"create_follow_up",oid,{**payload,"subject":"Modified"})
    client=TestClient(app);response=client.post(f"/api/opportunities/{oid}/follow-ups",json={**payload,"approval_id":aid})
    assert response.status_code==200 and response.json()["persisted"]
    assert any(x["subject"]==payload["subject"] for x in client.get(f"/api/opportunities/{oid}").json()["follow_up_tasks"])

def test_audit_redacts_secrets():
    from core.audit import record,recent
    record("tester","secret_test","test",None,{"api_key":"do-not-log","safe":"ok"})
    details=json.loads(recent(1)[0]["details_json"])
    assert details=={"api_key":"[REDACTED]","safe":"ok"}

