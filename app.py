import importlib
import streamlit as st
from core.auth import authenticate
from core.session import clear_session,session_is_valid
from core.database import table_exists
from database.import_data import initialize_database
from ui.theme import apply_theme

st.set_page_config(page_title="SalesOps AI",page_icon="📊",layout="wide",initial_sidebar_state="expanded")
apply_theme()
if not table_exists("users"):
    initialize_database(overwrite=False,profile="mvp",seed=42)

if st.query_params.get("view") == "crm":
    from ui.crm_page import render_crm
    render_crm()
    st.stop()

session_expired="user" in st.session_state and not session_is_valid(st.session_state)
if "user" not in st.session_state or session_expired:
    if session_expired:clear_session(st.session_state)
    from ui.auth.login_page import render_login
    render_login(session_expired=session_expired)
    st.stop()

PAGES={"📊 Sales Intelligence":"pages.Sales_Intelligence","✨ AI Agent & Assistant":"pages.AI_Agent","📝 Requirements Studio":"pages.Requirements_Studio","⚙️ Workflow Studio":"pages.Workflow_Studio","🔌 Integration & RPA Hub":"pages.Integration_RPA","🛡️ Governance & Approvals":"pages.Governance","🎓 Citizen Developer Hub":"pages.Citizen_Developer_Hub","🧩 Power Platform Blueprint":"pages.Power_Platform_Blueprint"}
with st.sidebar:
    st.markdown('<div class="sidebar-logo"><div class="sidebar-logo-mark">S</div><div class="sidebar-brand">SalesOps AI</div></div><div class="sidebar-sub">Business Applications & Automation</div>',unsafe_allow_html=True)
    selected=st.radio("Navigation",list(PAGES),label_visibility="collapsed",key="navigation")
    st.markdown("<div style='height:24px'></div>",unsafe_allow_html=True)
    st.markdown(f'<div class="user-card"><div class="user-name">{st.session_state.user["display_name"]}</div><div class="user-role">{st.session_state.user["role"]}</div></div>',unsafe_allow_html=True)
    if st.button("Sign out",width="stretch"):clear_session(st.session_state);st.rerun()

importlib.import_module(PAGES[selected]).render(st.session_state.user)

