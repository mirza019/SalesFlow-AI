from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.common import header

MAPPING=[
    {"Current capability":"Sales intelligence dashboard","Power Platform target":"Power BI + Dataverse","Implementation approach":"Model governed sales tables in Dataverse and publish role-filtered semantic models.","Status":"Architecture mapped"},
    {"Current capability":"Requirements Studio","Power Platform target":"Power Apps","Implementation approach":"Canvas app captures business outcomes, validation rules, owners, risk and acceptance criteria.","Status":"Prototype equivalent"},
    {"Current capability":"Workflow Studio","Power Platform target":"Power Automate","Implementation approach":"Convert validated workflow JSON into solution-aware cloud flows with connection references.","Status":"Prototype equivalent"},
    {"Current capability":"AI Agent & Assistant","Power Platform target":"Copilot Studio + Azure AI","Implementation approach":"Expose approved actions and grounded Dataverse queries as governed agent tools.","Status":"Prototype equivalent"},
    {"Current capability":"CRM connector and RPA","Power Platform target":"Custom connector + desktop flows","Implementation approach":"Use API-first connectors; retain desktop automation only for legacy screens without APIs.","Status":"Demonstrated locally"},
    {"Current capability":"Approvals and audit","Power Platform target":"Approvals + Dataverse audit + Purview","Implementation approach":"Bind approval records to canonical action payloads and retain immutable execution evidence.","Status":"Control demonstrated"},
    {"Current capability":"Citizen Developer Hub","Power Platform target":"CoE Starter Kit","Implementation approach":"Publish templates, ownership rules, inventory, adoption metrics and maker guidance.","Status":"Enablement mapped"},
]

def _card(title,target,description,icon):
    st.markdown(f'''<div class="card"><div class="kpi-top"><div class="kpi-icon">{icon}</div><div><div class="eyebrow">Microsoft target</div><div class="section-title">{title}</div></div></div><div class="small-muted"><b>{target}</b><br>{description}</div></div>''',unsafe_allow_html=True)

def render(user):
    header("Power Platform Blueprint","A transparent migration and governance map from this Python prototype to an enterprise Microsoft Power Platform solution.")
    st.info("Portfolio architecture blueprint — this application demonstrates equivalent patterns but does not claim to be deployed on Microsoft Power Platform.")

    st.markdown('<div class="section-title">Solution architecture</div><div class="section-subtitle">Recommended production composition for Global Sales Operations</div>',unsafe_allow_html=True)
    st.markdown('''<div class="workflow-flow">
      <div class="flow-step flow-step-active">Power Apps<br><small>Business experience</small></div><div class="flow-arrow">→</div>
      <div class="flow-step">Dataverse<br><small>Governed sales data</small></div><div class="flow-arrow">→</div>
      <div class="flow-step">Power Automate<br><small>Workflow orchestration</small></div><div class="flow-arrow">→</div>
      <div class="flow-step">Copilot Studio<br><small>Grounded agents</small></div><div class="flow-arrow">→</div>
      <div class="flow-step">CRM & APIs<br><small>Enterprise systems</small></div>
    </div>''',unsafe_allow_html=True)

    cards=st.columns(3)
    with cards[0]:_card("Business applications","Power Apps","Role-aware canvas or model-driven experiences for sales operations and citizen developers.","▦")
    with cards[1]:_card("Automation and agents","Power Automate · Copilot Studio","Solution-aware flows, human approvals and agents limited to registered business actions.","✦")
    with cards[2]:_card("Data and insight","Dataverse · Power BI","Managed data model, row-level security, audit history and reusable sales reporting.","◈")

    st.markdown('<div style="height:18px"></div><div class="section-title">Capability mapping</div><div class="section-subtitle">What the current prototype proves and how it translates</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(MAPPING),width="stretch",hide_index=True,column_config={"Current capability":st.column_config.TextColumn(width="medium"),"Power Platform target":st.column_config.TextColumn(width="medium"),"Implementation approach":st.column_config.TextColumn(width="large"),"Status":st.column_config.TextColumn(width="small")})

    left,right=st.columns([1,1],gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Environment and ALM strategy</div><div class="section-subtitle">Move successful prototypes safely toward production</div>',unsafe_allow_html=True)
            st.markdown("""
1. **Personal developer environment** — isolated exploration and component tests.
2. **Development environment** — solution-aware apps, flows and connection references.
3. **Test environment** — representative synthetic data, automated tests and business acceptance.
4. **Production environment** — managed solutions, service principals and monitored connectors.
5. **Retirement** — owner review, dependency check, export, retention decision and removal.
""")
            st.markdown('<div class="callout"><b>Deployment principle</b><br>Package components in managed solutions and promote them through pipelines; never edit production flows directly.</div>',unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Governance controls</div><div class="section-subtitle">Controls required for decentralized business applications</div>',unsafe_allow_html=True)
            controls=pd.DataFrame([
                ["DLP policies","Separate business, non-business and blocked connectors."],
                ["Managed environments","Usage insights, sharing limits and solution checks."],
                ["Identity","Entra ID groups, least privilege and service principals."],
                ["Data access","Dataverse security roles, teams and field-level controls."],
                ["CoE inventory","Ownership, orphan detection, adoption and compliance reporting."],
                ["AI governance","Approved knowledge, tool allowlists, prompt versions and evaluations."],
            ],columns=["Control","Application"])
            st.dataframe(controls,width="stretch",hide_index=True)

    st.markdown('<div class="section-title">Migration roadmap</div><div class="section-subtitle">A pragmatic sequence that preserves business value and control</div>',unsafe_allow_html=True)
    roadmap=st.columns(4)
    phases=[("01 · Discover","Inventory data, owners, connectors, risks and success measures."),("02 · Validate","Recreate one requirements-to-approval flow with synthetic data."),("03 · Industrialize","Introduce Dataverse, solutions, pipelines, DLP and monitoring."),("04 · Scale","Publish templates, maker training, CoE reporting and lifecycle reviews.")]
    for col,(title,description) in zip(roadmap,phases):
        with col:st.markdown(f'<div class="card"><div class="eyebrow">Phase</div><div class="section-title">{title}</div><div class="small-muted">{description}</div></div>',unsafe_allow_html=True)

