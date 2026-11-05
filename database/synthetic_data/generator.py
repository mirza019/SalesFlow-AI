from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

from .business_rules import STAGE_PROBABILITY, money
from .config import COUNTRIES, CURRENCIES, REGIONS, GenerationConfig
from .relationships import distribute, parent_ids

COMPANY_A = ["Apex", "Atlas", "BluePeak", "Core", "Delta", "Evergreen", "Frontier", "Helios", "Ion", "Keystone", "Nova", "Orion", "Pioneer", "Quantum", "Vertex"]
COMPANY_B = ["Engineering", "Industries", "Manufacturing", "Energy", "Systems", "Infrastructure", "Automation", "Resources"]
FIRST = ["Alex", "Avery", "Casey", "Dana", "Emery", "Jordan", "Kai", "Morgan", "Noor", "Riley", "Sam", "Taylor"]
LAST = ["Bauer", "Brooks", "Costa", "Evans", "Gupta", "Khan", "Meyer", "Patel", "Reed", "Silva", "Smith", "Weber"]

class SyntheticSalesGenerator:
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.counts = config.counts
        self.start = pd.Timestamp(config.start_date)
        self.end = pd.Timestamp(config.end_date)
        self.tables: dict[str, pd.DataFrame] = {}

    def ids(self, prefix: str, n: int) -> list[str]:
        return [f"{prefix}{i:06d}" for i in range(1, n + 1)]

    def dates(self, n: int, start=None, end=None) -> pd.Series:
        lo, hi = pd.Timestamp(start or self.start), pd.Timestamp(end or self.end)
        return pd.to_datetime(self.rng.integers(lo.value // 86_400_000_000_000, hi.value // 86_400_000_000_000 + 1, n), unit="D")

    def generate(self) -> dict[str, pd.DataFrame]:
        self._people_and_catalog(); self._pipeline(); self._quotations_orders()
        self._activities_approvals_targets(); self._operations()
        return self.tables

    def _people_and_catalog(self) -> None:
        n = self.counts["customers"]
        countries = self.rng.choice(COUNTRIES, n, p=[.25, .23, .14, .16, .10, .12])
        self.tables["customers"] = pd.DataFrame({
            "customer_id": self.ids("CUS-", n),
            "customer_name": [f"{COMPANY_A[i % len(COMPANY_A)]} {COMPANY_B[(i // len(COMPANY_A)) % len(COMPANY_B)]} {i+1}" for i in range(n)],
            "country": countries, "region": [REGIONS[x] for x in countries],
            "segment": self.rng.choice(["Enterprise", "Mid-Market", "Strategic"], n, p=[.52,.33,.15]),
            "industry": self.rng.choice(["Power", "Oil & Gas", "Chemicals", "Mining", "Manufacturing", "Utilities"], n),
            "currency": [CURRENCIES[x] for x in countries], "created_at": self.dates(n), "is_active": self.rng.random(n) > .04,
        })
        n = self.counts["customer_contacts"]
        cust = parent_ids("CUS-", len(self.tables["customers"]), n, self.rng)
        self.tables["customer_contacts"] = pd.DataFrame({
            "contact_id": self.ids("CON-", n), "customer_id": cust,
            "first_name": [FIRST[i % len(FIRST)] for i in range(n)], "last_name": [LAST[(i*7) % len(LAST)] for i in range(n)],
            "job_title": self.rng.choice(["Procurement Manager", "Plant Director", "Service Manager", "Engineer", "CFO"], n),
            "email": [f"contact{i+1}@example-{(i%997)+1}.test" for i in range(n)],
            "phone": [f"+00-555-{i+1:07d}" for i in range(n)], "is_primary": np.array([i % 3 == 0 for i in range(n)]),
        })
        n = self.counts["sales_representatives"]
        rep_countries = np.resize(np.array(COUNTRIES), n); self.rng.shuffle(rep_countries)
        self.tables["sales_representatives"] = pd.DataFrame({
            "sales_rep_id": self.ids("REP-", n), "name": [f"{FIRST[i%12]} {LAST[(i*5)%12]} {i+1}" for i in range(n)],
            "email": [f"rep{i+1}@salesflow.example" for i in range(n)], "country": rep_countries,
            "region": [REGIONS[x] for x in rep_countries], "hire_date": self.dates(n, "2015-01-01", "2024-12-31"), "is_active": True,
        })
        n = self.counts["products_services"]
        cats = self.rng.choice(["Industrial Equipment", "Spare Parts", "Maintenance Service", "Modernization Project", "Service Contract", "Long-term Service Agreement"], n)
        ranges = {"Industrial Equipment": (50_000,2_000_000), "Spare Parts": (100,75_000), "Maintenance Service": (5_000,250_000), "Modernization Project": (100_000,5_000_000), "Service Contract": (20_000,500_000), "Long-term Service Agreement": (250_000,8_000_000)}
        prices = [money(self.rng.uniform(*ranges[c])) for c in cats]
        self.tables["products_services"] = pd.DataFrame({"product_id":self.ids("PRD-",n),"sku":[f"SKU-{i:05d}" for i in range(1,n+1)],"name":[f"{c} {i+1}" for i,c in enumerate(cats)],"category":cats,"list_price":prices,"standard_cost":[money(p*self.rng.uniform(.45,.72)) for p in prices],"currency":"EUR","is_active":True})

    def _pipeline(self) -> None:
        n = self.counts["sales_opportunities"]
        created = self.dates(n, self.start, self.end - timedelta(days=30))
        cycles = self.rng.integers(30, 550, n)
        stages = self.rng.choice(list(STAGE_PROBABILITY), n, p=[.12,.15,.14,.18,.16,.15,.10])
        customer_ids = parent_ids("CUS-", len(self.tables["customers"]), n, self.rng)
        rep_ids = parent_ids("REP-", len(self.tables["sales_representatives"]), n, self.rng)
        cust_currency = self.tables["customers"].set_index("customer_id")["currency"]
        self.tables["sales_opportunities"] = pd.DataFrame({
            "opportunity_id":self.ids("OPP-",n),"customer_id":customer_ids,"sales_rep_id":rep_ids,
            "name":[f"Industrial sales opportunity {i+1}" for i in range(n)],"stage":stages,
            "probability":[STAGE_PROBABILITY[x] for x in stages],"created_date":created,
            "expected_close_date":created + pd.to_timedelta(cycles,unit="D"),
            "actual_close_date":[(d + timedelta(days=int(c))) if s.startswith("Closed") else pd.NaT for d,c,s in zip(created,cycles,stages)],
            "currency":[cust_currency[x] for x in customer_ids],"deal_value":0.0,"source":self.rng.choice(["Direct","Partner","Referral","Tender","Existing Customer"],n),
            "last_stage_change_date":created + pd.to_timedelta((cycles*self.rng.uniform(.2,.9,n)).astype(int),unit="D"),
        })
        line_n = self.counts["opportunity_line_items"]
        counts = distribute(line_n,n,self.rng); opp_index=np.repeat(np.arange(n),counts)
        product_index=self.rng.integers(0,len(self.tables["products_services"]),line_n)
        qty=self.rng.integers(1,12,line_n); price=self.tables["products_services"].iloc[product_index]["list_price"].to_numpy()
        discount=np.round(self.rng.beta(2,8,line_n)*35,2)
        totals=np.array([money(q*p*(1-d/100)) for q,p,d in zip(qty,price,discount)])
        self.tables["opportunity_line_items"]=pd.DataFrame({"opportunity_line_item_id":self.ids("OLI-",line_n),"opportunity_id":self.tables["sales_opportunities"].iloc[opp_index]["opportunity_id"].to_numpy(),"product_id":self.tables["products_services"].iloc[product_index]["product_id"].to_numpy(),"quantity":qty,"unit_price":price,"discount_percent":discount,"line_total":totals})
        totals_by_opp=self.tables["opportunity_line_items"].groupby("opportunity_id")["line_total"].sum()
        self.tables["sales_opportunities"]["deal_value"]=self.tables["sales_opportunities"]["opportunity_id"].map(totals_by_opp).map(money)

    def _quotations_orders(self) -> None:
        opp=self.tables["sales_opportunities"]; n=self.counts["quotations"]
        opp_idx=np.arange(n)%len(opp); self.rng.shuffle(opp_idx)
        qcreated=opp.iloc[opp_idx]["created_date"].reset_index(drop=True)+pd.to_timedelta(self.rng.integers(3,90,n),unit="D")
        statuses=np.array(["Accepted"]*min(self.counts["sales_orders"],n)+["Draft","Sent","Expired","Rejected"]*n)[:n]; self.rng.shuffle(statuses)
        self.tables["quotations"]=pd.DataFrame({"quotation_id":self.ids("QUO-",n),"opportunity_id":opp.iloc[opp_idx]["opportunity_id"].to_numpy(),"quotation_number":[f"Q-{2023+(i%4)}-{i+1:06d}" for i in range(n)],"status":statuses,"created_date":qcreated,"expiration_date":qcreated+pd.to_timedelta(self.rng.integers(30,121,n),unit="D"),"currency":opp.iloc[opp_idx]["currency"].to_numpy(),"subtotal":0.0,"discount_amount":0.0,"total_amount":0.0,"version":self.rng.integers(1,4,n)})
        ln=self.counts["quotation_line_items"]; counts=distribute(ln,n,self.rng); qidx=np.repeat(np.arange(n),counts)
        pidx=self.rng.integers(0,len(self.tables["products_services"]),ln); qty=self.rng.integers(1,10,ln); price=self.tables["products_services"].iloc[pidx]["list_price"].to_numpy(); disc=np.round(self.rng.beta(2,8,ln)*35,2); total=np.array([money(q*p*(1-d/100)) for q,p,d in zip(qty,price,disc)])
        self.tables["quotation_line_items"]=pd.DataFrame({"quotation_line_item_id":self.ids("QLI-",ln),"quotation_id":self.tables["quotations"].iloc[qidx]["quotation_id"].to_numpy(),"product_id":self.tables["products_services"].iloc[pidx]["product_id"].to_numpy(),"quantity":qty,"unit_price":price,"discount_percent":disc,"line_total":total})
        grp=self.tables["quotation_line_items"].groupby("quotation_id").agg(subtotal=("line_total","sum"),discount_amount=("line_total",lambda x:0.0))
        self.tables["quotations"]["subtotal"]=self.tables["quotations"]["quotation_id"].map(grp.subtotal).map(money); self.tables["quotations"]["total_amount"]=self.tables["quotations"]["subtotal"]
        n=self.counts["sales_orders"]; accepted=self.tables["quotations"][self.tables["quotations"].status=="Accepted"].head(n).reset_index(drop=True)
        if len(accepted)<n: raise ValueError("Profile requires more orders than quotations")
        order_date=accepted.created_date+pd.to_timedelta(self.rng.integers(5,60,n),unit="D")
        self.tables["sales_orders"]=pd.DataFrame({"order_id":self.ids("ORD-",n),"quotation_id":accepted.quotation_id,"opportunity_id":accepted.opportunity_id,"order_number":[f"SO-{i+1:07d}" for i in range(n)],"order_date":order_date,"status":self.rng.choice(["Confirmed","In Fulfillment","Delivered","Completed"],n),"currency":accepted.currency,"total_amount":accepted.total_amount,"amendment_reason":""})
        ln=self.counts["order_line_items"]; counts=distribute(ln,n,self.rng); rows=[]; oid=1
        qlines=self.tables["quotation_line_items"]
        for order_idx,count in enumerate(counts):
            qid=accepted.iloc[order_idx].quotation_id; src=qlines[qlines.quotation_id==qid]
            for j in range(count):
                s=src.iloc[j%len(src)]; rows.append((f"ORI-{oid:06d}",f"ORD-{order_idx+1:06d}",s.product_id,s.quantity,s.unit_price,s.discount_percent,s.line_total)); oid+=1
        self.tables["order_line_items"]=pd.DataFrame(rows,columns=["order_line_item_id","order_id","product_id","quantity","unit_price","discount_percent","line_total"])

    def _activities_approvals_targets(self) -> None:
        n=self.counts["sales_activities"]; oppids=parent_ids("OPP-",len(self.tables["sales_opportunities"]),n,self.rng); oppmap=self.tables["sales_opportunities"].set_index("opportunity_id"); dates=self.dates(n)
        types=self.rng.choice(["Call","Email","Meeting","Site Visit","Follow-up"],n)
        due=dates+pd.to_timedelta(self.rng.integers(1,31,n),unit="D")
        completed=pd.Series(due+pd.to_timedelta(self.rng.integers(-3,4,n),unit="D"))
        completed[self.rng.random(n)<=.22]=pd.NaT
        self.tables["sales_activities"]=pd.DataFrame({"activity_id":self.ids("ACT-",n),"opportunity_id":oppids,"sales_rep_id":[oppmap.loc[x].sales_rep_id for x in oppids],"activity_type":types,"subject":[f"{t} for customer engagement" for t in types],"activity_date":dates,"due_date":due,"completed_date":completed,"status":["Completed" if not pd.isna(x) else "Open" for x in completed]})
        n=self.counts["approval_requests"]; q=self.tables["quotations"].iloc[np.arange(n)%len(self.tables["quotations"])].reset_index(drop=True); req=q.created_date+pd.to_timedelta(1,unit="D")
        self.tables["approval_requests"]=pd.DataFrame({"approval_request_id":self.ids("APR-",n),"quotation_id":q.quotation_id,"opportunity_id":q.opportunity_id,"approval_type":"High Discount","requested_at":req,"resolved_at":req+pd.to_timedelta(self.rng.integers(1,15,n),unit="D"),"status":self.rng.choice(["Approved","Rejected","Pending"],n,p=[.72,.18,.10]),"requested_discount_percent":np.round(self.rng.uniform(15.01,35,n),2)})
        n=self.counts["sales_targets"]; reps=self.tables["sales_representatives"].sales_rep_id.to_numpy(); periods=pd.date_range(self.start.to_period("M").start_time,self.end.to_period("M").start_time,freq="MS")
        self.tables["sales_targets"]=pd.DataFrame({"target_id":self.ids("TGT-",n),"sales_rep_id":[reps[i%len(reps)] for i in range(n)],"period_start":[periods[(i//len(reps))%len(periods)] for i in range(n)],"period_end":[periods[(i//len(reps))%len(periods)]+pd.offsets.MonthEnd(1) for i in range(n)],"currency":"EUR","target_amount":[money(self.rng.uniform(250_000,2_500_000)) for _ in range(n)]})
        n=self.counts["exchange_rates"]; curr=list(set(CURRENCIES.values())); dates=self.dates(n); base={"EUR":1,"USD":1.09,"GBP":.86,"INR":90.2,"AED":4.0,"BRL":5.4}
        cs=np.resize(curr,n); self.rng.shuffle(cs)
        self.tables["exchange_rates"]=pd.DataFrame({"exchange_rate_id":self.ids("FX-",n),"rate_date":dates,"base_currency":"EUR","quote_currency":cs,"rate":[round(base[c]*self.rng.uniform(.94,1.06),6) for c in cs],"source":"Synthetic historical reference"})

    def _operations(self) -> None:
        n=self.counts["workflow_definitions"]; self.tables["workflow_definitions"]=pd.DataFrame({"workflow_definition_id":self.ids("WFD-",n),"name":[f"Sales workflow {i+1}" for i in range(n)],"category":self.rng.choice(["Approval","Follow-up","Data Quality","Quotation","Order"],n),"version":1,"is_active":True,"synthetic_record":True})
        n=self.counts["workflow_executions"]; defs=parent_ids("WFD-",len(self.tables["workflow_definitions"]),n,self.rng); started=self.dates(n); duration=self.rng.integers(5,7200,n)
        self.tables["workflow_executions"]=pd.DataFrame({"workflow_execution_id":self.ids("WFE-",n),"workflow_definition_id":defs,"started_at":started,"completed_at":started+pd.to_timedelta(duration,unit="s"),"status":self.rng.choice(["Succeeded","Failed","Cancelled"],n,p=[.88,.09,.03]),"synthetic_record":True})
        n=self.counts["rpa_execution_logs"]; wf=parent_ids("WFE-",len(self.tables["workflow_executions"]),n,self.rng); started=self.dates(n)
        self.tables["rpa_execution_logs"]=pd.DataFrame({"rpa_execution_log_id":self.ids("RPA-",n),"workflow_execution_id":wf,"robot_name":self.rng.choice(["CRM Extract","CRM Update","Quotation Export","Follow-up Creator"],n),"started_at":started,"completed_at":started+pd.to_timedelta(self.rng.integers(10,1800,n),unit="s"),"outcome":self.rng.choice(["Success","Business Exception","System Error"],n,p=[.9,.07,.03]),"records_processed":self.rng.integers(1,500,n),"synthetic_record":True})

    def fingerprint(self) -> str:
        h=hashlib.sha256()
        for name in sorted(self.tables): h.update(name.encode()); h.update(pd.util.hash_pandas_object(self.tables[name],index=True).values.tobytes())
        return h.hexdigest()

    def export(self, formats: str, overwrite: bool) -> dict:
        out=self.config.output_dir
        selected=[formats] if formats!="both" else ["csv","parquet"]
        targets=[out/fmt/f"{name}.{'csv' if fmt=='csv' else 'parquet'}" for fmt in selected for name in self.tables]
        existing=[p for p in targets if p.exists()]
        if existing and not overwrite: raise FileExistsError(f"Output exists: {existing[0]}; pass --overwrite")
        for p in targets: p.parent.mkdir(parents=True,exist_ok=True)
        for name,df in self.tables.items():
            if "csv" in selected: df.to_csv(out/"csv"/f"{name}.csv",index=False,date_format="%Y-%m-%dT%H:%M:%S")
            if "parquet" in selected: df.to_parquet(out/"parquet"/f"{name}.parquet",index=False)
        manifest={"profile":self.config.profile,"seed":self.config.seed,"generated_at":pd.Timestamp.now(tz="UTC").isoformat(),"record_counts":{n:len(d) for n,d in self.tables.items()},"total_records":sum(map(len,self.tables.values())),"fingerprint":self.fingerprint(),"formats":selected}
        (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        return manifest
