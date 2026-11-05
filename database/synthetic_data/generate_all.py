from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import GenerationConfig
from .generator import SyntheticSalesGenerator
from .inject_issues import inject_issues
from .validators import save_validation_reports, validate_tables

def parse_args():
    p=argparse.ArgumentParser(description="Generate deterministic SalesFlow AI synthetic data")
    p.add_argument("--profile",choices=["mvp","standard","full"],default="full")
    p.add_argument("--seed",type=int,default=42); p.add_argument("--format",choices=["csv","parquet","both"],default="both")
    p.add_argument("--validate",action="store_true"); p.add_argument("--overwrite",action="store_true")
    p.add_argument("--output-dir",type=Path,default=Path("database/generated")); return p.parse_args()

def main():
    a=parse_args(); cfg=GenerationConfig(profile=a.profile,seed=a.seed,output_dir=a.output_dir)
    gen=SyntheticSalesGenerator(cfg); tables=gen.generate()
    issues,_=inject_issues(tables,cfg.counts["crm_data_quality_issues"],gen.rng,cfg.output_dir,a.format,a.overwrite)
    tables["crm_data_quality_issues"]=issues
    manifest=gen.export(a.format,a.overwrite)
    report=validate_tables(tables,cfg.counts,issues) if a.validate else {"passed":None,"message":"Validation not requested"}
    save_validation_reports(report,cfg.output_dir)
    summary={"profile":a.profile,"seed":a.seed,"total_records":manifest["total_records"],"record_counts":manifest["record_counts"],"validation":report.get("passed")}
    (cfg.output_dir/"reports"/"generation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    if a.validate and not report["passed"]: raise SystemExit(1)

if __name__=="__main__": main()
