import json
import streamlit as st
from core.database import query
from core.workflow_engine import preview,run,save_workflow,set_state
from core.workflow_templates import TEMPLATES
from ui.components.common import header,status

def render(user):
    header("Workflow Studio","Configure reliable sales automations without writing code.")
    st.markdown("### Template library");st.caption("Start from a governed pattern, then configure only registered components.");cols=st.columns(3,gap="medium")
    for col,(key,t) in zip(cols,TEMPLATES.items()):
        with col:
            st.markdown(f'<div class="card"><div class="eyebrow">Template</div><div class="section-title">{t["name"]}</div><div class="small-muted">{t["purpose"]}</div><div class="divider"></div><div class="small-muted"><b>Output</b><br>{", ".join(t["expected_outputs"])}</div></div>',unsafe_allow_html=True)
            if st.button("Use template",key=f"template_{key}",width="stretch"):st.session_state.template_key=key
    key=st.session_state.get("template_key","data_quality");t=TEMPLATES[key]
    st.markdown("### Workflow designer")
    with st.form("workflow_config",border=True):
        name=st.text_input("Workflow name",t["name"]);settings=st.columns(3);trigger=settings[0].selectbox("Trigger",["manual","daily","weekly"],index=["manual","daily","weekly"].index(t["trigger"]));source=settings[1].selectbox("Data source",["sales_database","crm_connector"]);condition=settings[2].selectbox("Condition",["all","overdue","missing_data","expiring_quotation"],index=["all","overdue","missing_data","expiring_quotation"].index(t["condition"]));settings2=st.columns(3);action=settings2[0].selectbox("Action",["report","ai_summary","follow_up_task"],index=["report","ai_summary","follow_up_task"].index(t["action"]));limit=settings2[1].number_input("Preview limit",1,100,20);approval=settings2[2].checkbox("Manager approval required",value=t["approval_required"]);submitted=st.form_submit_button("Preview execution",type="primary",width="stretch")
    config={"trigger":trigger,"data_source":source,"condition":condition,"action":action,"approval_required":approval,"parameters":{"limit":limit,"days":30}}
    st.markdown(f'<div class="workflow-flow"><span class="flow-step flow-step-active">⚡<br>{trigger}</span><span class="flow-arrow">→</span><span class="flow-step flow-step-active">▤<br>{source}</span><span class="flow-arrow">→</span><span class="flow-step flow-step-active">◇<br>{condition}</span><span class="flow-arrow">→</span><span class="flow-step flow-step-active">✦<br>{action}</span><span class="flow-arrow">→</span><span class="flow-step {"flow-step-active" if approval else ""}">✓<br>{"Approval" if approval else "No approval"}</span><span class="flow-arrow">→</span><span class="flow-step">▶<br>Execution</span></div>',unsafe_allow_html=True)
    if submitted:
        try:st.session_state.workflow_preview=preview(config);st.dataframe(st.session_state.workflow_preview,use_container_width=True)
        except Exception as exc:st.error(str(exc))
    if st.button("Save draft",width="stretch"):
        try:wid=save_workflow(user,name,key,config);st.success(f"Workflow #{wid} saved.")
        except Exception as exc:st.error(str(exc))
    st.markdown("### Saved workflows")
    for wf in query("SELECT * FROM workflows ORDER BY id DESC LIMIT 20"):
        with st.expander(f"#{wf['id']} {wf['name']} · {wf['state']}"):
            status(wf["state"]);st.json(json.loads(wf["config_json"]));c1,c2,c3=st.columns(3)
            if c1.button("Run test",key=f"test_{wf['id']}"):
                try:st.json(run(user,wf["id"],True))
                except Exception as exc:st.error(str(exc))
            if c2.button("Activate",key=f"activate_{wf['id']}"):
                try:set_state(user,wf["id"],"active");st.success("Activated")
                except Exception as exc:st.error(str(exc))
            if c3.button("Pause",key=f"pause_{wf['id']}"):set_state(user,wf["id"],"paused");st.success("Paused")
    st.markdown("### Execution history");st.dataframe(query("SELECT * FROM workflow_runs ORDER BY id DESC LIMIT 50"),use_container_width=True)

