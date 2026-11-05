# Synthetic sales data system

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Safe defaults live in `.env.example`; never commit `.env`. Generated files are ignored by Git.

## Generate and validate

```bash
python -m database.synthetic_data.generate_all --profile mvp --seed 42 --format both --validate --overwrite
python -m database.synthetic_data.generate_all --profile standard --seed 42 --format both --validate --overwrite
python -m database.synthetic_data.generate_all --profile full --seed 42 --format both --validate --overwrite
```

Without `--overwrite`, existing outputs are protected. Clean canonical files are written beneath `database/generated/{csv,parquet}`. Corrupted CRM extracts are isolated in `database/generated/corrupted`; evaluation truth is isolated in `ground_truth`. Reports and the manifest record counts, checks, seed, profile, and fingerprint.

Generation creates catalog and accounts, pipeline and commercial documents, then activities, targets, exchange rates, and synthetic operational history. Controlled defects are applied only to copies; canonical keys are never corrupted.

## PostgreSQL and consumers

Apply `database/migrations/001_synthetic_sales_schema.sql` to an explicitly selected development schema. Loading is separate from generation, requires confirmation, and never drops tables. Gemini agents must never access `ground_truth`. RPA tests consume corrupted extracts through the future legacy CRM UI and verify against `rpa_test_scenarios.md`.
