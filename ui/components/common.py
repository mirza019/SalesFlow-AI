import html
import streamlit as st

def header(title,subtitle):st.markdown(f'<div class="page-header"><div><div class="page-title">{html.escape(title)}</div><div class="page-subtitle">{html.escape(subtitle)}</div></div></div>',unsafe_allow_html=True)
def kpi(label,value,note="",icon="●",delta="",sentiment="neutral"):
    delta_html=f'<span class="kpi-delta delta-{html.escape(sentiment)}">{html.escape(delta)}</span> · ' if delta else ""
    st.markdown(f'<div class="card kpi"><div class="kpi-top"><div class="kpi-icon">{html.escape(icon)}</div><div class="kpi-label">{html.escape(label)}</div></div><div class="kpi-value">{html.escape(value)}</div><div class="kpi-note">{delta_html}{html.escape(note)}</div></div>',unsafe_allow_html=True)
def status(value):
    cls="green" if value in {"active","approved","succeeded","connected","tested"} else "red" if value in {"rejected","failed","error"} else "orange" if value in {"pending","paused"} else "purple"
    st.markdown(f'<span class="badge badge-{cls}">{html.escape(str(value).title())}</span>',unsafe_allow_html=True)
def card(title,body):st.markdown(f'<div class="card"><div class="section-title">{html.escape(title)}</div><div class="small-muted">{html.escape(body)}</div></div>',unsafe_allow_html=True)

