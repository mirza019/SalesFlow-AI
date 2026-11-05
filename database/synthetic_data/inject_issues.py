from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ISSUE_PLAN = [
    ("quotations", "total_amount", "missing_quotation_value", "high", "Recalculate from quotation line items"),
    ("customers", "customer_name", "duplicate_customer_name", "medium", "Merge or mark the duplicate customer"),
    ("customer_contacts", "email", "missing_contact_detail", "medium", "Obtain and validate an email address"),
    ("sales_opportunities", "stage", "outdated_opportunity_stage", "high", "Review activity and update the stage"),
    ("sales_activities", "due_date", "overdue_follow_up", "high", "Complete or reschedule the follow-up"),
    ("quotations", "expiration_date", "expired_quotation", "medium", "Renew or close the quotation"),
    ("quotation_line_items", "discount_percent", "invalid_discount", "high", "Request approval or restore allowed discount"),
    ("sales_opportunities", "currency", "currency_mismatch", "high", "Align with the customer commercial currency"),
    ("sales_opportunities", "deal_value", "inconsistent_opportunity_value", "high", "Recalculate from opportunity line items"),
    ("sales_activities", "activity_date", "incorrect_date_format", "medium", "Parse and normalize the date"),
]

def inject_issues(tables: dict[str, pd.DataFrame], count: int, rng: np.random.Generator, output_dir: Path, formats: str, overwrite: bool) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    corrupted: dict[str, pd.DataFrame] = {}
    records: list[dict] = []
    timestamp = pd.Timestamp.now(tz="UTC").isoformat()
    for i in range(count):
        dataset, column, kind, severity, resolution = ISSUE_PLAN[i % len(ISSUE_PLAN)]
        if dataset not in corrupted:
            corrupted[dataset] = tables[dataset].copy()
            # Raw CRM extracts deliberately allow malformed dates. Serialize all
            # datetime columns first so a bad string can coexist in staging data.
            for date_column in corrupted[dataset].select_dtypes(include=["datetime", "datetimetz"]).columns:
                corrupted[dataset][date_column] = corrupted[dataset][date_column].dt.strftime("%Y-%m-%dT%H:%M:%S")
        df = corrupted[dataset]; row = (i // len(ISSUE_PLAN)) % len(df)
        pk = df.columns[0]; original = df.at[row, column]
        if kind == "missing_quotation_value" or kind == "missing_contact_detail": value = None
        elif kind == "duplicate_customer_name": value = df.at[max(0, row - 1), column]
        elif kind == "outdated_opportunity_stage": value = "Qualification"
        elif kind == "overdue_follow_up": value = "2023-01-01"
        elif kind == "expired_quotation": value = "2022-12-31"
        elif kind == "invalid_discount": value = 55.0
        elif kind == "currency_mismatch": value = "ZZZ"
        elif kind == "inconsistent_opportunity_value": value = float(original) * 1.75
        else: value = "31/31/2025"
        df.at[row, column] = value
        records.append({"issue_id":f"DQI-{i+1:06d}","dataset":dataset,"record_id":str(df.at[row,pk]),"column_name":column,"issue_type":kind,"original_value":"" if pd.isna(original) else str(original),"corrupted_value":"" if value is None else str(value),"severity":severity,"expected_resolution":resolution,"injection_timestamp":timestamp})
    issues = pd.DataFrame(records)
    # This is the 18th synthetic historical dataset; the separate ground-truth file is evaluation-only.
    operational = issues[["issue_id","dataset","record_id","column_name","issue_type","severity","injection_timestamp"]].copy()
    operational["status"] = "Open"; operational["synthetic_record"] = True
    selected=[formats] if formats!="both" else ["csv","parquet"]
    for fmt in selected:
        base=output_dir/"corrupted"/fmt; base.mkdir(parents=True,exist_ok=True)
        for name,df in corrupted.items():
            path=base/f"{name}.{'csv' if fmt=='csv' else 'parquet'}"
            if path.exists() and not overwrite: raise FileExistsError(f"Output exists: {path}; pass --overwrite")
            if fmt=="csv": df.to_csv(path,index=False,date_format="%Y-%m-%dT%H:%M:%S")
            else: df.to_parquet(path,index=False)
    gt=output_dir/"ground_truth"; gt.mkdir(parents=True,exist_ok=True)
    issues.to_csv(gt/"injected_issues.csv",index=False)
    summary={"total_issues":len(issues),"by_type":issues.issue_type.value_counts().sort_index().to_dict(),"by_severity":issues.severity.value_counts().sort_index().to_dict(),"affected_datasets":sorted(corrupted)}
    (gt/"injection_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return operational, corrupted

