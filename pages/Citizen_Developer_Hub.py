import streamlit as st
from core.workflow_templates import TEMPLATES
from ui.components.common import header

def render(user):
    header("Citizen Developer Hub","Reusable patterns and guardrails for safe, no-code sales automation.")
    st.markdown("### Build your first sales automation in five steps")
    steps=["Choose a business-tested template.","Configure its trigger, data source, condition, and action.","Preview verified records in test mode.","Request manager approval for CRM-changing actions.","Activate, monitor execution history, and refine safely."]
    for i,step in enumerate(steps,1):st.markdown(f"**{i}.** {step}")
    st.markdown("### Template library")
    cols=st.columns(3)
    for col,t in zip(cols,TEMPLATES.values()):
        with col:
            st.markdown(f'<div class="card"><div class="section-title">{t["name"]}</div><div class="small-muted">{t["purpose"]}</div><div class="divider"></div><b>Inputs</b><br>{", ".join(t["required_inputs"])}<br><br><b>Outputs</b><br>{", ".join(t["expected_outputs"])}<br><br><b>Permissions</b><br>{", ".join(t["permissions"])}<br><br><b>Testing</b><br>{t["testing"]}<br><br><b>Common error</b><br>{t["common_errors"]}</div>',unsafe_allow_html=True)
    st.markdown("### Natural-language examples")
    st.code("Every Monday, identify opportunities without contact for 14 days and prepare follow-up tasks.\nFind quotations expiring within 30 days and create a report.\nCheck CRM opportunity completeness weekly and notify the sales manager.")
