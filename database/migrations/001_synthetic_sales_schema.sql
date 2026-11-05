-- PostgreSQL-compatible normalized sales schema. Generated files can be staged with TEXT columns,
-- while clean operational tables should use these representative constraints.
CREATE TABLE IF NOT EXISTS customers (
  customer_id text PRIMARY KEY, customer_name text NOT NULL, country text NOT NULL,
  region text NOT NULL, segment text NOT NULL, industry text NOT NULL,
  currency char(3) NOT NULL, created_at timestamp NOT NULL, is_active boolean NOT NULL
);
CREATE TABLE IF NOT EXISTS sales_representatives (
  sales_rep_id text PRIMARY KEY, name text NOT NULL, email text UNIQUE NOT NULL,
  country text NOT NULL, region text NOT NULL, hire_date date NOT NULL, is_active boolean NOT NULL
);
CREATE TABLE IF NOT EXISTS sales_opportunities (
  opportunity_id text PRIMARY KEY, customer_id text NOT NULL REFERENCES customers(customer_id),
  sales_rep_id text NOT NULL REFERENCES sales_representatives(sales_rep_id), name text NOT NULL,
  stage text NOT NULL, probability smallint NOT NULL CHECK (probability BETWEEN 0 AND 100),
  created_date date NOT NULL, expected_close_date date NOT NULL, actual_close_date date,
  currency char(3) NOT NULL, deal_value numeric(18,2) NOT NULL, source text NOT NULL,
  last_stage_change_date date NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_opportunities_customer ON sales_opportunities(customer_id);
CREATE INDEX IF NOT EXISTS ix_opportunities_rep_stage ON sales_opportunities(sales_rep_id, stage);
-- Remaining generated tables follow the same PK/FK definitions documented in data_dictionary.md.

