from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FULL_COUNTS = {
    "customers": 5_000, "customer_contacts": 12_000,
    "sales_representatives": 150, "products_services": 500,
    "sales_opportunities": 20_000, "opportunity_line_items": 45_000,
    "quotations": 25_000, "quotation_line_items": 55_000,
    "sales_orders": 12_000, "order_line_items": 24_000,
    "sales_activities": 35_000, "approval_requests": 4_000,
    "sales_targets": 1_800, "exchange_rates": 3_000,
    "crm_data_quality_issues": 5_000, "workflow_definitions": 40,
    "workflow_executions": 3_000, "rpa_execution_logs": 2_000,
}

# Exact, deterministic profiles. Standard totals 75,000 and MVP totals 10,000.
def scaled_counts(total: int) -> dict[str, int]:
    names = list(FULL_COUNTS)
    weights = [FULL_COUNTS[n] for n in names]
    raw = [total * w / sum(weights) for w in weights]
    counts = {n: max(1, int(v)) for n, v in zip(names, raw)}
    delta = total - sum(counts.values())
    order = sorted(range(len(names)), key=lambda i: raw[i] - int(raw[i]), reverse=delta > 0)
    step = 1 if delta > 0 else -1
    for i in range(abs(delta)):
        key = names[order[i % len(order)]]
        if step > 0 or counts[key] > 1:
            counts[key] += step
    # Preserve minimum parents for dependent entities.
    return counts

PROFILE_COUNTS = {"mvp": scaled_counts(10_000), "standard": scaled_counts(75_000), "full": FULL_COUNTS}

COUNTRIES = ["Germany", "United States", "United Kingdom", "India", "United Arab Emirates", "Brazil"]
CURRENCIES = {"Germany": "EUR", "United States": "USD", "United Kingdom": "GBP", "India": "INR", "United Arab Emirates": "AED", "Brazil": "BRL"}
REGIONS = {"Germany": "Central Europe", "United States": "North America", "United Kingdom": "Northern Europe", "India": "South Asia", "United Arab Emirates": "Middle East", "Brazil": "Latin America"}

@dataclass(frozen=True)
class GenerationConfig:
    profile: str = "full"
    seed: int = 42
    output_dir: Path = Path("database/generated")
    start_date: str = "2023-11-01"
    end_date: str = "2026-10-31"

    @property
    def counts(self) -> dict[str, int]:
        return dict(PROFILE_COUNTS[self.profile])

