from __future__ import annotations
from html import escape
from fastapi import FastAPI,Form,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from pydantic import BaseModel
from core.approvals import assert_approved
from core.audit import record
from core.database import execute,query

app=FastAPI(title="SalesOps Legacy CRM Simulator")

class FollowUp(BaseModel):
    subject:str; due_date:str; approval_id:int

def ensure_table():
    execute("CREATE TABLE IF NOT EXISTS crm_follow_up_tasks (id INTEGER PRIMARY KEY, opportunity_id TEXT NOT NULL, subject TEXT NOT NULL, due_date TEXT NOT NULL, approval_id INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

@app.on_event("startup")
def startup():ensure_table()

@app.get("/health")
def health():return {"status":"ok"}

@app.get("/api/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id:str):
    rows=query("SELECT * FROM sales_opportunities WHERE opportunity_id=?",(opportunity_id,))
    if not rows:raise HTTPException(404,"Opportunity not found")
    return {"opportunity":rows[0],"activities":query("SELECT * FROM sales_activities WHERE opportunity_id=? ORDER BY activity_date DESC",(opportunity_id,)),"follow_up_tasks":query("SELECT * FROM crm_follow_up_tasks WHERE opportunity_id=? ORDER BY id DESC",(opportunity_id,))}

@app.post("/api/opportunities/{opportunity_id}/follow-ups")
def create_follow_up(opportunity_id:str,item:FollowUp):
    payload={"subject":item.subject,"due_date":item.due_date}
    try:assert_approved(item.approval_id,"create_follow_up",opportunity_id,payload)
    except PermissionError as exc:raise HTTPException(403,str(exc))
    task_id=execute("INSERT INTO crm_follow_up_tasks(opportunity_id,subject,due_date,approval_id) VALUES(?,?,?,?)",(opportunity_id,item.subject,item.due_date,item.approval_id));record("crm-simulator","follow_up_created","opportunity",opportunity_id,{"task_id":task_id,"approval_id":item.approval_id});return {"id":task_id,"persisted":True}

@app.get("/",response_class=HTMLResponse)
def crm_ui(opportunity_id:str="OPP-000001",message:str=""):
    try:data=get_opportunity(opportunity_id)
    except HTTPException:return HTMLResponse("<h1>Opportunity not found</h1>",404)
    o=data["opportunity"]
    tasks="".join(f"<li data-testid='task-{x['id']}'><span class='task-check'>✓</span><span><b>{escape(x['subject'])}</b><small>Due {escape(x['due_date'])} · Approval #{x['approval_id']}</small></span></li>" for x in data["follow_up_tasks"])
    if not tasks:tasks="<li class='empty'><span>No approved follow-up tasks yet.</span></li>"
    notice=f"<div class='notice {'error' if message.startswith('Error:') else 'success'}'>{escape(message)}</div>" if message else ""
    oid=escape(opportunity_id);name=escape(str(o['name']));stage=escape(str(o['stage']));currency=escape(str(o['currency']))
    probability=float(o['probability']);probability_text=f"{probability:.0%}" if probability<=1 else f"{probability:.0f}%"
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>SalesOps CRM</title><style>
*{{box-sizing:border-box}}:root{{--blue:#2563EB;--blue2:#1D4ED8;--navy:#10243A;--body:#334155;--muted:#64748B;--line:#DCE6F2;--canvas:#F3F7FC;--soft:#EFF6FF;--white:#fff;--green:#15803D;--red:#B91C1C}}
body{{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--canvas);color:var(--body);font-size:15px;line-height:1.5}}
.topbar{{height:72px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 max(24px,calc((100vw - 1180px)/2));position:sticky;top:0;z-index:5}}
.brand{{display:flex;align-items:center;gap:11px;color:var(--navy);font-size:18px;font-weight:750}}.mark{{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;background:var(--blue);color:#fff;box-shadow:0 5px 14px rgba(37,99,235,.24)}}.product{{color:var(--muted);font-size:12px;font-weight:600;padding:5px 10px;border:1px solid var(--line);border-radius:999px;background:#F8FBFF}}
main{{max-width:1180px;margin:0 auto;padding:42px 24px 60px}}.eyebrow{{font-size:12px;font-weight:750;letter-spacing:.08em;color:var(--blue);text-transform:uppercase}}h1{{font-size:32px;line-height:1.2;letter-spacing:-.035em;color:var(--navy);margin:5px 0}}.lead{{color:var(--muted);margin:0 0 26px}}
.search{{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:end;background:#fff;border:1px solid var(--line);border-radius:15px;padding:18px;box-shadow:0 3px 12px rgba(15,39,71,.04)}}label{{display:block;color:var(--body);font-size:13px;font-weight:650}}input{{display:block;width:100%;height:46px;margin-top:7px;padding:0 13px;border:1px solid #C9D6E5;border-radius:10px;background:#fff;color:var(--navy);font:inherit;outline:none}}input:focus{{border-color:#3B82F6;box-shadow:0 0 0 3px rgba(59,130,246,.13)}}button{{height:46px;padding:0 22px;border:1px solid var(--blue);border-radius:10px;background:var(--blue);color:#fff;font:inherit;font-weight:650;cursor:pointer}}button:hover{{background:var(--blue2);border-color:var(--blue2)}}
.notice{{margin:18px 0 0;padding:12px 15px;border-radius:10px;font-weight:600}}.notice.success{{color:var(--green);background:#ECFDF3;border:1px solid #BBF7D0}}.notice.error{{color:var(--red);background:#FEF2F2;border:1px solid #FECACA}}
.opportunity{{margin:26px 0 17px}}.opportunity h2{{font-size:24px;color:var(--navy);letter-spacing:-.025em;margin:0}}.opportunity p{{margin:5px 0;color:var(--muted)}}.status{{display:inline-flex;margin-left:7px;padding:3px 9px;border-radius:999px;background:#DBEAFE;color:#1D4ED8;font-size:12px;font-weight:700}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}.metric{{background:#fff;border:1px solid var(--line);border-radius:13px;padding:15px}}.metric small{{display:block;color:var(--muted);font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.04em}}.metric b{{display:block;color:var(--navy);font-size:19px;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.workspace{{display:grid;grid-template-columns:1.1fr .9fr;gap:20px}}.card{{background:#fff;border:1px solid var(--line);border-radius:15px;padding:22px;box-shadow:0 3px 12px rgba(15,39,71,.035)}}.card h3{{font-size:18px;color:var(--navy);margin:0 0 4px}}.sub{{font-size:13px;color:var(--muted);margin:0 0 18px}}.form-grid{{display:grid;gap:14px}}.save{{width:100%;margin-top:3px}}
.governance{{margin-top:15px;padding:12px 14px;border-left:3px solid var(--blue);border-radius:0 9px 9px 0;background:#F8FBFF;font-size:12px;color:var(--muted)}}.governance b{{display:block;color:var(--navy);font-size:13px;margin-bottom:2px}}
.tasks{{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:9px}}.tasks li{{display:flex;align-items:flex-start;gap:11px;padding:12px;border:1px solid #E5EDF7;background:#F8FBFF;border-radius:10px}}.task-check{{display:grid;place-items:center;flex:0 0 25px;height:25px;border-radius:50%;background:#DCFCE7;color:var(--green);font-weight:800}}.tasks b{{display:block;color:var(--navy);font-size:13px}}.tasks small{{display:block;color:var(--muted);margin-top:2px}}.tasks .empty{{color:var(--muted);background:#fff;border-style:dashed}}
@media(max-width:780px){{.topbar{{padding:0 18px}}main{{padding:28px 16px}}.search{{grid-template-columns:1fr}}.search button{{width:100%}}.metrics{{grid-template-columns:repeat(2,1fr)}}.workspace{{grid-template-columns:1fr}}h1{{font-size:27px}}}}
</style></head><body>
<header class='topbar'><div class='brand'><span class='mark'>S</span>SalesOps CRM</div><span class='product'>Connected simulator</span></header>
<main><div class='eyebrow'>Customer relationship management</div><h1>Opportunity Workspace</h1><p class='lead'>Review sales opportunities and create governed, approval-bound follow-up tasks.</p>
<form class='search' method='get'><label>Opportunity ID<input data-testid='opportunity-search' name='opportunity_id' value='{oid}' placeholder='OPP-000001'></label><button data-testid='search-button'>Search opportunity</button></form>{notice}
<section class='opportunity'><h2 data-testid='opportunity-name'>{name}<span class='status'>{stage}</span></h2><p>{oid} · Connected sales record</p></section>
<section class='metrics'><div class='metric'><small>Stage</small><b>{stage}</b></div><div class='metric'><small>Deal value</small><b>{float(o['deal_value']):,.2f} {currency}</b></div><div class='metric'><small>Probability</small><b>{probability_text}</b></div><div class='metric'><small>Expected close</small><b>{escape(str(o['expected_close_date']))[:10]}</b></div></section>
<div class='workspace'><section class='card'><h3>Follow-up tasks</h3><p class='sub'>Saved tasks verified against approved payloads.</p><ul class='tasks' data-testid='task-list'>{tasks}</ul></section>
<section class='card'><h3>Create approved follow-up</h3><p class='sub'>Every field must match the approved SalesOps request exactly.</p><form class='form-grid' method='post' action='/ui/follow-up'><input type='hidden' name='opportunity_id' value='{oid}'><label>Subject<input data-testid='followup-subject' name='subject' placeholder='Schedule customer follow-up' required></label><label>Due date<input data-testid='followup-due-date' type='date' name='due_date' required></label><label>Approval ID<input data-testid='approval-id' type='number' min='1' name='approval_id' placeholder='Enter approved request ID' required></label><button class='save' data-testid='save-followup'>Save approved task</button></form><div class='governance'><b>Governed action</b>SalesOps approval is required before this CRM record can be changed.</div></section></div></main></body></html>"""

@app.post("/ui/follow-up")
def ui_follow_up(opportunity_id:str=Form(...),subject:str=Form(...),due_date:str=Form(...),approval_id:int=Form(...)):
    try:create_follow_up(opportunity_id,FollowUp(subject=subject,due_date=due_date,approval_id=approval_id));msg="Task saved and verified"
    except HTTPException as exc:msg=f"Error: {exc.detail}"
    return RedirectResponse(f"/?opportunity_id={opportunity_id}&message={msg.replace(' ','%20')}",status_code=303)

