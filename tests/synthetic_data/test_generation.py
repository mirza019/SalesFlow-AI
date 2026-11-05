from database.synthetic_data.config import GenerationConfig
from database.synthetic_data.generator import SyntheticSalesGenerator
from database.synthetic_data.inject_issues import inject_issues
from database.synthetic_data.validators import validate_tables

def test_mvp_counts_relationships_and_determinism(tmp_path):
    cfg=GenerationConfig(profile="mvp",seed=42,output_dir=tmp_path)
    first=SyntheticSalesGenerator(cfg); tables=first.generate()
    canonical_fingerprint=first.fingerprint()
    issues,_=inject_issues(tables,cfg.counts["crm_data_quality_issues"],first.rng,tmp_path,"csv",True)
    tables["crm_data_quality_issues"]=issues
    report=validate_tables(tables,cfg.counts,issues)
    assert report["passed"], [x for x in report["checks"] if not x["passed"]]
    second=SyntheticSalesGenerator(cfg); second.generate()
    assert canonical_fingerprint == second.fingerprint()

