# KPI specification

All monetary KPIs are converted to EUR using the latest exchange rate on or before the event date. SQL implementations must use closed calendar periods and preserve two-decimal commercial rounding.

| KPI | Definition |
|---|---|
| Pipeline value | Sum of open opportunity `deal_value` at period end |
| Weighted pipeline | Sum of open `deal_value * probability / 100` |
| Win rate | Closed-won opportunities / all closed opportunities in the window |
| Sales conversion rate | Closed-won opportunities / opportunities created in the cohort |
| Quotation-to-order conversion | Distinct quotations producing an order / sent, expired, rejected, or accepted quotations |
| Average deal size | Closed-won value / count of closed-won opportunities |
| Sales cycle duration | Average days from opportunity creation to actual close |
| Target attainment | Recognized order value / target amount for representative and period |
| Overdue follow-up rate | Open activities past due / all open follow-up activities |
| Data completeness | Populated required CRM fields / required CRM fields evaluated |
| Approval turnaround | Average resolved timestamp minus requested timestamp for resolved approvals |

