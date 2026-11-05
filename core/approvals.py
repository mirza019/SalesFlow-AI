from __future__ import annotations
import hashlib,json
from .auth import require_permission
from .audit import record
from .database import execute,query

def payload_hash(payload:dict)->str:return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def request_approval(user:dict,action_type:str,target_id:str,payload:dict)->int:
    require_permission(user,"request_change"); digest=payload_hash(payload)
    approval_id=execute("INSERT INTO approvals(action_type,target_id,payload_json,payload_hash,requested_by) VALUES(?,?,?,?,?)",(action_type,target_id,json.dumps(payload,sort_keys=True),digest,user["username"]))
    record(user["username"],"approval_requested",action_type,str(approval_id),{"target_id":target_id,"payload_hash":digest}); return approval_id

def review(user:dict,approval_id:int,decision:str)->None:
    require_permission(user,"approve_change")
    if decision not in {"approved","rejected"}:raise ValueError("Decision must be approved or rejected")
    row=query("SELECT * FROM approvals WHERE id=?",(approval_id,))
    if not row or row[0]["status"]!="pending":raise ValueError("Approval is not pending")
    if row[0]["requested_by"]==user["username"]:raise PermissionError("Requester cannot approve their own action")
    execute("UPDATE approvals SET status=?,reviewed_by=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?",(decision,user["username"],approval_id)); record(user["username"],f"approval_{decision}",row[0]["action_type"],str(approval_id),{"target_id":row[0]["target_id"]})

def assert_approved(approval_id:int,action_type:str,target_id:str,payload:dict)->None:
    rows=query("SELECT * FROM approvals WHERE id=?",(approval_id,))
    if not rows:raise PermissionError("Approval not found")
    row=rows[0]
    if row["status"]!="approved" or row["action_type"]!=action_type or row["target_id"]!=target_id or row["payload_hash"]!=payload_hash(payload):raise PermissionError("Approval does not match this exact action and payload")

def approval_match(approval_id:int,action_type:str,target_id:str,payload:dict)->dict:
    rows=query("SELECT id,action_type,target_id,payload_json,payload_hash,status,requested_by,reviewed_by,requested_at,reviewed_at FROM approvals WHERE id=?",(approval_id,))
    if not rows:return {"valid":False,"reason":"Approval ID was not found.","approval":None}
    row=rows[0]
    if row["status"]!="approved":return {"valid":False,"reason":f"Approval is {row['status']}; it must be approved by a different authorized user.","approval":row}
    if row["action_type"]!=action_type:return {"valid":False,"reason":f"Approval covers {row['action_type']}, not {action_type}.","approval":row}
    if row["target_id"]!=target_id:return {"valid":False,"reason":f"Approval covers {row['target_id']}, not {target_id}.","approval":row}
    if row["payload_hash"]!=payload_hash(payload):return {"valid":False,"reason":"The subject or due date differs from the approved payload.","approval":row}
    return {"valid":True,"reason":"Exact target and payload match the approved request.","approval":row}

def list_approvals(status=None):return query("SELECT * FROM approvals WHERE (? IS NULL OR status=?) ORDER BY id DESC",(status,status))

