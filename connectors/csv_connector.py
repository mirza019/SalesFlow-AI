from __future__ import annotations
import pandas as pd
REQUIRED={"opportunities":{"opportunity_id","customer_id","sales_rep_id","stage","deal_value"},"customers":{"customer_id","customer_name","country"}}
def validate_csv(file,entity:str):
    if entity not in REQUIRED:raise ValueError("Unsupported import entity")
    frame=pd.read_csv(file); missing=sorted(REQUIRED[entity]-set(frame.columns))
    return {"valid":not missing,"missing_columns":missing,"rows":len(frame),"preview":frame.head(20)}

