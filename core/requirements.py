from __future__ import annotations
import json,re
from .database import execute

def deterministic_spec(text:str)->dict:
    if len(text.strip())<20:raise ValueError("Please describe the objective, timing, condition, and expected action.")
    lower=text.lower(); weekly="monday" in lower or "weekly" in lower; follow="follow" in lower; overdue="overdue" in lower or "not been contacted" in lower
    return {"business_objective":text.strip(),"required_data":["sales_opportunities","sales_activities","sales_representatives"],"trigger":"weekly" if weekly else "manual","conditions":["opportunity is overdue","no recent follow-up activity"] if overdue else ["user-defined filter requires review"],"actions":["prepare follow-up tasks"] if follow else ["generate report"],"approval_requirements":"Sales Manager approval" if follow else "None","expected_outcome":"Evidence-based actions assigned to responsible representatives","success_criteria":["All selected records include source opportunity IDs","No CRM change occurs without exact-payload approval"],"clarification_questions":[] if (weekly or "daily" in lower or "manual" in lower) else ["When should this process run?"]}

def to_workflow(spec:dict)->dict:
    follow=any("follow-up" in x for x in spec.get("actions",[])); overdue=any("overdue" in x for x in spec.get("conditions",[]))
    return {"trigger":spec.get("trigger","manual"),"data_source":"sales_database","condition":"overdue" if overdue else "all","action":"follow_up_task" if follow else "report","approval_required":follow,"parameters":{"limit":20}}

def save_spec(user:dict,title:str,spec:dict,status="draft")->int:
    return execute("INSERT INTO requirement_specs(title,specification_json,status,created_by) VALUES(?,?,?,?)",(title,json.dumps(spec),status,user["username"]))
