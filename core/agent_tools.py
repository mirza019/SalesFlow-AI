from __future__ import annotations
from datetime import date,timedelta
from pydantic import BaseModel,Field
from .database import query
from .kpis import dashboard_metrics,regional_performance

class LimitArgs(BaseModel):limit:int=Field(20,ge=1,le=100)
class DaysArgs(BaseModel):days:int=Field(30,ge=1,le=180)

def retrieve_sales_kpis(_:dict|None=None):return dashboard_metrics()
def find_overdue_opportunities(args:dict):
    a=LimitArgs.model_validate(args); return query("""SELECT o.opportunity_id,o.name,o.stage,o.expected_close_date,o.deal_value,o.currency,r.name sales_rep_name FROM sales_opportunities o JOIN sales_representatives r ON r.sales_rep_id=o.sales_rep_id WHERE o.stage NOT LIKE 'Closed%' AND date(o.expected_close_date)<date('now') ORDER BY date(o.expected_close_date) LIMIT ?""",(a.limit,))
def detect_missing_crm_data(args:dict):
    a=LimitArgs.model_validate(args); return query("SELECT opportunity_id,name,stage,deal_value FROM sales_opportunities WHERE name IS NULL OR stage IS NULL OR deal_value IS NULL OR deal_value<=0 LIMIT ?",(a.limit,))
def find_expiring_quotations(args:dict):
    a=DaysArgs.model_validate(args); return query("SELECT quotation_id,opportunity_id,expiration_date,total_amount,currency FROM quotations WHERE status IN ('Draft','Sent') AND date(expiration_date) BETWEEN date('now') AND date('now',?) ORDER BY expiration_date",(f'+{a.days} day',))
def compare_regional_performance(_:dict|None=None):return regional_performance().to_dict("records")
def prepare_follow_up_actions(args:dict):
    return [{"opportunity_id":x["opportunity_id"],"task":"Contact customer and review close plan","requires_approval":True} for x in find_overdue_opportunities(args)]

TOOLS={"retrieve_sales_kpis":retrieve_sales_kpis,"find_overdue_opportunities":find_overdue_opportunities,"detect_missing_crm_data":detect_missing_crm_data,"find_expiring_quotations":find_expiring_quotations,"compare_regional_performance":compare_regional_performance,"prepare_follow_up_actions":prepare_follow_up_actions}
def run_tool(name:str,args:dict|None=None):
    if name not in TOOLS:raise ValueError("Tool is not allowlisted")
    return TOOLS[name](args or {})
