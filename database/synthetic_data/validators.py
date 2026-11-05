from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
from .business_rules import money

PKS={"customers":"customer_id","customer_contacts":"contact_id","sales_representatives":"sales_rep_id","products_services":"product_id","sales_opportunities":"opportunity_id","opportunity_line_items":"opportunity_line_item_id","quotations":"quotation_id","quotation_line_items":"quotation_line_item_id","sales_orders":"order_id","order_line_items":"order_line_item_id","sales_activities":"activity_id","approval_requests":"approval_request_id","sales_targets":"target_id","exchange_rates":"exchange_rate_id","crm_data_quality_issues":"issue_id","workflow_definitions":"workflow_definition_id","workflow_executions":"workflow_execution_id","rpa_execution_logs":"rpa_execution_log_id"}
FKS=[("customer_contacts","customer_id","customers","customer_id"),("sales_opportunities","customer_id","customers","customer_id"),("sales_opportunities","sales_rep_id","sales_representatives","sales_rep_id"),("opportunity_line_items","opportunity_id","sales_opportunities","opportunity_id"),("opportunity_line_items","product_id","products_services","product_id"),("quotations","opportunity_id","sales_opportunities","opportunity_id"),("quotation_line_items","quotation_id","quotations","quotation_id"),("quotation_line_items","product_id","products_services","product_id"),("sales_orders","quotation_id","quotations","quotation_id"),("sales_orders","opportunity_id","sales_opportunities","opportunity_id"),("order_line_items","order_id","sales_orders","order_id"),("order_line_items","product_id","products_services","product_id"),("sales_activities","opportunity_id","sales_opportunities","opportunity_id"),("sales_targets","sales_rep_id","sales_representatives","sales_rep_id"),("workflow_executions","workflow_definition_id","workflow_definitions","workflow_definition_id"),("rpa_execution_logs","workflow_execution_id","workflow_executions","workflow_execution_id")]

def validate_tables(tables: dict[str,pd.DataFrame], expected: dict[str,int], ground_truth: pd.DataFrame|None=None) -> dict:
    checks=[]
    def add(name,passed,details=""): checks.append({"check":name,"passed":bool(passed),"details":details})
    for name,count in expected.items(): add(f"row_count:{name}",name in tables and len(tables[name])==count,f"expected={count}, actual={len(tables.get(name,[]))}")
    for name,pk in PKS.items():
        if name in tables: add(f"primary_key:{name}",tables[name][pk].notna().all() and tables[name][pk].is_unique)
    for child,col,parent,pcol in FKS:
        if child in tables and parent in tables: add(f"foreign_key:{child}.{col}",tables[child][col].isin(tables[parent][pcol]).all())
    q=tables["quotations"]; add("quotation_date_sequence",(q.expiration_date>q.created_date).all())
    o=tables["sales_orders"]; accepted=set(q.loc[q.status=="Accepted","quotation_id"]); add("orders_reference_accepted_quotations",o.quotation_id.isin(accepted).all())
    opp=tables["sales_opportunities"]; add("opportunity_date_sequence",(opp.expected_close_date>=opp.created_date).all())
    stage={"Prospecting":10,"Qualification":25,"Needs Analysis":40,"Proposal":60,"Negotiation":80,"Closed Won":100,"Closed Lost":0}; add("stage_probability_consistency",(opp.probability==opp.stage.map(stage)).all())
    valid={"EUR","USD","GBP","INR","AED","BRL"}; currency_cols=[(n,c) for n,c in [("customers","currency"),("sales_opportunities","currency"),("quotations","currency"),("sales_orders","currency")] if n in tables]; add("valid_currencies",all(tables[n][c].isin(valid).all() for n,c in currency_cols))
    for name in ["opportunity_line_items","quotation_line_items","order_line_items"]:
        d=tables[name]
        calculated=pd.Series([money(q*p*(1-disc/100)) for q,p,disc in zip(d.quantity,d.unit_price,d.discount_percent)],index=d.index)
        add(f"monetary_calculation:{name}",(calculated-d.line_total).abs().max()<=0.001)
    if ground_truth is not None: add("ground_truth_count",len(ground_truth)==expected["crm_data_quality_issues"]); add("ground_truth_required_fields",ground_truth.notna().all().all())
    return {"passed":all(x["passed"] for x in checks),"checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),"checks":checks}

def save_validation_reports(report:dict,output_dir:Path)->None:
    reports=output_dir/"reports"; reports.mkdir(parents=True,exist_ok=True)
    (reports/"data_quality_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    relation={"passed":all(c["passed"] for c in report["checks"] if c["check"].startswith("foreign_key:")),"checks":[c for c in report["checks"] if c["check"].startswith("foreign_key:")]}
    (reports/"relationship_validation.json").write_text(json.dumps(relation,indent=2),encoding="utf-8")

