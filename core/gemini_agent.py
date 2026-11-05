from __future__ import annotations
import json,os
from pathlib import Path
from dotenv import load_dotenv
from .agent_tools import run_tool
from .database import execute

ENV_PATH=Path(__file__).resolve().parents[1]/".env"
load_dotenv(ENV_PATH,override=True)

def _safe_error(exc:Exception)->str:
    message=str(exc).lower()
    if "reported as leaked" in message:return "Google rejected the configured API key because it was reported as leaked. Revoke it and create a new key."
    if "api key not valid" in message or "invalid api key" in message:return "The configured Gemini API key is invalid. Check GEMINI_API_KEY in .env."
    if "quota" in message or "resource_exhausted" in message:return "The Gemini quota is currently exhausted. Check the project's quota or retry after reset."
    if "not found" in message and "model" in message:return f"The configured Gemini model '{os.getenv('GEMINI_MODEL','gemini-2.0-flash')}' is unavailable for this API key."
    return f"Gemini request failed ({type(exc).__name__}). Check the configured key, model access, and network connection."

def _select_tool(prompt:str):
    p=prompt.lower()
    if "overdue" in p:return "find_overdue_opportunities",{"limit":20}
    if "expir" in p and "quot" in p:return "find_expiring_quotations",{"days":30}
    if "missing" in p or "quality" in p:return "detect_missing_crm_data",{"limit":20}
    if "region" in p:return "compare_regional_performance",{}
    if "follow" in p:return "prepare_follow_up_actions",{"limit":20}
    return "retrieve_sales_kpis",{}

def ask(user:dict,prompt:str)->dict:
    # Streamlit keeps imported modules alive between reruns. Reload local
    # configuration so a rotated key takes effect without a server restart.
    load_dotenv(ENV_PATH,override=True)
    tool,args=_select_tool(prompt); verified=run_tool(tool,args)
    api_key=os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client=genai.Client(api_key=api_key)
            instruction="You are a sales operations analyst. Explain only the verified JSON evidence. Separate findings, business implications, and recommendations. Do not claim any CRM action was executed. Mention relevant opportunity IDs."
            response=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-2.0-flash"),contents=f"{instruction}\nQuestion: {prompt}\nVerified tool: {tool}\nVerified data: {json.dumps(verified,default=str)[:30000]}")
            answer=response.text
            source="Gemini interpretation"
        except Exception as exc:
            answer=f"AI interpretation is unavailable. {_safe_error(exc)} Verified database evidence is still shown below."
            source="Verified-data fallback"
    else:
        count=len(verified) if isinstance(verified,list) else len(verified)
        answer=f"Gemini is not configured. The allowlisted `{tool}` tool returned {count} verified result fields/records. Review the evidence below; proposed CRM changes still require approval."
        source="Verified-data fallback"
    execute("INSERT INTO conversations(username,role,content) VALUES(?,?,?)",(user["username"],"user",prompt))
    execute("INSERT INTO conversations(username,role,content) VALUES(?,?,?)",(user["username"],"assistant",answer))
    return {"answer":answer,"verified_data":verified,"tool":tool,"source":source}

