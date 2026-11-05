from fastapi import APIRouter
from app.api.v1 import auth, customers, opportunities, quotations, sales_analytics, agents, workflows, approvals, rpa_jobs, integrations, audit

api_router = APIRouter()
for module in (auth, customers, opportunities, quotations, sales_analytics, agents, workflows, approvals, rpa_jobs, integrations, audit):
    api_router.include_router(module.router)

