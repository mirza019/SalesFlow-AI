from __future__ import annotations
import json,os
from pathlib import Path
from core.approvals import assert_approved
from core.audit import record

def create_follow_up(user:dict,opportunity_id:str,subject:str,due_date:str,approval_id:int,base_url=None,headless=True)->dict:
    payload={"subject":subject,"due_date":due_date};assert_approved(approval_id,"create_follow_up",opportunity_id,payload)
    base_url=base_url or os.getenv("CRM_WEB_URL","http://127.0.0.1:8001")
    screenshots=Path("database/rpa_screenshots");screenshots.mkdir(parents=True,exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=headless);page=browser.new_page();page.set_default_timeout(10_000)
            for attempt in range(3):
                try:page.goto(f"{base_url}/?opportunity_id={opportunity_id}",wait_until="networkidle");break
                except Exception:
                    if attempt==2:raise
            page.get_by_test_id("followup-subject").fill(subject);page.get_by_test_id("followup-due-date").fill(due_date);page.get_by_test_id("approval-id").fill(str(approval_id));page.get_by_test_id("save-followup").click();page.wait_for_url("**message=**");message=page.get_by_test_id("message").inner_text();verified="saved and verified" in message.lower() and page.get_by_test_id("task-list").get_by_text(subject,exact=False).count()>0
            browser.close()
        result={"status":"succeeded" if verified else "verification_failed","verified":verified,"message":message}
        record(user["username"],"rpa_follow_up", "opportunity",opportunity_id,{**result,"approval_id":approval_id},verified);return result
    except Exception as exc:
        record(user["username"],"rpa_follow_up","opportunity",opportunity_id,{"error":str(exc),"approval_id":approval_id},False);raise
