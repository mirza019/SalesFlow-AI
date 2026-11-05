import json
import streamlit as st
from core.requirements import deterministic_spec,to_workflow,save_spec
from core.workflow_engine import save_workflow
from ui.components.common import header,status

def render(user):
    header("Requirements Studio","Turn business problems into reviewable, governed workflow specifications.")
    left,right=st.columns([1,1.15],gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Business request</div><div class="section-subtitle">Describe the outcome in plain language. Include timing, conditions, and expected action.</div>',unsafe_allow_html=True)
            with st.form("requirements_input"):
                text=st.text_area("Problem description",height=180,placeholder="Every Monday, identify sales opportunities that have not been contacted for 14 days and prepare follow-up tasks.")
                objective=st.text_input("Stakeholder objective",placeholder="Reduce overdue follow-ups")
                source=st.selectbox("Primary data source",["Sales database","CRM connector"])
                analyze=st.form_submit_button("Analyze requirements",type="primary",width="stretch")
            if analyze:
                try:st.session_state.requirement_spec=deterministic_spec(text);st.session_state.requirement_title=objective
                except ValueError as exc:st.warning(str(exc))
            st.markdown('<div class="callout"><b>Good request pattern</b><br>When [trigger], find [records] where [condition], then [action], with [approval] before any system change.</div>',unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Structured specification</div><div class="section-subtitle">Review verified fields before saving or generating a workflow.</div>',unsafe_allow_html=True)
            spec=st.session_state.get("requirement_spec")
            if not spec:st.info("Analyze a business request to create a structured specification.");return
            status("draft")
            for label,key in [("Business objective","business_objective"),("Required data","required_data"),("Trigger","trigger"),("Conditions","conditions"),("Actions","actions"),("Approval requirements","approval_requirements"),("Acceptance criteria","success_criteria")]:
                value=spec.get(key,"—");display=" · ".join(value) if isinstance(value,list) else str(value)
                st.markdown(f"**{label}**  \n{display}")
            with st.expander("Edit specification JSON"):
                edited=st.text_area("Specification",json.dumps(spec,indent=2),height=320,label_visibility="collapsed")
            try:parsed=json.loads(edited)
            except json.JSONDecodeError:st.error("The specification must remain valid JSON.");return
            st.markdown("**Proposed workflow**");st.json(to_workflow(parsed),expanded=False)
            c1,c2=st.columns(2)
            if c1.button("Save draft",width="stretch"):
                rid=save_spec(user,st.session_state.get("requirement_title") or "Sales operations requirement",parsed,"draft");st.success(f"Requirement #{rid} saved.")
            if c2.button("Generate workflow",type="primary",width="stretch"):
                title=st.session_state.get("requirement_title") or "Generated workflow";rid=save_spec(user,title,parsed,"approved");wf=to_workflow(parsed);wid=save_workflow(user,title,"overdue_followup" if wf["action"]=="follow_up_task" else "weekly_report",wf);st.success(f"Requirement #{rid} approved; workflow #{wid} created.")

