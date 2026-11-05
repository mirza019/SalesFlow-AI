from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
from .database import query

OPEN_STAGES=("Prospecting","Qualification","Needs Analysis","Proposal","Negotiation")

def _period(period: str, custom_start=None, custom_end=None):
    end=pd.Timestamp(custom_end or date.today())
    days={"Last 30 Days":30,"Last 90 Days":90,"Last 12 Months":365}.get(period,365)
    return pd.Timestamp(custom_start or end-timedelta(days=days)),end

def opportunity_frame(period="Last 12 Months",custom_start=None,custom_end=None,region="All regions") -> pd.DataFrame:
    start,end=_period(period,custom_start,custom_end)
    rows=query("""SELECT o.*, c.region, c.country,
      COALESCE((SELECT rate FROM exchange_rates e WHERE e.quote_currency=o.currency AND date(e.rate_date)<=date(o.created_date) ORDER BY date(e.rate_date) DESC LIMIT 1),1) fx_rate
      FROM sales_opportunities o JOIN customers c ON c.customer_id=o.customer_id
      WHERE date(o.created_date) BETWEEN date(?) AND date(?)""",(start.date().isoformat(),end.date().isoformat()))
    df=pd.DataFrame(rows)
    if not df.empty:
        df["deal_value_eur"]=df.deal_value/df.fx_rate.replace(0,1)
        df["weighted_value_eur"]=df.deal_value_eur*df.probability/100
        df["created_date"]=pd.to_datetime(df.created_date); df["expected_close_date"]=pd.to_datetime(df.expected_close_date)
        if region and region!="All regions":df=df[df.region.eq(region)]
    return df

def dashboard_metrics(period="Last 12 Months",custom_start=None,custom_end=None,region="All regions") -> dict:
    df=opportunity_frame(period,custom_start,custom_end,region); _,end=_period(period,custom_start,custom_end)
    if df.empty: return {k:0 for k in ["pipeline_value","weighted_pipeline","win_rate","overdue_opportunities","expiring_quotations"]}
    open_df=df[df.stage.isin(OPEN_STAGES)]; closed=df[df.stage.isin(["Closed Won","Closed Lost"])]
    exp=query("""SELECT COUNT(*) n FROM quotations q JOIN sales_opportunities o ON o.opportunity_id=q.opportunity_id JOIN customers c ON c.customer_id=o.customer_id
      WHERE q.status IN ('Draft','Sent') AND date(q.expiration_date) BETWEEN date(?) AND date(?) AND (?='All regions' OR c.region=?)""",(end.date().isoformat(),(end+timedelta(days=30)).date().isoformat(),region,region))[0]["n"]
    return {"pipeline_value":float(open_df.deal_value_eur.sum()),"weighted_pipeline":float(open_df.weighted_value_eur.sum()),"win_rate":float((closed.stage.eq('Closed Won').mean()*100) if len(closed) else 0),"overdue_opportunities":int(((open_df.expected_close_date<end)).sum()),"expiring_quotations":int(exp)}

def pipeline_by_month(period="Last 12 Months",region="All regions") -> pd.DataFrame:
    df=opportunity_frame(period,region=region)
    if df.empty:return pd.DataFrame(columns=["month","Pipeline Value","Weighted Pipeline"])
    df["month"]=df.created_date.dt.to_period("M").dt.to_timestamp()
    return df.groupby("month",as_index=False).agg(**{"Pipeline Value":("deal_value_eur","sum"),"Weighted Pipeline":("weighted_value_eur","sum")})

def stage_distribution(period="Last 12 Months",region="All regions") -> pd.DataFrame:
    df=opportunity_frame(period,region=region)
    if df.empty:return pd.DataFrame(columns=["stage","value"])
    mapped=df.stage.replace({"Needs Analysis":"Qualification","Closed Won":"Won","Closed Lost":"Closing","Prospecting":"Qualification"})
    return df.assign(stage=mapped).groupby("stage",as_index=False).deal_value_eur.sum().rename(columns={"deal_value_eur":"value"})

def regional_performance(period="Last 12 Months",region="All regions") -> pd.DataFrame:
    df=opportunity_frame(period,region=region)
    if df.empty:return pd.DataFrame(columns=["region","Pipeline Value","Weighted Pipeline"])
    return df.groupby("region",as_index=False).agg(**{"Pipeline Value":("deal_value_eur","sum"),"Weighted Pipeline":("weighted_value_eur","sum")})

def data_quality() -> dict:
    total=query("SELECT COUNT(*) n FROM sales_opportunities")[0]["n"]
    complete=query("SELECT COUNT(*) n FROM sales_opportunities WHERE customer_id IS NOT NULL AND sales_rep_id IS NOT NULL AND deal_value>0 AND stage IS NOT NULL")[0]["n"]
    contacts=query("SELECT COUNT(*) n FROM customer_contacts WHERE email IS NOT NULL AND email<>'' AND phone IS NOT NULL AND phone<>''")[0]["n"]
    contact_total=query("SELECT COUNT(*) n FROM customer_contacts")[0]["n"]
    active=query("SELECT COUNT(DISTINCT opportunity_id) n FROM sales_activities WHERE date(activity_date)>=date('now','-90 day')")[0]["n"]
    qcomplete=query("SELECT COUNT(*) n FROM quotations WHERE total_amount IS NOT NULL AND expiration_date IS NOT NULL")[0]["n"]
    qtotal=query("SELECT COUNT(*) n FROM quotations")[0]["n"]
    scores={"Customer completeness":100*contacts/max(contact_total,1),"Opportunity validity":100*complete/max(total,1),"Recent activity coverage":100*active/max(total,1),"Quotation completeness":100*qcomplete/max(qtotal,1)}
    return {"score":sum(scores.values())/len(scores),"components":scores,"primary_problem":min(scores,key=scores.get),"issue_count":query("SELECT COUNT(*) n FROM crm_data_quality_issues")[0]["n"] if query("SELECT 1 FROM sqlite_master WHERE type='table' AND name='crm_data_quality_issues'") else 0}

def available_regions()->list[str]:
    return [x["region"] for x in query("SELECT DISTINCT region FROM customers ORDER BY region")]

def opportunities_requiring_attention(region="All regions",limit=25)->pd.DataFrame:
    sql="""SELECT o.opportunity_id, c.customer_name AS customer, c.region,
      ROUND(o.deal_value / COALESCE((SELECT rate FROM exchange_rates e WHERE e.quote_currency=o.currency AND date(e.rate_date)<=date(o.created_date) ORDER BY date(e.rate_date) DESC LIMIT 1),1),2) AS deal_value_eur,
      o.stage AS sales_stage, MAX(a.activity_date) AS last_activity,
      CASE WHEN date(o.expected_close_date)<date('now') THEN 'Overdue close'
           WHEN MAX(a.activity_date) IS NULL OR date(MAX(a.activity_date))<date('now','-30 day') THEN 'No recent activity'
           ELSE 'Monitor' END AS risk
      FROM sales_opportunities o JOIN customers c ON c.customer_id=o.customer_id
      LEFT JOIN sales_activities a ON a.opportunity_id=o.opportunity_id
      WHERE o.stage NOT LIKE 'Closed%' AND (?='All regions' OR c.region=?)
      GROUP BY o.opportunity_id,c.customer_name,c.region,o.deal_value,o.currency,o.created_date,o.stage,o.expected_close_date
      HAVING risk<>'Monitor' ORDER BY deal_value_eur DESC LIMIT ?"""
    frame=pd.DataFrame(query(sql,(region,region,limit)))
    if not frame.empty:frame["recommended_action"]=frame.risk.map({"Overdue close":"Review close plan and contact customer","No recent activity":"Prepare representative follow-up"})
    return frame
