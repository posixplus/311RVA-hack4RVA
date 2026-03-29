# RVA 311 Bridge — 24/7 AI-Powered Multilingual City Services Assistant

**Hack4RVA 2026 · Thriving & Inclusive Communities Pillar along with Thriving Neighborhood**

**Team - The RVA Transformers**

**Aravindan, Alex, Jayakanthan & Ranga**

RVA 311 Bridge extends Richmond's 311 system to provide **24/7 after-hours assistance** through an AI-powered chatbot and IVR phone line. Residents can report issues, find city resources, and get connected to the right department — in **English, Spanish, and Arabic** — without needing an account or sharing personal information.

**🌐 Live Demo:** [https://d3rgw4i46ms5xk.cloudfront.net](https://d3rgw4i46ms5xk.cloudfront.net)

**Live VOICE IVR: 1-855-953-7650**
**NOTE: For this hackathon, the practical limit is the Lex session cap of 25 concurrent calls. IF you get an error, please retry after few minutes**

## The Problem

Richmond's 311 system operates during business hours only. After hours, residents — especially immigrants, refugees, and non-English speakers — have no way to access city services, report emergencies, or find critical resources like shelters, legal aid, or food assistance. Language barriers and fear of sharing personal information create additional obstacles.

## Our Solution

A privacy-first, multilingual assistant that:

- **Answers questions 24/7** using verified Richmond city documents (RAG-powered, not hallucinated)
- **Supports 14 service categories** from emergency preparedness to housing assistance
- **Protects privacy** — no PII collected, no login required, no immigration status asked
- **Hands off to nonprofits** — one-click referral to IRC Richmond, Sacred Heart Center, Central Virginia Legal Aid, and more
- **Cites sources** — every response references the document it came from
- **Includes BizNavigator** — a self-guided business startup tool with live Richmond contract data

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                           │
│                    (d3rgw4i46ms5xk.cloudfront.net)              │
├─────────────────────────────────────────────────────────────────┤
│  React + Vite Frontend          │  BizNavigator (static HTML)   │
│  - Chat Interface               │  - Business startup guide     │
│  - Category Grid (14 services)  │  - Live contract data         │
│  - FAQ Page (bilingual)         │  - Permit checklist builder   │
│  - Admin Dashboard              │  - Cost & timeline estimator  │
│  - Nonprofit Handoff            │                               │
├─────────────────────┬───────────┴───────────────────────────────┤
│   API Gateway REST  │  Amazon Connect IVR                       │
│   /chat endpoint    │  Phone-based access (EN/ES/AR)            │
├─────────────────────┴───────────────────────────────────────────┤
│                    Lambda Orchestrator                           │
│  - Bedrock RAG (retrieve_and_generate)                          │
│  - Claude Haiku 4.5 (converse API)                              │
│  - Conversation context (multi-turn)                            │
│  - PII redaction (AWS Comprehend)                               │
│  - Source citation extraction                                   │
├─────────────────────────────────────────────────────────────────┤
│  Bedrock Knowledge Base    │  DynamoDB Sessions  │  S3 Logs     │
│  (OpenSearch Serverless)   │  (TTL: 7 days)      │  (Redacted)  │
│  10 verified city docs     │                     │              │
└────────────────────────────┴─────────────────────┴──────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, React Router, custom RVA 311-styled CSS |
| AI/ML | Amazon Bedrock (Claude Haiku 4.5), RAG with Titan Text Embeddings V2 |
| Vector Search | OpenSearch Serverless |
| Backend | AWS Lambda (Python 3.12), API Gateway REST |
| IVR | Amazon Connect contact flow |
| Database | DynamoDB (session storage, 7-day TTL) |
| Privacy | AWS Comprehend PII redaction |
| Infrastructure | AWS CDK (Python), 6 stacks |
| Hosting | S3 + CloudFront |

## Project Structure

```
HackRVA/
├── infrastructure/            # AWS CDK (Python)
│   ├── app.py                 # CDK app entry point (6 stacks)
│   ├── stacks/
│   │   ├── storage_stack.py   # DynamoDB, S3 buckets
│   │   ├── rag_stack.py       # OpenSearch Serverless collection
│   │   ├── rag_kb_stack.py    # Bedrock Knowledge Base
│   │   ├── api_stack.py       # API Gateway + Lambda orchestrator
│   │   ├── connect_stack.py   # Amazon Connect IVR
│   │   └── web_stack.py       # S3 + CloudFront website hosting
│   └── lambdas/
│       ├── orchestrator/      # Main chat handler (RAG + Claude Haiku 4.5)
│       ├── handoff/           # Nonprofit referral handler
│       ├── email_summary/     # Conversation summary emailer
│       ├── dashboard/         # Admin dashboard API
│       ├── redaction/         # PII redaction via Comprehend
│       └── doc_sync/          # Document sync to Knowledge Base
├── website/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx            # Main app with routing
│   │   ├── config.js          # 14 service categories
│   │   └── components/
│   │       ├── ChatInterface.jsx   # Chat UI, sources, handoff
│   │       ├── CategoryGrid.jsx    # Service category selector
│   │       ├── FAQs.jsx            # Bilingual FAQ page
│   │       ├── Sidebar.jsx         # Navigation sidebar
│   │       ├── Header.jsx          # Top bar with Home/Language
│   │       ├── AdminDashboard.jsx  # Manager dashboard
│   │       └── ...
│   └── public/
│       ├── biznavigator.html  # BizNavigator business startup tool
│       └── faqs.html          # Static FAQ fallback
├── connect/                   # Amazon Connect contact flow JSON
├── docs/                      # Source documents for RAG Knowledge Base
│   └── richmond-manuals/      # 10 verified city PDFs (EN + ES)
├── scripts/                   # Deployment & utility scripts
├── local-server/              # Local dev server (Featherless AI)
└── pinecone/                  # Alternative vector DB upload script
```

## Quick Start

### Prerequisites

- AWS Account with Bedrock model access enabled
- AWS CLI configured (`aws configure` with `us-east-1`)
- Python 3.12+, Node.js 18+
- AWS CDK CLI (`npm install -g aws-cdk`)

### Deploy Infrastructure

```bash
cd infrastructure
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy --all
```

### Deploy Website

```bash
cd website
cp .env.example .env
# Edit .env with your API Gateway endpoint
npm install && npm run build
aws s3 sync build/ s3://YOUR-WEBSITE-BUCKET --delete
aws cloudfront create-invalidation --distribution-id YOUR-DIST-ID --paths "/*"
```

### Deploy Lambda (direct update)

```bash
cd infrastructure
zip -j /tmp/orchestrator.zip lambdas/orchestrator/handler.py
aws lambda update-function-code --function-name richmond-orchestrator \
  --zip-file fileb:///tmp/orchestrator.zip
```

See [QUICKSTART.md](QUICKSTART.md) for the full deployment walkthrough and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed configuration.

## Service Categories

| Category | Voice (IVR) | Web | Description |
|----------|:-----------:|:---:|-------------|
| Emergency Preparedness | ✅ | ✅ | Storm damage, shelters, freezing weather safety |
| Immigration & Refugee Support | ✅ | ✅ | Legal aid, ICE rights, multilingual resources |
| Business Support Services | — | ✅ | BizNavigator: permits, licensing, contracts (online only) |
| Roads, Alleys, Sidewalks & Ramps | ✅ | ✅ | Potholes, sidewalk repair, ADA ramps |
| Lights, Signs & Traffic Signals | ✅ | ✅ | Streetlight outages, damaged signs |
| Trees & Vegetation | ✅ | ✅ | Fallen trees, overgrown vegetation |
| Parks & Public Spaces | ✅ | ✅ | Park maintenance, playground issues |
| Trash Collection & Cleanup | ✅ | ✅ | Missed pickup, illegal dumping |
| Housing & Rental Assistance | ✅ | ✅ | RRHA, emergency housing, rent assistance |
| Food & Nutrition Assistance | ✅ | ✅ | SNAP, food banks, meal programs |
| Healthcare & Mental Health | ✅ | ✅ | CrossOver, BHA crisis line, Medicaid |
| Animals | ✅ | ✅ | Stray animals, animal control |
| Water & Sewer | ✅ | ✅ | Water main breaks, sewer backups |
| Noise & Nuisance Complaints | ✅ | ✅ | Noise violations, property complaints |

## Frequently Asked Questions

> **Note:** Some responses may be limited as we did not have access to all documentation from Richmond 311 during this hackathon build. For complete and authoritative answers, please call 311 during business hours or visit [rva.gov](https://www.rva.gov).

### General

**What is RVA 311 Bridge?**
RVA 311 Bridge is a City of Richmond resource assistant that helps residents submit service requests, find city resources, and get connected to the right department — all in one place. It extends 311 services to 24/7 availability using an AI-powered assistant backed by verified Richmond city documents. Available in English, Spanish, and Arabic.

**Who can use this tool?**
Any Richmond resident or visitor can use RVA 311 Bridge to report city issues, request services, or get information. No account is required to browse or chat — you only need to create an account to track your requests over time.

**What languages are supported?**
English (EN), Spanish (ES), and Arabic (AR). You can switch languages at any time using the Language menu. The AI assistant responds in the selected language.

**Is this an official City of Richmond service?**
RVA 311 Bridge is a prototype developed at Hack4RVA 2026 to demonstrate how AI can extend 311 services after hours. It uses publicly available Richmond city documents but is not an official City service. For authoritative information, please call 311 during business hours or visit rva.gov.

**How does the AI assistant work?**
The assistant uses Retrieval Augmented Generation (RAG) to search verified Richmond city documents before answering. It does not make up information — every response is grounded in uploaded documents and cites its sources. If information is not available, it will tell you honestly and suggest contacting the appropriate agency.

### Submitting Service Requests

**What types of service requests can I submit?**
You can submit requests across 14 categories including Emergency Preparedness (storm damage, downed trees), Immigration & Refugee Support (legal aid, multilingual resources), Business Support Services (licenses, permits), Roads & Sidewalks, Lights & Traffic Signals, Trees & Vegetation, Parks & Public Spaces, Trash Collection & Cleanup, Housing & Rental Assistance, Food & Nutrition Assistance, Healthcare & Mental Health, Animals, Water & Sewer, and Noise & Nuisance Complaints.

**How do I submit a service request?**
Click a category from the home screen, then chat with the AI assistant about your issue. You can also follow the four-step form: What (category) → Where (location) → Why (description) → Who (contact info). You can submit without an account, but creating one lets you track your request.

**What happens after I submit a request?**
Your request is logged and assigned a unique Session ID. The status will show as ACTIVE while being reviewed, COMPLETED when resolved, or HANDED OFF if it has been referred to a partner nonprofit or city department.

**Can I submit a request in Spanish or Arabic?**
Yes. Switch to your preferred language using the Language toggle before starting a chat, and the assistant will respond in that language.

**What does "Handed Off" mean?**
Handed Off means your session has been forwarded to a partner agency — such as IRC Richmond, ReEstablish Richmond, Sacred Heart Center, Central Virginia Legal Aid, or another nonprofit — that is better equipped to help with your specific need.

### Emergency & Non-Emergency Issues

**What should I do in a life-threatening emergency?**
Call **911** immediately. RVA 311 Bridge is for non-emergency service requests and information only.

**Who do I call for non-emergency police matters?**
For non-emergency police situations — such as reporting downed trees blocking roads or storm damage — call the Richmond non-emergency police line at **804-646-5100**.

**What if my issue is urgent but not an emergency?**
Use the Emergency Preparedness category to flag urgent non-emergency issues like storm damage, road hazards, or freezing weather safety questions. City staff monitor these requests and prioritize accordingly.

**What crisis hotlines are available 24/7?**

| Service | Number |
|---------|--------|
| Emergency | **911** |
| Richmond BHA Crisis Line | **804-819-4100** (24/7 mental health) |
| National Crisis Line | **988** |
| Immigration Emergency | **1-855-435-7693** (1-855-HELP-MY-FAMILY) |
| Domestic Violence Hotline | **800-799-7233** |
| Human Trafficking Hotline | **888-373-7888** |

### Immigrant & Refugee Services

**Where can I get temporary housing or shelter assistance?**
Contact RRHA (Richmond Redevelopment & Housing Authority) at 804-780-4200, Dept. of Social Services Emergency Assistance at 804-646-7201, IRC Richmond for refugee-specific housing, or ReEstablish Richmond. You can also use the Hand Off button in the chat to connect directly.

**Do I need to share my immigration status to use this tool?**
**No.** RVA 311 Bridge does not collect or store immigration status, and you are never asked for it. The tool is designed with privacy-first principles — no PII is collected or stored. All residents can access services regardless of immigration status.

**What if I need legal help with an immigration issue?**
Contact Central Virginia Legal Aid Society at **804-648-1012** for free legal help. For 24/7 immigration emergency support, call **1-855-HELP-MY-FAMILY** (1-855-435-7693).

**What are my rights if I encounter ICE or CBP officers?**
Stay calm — do not run, argue, or resist. You have the right to remain silent. Do NOT open your door — officers need a warrant signed by a judge to enter. ICE administrative forms are NOT judge-signed warrants. Ask: "Are you from ICE or CBP?" For 24/7 support: 1-855-HELP-MY-FAMILY. Richmond Legal Aid: 804-648-1012.

### Business Support Services

**I want to start a business in Richmond. Where do I begin?**
Use the Business Support Services category on the home screen. It opens the RVA BizNavigator — a self-guided webpage that walks you through business registration, permits, licensing, zoning requirements, and local resources specific to your business type, location, and industry. The tool pulls live contract data from Richmond's open data portal and links to SAM.gov and eVA Virginia for procurement opportunities.

**Can I get business support over the phone?**
The Business Support Services tool is currently online only. For phone-based business assistance, contact the City of Richmond Department of Economic Development or call 311 during business hours.

### Privacy & Data

**Is my personal information kept private?**
Yes. RVA 311 Bridge is designed with privacy-first principles. No personally identifiable information (PII) is collected or stored. Chat conversations are processed with automatic PII redaction using AWS Comprehend before any data is logged.

**Will my request be visible to others?**
The Service Requests Dashboard shows aggregate anonymized data only (category counts, language distribution, etc.). Individual conversations are private and are not displayed publicly.

**What data is collected during a chat?**
The system logs: category selected, language used, message count, and session timestamps. All message content is PII-redacted before storage. No names, addresses, phone numbers, or immigration status are stored. Sessions expire automatically after 7 days.

**Can I use this tool anonymously?**
Yes. No login, account, or personal information is required to use the chat assistant. You can browse categories and ask questions completely anonymously.

### Tracking & Account

**Do I need an account to submit a request?**
No. You can chat and get assistance without signing in. However, creating a free account lets you view your request history and receive status updates via email.

**How do I check the status of my request?**
Visit the Dashboard page from the sidebar. The public dashboard shows all sessions in anonymized form. If you have admin access, you can view full session details.

**Can I get a summary of my conversation sent to me?**
Yes. At the end of a conversation, you can request a summary delivered to your email address. This is optional and your email is only used for delivery — it is not stored permanently.

## Quick Contact Numbers

| Service | Phone | Hours |
|---------|-------|-------|
| Emergency | **911** | 24/7 |
| Richmond 311 | **311** | Business hours |
| Non-Emergency Police | **804-646-5100** | 24/7 |
| Richmond BHA Crisis Line | **804-819-4100** | 24/7 mental health |
| Central Virginia Legal Aid | **804-648-1012** | Business hours |
| Immigration Emergency | **1-855-435-7693** | 24/7 (1-855-HELP-MY-FAMILY) |
| Central Virginia Foodbank | **804-521-2500** | Business hours |
| CrossOver Healthcare | **804-655-4800** | Free primary care |
| National Crisis Line | **988** | 24/7 |
| Domestic Violence Hotline | **800-799-7233** | 24/7 |
| Human Trafficking Hotline | **888-373-7888** | 24/7 |

## Nonprofit Handoff Partners

The chat interface includes a one-click handoff button to connect residents with these trusted community organizations:

| Organization | Focus Area |
|-------------|-----------|
| [IRC Richmond](https://www.rescue.org/united-states/richmond-va) | Refugee resettlement, employment, ESL |
| [ReEstablish Richmond](https://www.reestablishrichmond.org) | Immigrant integration, housing, workforce |
| [Sacred Heart Center](https://www.sacredheartcenter.org) | Latino community services, education |
| [Afghan Community Support](https://www.rescue.org) | Afghan refugee resettlement services |
| [Central Virginia Legal Aid](https://cvlas.org) | Free immigration & civil legal help |
| [Richmond BHA](https://www.rbha.org) | Mental health & substance use crisis |
| [CrossOver Healthcare Ministry](https://www.crossoverministry.org) | Free primary care for uninsured |

## Privacy by Design

RVA 311 Bridge was built with the safety and dignity of vulnerable community members as a core principle:

- **No PII collected** — no names, addresses, phone numbers, or immigration status stored
- **No login required** — fully anonymous browsing and chat
- **Automatic PII redaction** — AWS Comprehend scrubs any accidentally shared personal data before logging
- **No immigration status** — never asked, never stored, never shared
- **7-day session TTL** — all session data auto-expires from DynamoDB
- **No internal system integration** — does not connect to any agency databases (HIPAA/policy wall)
- **Source citations** — every AI response references the document it came from, no hallucination
- **Human handoff** — connects to real people at real organizations, never replaces case managers

## Knowledge Base Documents

The RAG system is powered by these verified Richmond city documents:

| Document | Languages |
|----------|-----------|
| Know Your Rights: Encounter with ICE | EN, ES |
| Staying Safe During Freezing Temperatures (SettleIn US) | EN, ES |
| Mental Health Resources for Immigrants & Refugees (USAHello) | EN, ES |
| SNAP Work Requirements Flyer | EN, ES |
| Step-by-Step Family Preparedness Plan | EN, ES |
| Richmond Family Emergency Full Documentation | EN |
| Richmond Healthcare & Medicaid Full Documentation | EN |
| Richmond Housing Full Documentation | EN |
| Richmond Immigration & Legal Full Documentation | EN |
| Richmond Job Training & Employment Full Documentation | EN |
| Richmond Mental Health Full Documentation | EN |

## Environment Variables

This project uses `.env` files that are **excluded from git** for security. Copy the example files and fill in your values:

```bash
# Website
cp website/.env.example website/.env
# Edit: VITE_API_ENDPOINT=https://YOUR-API-GATEWAY-URL/prod

# Local development server (optional)
cp local-server/.env.example local-server/.env
# Edit: FEATHERLESS_API_KEY=your_key_here
```

Lambda environment variables are set automatically by CDK:
- `KNOWLEDGE_BASE_ID` — Bedrock Knowledge Base ID
- `BEDROCK_MODEL_ID` — `us.anthropic.claude-haiku-4-5-20251001-v1:0`
- `SESSIONS_TABLE` — DynamoDB table name
- `LOGS_BUCKET` — S3 logs bucket name
- `BEDROCK_REGION` — `us-east-1`

## Additional Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Step-by-step deployment guide for hackathon |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Detailed AWS configuration reference |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | CDK stack architecture details |
| [README_INFRASTRUCTURE.md](README_INFRASTRUCTURE.md) | Infrastructure design decisions |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Live demo walkthrough script |
| [LOCAL_GROQ_SETUP.md](LOCAL_GROQ_SETUP.md) | Local development with Featherless AI |

## Team

Built at **Hack4RVA 2026** for the **Thriving & Inclusive Communities** pillar.

**Hackathon Challenge:** How might we use technology to improve access to city services for Richmond's immigrant and refugee communities — especially after hours, across languages, and without compromising privacy?

---

*RVA 311 Bridge is a hackathon prototype. It is not an official City of Richmond service. For authoritative information, call 311 during business hours or visit [rva.gov](https://www.rva.gov).*
