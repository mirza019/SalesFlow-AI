from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core.gemini_agent import ask
from core.kpis import (available_regions, dashboard_metrics, data_quality,
    opportunities_requiring_attention, pipeline_by_month, regional_performance,
    stage_distribution)
from core.workflow_engine import save_workflow
from core.workflow_templates import TEMPLATES
from ui.components.common import card, header, kpi
from ui.charts.dashboard import pipeline_chart, quality_gauge, region_chart, stage_chart

def eur(value):
    if abs(value)>=1_000_000_000:return f"€{value/1_000_000_000:,.2f}B"
    return f"€{value/1_000_000:,.1f}M" if abs(value)>=1_000_000 else f"€{value:,.0f}"

def comparison(current, previous, inverse=False, percentage=False):
    if previous in (None,0):return "No prior baseline","neutral"
    change=current-previous if percentage else (current-previous)/abs(previous)*100
    good=change<0 if inverse else change>0
    suffix=" pts" if percentage else "%"
    return f"{change:+.1f}{suffix} vs previous",("good" if good else "bad" if change else "neutral")

def render(user):
    header_row=st.columns([5,1.35,1.35,.55],gap="small")
    with header_row[0]:header("Sales Intelligence","Monitor pipeline health, sales performance, and operational priorities.")
    with header_row[1]:period=st.selectbox("Date range",["Last 30 Days","Last 90 Days","Last 12 Months"],index=2,key="dashboard_period")
    with header_row[2]:region=st.selectbox("Region",["All regions",*available_regions()],key="dashboard_region")
    with header_row[3]:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        if st.button("↻",help="Refresh dashboard",width="stretch",key="dashboard_refresh"):st.rerun()

    days={"Last 30 Days":30,"Last 90 Days":90,"Last 12 Months":365}[period]
    end=pd.Timestamp(date.today());start=end-timedelta(days=days);previous_end=start-timedelta(days=1);previous_start=previous_end-timedelta(days=days)
    metrics=dashboard_metrics(period,region=region)
    previous=dashboard_metrics(period,previous_start,previous_end,region)
    deltas=[comparison(metrics["pipeline_value"],previous["pipeline_value"]),comparison(metrics["weighted_pipeline"],previous["weighted_pipeline"]),comparison(metrics["win_rate"],previous["win_rate"],percentage=True),comparison(metrics["overdue_opportunities"],previous["overdue_opportunities"],inverse=True),comparison(metrics["expiring_quotations"],previous["expiring_quotations"],inverse=True)]
    values=[("Total Pipeline",eur(metrics["pipeline_value"]),"Open pipeline converted to EUR","▥"),("Weighted Pipeline",eur(metrics["weighted_pipeline"]),"Probability-adjusted value","◈"),("Win Rate",f'{metrics["win_rate"]:.1f}%',"Closed-won / all closed","↗"),("Overdue Opportunities",f'{metrics["overdue_opportunities"]:,}',"Open deals past expected close","!"),("Expiring Quotations",f'{metrics["expiring_quotations"]:,}',"Within the next 30 days","◷")]
    for col,item,delta in zip(st.columns(5,gap="medium"),values,deltas):
        with col:kpi(*item,delta=delta[0],sentiment=delta[1])

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
    row1=st.columns([3,2],gap="medium")
    with row1[0]:
        with st.container(border=True):
            st.markdown('<div class="section-title">Pipeline Development</div><div class="section-subtitle">Monthly open and probability-weighted pipeline in EUR</div>',unsafe_allow_html=True)
            st.plotly_chart(pipeline_chart(pipeline_by_month(period,region)),width="stretch",config={"displayModeBar":False})
    with row1[1]:
        with st.container(border=True):
            st.markdown('<div class="section-title">Pipeline by Stage</div><div class="section-subtitle">Share of total pipeline value in EUR by current sales stage</div>',unsafe_allow_html=True)
            st.plotly_chart(stage_chart(stage_distribution(period,region)),width="stretch",config={"displayModeBar":False})
            st.caption("Each color is a sales stage. Percentages show that stage’s share of total pipeline value—not its share of opportunity count.")

    quality=data_quality();row2=st.columns([3,2],gap="medium")
    with row2[0]:
        with st.container(border=True):
            st.markdown('<div class="section-title">Regional Performance</div><div class="section-subtitle">Pipeline and weighted value converted using historical exchange rates</div>',unsafe_allow_html=True)
            st.plotly_chart(region_chart(regional_performance(period,region)),width="stretch",config={"displayModeBar":False})
    with row2[1]:
        with st.container(border=True):
            st.markdown('<div class="section-title">CRM Data Quality</div><div class="section-subtitle">Completeness, stage validity, activity coverage, and quotation quality</div>',unsafe_allow_html=True)
            st.plotly_chart(quality_gauge(quality["score"]),width="stretch",config={"displayModeBar":False})
            component_cols=st.columns(2)
            for idx,(name,value) in enumerate(quality["components"].items()):component_cols[idx%2].metric(name,f"{value:.0f}%")
            st.caption(f"Primary improvement area: {quality['primary_problem']} · {quality['issue_count']:,} recorded issues")

    st.markdown("### Opportunities requiring attention")
    attention=opportunities_requiring_attention(region,25)
    if attention.empty:st.success("No opportunities meet the current risk rules.")
    else:
        risk=st.multiselect("Risk filter",sorted(attention.risk.unique()),default=sorted(attention.risk.unique()),key="attention_risk")
        visible=attention[attention.risk.isin(risk)].rename(columns={"opportunity_id":"Opportunity ID","customer":"Customer","region":"Region","deal_value_eur":"Deal Value (EUR)","sales_stage":"Sales Stage","last_activity":"Last Activity","risk":"Risk","recommended_action":"Recommended Action"})
        st.dataframe(visible,width="stretch",hide_index=True,column_config={"Deal Value (EUR)":st.column_config.NumberColumn(format="€ %.2f"),"Opportunity ID":st.column_config.TextColumn(width="small"),"Recommended Action":st.column_config.TextColumn(width="large")})

    with st.expander("AI Sales Assistant — verified analysis and recommendations",expanded=False):
        suggestions=st.columns(4)
        prompts=["Which opportunities need attention?","Why did the win rate change?","Identify missing CRM information.","Recommend actions for this week's pipeline."]
        for col,prompt_text in zip(suggestions,prompts):
            if col.button(prompt_text,key=f"dash_prompt_{prompt_text}",width="stretch"):st.session_state.dashboard_prompt=prompt_text
        history=st.session_state.setdefault("dashboard_chat",[])
        for message in history[-8:]:
            with st.chat_message(message["role"]):st.markdown(message["content"])
        prompt=st.chat_input("Ask SalesOps AI…",key="dashboard_chat_input") or st.session_state.pop("dashboard_prompt",None)
        if prompt:
            history.append({"role":"user","content":prompt})
            with st.spinner("Retrieving verified evidence…"):result=ask(user,prompt)
            history.append({"role":"assistant","content":result["answer"]});st.session_state.last_verified=result;st.rerun()
        if st.session_state.get("last_verified"):
            st.markdown("**Verified numerical evidence**")
            with st.expander(f"Allowlisted tool: {st.session_state.last_verified['tool']}"):st.json(st.session_state.last_verified["verified_data"])

    st.markdown("### Governed actions")
    actions=st.columns(3,gap="medium")
    configs=[("Run Data Quality Check","Detect incomplete CRM records and prepare a reviewable report.","data_quality"),("Create Follow-up Tasks","Prepare approval-bound tasks for responsible representatives.","overdue_followup"),("Generate Weekly Sales Report","Create a reproducible sales intelligence report.","weekly_report")]
    for col,(title,description,key) in zip(actions,configs):
        with col:
            card(title,description)
            if st.button("Create workflow draft",key=f"quick_{key}",width="stretch"):
                template=TEMPLATES[key];config={x:template[x] for x in ["trigger","data_source","condition","action","approval_required"]};config["parameters"]={"limit":20};workflow_id=save_workflow(user,template["name"],key,config);st.success(f"Workflow draft #{workflow_id} created.")
