from __future__ import annotations
import os
import httpx
BASE=os.getenv("CRM_API_URL","http://127.0.0.1:8001")
def status():
    try:
        r=httpx.get(f"{BASE}/health",timeout=2); return {"connected":r.is_success,"status_code":r.status_code}
    except Exception as exc:return {"connected":False,"error":str(exc)}
def opportunity(opportunity_id:str):
    r=httpx.get(f"{BASE}/api/opportunities/{opportunity_id}",timeout=5);r.raise_for_status();return r.json()
