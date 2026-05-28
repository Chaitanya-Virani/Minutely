# Acme Corp — Internal Knowledge Base & System Context

## Company Overview

**Company:** Acme Corporation  
**Industry:** B2B SaaS — Enterprise Data Analytics  
**Founded:** 2018  
**Headquarters:** San Francisco, CA  
**Employees:** ~320 (as of Q1 2026)  
**ARR:** $28M (FY2025)  
**Funding Stage:** Series B ($45M raised, led by Sequoia)

---

## Product Suite

### 1. Acme Insights Platform (Core Product)
- Real-time business intelligence dashboard for mid-market and enterprise clients
- Connects to 60+ data sources (Salesforce, HubSpot, Snowflake, BigQuery, PostgreSQL, etc.)
- Features: automated anomaly detection, AI-generated weekly summaries, custom KPI tracking
- Pricing: $2,500–$15,000/month depending on seats and data volume
- SLA: 99.9% uptime guaranteed

### 2. Acme DataBridge
- ETL/ELT pipeline management tool
- Supports real-time and batch ingestion
- Built on Apache Kafka + dbt + Airflow
- Available as add-on: $800/month

### 3. Acme AI Analyst (Beta — Q2 2026 Launch)
- Natural language interface over connected data sources
- Powered by RAG architecture using Claude API
- Allows non-technical users to query dashboards via chat
- Early access pricing: $500/month per workspace

---

## Engineering Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI (Python 3.12) |
| Data Processing | Apache Spark, dbt, Airflow |
| Databases | PostgreSQL 15, Redis 7, ClickHouse |
| Vector DB | Qdrant (self-hosted on Kubernetes) |
| Embeddings | Voyage AI (voyage-3) |
| LLM | Claude 3.5 Sonnet (Anthropic) |
| Infrastructure | AWS (EKS, RDS, ElastiCache, S3) |
| Observability | Datadog, Langfuse, OpenTelemetry |
| CI/CD | GitHub Actions + ArgoCD |
| Auth | Auth0 (enterprise SSO), JWT |

---

## Team Structure

### Engineering (82 people)
- **Platform Engineering:** 14 engineers — infrastructure, Kubernetes, observability
- **Backend:** 22 engineers — API, data pipelines, integrations
- **Frontend:** 16 engineers — dashboards, UI components
- **ML/AI:** 12 engineers — embeddings, RAG, model fine-tuning
- **QA/Reliability:** 10 engineers — E2E testing, chaos engineering
- **Security:** 8 engineers — compliance, penetration testing, IAM

### Leadership
- **CEO:** Sarah Chen (ex-Palantir, 12 years in data infrastructure)
- **CTO:** Marcus Rivera (ex-Databricks, led Spark integrations team)
- **VP Engineering:** Priya Nair (ex-Stripe, built payments reliability systems)
- **Head of AI:** Dr. James Park (PhD, NLP — ex-Google DeepMind)
- **VP Sales:** Tom Harrington (ex-Tableau)
- **VP Customer Success:** Laura Kim

---

## SLA & Support Tiers

| Tier | Response Time | Uptime SLA | Dedicated CSM |
|---|---|---|---|
| Starter | 48h | 99.5% | No |
| Growth | 12h | 99.9% | No |
| Enterprise | 2h | 99.99% | Yes |
| Platinum | 30min | 99.99% | Yes + On-call |

---

## Security & Compliance

- SOC 2 Type II certified (renewed January 2026)
- GDPR compliant (DPA available for EU customers)
- HIPAA-eligible configurations available (Enterprise tier only)
- CCPA compliant
- Data encryption: AES-256 at rest, TLS 1.3 in transit
- SSO support: Okta, Azure AD, Google Workspace
- Audit logs: 90-day retention (Enterprise), 1-year (Platinum)
- Customer data isolation: per-tenant Kubernetes namespaces + row-level security in PostgreSQL
- Penetration testing: quarterly (third-party via Cobalt)

---

## Data Retention & Privacy Policies

- Customer-uploaded data: retained for contract duration + 30 days post-termination
- Anonymized usage telemetry: retained 24 months for product analytics
- AI query logs: retained 90 days, opt-out available for Enterprise
- Data residency options: US-East, EU-West, APAC-Singapore
- Right to deletion: fulfilled within 30 days of request

---

## Known Product Limitations (as of Q1 2026)

- DataBridge does not support real-time CDC (change data capture) for Oracle — planned Q3 2026
- AI Analyst does not support multi-modal inputs (images, PDFs) — on roadmap
- Dashboard export to PowerPoint is limited to 20 slides — engineering ticket open
- Salesforce connector has 15-min sync delay for orgs with >5M records
- Max concurrent WebSocket connections per tenant: 500 (scaling planned Q2 2026)

---

## Pricing & Contracts

- Annual contracts only for Enterprise and Platinum
- Month-to-month available for Starter and Growth
- Volume discounts: 10% for 2-year, 20% for 3-year commitments
- Free trial: 14 days (Starter/Growth only, no credit card required)
- Custom MSA available for deals >$100K ARR
- Net-30 payment terms standard; Net-60 available for Enterprise

---

## Support & Escalation Process

1. **L1 Support** — In-app chat, email, documentation search (all tiers)
2. **L2 Engineering** — Escalated by L1 for technical root-cause issues
3. **L3 Platform/Security** — Critical incidents, data breaches, outages
4. **Executive Escalation** — VP CS or CEO involvement for Platinum tier churn risk

Incident communication: StatusPage (status.acmecorp.com) + email/Slack webhooks

---

## Integrations Roadmap (2026)

| Integration | Status | ETA |
|---|---|---|
| Databricks Unity Catalog | In Progress | Q2 2026 |
| Microsoft Fabric | Planned | Q3 2026 |
| Oracle CDC | Planned | Q3 2026 |
| Tableau Embedding | In Progress | Q2 2026 |
| Workday HRIS | Planned | Q4 2026 |
| SAP ERP | Exploring | 2027 |

---

## Cultural Values

- **Ship fast, learn faster** — Two-week sprints, bi-weekly releases
- **Data-informed decisions** — Every major decision backed by metrics
- **Customer obsession** — NPS target: 60+ (current: 54)
- **Radical transparency** — Weekly all-hands, OKRs public internally
- **Psychological safety** — Blameless post-mortems, no blame culture
