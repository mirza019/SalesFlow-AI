import streamlit as st
from core.gemini_agent import ask
from ui.components.common import header
def render(user):
    header("AI Agent & Assistant","Ask grounded sales questions and keep verified evidence separate from AI interpretation.")
    prompt_cols=st.columns(5)
    prompts=["Which opportunities need attention?","Why did the win rate change?","Identify missing CRM information.","Recommend actions for this week's pipeline.","Create an overdue follow-up workflow."]
    for col,q in zip(prompt_cols,prompts):
        if col.button(q,key=q,width="stretch"):st.session_state.agent_prompt=q
    workspace=st.columns([3,2],gap="large")
    with workspace[0]:
        with st.container(border=True):
            st.markdown('<div class="section-title">Conversation</div><div class="section-subtitle">Responses use only allowlisted database tools.</div>',unsafe_allow_html=True)
            history=st.session_state.setdefault("agent_chat",[])
            if not history:st.info("Choose a suggested prompt or ask a sales operations question.")
            for m in history:
                with st.chat_message(m["role"]):st.markdown(m["content"])
            prompt=st.chat_input("Ask SalesOps AI…") or st.session_state.pop("agent_prompt",None)
            if prompt:
                history.append({"role":"user","content":prompt});result=ask(user,prompt);history.append({"role":"assistant","content":result["answer"]});st.session_state.agent_result=result;st.rerun()
    with workspace[1]:
        with st.container(border=True):
            st.markdown('<div class="section-title">Verified evidence</div><div class="section-subtitle">Deterministic output from the selected controlled tool.</div>',unsafe_allow_html=True)
            result=st.session_state.get("agent_result")
            if result:
                st.caption(f"Source: {result['tool']} · {result['source']}");st.dataframe(result["verified_data"],width="stretch",hide_index=True)
            else:st.info("Evidence will appear after the first question.")
            st.markdown('<div class="callout"><b>Governance</b><br>AI interpretation is advisory. Any CRM-changing action requires an approval bound to the exact target and payload.</div>',unsafe_allow_html=True)
