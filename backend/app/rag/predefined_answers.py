
PREDEFINED_ANSWERS = {
    'What is the annual leave policy?': """## Annual Leave Policy

**Entitlement:**
- Employees are entitled to **21 days of paid annual leave** per calendar year.
- New employees accrue leave at a rate of **1.75 days per month**.
- Leave not taken within the year may be carried over (maximum **5 days** carry-over).

**Eligibility:**
- Full-time employees are eligible after completing **3 months** of probation.
- Part-time employees receive pro-rated leave based on their working hours.

**Applying for Leave:**
1. Submit a leave request through the **HR Portal** at least **5 working days** in advance.
2. Obtain line manager approval before confirming travel arrangements.
3. Ensure handover notes are completed before leaving.

**Public Holidays:**
- All public holidays are in addition to your annual leave entitlement.
- If a holiday falls on a weekend, the next working day is observed.

> For urgent queries, contact HR at **hr@company.com** or extension **1200**.""",

    'Explain maternity benefits': """## Maternity Benefits

**Maternity Leave:**
- Eligible employees receive **26 weeks** of maternity leave.
- First **13 weeks** are paid at **full salary**.
- Remaining 13 weeks at **50% salary** (or statutory minimum, whichever is higher).

**Eligibility:**
- Employee must have completed at least **12 months** of continuous service.
- Notice must be given at least **8 weeks** before the expected due date.

**Benefits During Leave:**
- **Health insurance** continues at full employer contribution.
- **Pension contributions** are maintained throughout the leave period.
- Annual leave continues to **accrue** during maternity leave.

**Return to Work:**
- The same or equivalent role is guaranteed upon return.
- **Flexible working** arrangements may be requested.
- **Phased return** (gradual increase in hours) is supported for up to 4 weeks.

**Additional Support:**
- **Nursing facilities** available on-site (dedicated room).
- **Employee Assistance Program (EAP)** counselling available.

> Contact the HR team at **hr@company.com** for a confidential maternity planning meeting.""",

    'How does the onboarding process work?': """## Employee Onboarding Process

- **Day 1:** Welcome meeting with HR, IT setup, office tour, and ID/access card issuance.
- **Day 2–3:** Department introduction, meet team members, set up workstation.
- **Day 4–5:** Overview of company policies, compliance training, and safety induction.

- Shadowing sessions with your direct team.
- Introduction to tools, systems, and workflows specific to your role.
- First 1-on-1 meeting with your line manager to set 30-day goals.

- Attend all relevant team meetings and stand-ups.
- Complete mandatory **e-learning modules** (compliance, security, DEI).
- Mid-point check-in with HR at the **2-week mark**.

- Regular feedback sessions with your manager.
- Set **90-day objectives** aligned with your role.
- Final probation review meeting with HR and line manager.

**Key Contacts During Onboarding:**
| Contact | Purpose |
|---|---|
| HR Business Partner | Policies, benefits, paperwork |
| IT Helpdesk (ext. 1100) | System access, equipment |
| Line Manager | Role expectations, team introduction |

> Questions? Email **onboarding@company.com**""",

    'What are the performance review guidelines?': """## Performance Review Guidelines

**Review Cycles:**
- **Mid-Year Review:** Conducted in **July** (informal check-in and goal adjustment).
- **Annual Review:** Conducted in **January** (formal evaluation and rating).

**Rating Scale:**
| Rating | Description |
|---|---|
| 5 – Exceptional | Consistently exceeds all expectations |
| 4 – Exceeds Expectations | Frequently surpasses targets |
| 3 – Meets Expectations | Delivers all required outcomes |
| 2 – Needs Improvement | Some areas require development |
| 1 – Unsatisfactory | Consistently below expectations |

**Process:**
1. **Self-Assessment** submitted by employee (2 weeks before review date).
2. **Manager Assessment** completed independently.
3. **Calibration session** held at department level for consistency.
4. **One-on-One Review Meeting** – discussion of ratings and feedback.
5. **Development Plan** agreed and documented in the HR system.

**What is Evaluated:**
- Goal achievement (50% weighting)
- Competency/behavioural standards (30% weighting)
- Team collaboration and values alignment (20% weighting)

**Outcome:**
- Ratings directly influence **salary reviews** and **bonus eligibility**.
- Ratings of 2 or below trigger a **Performance Improvement Plan (PIP)**.""",

    'Summarize all uploaded documents': """## Knowledge Base Document Summary

The knowledge base contains enterprise documents across the following categories:

**HR & People Policies**
- Annual Leave Policy
- Maternity & Paternity Benefits
- Performance Review Framework
- Employee Onboarding Guide
- Code of Conduct

**Compliance & Legal**
- Data Protection Policy (GDPR)
- Anti-Bribery & Corruption Policy
- Whistleblowing Policy
- Information Security Policy

**Operations & Finance**
- Expense Reimbursement Policy
- Budget Approval Procedures
- Procurement Guidelines

**IT & Security**
- Acceptable Use Policy
- Remote Access Guidelines
- Incident Response Procedure

> **Note:** This summary reflects the documents hardcoded as examples. Upload actual documents via the **Admin Dashboard** to index real content into the knowledge base.""",

    'What policies are in the knowledge base?': """## Policies in the Knowledge Base

The following policy documents are available for querying:

- Annual Leave & Holiday Policy
- Flexible & Remote Working Policy
- Maternity, Paternity & Adoption Leave
- Disciplinary & Grievance Procedure
- Performance Management Framework

- Acceptable Use Policy (AUP)
- Information Security Policy
- Data Classification Policy
- Remote Access & VPN Policy
- Bring Your Own Device (BYOD) Policy

- Expense Claim & Reimbursement Policy
- Travel & Accommodation Policy
- Procurement & Purchasing Policy
- Budget Control Framework

- GDPR / Data Protection Policy
- Anti-Money Laundering (AML) Policy
- Anti-Bribery & Corruption Policy
- Equal Opportunities & DEI Policy

> Admins can upload additional policy documents via the **Document Management** section of the dashboard.""",

    'Show system overview': """## System Overview

| Component | Status | Details |
|---|---|---|
| Vector Store | Active | Pinecone (us-east-1) |
| AI Provider | Active | Google Gemini 2.0 Flash |
| Embedding Model | Active | Gemini Embedding 001 (3072-dim) |
| Database | Connected | PostgreSQL (Neon Cloud) |
| API Server | Running | FastAPI on port 8002 |
| Frontend | Running | React + Vite on port 5173 |

- **Roles Supported:** Admin, HR, Manager, Employee
- **Authentication:** JWT Bearer Token
- **Session Management:** Active sessions tracked in DB

1. Upload → Text Extraction → Chunking → Embedding → Pinecone Index
2. Retrieval → Grading → LLM Generation → Hallucination Check → Response

- Currently configured to retrieve top **5** most relevant chunks per query.""",

    'List all document categories': """## Document Categories

Documents in the knowledge base are organized into the following categories:

1. **Human Resources** – Leave, benefits, onboarding, performance
2. **Compliance & Legal** – GDPR, anti-bribery, whistleblowing
3. **Information Technology** – Security, acceptable use, remote access
4. **Finance & Operations** – Expenses, budgets, procurement
5. **Health & Safety** – Workplace safety, emergency procedures
6. **Learning & Development** – Training paths, certification policies""",

    'What are the budget approval procedures?': """## Budget Approval Procedures

| Amount | Approver Required |
|---|---|
| Up to £1,000 | Line Manager |
| £1,001 – £10,000 | Department Head |
| £10,001 – £50,000 | Finance Director |
| Above £50,000 | Executive Committee |

1. **Raise a Purchase Request (PR)** in the finance system with full justification.
2. Attach supporting documentation (quotes, business case, ROI analysis).
3. Submit to your **line manager** for first-level approval.
4. The request is auto-routed for additional approvals based on the amount.
5. Finance team processes PO upon full approval (typically **3–5 working days**).

- Include at least **3 competitive quotes** for purchases above £5,000.
- Clearly state the **business justification** and expected ROI.
- Reference the relevant **budget code** from your department cost centre.

> For urgent approvals, contact the Finance team at **finance@company.com** or ext. **1300**.""",

    'How do I handle conflict resolution?': """## Conflict Resolution Guidelines for Managers

Address conflicts **early and directly**. Unresolved conflict impacts team morale, productivity, and retention.

**Step 1 – Early Identification**
- Watch for signs: tension in meetings, reduced collaboration, complaints.
- Act within **48 hours** of becoming aware of an issue.

**Step 2 – Individual Meetings**
- Meet with each party separately to understand their perspective.
- Listen actively — do not judge or take sides.

**Step 3 – Facilitated Discussion**
- Bring parties together in a neutral setting.
- Establish ground rules: respect, no interruptions, focus on behaviour not personality.

**Step 4 – Agree on Actions**
- Document agreed steps and responsibilities.
- Set a **follow-up review date** (usually 2 weeks).

**Step 5 – Escalation**
- If unresolved, escalate to **HR Business Partner**.
- Formal grievance procedures may be initiated if required.

- Allegations of **harassment, discrimination, or bullying**.
- Situations involving **legal or safety risk**.""",

    'Explain resource allocation guidelines': """## Resource Allocation Guidelines

- Resources should be allocated based on **business priority**, **availability**, and **capability**.
- Use the **Capacity Planning Tool** in the project management system to plan allocations.

1. **Identify requirements** – Define skill sets, hours, and timelines needed.
2. **Check availability** – Review team capacity dashboards for the planning period.
3. **Submit allocation request** – Use the Resource Management System (RMS).
4. **Manager approval** – Department head confirms and approves the allocation.
5. **Communication** – Notify the allocated employee and update project plans.

- No employee should be allocated more than **80% of their time** to a single project (to allow for BAU work).
- Temporary **cross-department allocations** require written agreement from both managers.
- Contractor requests must go through **Procurement** with a valid PO.""",

    'What are managerial KPIs?': """## Managerial Key Performance Indicators (KPIs)

| KPI | Target |
|---|---|
| Team Attrition Rate | < 10% annually |
| Employee Engagement Score | > 75% (survey) |
| Time-to-Fill Vacancies | < 45 days |
| Absenteeism Rate | < 3% monthly |

| KPI | Target |
|---|---|
| On-Time Project Delivery | > 85% |
| Budget Adherence | ±5% of approved budget |
| Utilisation Rate | 75–80% of team capacity |
| SLA Compliance | > 95% |

| KPI | Target |
|---|---|
| Performance Reviews Completed | 100% on schedule |
| Training Hours per Employee | Minimum 20 hrs/year |
| Succession Plans in Place | 100% for critical roles |""",

    'What is the holiday schedule?': """## Holiday Schedule

| Date | Holiday |
|---|---|
| 1 January | New Year's Day |
| 18 April | Good Friday |
| 21 April | Easter Monday |
| 5 May | Early May Bank Holiday |
| 26 May | Spring Bank Holiday |
| 25 August | Summer Bank Holiday |
| 25 December | Christmas Day |
| 26 December | Boxing Day |

- The company observes **2 additional discretionary days** per year (dates announced by HR in Q4 for the following year).

- Public holidays are **in addition** to your annual leave entitlement.
- If a holiday falls on a weekend, the **next working day** is the substitute day.
- Employees in different regions should check with HR for **regional variations**.""",

    'How do I submit an expense report?': """## Submitting an Expense Report

1. **Collect all receipts** – Keep originals; photos accepted via the expense app.
2. **Log into the Expense Portal** at **expenses.company.com** (or via the mobile app).
3. **Create a new claim** – Select the expense category and date.
4. **Upload receipts** – Attach scanned/photographed images of all receipts.
5. **Add business justification** – Briefly describe the business purpose.
6. **Submit for approval** – Claim is sent automatically to your line manager.
7. **Reimbursement** – Approved claims are paid in the **next payroll cycle** (within 30 days).

- Travel (rail, flights, taxis) – economy class only for domestic travel
- Accommodation – up to **£150/night** (pre-approved for higher amounts)
- Meals – up to **£35/day** when travelling
- Client entertainment – requires **senior manager approval**

- Alcohol (unless part of an approved client entertainment budget)
- Personal items or fines
- Journeys to/from your normal place of work (commuting)

> **Deadline:** Submit expenses within **30 days** of the spend. Late submissions may not be reimbursed.""",

    'Explain the remote work policy': """## Remote Work Policy

- All **permanent employees** who have completed their probation period are eligible for remote working arrangements.
- Eligibility is subject to role suitability (some roles require on-site presence).

- **Hybrid model:** Minimum **3 days in the office** per week (specific days agreed with your manager).
- Fully remote arrangements may be considered on a **case-by-case basis** with written approval from HR and department head.

- Maintain a **secure, private workspace** at home.
- Be **contactable and available** during core hours (9am – 5pm, Monday–Friday).
- Attend **all scheduled meetings** (in-person or via video call).
- Use **company-approved tools** only (VPN required when accessing company systems).

- The company provides a **laptop and essential peripherals**.
- A **£250 home office allowance** is available once per year (claim via expenses).
- Employees are responsible for their own internet connection.""",

    'What are the company values?': """## Company Values & Culture

Our five core values guide everything we do — from how we make decisions to how we treat each other.

---

> *We do what is right, not what is easy.*
- We are honest and transparent in all our interactions.
- We take accountability for our actions and decisions.

> *We embrace change and continuously improve.*
- We encourage creative thinking and experimentation.
- We learn from failure and celebrate progress.

> *We achieve more together than apart.*
- We respect diverse perspectives and backgrounds.
- We share knowledge openly and support each other's success.

> *Our customers are at the heart of everything we do.*
- We listen to feedback and act on it.
- We deliver quality with care and consistency.

> *We hold ourselves to the highest standards.*
- We take pride in our work and strive to exceed expectations.
- We invest in our own development and that of our colleagues."""
}