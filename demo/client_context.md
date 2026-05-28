# Client Context: GlobalRetail Enterprises

## Account Overview

| Field | Details |
|---|---|
| **Client Name** | GlobalRetail Enterprises, Inc. |
| **Industry** | Omnichannel Retail & E-Commerce |
| **Headquarters** | Chicago, IL |
| **Employees** | ~8,400 globally |
| **Annual Revenue** | ~$2.1B |
| **Contract Tier** | Enterprise |
| **Contract Value** | $142,000/year |
| **Contract Start** | March 1, 2024 |
| **Renewal Date** | February 28, 2027 |
| **CSM Owner** | Laura Kim (Acme) |
| **AE Owner** | Derek Santos (Acme) |
| **Account Health** | 🟡 At Risk |
| **NPS Score** | 32 (flagged — below internal threshold of 50) |
| **Last QBR** | January 15, 2026 |
| **Next QBR** | April 15, 2026 |

---

## Client Stakeholders

### Primary Contacts

| Name | Title | Role | Relationship |
|---|---|---|---|
| Jennifer Walsh | VP of Data & Analytics | Executive Sponsor | Warm — engaged quarterly |
| Carlos Mendoza | Head of Data Engineering | Technical Champion | Strong — daily platform user |
| Rachel Okonkwo | Director of BI & Reporting | Power User | Neutral — frustrated with export limits |
| Brian Tao | IT Security Lead | Procurement/Security | Formal — focused on compliance |
| Stephanie Huang | CFO Office — FP&A Manager | Data Consumer | Passive — occasional user |

### Potential Detractors
- **Rachel Okonkwo** — Filed 3 support tickets in Q4 2025 related to PowerPoint export limitations and slow Salesforce sync. Sentiment in last call: "This is blocking my team's Monday reporting workflow."
- **Brian Tao** — Raised concerns about AI query log retention during Q1 2026 security review. Wants opt-out confirmed in writing.

---

## Deployed Modules

| Module | Status | Usage |
|---|---|---|
| Acme Insights Platform | ✅ Active | High — ~140 MAU |
| Acme DataBridge | ✅ Active | Medium — 18 active pipelines |
| Acme AI Analyst | 🔵 Beta Pilot | Low — 6 users in pilot |

---

## Data Sources Connected

- **Salesforce CRM** (Sales Cloud) — 6.8M records, 15-min sync delay flagged as issue
- **Snowflake Data Warehouse** — Primary analytics source, 3 schemas connected
- **Google Analytics 4** — Web & app behavioral data
- **NetSuite ERP** — Financial data (inventory, COGS, margin)
- **Shopify Plus** — E-commerce transaction data (4 storefronts)
- **Meta Ads & Google Ads** — Marketing spend attribution

---

## Active Use Cases

### 1. Omnichannel Revenue Dashboard
- Tracks same-store sales vs. e-commerce revenue by region
- 47 custom KPIs configured
- Updated daily at 6 AM CT via DataBridge pipeline
- ~90 users access this weekly

### 2. Inventory Velocity Reporting
- Monitors SKU-level sell-through rates across 14 distribution centers
- Triggers Slack alerts when inventory falls below reorder threshold
- Built by Carlos Mendoza's team using Acme API

### 3. Marketing Attribution (In Progress)
- Connecting Meta Ads + Google Ads + GA4 for multi-touch attribution
- Blocked on GA4 custom dimensions mapping — ticket #ACME-8821 open since Dec 2025

### 4. AI Analyst Pilot
- 6 FP&A and merchandising users testing natural language queries
- Pilot goal: reduce ad-hoc data requests to engineering team by 40%
- Current blocker: AI Analyst cannot query NetSuite ERP schema (permissions issue)

---

## Support History (Last 6 Months)

| Ticket ID | Date | Severity | Issue | Status |
|---|---|---|---|---|
| ACME-8821 | Dec 12, 2025 | P2 | GA4 custom dimensions mapping broken | Open |
| ACME-9104 | Jan 8, 2026 | P3 | PowerPoint export truncated at 20 slides | Open |
| ACME-9211 | Jan 22, 2026 | P2 | Salesforce sync delay >30min on high-record days | Resolved |
| ACME-9380 | Feb 5, 2026 | P1 | DataBridge pipeline failure — Snowflake auth token expired | Resolved in 47min |
| ACME-9502 | Feb 28, 2026 | P3 | AI Analyst: NetSuite schema not visible | In Progress |
| ACME-9601 | Mar 15, 2026 | P2 | Salesforce connector latency spike — 45min delay | Resolved in 4h |

**Total Open Tickets:** 3  
**Avg Resolution Time (last 6 months):** 18.4 hours  
**P1 SLA Met:** 100% (1/1)  
**P2 SLA Met:** 67% (2/3 — ACME-8821 breached 12-hour SLA)

---

## Business Context & Strategic Goals (FY2026)

1. **Profitability Push** — Board mandate: achieve 12% EBITDA margin by Q4 2026 (currently at 7.2%)
2. **SKU Rationalization** — Reduce active SKUs by 18% using data-driven inventory analysis
3. **E-commerce Growth** — Target 35% of total revenue from digital channels (currently 24%)
4. **Data Democratization** — Reduce dependency on data engineering for business user reporting (hence AI Analyst pilot)
5. **Marketing Efficiency** — Reduce blended CAC by 20% using attribution data

---

## Expansion Opportunities

| Opportunity | Estimated Value | Owner | Probability |
|---|---|---|---|
| AI Analyst full rollout (from 6 → 80 users) | +$36,000/year | Derek Santos | 40% |
| Acme DataBridge — Oracle CDC add-on (if shipped Q3) | +$9,600/year | Carlos Mendoza | 65% |
| Data residency migration to EU-West (London office expansion) | +$8,000/year | Brian Tao | 25% |

**Total Upsell Pipeline:** ~$53,600/year

---

## Renewal Risk Assessment

**Current Risk Level: 🟡 MEDIUM-HIGH**

### Risk Factors
- NPS at 32 — 18 points below internal satisfaction threshold
- Rachel Okonkwo's team blocked by export limitation (no fix ETA communicated)
- GA4 mapping ticket (ACME-8821) open >90 days — breached P2 SLA
- AI Analyst pilot has low engagement — 6 of 6 pilot users report friction with NetSuite integration
- Jennifer Walsh mentioned competing evaluation with Sigma Computing in January QBR

### Mitigation Actions (Assigned)
- [ ] Derek Santos: Schedule executive alignment call with Jennifer Walsh before April QBR
- [ ] Laura Kim: Provide written SLA breach acknowledgment + remediation plan for ACME-8821
- [ ] Engineering: Prioritize ACME-9502 (NetSuite AI Analyst access) — target fix: April 5, 2026
- [ ] Product: Communicate PowerPoint export roadmap item with ETA in writing
- [ ] CSM: Offer complimentary 30-day AI Analyst seat expansion to 20 users to boost pilot engagement

---

## Key Contractual Terms

- **Data residency:** US-East (Chicago availability zone preferred)
- **Audit log retention:** 1 year (Enterprise tier standard)
- **AI query logs:** Client requested opt-out — **confirmed opt-out active since Feb 2026**
- **Uptime SLA:** 99.99% (Platinum-equivalent negotiated during renewal)
- **Payment terms:** Net-45 (exception granted at signing)
- **Data deletion:** 45-day SLA on termination (negotiated above standard 30-day)
- **MSA signed:** March 1, 2024 (custom — includes IP indemnification clause)

---

## Communication Log

| Date | Type | Participants | Summary |
|---|---|---|---|
| Mar 15, 2026 | Email | Laura Kim → Jennifer Walsh | Sent SLA breach acknowledgment for ACME-8821 |
| Feb 20, 2026 | Call | Derek Santos + Jennifer Walsh | Discussed renewal timeline, competitor evaluation mentioned |
| Jan 15, 2026 | QBR | Full team | Covered Q4 performance, flagged AI Analyst pilot slow start |
| Dec 10, 2025 | Slack | Carlos Mendoza → Support | GA4 issue first reported |
| Nov 5, 2025 | Call | Laura Kim + Rachel Okonkwo | Export limitations escalation — no resolution given |

---

## Notes for AI Analyst & CSM Prep

- Always acknowledge the SLA breach on ACME-8821 proactively — do not wait for client to raise it
- Jennifer Walsh responds well to data-backed updates — lead with metrics (uptime %, resolution times)
- Carlos Mendoza is the internal champion — keep him informed on technical roadmap
- Avoid discussing Oracle CDC until Q3 timeline is confirmed in writing
- Brian Tao will ask about AI query log opt-out confirmation at every touchpoint — have written confirmation ready
- Rachel Okonkwo's export issue is highest churn signal — needs concrete ETA or workaround
