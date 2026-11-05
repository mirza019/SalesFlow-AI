from __future__ import annotations
import json
from .database import execute, query

SENSITIVE_KEYS={"password","secret","token","api_key"}
def _redact(value):
    if isinstance(value,dict):return {k:("[REDACTED]" if k.lower() in SENSITIVE_KEYS else _redact(v)) for k,v in value.items()}
    if isinstance(value,list):return [_redact(x) for x in value]
    return value

def record(actor:str,event_type:str,target_type:str,target_id:str|None,details:dict,success:bool=True)->int:
    return execute("INSERT INTO audit_log(actor,event_type,target_type,target_id,details_json,success) VALUES(?,?,?,?,?,?)",(actor,event_type,target_type,target_id,json.dumps(_redact(details),default=str),int(success)))

def recent(limit=100):return query("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",(limit,))

