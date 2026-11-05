from __future__ import annotations
import json
from pydantic import BaseModel
from .agent_tools import run_tool
from .audit import record
from .auth import require_permission
from .database import execute,query
from .workflow_templates import TEMPLATES

class WorkflowConfig(BaseModel):
    trigger:str; data_source:str; condition:str; action:str; approval_required:bool=False; parameters:dict={}

ALLOWED={"trigger":{"manual","daily","weekly"},"data_source":{"sales_database","crm_connector"},"condition":{"all","overdue","missing_data","expiring_quotation"},"action":{"report","ai_summary","follow_up_task"}}
def validate_config(config:dict)->WorkflowConfig:
    model=WorkflowConfig.model_validate(config)
    for key,valid in ALLOWED.items():
        if getattr(model,key) not in valid:raise ValueError(f"Unsupported {key}")
    if model.action=="follow_up_task" and not model.approval_required:raise ValueError("CRM-changing follow-up tasks require approval")
    return model

def save_workflow(user:dict,name:str,template_key:str,config:dict,state="draft")->int:
    require_permission(user,"build_workflow"); valid=validate_config(config)
    if template_key not in TEMPLATES:raise ValueError("Unknown template")
    wid=execute("INSERT INTO workflows(name,template_key,config_json,state,created_by) VALUES(?,?,?,?,?)",(name,template_key,valid.model_dump_json(),state,user["username"]))
    execute("INSERT INTO workflow_versions(workflow_id,version,config_json,created_by) VALUES(?,?,?,?)",(wid,1,valid.model_dump_json(),user["username"])); record(user["username"],"workflow_saved","workflow",str(wid),{"state":state}); return wid

def set_state(user:dict,workflow_id:int,state:str):
    if state not in {"draft","tested","active","paused","archived"}:raise ValueError("Invalid workflow state")
    if state=="active":require_permission(user,"activate_workflow")
    execute("UPDATE workflows SET state=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(state,workflow_id)); record(user["username"],"workflow_state_changed","workflow",str(workflow_id),{"state":state})

def preview(config:dict):
    c=validate_config(config)
    mapping={"overdue":("find_overdue_opportunities",{"limit":int(c.parameters.get("limit",20))}),"missing_data":("detect_missing_crm_data",{"limit":int(c.parameters.get("limit",20))}),"expiring_quotation":("find_expiring_quotations",{"days":int(c.parameters.get("days",30))}),"all":("retrieve_sales_kpis",{})}
    tool,args=mapping[c.condition]; return run_tool(tool,args)

def run(user:dict,workflow_id:int,test_mode=True):
    rows=query("SELECT * FROM workflows WHERE id=?",(workflow_id,));
    if not rows:raise ValueError("Workflow not found")
    row=rows[0]; cfg=json.loads(row["config_json"]); run_id=execute("INSERT INTO workflow_runs(workflow_id,status,test_mode) VALUES(?,?,?)",(workflow_id,"running",int(test_mode)))
    try:
        result=preview(cfg)
        if cfg["action"]=="follow_up_task" and not test_mode:raise PermissionError("Use the approved RPA path for CRM-changing actions")
        execute("UPDATE workflow_runs SET status='succeeded',result_json=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",(json.dumps(result,default=str),run_id)); set_state(user,workflow_id,"tested" if test_mode else row["state"]); return {"run_id":run_id,"status":"succeeded","result":result}
    except Exception as exc:
        execute("UPDATE workflow_runs SET status='failed',error=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",(str(exc),run_id)); record(user["username"],"workflow_failed","workflow",str(workflow_id),{"error":str(exc)},False); raise

