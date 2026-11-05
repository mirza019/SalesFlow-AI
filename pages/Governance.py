import json
import streamlit as st
from core.approvals import list_approvals,review
from core.audit import recent
from core.database import query
from ui.components.common import header,status

def render(user):
    header("Governance & Approvals","Review sensitive actions, workflow lifecycle, failures, and immutable audit evidence.")
    counts={s:len(list_approvals(s)) for s in ["pending","approved","rejected"]};cols=st.columns(4)
    for col,(label,value) in zip(cols,[*counts.items(),("execution failures",query("SELECT COUNT(*) n FROM workflow_runs WHERE status='failed'")[0]["n"])]):
        with col:st.metric(label.title(),value)
    st.markdown("### Pending approval review")
    pending=list_approvals("pending")
    if not pending:st.info("No pending approvals.")
    for item in pending:
        with st.expander(f"#{item['id']} {item['action_type']} → {item['target_id']}"):
            st.json(json.loads(item["payload_json"]));st.caption(f"Requested by {item['requested_by']} · payload hash {item['payload_hash'][:12]}…")
            c1,c2=st.columns(2)
            if c1.button("Approve",key=f"approve_{item['id']}"):
                try:review(user,item["id"],"approved");st.success("Approved exact payload.");st.rerun()
                except Exception as exc:st.error(str(exc))
            if c2.button("Reject",key=f"reject_{item['id']}"):
                try:review(user,item["id"],"rejected");st.warning("Rejected.");st.rerun()
                except Exception as exc:st.error(str(exc))
    tabs=st.tabs(["All approvals","Workflow versions","Audit history","Execution failures"])
    with tabs[0]:st.dataframe(list_approvals(),use_container_width=True)
    with tabs[1]:st.dataframe(query("SELECT * FROM workflow_versions ORDER BY id DESC"),use_container_width=True)
    with tabs[2]:st.dataframe(recent(200),use_container_width=True)
    with tabs[3]:st.dataframe(query("SELECT * FROM workflow_runs WHERE status='failed' ORDER BY id DESC"),use_container_width=True)

