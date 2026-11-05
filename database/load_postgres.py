"""Explicit, non-destructive PostgreSQL loader with manifest count checks."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, inspect, text

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database-url",required=True)
    p.add_argument("--input-dir",type=Path,default=Path("database/generated/csv"))
    p.add_argument("--schema",default="salesflow_synthetic")
    p.add_argument("--if-exists",choices=["fail","append"],default="fail")
    p.add_argument("--confirm",action="store_true")
    a=p.parse_args()
    if not a.confirm: raise SystemExit("Refusing to load without --confirm. No tables are dropped by this command.")
    manifest=json.loads((a.input_dir.parent/"manifest.json").read_text())
    engine=create_engine(a.database_url)
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{a.schema}"'))
    existing=set(inspect(engine).get_table_names(schema=a.schema))
    conflicts=existing.intersection(manifest["record_counts"])
    if conflicts and a.if_exists=="fail":
        raise SystemExit(f"Target tables already exist: {sorted(conflicts)}. Use --if-exists append explicitly; tables are never dropped.")
    results={}
    for name,expected in manifest["record_counts"].items():
        path=a.input_dir/f"{name}.csv"
        if not path.exists(): raise FileNotFoundError(path)
        with engine.connect() as conn:
            before=conn.execute(text(f'SELECT count(*) FROM "{a.schema}"."{name}"')).scalar_one() if name in existing else 0
        frame=pd.read_csv(path)
        frame.to_sql(name,engine,schema=a.schema,if_exists="append" if name in existing else "fail",index=False,chunksize=10_000,method="multi")
        with engine.connect() as conn: after=conn.execute(text(f'SELECT count(*) FROM "{a.schema}"."{name}"')).scalar_one()
        loaded=after-before; results[name]={"expected":expected,"loaded":loaded,"passed":loaded==expected}
    print(json.dumps({"passed":all(x["passed"] for x in results.values()),"tables":results},indent=2))
    if not all(x["passed"] for x in results.values()): raise SystemExit(1)

if __name__=="__main__": main()

