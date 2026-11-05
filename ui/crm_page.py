from __future__ import annotations

from datetime import date

import streamlit as st

from core.approvals import assert_approved
from core.audit import record
from core.database import execute, query


def _ensure_table() -> None:
    execute(
        "CREATE TABLE IF NOT EXISTS crm_follow_up_tasks ("
        "id INTEGER PRIMARY KEY, opportunity_id TEXT NOT NULL, subject TEXT NOT NULL, "
        "due_date TEXT NOT NULL, approval_id INTEGER NOT NULL, "
        "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )


def _styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] {display:none}
        [data-testid="stAppViewContainer"] {background:#F3F7FC}
        .block-container {max-width:1180px;padding:2rem 2rem 4rem}
        .crm-top {display:flex;align-items:center;justify-content:space-between;margin-bottom:2.4rem}
        .crm-brand {display:flex;align-items:center;gap:.7rem;color:#10243A;font-size:1.15rem;font-weight:800}
        .crm-mark {display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:#2563EB;color:white}
        .crm-badge {padding:.35rem .7rem;border:1px solid #DCE6F2;border-radius:999px;background:white;color:#64748B;font-size:.75rem;font-weight:650}
        .crm-kicker {color:#2563EB;font-size:.75rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
        .crm-title {color:#10243A;font-size:2.15rem;letter-spacing:-.04em;margin:.25rem 0 .2rem}
        .crm-lead {color:#64748B;margin:0 0 1.4rem}
        .crm-record {margin:1.6rem 0 .8rem;color:#10243A;font-size:1.45rem;font-weight:800}
        .crm-record span {margin-left:.5rem;padding:.25rem .65rem;border-radius:999px;background:#DBEAFE;color:#1D4ED8;font-size:.75rem;vertical-align:middle}
        .crm-card {background:white;border:1px solid #DCE6F2;border-radius:15px;padding:1.25rem;margin-top:.75rem}
        .crm-card h3 {color:#10243A;margin:0 0 .2rem;font-size:1.05rem}
        .crm-card p {color:#64748B;margin:.1rem 0 .9rem;font-size:.84rem}
        .crm-task {padding:.8rem .9rem;margin:.5rem 0;border:1px solid #E5EDF7;border-radius:10px;background:#F8FBFF;color:#10243A}
        .crm-task small {display:block;color:#64748B;margin-top:.2rem}
        .crm-governance {margin-top:1rem;padding:.8rem;border-left:3px solid #2563EB;background:#F8FBFF;color:#64748B;font-size:.8rem}
        div[data-testid="stMetric"] {background:white;border:1px solid #DCE6F2;border-radius:13px;padding:1rem}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_crm() -> None:
    _ensure_table()
    _styles()
    st.markdown(
        '<div class="crm-top"><div class="crm-brand"><span class="crm-mark">S</span>'
        'SalesOps CRM</div><span class="crm-badge">Connected simulator</span></div>',
        unsafe_allow_html=True,
    )
    st.link_button("← Back to SalesOps AI", "./", width="content")
    st.markdown(
        '<div class="crm-kicker">Customer relationship management</div>'
        '<h1 class="crm-title">Opportunity Workspace</h1>'
        '<p class="crm-lead">Review opportunities and create governed, approval-bound follow-up tasks.</p>',
        unsafe_allow_html=True,
    )

    default_id = st.query_params.get("opportunity_id", "OPP-000001")
    with st.form("crm_search", border=False):
        search_col, button_col = st.columns([5, 1], vertical_alignment="bottom")
        with search_col:
            opportunity_id = st.text_input("Opportunity ID", value=default_id, placeholder="OPP-000001")
        with button_col:
            searched = st.form_submit_button("Search", type="primary", width="stretch")
    if searched:
        st.query_params["view"] = "crm"
        st.query_params["opportunity_id"] = opportunity_id.strip()

    rows = query("SELECT * FROM sales_opportunities WHERE opportunity_id=?", (opportunity_id.strip(),))
    if not rows:
        st.error("Opportunity not found. Try an ID such as OPP-000001.")
        return
    opportunity = rows[0]
    probability = float(opportunity["probability"])
    probability_text = f"{probability:.0%}" if probability <= 1 else f"{probability:.0f}%"
    st.markdown(
        f'<div class="crm-record">{opportunity["name"]}<span>{opportunity["stage"]}</span></div>',
        unsafe_allow_html=True,
    )
    metric_cols = st.columns(4)
    values = (
        ("Stage", opportunity["stage"]),
        ("Deal value", f'{float(opportunity["deal_value"]):,.2f} {opportunity["currency"]}'),
        ("Probability", probability_text),
        ("Expected close", str(opportunity["expected_close_date"])[:10]),
    )
    for column, (label, value) in zip(metric_cols, values):
        column.metric(label, value)

    tasks_col, form_col = st.columns([1.08, .92], gap="large")
    with tasks_col:
        st.markdown('<div class="crm-card"><h3>Follow-up tasks</h3><p>Saved tasks verified against approved payloads.</p>', unsafe_allow_html=True)
        tasks = query(
            "SELECT * FROM crm_follow_up_tasks WHERE opportunity_id=? ORDER BY id DESC",
            (opportunity_id.strip(),),
        )
        if tasks:
            for task in tasks:
                st.markdown(
                    f'<div class="crm-task">✓ &nbsp;<b>{task["subject"]}</b>'
                    f'<small>Due {task["due_date"]} · Approval #{task["approval_id"]}</small></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No approved follow-up tasks yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with form_col:
        st.markdown('<div class="crm-card"><h3>Create approved follow-up</h3><p>Every field must match the approved SalesOps request.</p>', unsafe_allow_html=True)
        with st.form("crm_follow_up", border=False, clear_on_submit=True):
            subject = st.text_input("Subject", placeholder="Schedule customer follow-up")
            due_date = st.date_input("Due date", value=date.today())
            approval_id = st.number_input("Approval ID", min_value=1, step=1)
            submitted = st.form_submit_button("Save approved task", type="primary", width="stretch")
        if submitted:
            payload = {"subject": subject.strip(), "due_date": due_date.isoformat()}
            try:
                if not payload["subject"]:
                    raise ValueError("Enter a follow-up subject.")
                assert_approved(int(approval_id), "create_follow_up", opportunity_id.strip(), payload)
                task_id = execute(
                    "INSERT INTO crm_follow_up_tasks(opportunity_id,subject,due_date,approval_id) VALUES(?,?,?,?)",
                    (opportunity_id.strip(), payload["subject"], payload["due_date"], int(approval_id)),
                )
                record("crm-simulator", "follow_up_created", "opportunity", opportunity_id.strip(), {"task_id": task_id, "approval_id": int(approval_id)})
                st.success("Task saved and verified")
            except (PermissionError, ValueError) as exc:
                st.error(str(exc))
        st.markdown('<div class="crm-governance"><b>Governed action</b><br>SalesOps approval is required before this CRM record can be changed.</div></div>', unsafe_allow_html=True)
