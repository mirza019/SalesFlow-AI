from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
import pandas as pd

from database.synthetic_data.config import GenerationConfig
from database.synthetic_data.generator import SyntheticSalesGenerator
from core.database import DB_PATH
from core.auth import hash_password

APP_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, display_name TEXT NOT NULL, role TEXT NOT NULL, password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY, username TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS requirement_specs (id INTEGER PRIMARY KEY, title TEXT NOT NULL, specification_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', created_by TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS workflows (id INTEGER PRIMARY KEY, name TEXT NOT NULL, template_key TEXT NOT NULL, config_json TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS workflow_versions (id INTEGER PRIMARY KEY, workflow_id INTEGER NOT NULL, version INTEGER NOT NULL, config_json TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(workflow_id) REFERENCES workflows(id));
CREATE TABLE IF NOT EXISTS workflow_runs (id INTEGER PRIMARY KEY, workflow_id INTEGER, status TEXT NOT NULL, test_mode INTEGER NOT NULL, result_json TEXT, error TEXT, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT, FOREIGN KEY(workflow_id) REFERENCES workflows(id));
CREATE TABLE IF NOT EXISTS approvals (id INTEGER PRIMARY KEY, action_type TEXT NOT NULL, target_id TEXT NOT NULL, payload_json TEXT NOT NULL, payload_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', requested_by TEXT NOT NULL, reviewed_by TEXT, requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, reviewed_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, actor TEXT NOT NULL, event_type TEXT NOT NULL, target_type TEXT NOT NULL, target_id TEXT, details_json TEXT NOT NULL, success INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS connector_syncs (id INTEGER PRIMARY KEY, connector TEXT NOT NULL, status TEXT NOT NULL, records INTEGER NOT NULL DEFAULT 0, details TEXT, synchronized_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_log(created_at);
"""

def initialize_database(overwrite: bool = False, profile: str = "mvp", seed: int = 42) -> dict:
    if DB_PATH.exists() and not overwrite:
        raise FileExistsError(f"{DB_PATH} already exists; use --overwrite for a scoped development rebuild")
    if DB_PATH.exists(): DB_PATH.unlink()
    generator = SyntheticSalesGenerator(GenerationConfig(profile=profile, seed=seed))
    tables = generator.generate()
    conn = sqlite3.connect(DB_PATH)
    try:
        for name, frame in tables.items(): frame.to_sql(name, conn, index=False, if_exists="replace")
        conn.executescript(APP_SCHEMA)
        demo_password = os.getenv("SALESOPS_DEMO_PASSWORD","salesops-demo")
        users=[("admin","Synthetic Administrator","Administrator",hash_password(demo_password)),("manager","Synthetic Sales Manager","Sales Manager",hash_password(demo_password)),("builder","Synthetic Citizen Developer","Citizen Developer",hash_password(demo_password))]
        conn.executemany("INSERT INTO users(username,display_name,role,password_hash) VALUES(?,?,?,?)",users)
        conn.commit()
    finally: conn.close()
    summary={"database":str(DB_PATH),"profile":profile,"seed":seed,"sales_records":sum(len(x) for x in tables.values()),"tables":{k:len(v) for k,v in tables.items()},"demo_users":[x[0] for x in users]}
    (DB_PATH.parent/"import_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument("--profile",choices=["mvp","standard","full"],default="mvp"); p.add_argument("--seed",type=int,default=42); p.add_argument("--overwrite",action="store_true"); a=p.parse_args()
    print(json.dumps(initialize_database(a.overwrite,a.profile,a.seed),indent=2))

if __name__=="__main__": main()

