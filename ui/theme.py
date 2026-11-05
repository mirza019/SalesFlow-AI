from pathlib import Path
import streamlit as st

def apply_theme():
    css=(Path(__file__).parent/"styles_premium.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)

