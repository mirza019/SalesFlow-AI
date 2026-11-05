from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st

from core.auth import authenticate
from core.session import establish_session

EMAIL_RE=re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def _styles()->None:
    css=(Path(__file__).parent/"login_styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

def _brand_panel()->None:
    st.markdown("""
    <section class="login-brand">
      <div class="login-logo"><span>S</span><strong>SalesOps AI</strong></div>
      <div class="login-kicker">BUSINESS APPLICATIONS · AGENTS · AUTOMATION</div>
      <h1>Smarter Sales Operations.<br><em>Powered by AI.</em></h1>
      <p class="login-lead">Turn business insights into intelligent decisions, connected workflows, and automated actions—all in one secure workspace.</p>
      <div class="capability-grid">
        <div class="capability"><b>✦</b><span><strong>AI-Powered Intelligence</strong><small>Transform sales data into actionable business insights.</small></span></div>
        <div class="capability"><b>↻</b><span><strong>Intelligent Automation</strong><small>Create and manage workflows with AI assistance.</small></span></div>
        <div class="capability"><b>⌘</b><span><strong>Connected Applications</strong><small>Integrate sales systems and automate repetitive work.</small></span></div>
      </div>
      <div class="preview-card" aria-label="Decorative product preview with illustrative data">
        <div class="preview-bar"><span><i></i> Sales Intelligence</span><small>Illustrative preview</small></div>
        <div class="preview-kpis"><div><small>Pipeline Value</small><strong>€24.8M</strong><em>↗ 8.2%</em></div><div><small>Win Rate</small><strong>34.7%</strong><em>↗ 2.4%</em></div></div>
        <div class="preview-main">
          <div class="mini-chart"><div><strong>Pipeline trend</strong><small>Last 6 months</small></div><svg viewBox="0 0 420 100" role="img" aria-label="Illustrative rising pipeline trend"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#60A5FA" stop-opacity=".32"/><stop offset="1" stop-color="#60A5FA" stop-opacity="0"/></linearGradient></defs><path d="M5 82 C55 75 65 65 105 68 S165 48 205 54 S265 32 305 38 S365 15 415 20 L415 98 L5 98Z" fill="url(#area)"/><path d="M5 82 C55 75 65 65 105 68 S165 48 205 54 S265 32 305 38 S365 15 415 20" fill="none" stroke="#2563EB" stroke-width="4" stroke-linecap="round"/></svg></div>
          <div class="preview-side"><div><small>✦ AI Sales Insight</small><strong>12 opportunities may require follow-up this week.</strong></div><div><small>Sales Automation</small><strong><i></i> Workflow preview · Ready</strong></div></div>
        </div>
      </div>
    </section>""",unsafe_allow_html=True)

def render_login(*,session_expired:bool=False)->None:
    _styles()
    st.markdown('<span class="login-shell-anchor"></span>',unsafe_allow_html=True)
    left,right=st.columns([1.15,.85],gap=None,vertical_alignment="center")
    with left:_brand_panel()
    with right:
        st.markdown('<div class="auth-heading"><div class="mobile-logo"><span>S</span><strong>SalesOps AI</strong></div><h2>Welcome back</h2><p>Sign in to your SalesOps AI workspace.</p></div>',unsafe_allow_html=True)
        if session_expired:st.warning("Your session has expired. Please sign in again.")
        with st.form("login",clear_on_submit=False,border=False):
            identity=st.text_input("Work Email",placeholder="name@company.com",autocomplete="username",key="login_identity")
            password=st.text_input("Password",type="password",autocomplete="current-password",key="login_password")
            submitted=st.form_submit_button("Sign In to Workspace",type="primary",width="stretch")
        if submitted:
            if "@" in identity and not EMAIL_RE.fullmatch(identity):
                st.error("Enter a valid work email address.")
            elif not identity.strip() or not password:
                st.error("Enter your work email and password.")
            else:
                try:user=authenticate(identity,password)
                except Exception:user=None;st.error("The sign-in service is temporarily unavailable.")
                if user:
                    establish_session(st.session_state,user);st.rerun()
                elif not st.session_state.get("service_error_shown"):
                    st.error("Unable to sign in. Please check your credentials.")
        st.markdown('<div class="trust-line"><span>● Protected workspace</span><span>● Role-based access</span><span>● Auditable actions</span></div>',unsafe_allow_html=True)
        demo_password=os.getenv("SALESOPS_DEMO_PASSWORD","salesops-demo")
        with st.popover("💡 View demo accounts",width="stretch"):
            st.markdown("**Choose a demonstration role**")
            st.caption("Use the email alias or short username. These accounts contain synthetic portfolio data only.")
            st.table({"Work email":["admin@salesops.local","manager@salesops.local","builder@salesops.local"],"Password":[demo_password]*3,"Role":["Administrator","Sales Manager","Citizen Developer"]})
        crm_url=os.getenv("CRM_WEB_URL","?view=crm")
        st.markdown('<div class="crm-entry-label">Open the separate CRM simulator without signing in.</div>',unsafe_allow_html=True)
        st.link_button("↗ Go to CRM",crm_url,width="content")
