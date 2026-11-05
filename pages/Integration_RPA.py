from datetime import date,datetime,timedelta
import json
import streamlit as st
from connectors import crm_connector,database_connector
from connectors.csv_connector import validate_csv
from core.approvals import approval_match,request_approval
from core.database import query
from rpa.crm_robot import create_follow_up
from ui.components.common import header,status

def render(user):
    header("Integration & RPA Hub","Controlled data exchange and approved browser automation.")
    st.markdown("### Connector management");cols=st.columns(3,gap="medium")
    with cols[0]:
        st.markdown('<div class="eyebrow">File import</div><div class="section-title">CSV Data Connector</div><div class="section-subtitle">Validate approved sales extracts before ingestion.</div>',unsafe_allow_html=True);uploaded=st.file_uploader("Import CSV",type="csv");entity=st.selectbox("Entity",["opportunities","customers"])
        if uploaded:
            result=validate_csv(uploaded,entity);st.success(f"Valid schema · {result['rows']} rows") if result["valid"] else st.error(f"Missing: {result['missing_columns']}");st.dataframe(result["preview"])
    with cols[1]:
        st.markdown('<div class="eyebrow">Relational data</div><div class="section-title">SQLite Database</div><div class="section-subtitle">Local governed sales operations store.</div>',unsafe_allow_html=True);db=database_connector.status();status("connected" if db["connected"] else "error");st.metric("Opportunities",db.get("opportunities",0));st.caption(db.get("database",db.get("error")))
    with cols[2]:
        st.markdown('<div class="eyebrow">Business system</div><div class="section-title">CRM REST API</div><div class="section-subtitle">Persistent simulator used by the browser robot.</div>',unsafe_allow_html=True);crm=crm_connector.status();status("connected" if crm["connected"] else "offline");st.caption("Last check: just now");st.caption("Service: 127.0.0.1:8001")
    st.markdown("### RPA execution")
    overdue=query("SELECT opportunity_id,name FROM sales_opportunities WHERE stage NOT LIKE 'Closed%' AND date(expected_close_date)<date('now') ORDER BY expected_close_date LIMIT 100")
    if not overdue:st.info("No overdue opportunities are available.");return
    with st.container(border=True):
      st.markdown('<div class="section-title">Approved CRM Follow-up Robot</div><div class="section-subtitle">Opens the CRM interface, creates a task, and verifies persistence.</div>',unsafe_allow_html=True)
      labels={f"{x['opportunity_id']} · {x['name']}":x["opportunity_id"] for x in overdue};choice=st.selectbox("Target opportunity",labels);oid=labels[choice];subject=st.text_input("Follow-up subject","Review overdue opportunity and confirm close plan");due=st.date_input("Due date",date.today()+timedelta(days=7));payload={"subject":subject,"due_date":due.isoformat()}
    if st.button("Request manager approval"):
        try:aid=request_approval(user,"create_follow_up",oid,payload);st.session_state.rpa_approval_id=aid;st.success(f"Approval request #{aid} created. A different Administrator or Sales Manager must approve it in Governance & Approvals.")
        except Exception as exc:st.error(str(exc))
    aid=st.number_input("Approved request ID",min_value=0,value=int(st.session_state.get("rpa_approval_id",0)))
    match=approval_match(int(aid),"create_follow_up",oid,payload) if aid else {"valid":False,"reason":"Enter an approved request ID.","approval":None}
    if match["valid"]:st.success(f"Approval #{int(aid)} verified: exact target and payload match.")
    else:
        st.warning(match["reason"])
        if match["approval"]:
            approved_payload=match["approval"]["payload_json"]
            st.caption(f"Approval #{int(aid)} → {match['approval']['target_id']} · status: {match['approval']['status']} · payload: {approved_payload}")
    if st.button("Run browser robot",type="primary",disabled=not match["valid"],width="stretch"):
        with st.spinner("Running Playwright and verifying persistence…"):
            try:
                result=create_follow_up(user,oid,subject,due.isoformat(),int(aid))
                st.session_state.rpa_result={**result,"opportunity_id":oid,"subject":subject,"due_date":due.isoformat(),"approval_id":int(aid),"completed_at":datetime.now().strftime("%d %b %Y, %H:%M:%S")}
            except Exception as exc:st.error(f"RPA failed: {exc}")
    result=st.session_state.get("rpa_result")
    if not result:
        prior=query("SELECT target_id,details_json,created_at FROM audit_log WHERE event_type='rpa_follow_up' AND success=1 ORDER BY id DESC LIMIT 1")
        if prior:
            details=json.loads(prior[0]["details_json"]);approval_id=details.get("approval_id",0)
            task=query("SELECT subject,due_date FROM crm_follow_up_tasks WHERE approval_id=? ORDER BY id DESC LIMIT 1",(approval_id,))
            if task:
                result={**details,"opportunity_id":prior[0]["target_id"],"subject":task[0]["subject"],"due_date":task[0]["due_date"],"approval_id":approval_id,"completed_at":prior[0]["created_at"]}
    if result:
        st.markdown("### Latest execution result")
        with st.container(border=True):
            result_header=st.columns([3,1])
            with result_header[0]:
                st.markdown('<div class="section-title">CRM Follow-up Completed</div><div class="section-subtitle">The browser robot submitted the task and checked the persisted CRM record.</div>',unsafe_allow_html=True)
            with result_header[1]:status(result["status"])
            summary=st.columns(4)
            summary[0].metric("Verification","Passed" if result["verified"] else "Failed")
            summary[1].metric("Opportunity",result["opportunity_id"])
            summary[2].metric("Approval",f"#{result['approval_id']}")
            summary[3].metric("Completed",result["completed_at"])
            if result["verified"]:st.success(result["message"],icon="✅")
            else:st.error(result["message"],icon="⚠️")
            detail_cols=st.columns(2)
            detail_cols[0].markdown(f"**Follow-up task**  \n{result['subject']}")
            detail_cols[1].markdown(f"**Due date**  \n{result['due_date']}")
