# RVA 311 Bridge — Quick Start Deployment Guide

**Hackathon: Hack4RVA 2026 | Pillar: Thriving and Inclusive Communities**
**Demo deadline: Saturday March 28, 2026 at 6 PM**

---

## What You're Deploying

A 24/7 AI-powered multilingual service assistant that extends Richmond's 311 system with:

- **Web chatbot** — RVA311-styled interface with all 14 service categories + enhanced immigrant/refugee support
- **IVR phone line** — Call in, select language (English/Spanish/Arabic), describe your need, get answers
- **RAG knowledge base** — Powered by your 10 uploaded PDFs (SNAP, ICE rights, mental health, emergency prep, freezing weather)
- **Manager dashboard** — Public redacted view + password-protected full view
- **Nonprofit handoff** — Demo hand-off to IRC Richmond, Sacred Heart Center, etc.
- **PII redaction** — All public data is automatically scrubbed via AWS Comprehend

**Privacy notice displayed on every interaction:**
> "This is a private service request and will not be posted publicly. It is not mandatory but you can create an account or sign in with your existing account, both of which can be done by continuing with your request. If you do not sign in, you will only receive email notifications for changes in request status. There will be no PII collected."

---

## Prerequisites (5 minutes)

1. **AWS Account** with $1000 credits activated
2. **AWS CLI installed and configured:**
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region: us-east-1, Output: json
   ```
3. **Node.js 18+** and **Python 3.9+** installed
4. **Bedrock model access enabled** in us-east-1:
   - Go to AWS Console → Amazon Bedrock → Model access
   - Enable: **Claude 3.5 Haiku** and **Titan Text Embeddings V2**
   - (Takes 1-2 minutes to activate)

**Not sure if you're ready?** Run the setup helper:
```bash
cd HackRVA
bash scripts/setup_aws.sh
```

---

## Deploy Everything (15-25 minutes)

### Option A: One-command deploy
```bash
cd HackRVA
bash scripts/deploy.sh
```

This will:
1. Check all prerequisites
2. Install CDK and Python dependencies
3. Bootstrap CDK in your account
4. Deploy 5 CloudFormation stacks (Storage → RAG → API → Connect → Web)
5. Upload your 10 PDF documents to the knowledge base
6. Build and deploy the website to S3 + CloudFront
7. Trigger Bedrock KB ingestion
8. Print all URLs and the phone number

### Option B: Step by step
```bash
# 1. Install dependencies
cd HackRVA/infrastructure
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk

# 2. Set environment
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_DEFAULT_REGION=us-east-1

# 3. Bootstrap and deploy
cdk bootstrap aws://${AWS_ACCOUNT_ID}/us-east-1
cdk deploy --all --require-approval never

# 4. Upload documents
cd ../scripts
bash upload_docs.sh ../docs/

# 5. Build and deploy website
cd ../website
echo "VITE_MODE=aws" > .env
echo "VITE_API_ENDPOINT=<YOUR_API_GATEWAY_URL>" >> .env
npm install && npm run build
aws s3 sync build s3://richmond-website-${AWS_ACCOUNT_ID}-us-east-1
```

---

## After Deployment

### Get your endpoints
```bash
# API endpoint
aws cloudformation describe-stacks --stack-name RichmondApi \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text

# Website URL (CloudFront)
aws cloudformation describe-stacks --stack-name RichmondWeb \
  --query 'Stacks[0].Outputs' --output table

# Connect instance
aws cloudformation describe-stacks --stack-name RichmondConnect \
  --query 'Stacks[0].Outputs' --output table
```

### Claim a phone number
1. AWS Console → Amazon Connect → `richmond-city-assistant`
2. Phone numbers → Claim a number → US → DID
3. Assign to "Richmond City Main Flow"
4. Cost: ~$1/month + $0.018/min

### Verify SES (for email delivery)
```bash
aws ses verify-email-identity --email-address your-email@gmail.com --region us-east-1
```

### Update website with real endpoints
```bash
cd HackRVA/website
cat > .env << EOF
VITE_MODE=aws
VITE_API_ENDPOINT=https://xxxxxx.execute-api.us-east-1.amazonaws.com/prod/
VITE_CONNECT_PHONE=(804) 555-3112
EOF
npm run build
aws s3 sync build s3://richmond-website-${AWS_ACCOUNT_ID}-us-east-1
```

---

## Demo Flow (for the 6 PM presentation)

### Web Demo
1. Open CloudFront URL in browser
2. Show the RVA311-style category grid
3. Click "Request Support Services" → "Immigrant and Refugee Services"
4. Chat: "I need help with food assistance for my family"
5. Show the AI response with cited sources from the RAG documents
6. Click "I'm satisfied" → enter email for summary delivery
7. Show "Hand off to Sacred Heart Center" button
8. Switch to Dashboard → show redacted public view
9. Log in as manager (password: `richmond311admin`) → show full view

### IVR Demo
1. Call the claimed phone number
2. Press 2 for Spanish
3. Say: "Necesito ayuda con beneficios SNAP"
4. Listen to the AI response in Spanish
5. Show the call summary that gets emailed to the nonprofit

### Dashboard Demo
1. Show `/dashboard` — public view with all interactions redacted
2. Show `/dashboard/admin` — manager login with full details
3. Show export to CSV

---

## Tear Down (after demo, or after 2 days)

```bash
cd HackRVA
bash scripts/destroy.sh
```

This empties all S3 buckets, destroys all CloudFormation stacks, and cleans up resources.

**Estimated 2-day cost: $80-120** (well within your $1000 budget)

| Service | 2-Day Cost |
|---------|-----------|
| OpenSearch Serverless | $6-10 |
| CloudFront | Free tier |
| Lambda | < $1 |
| Connect (phone) | $1 + calls |
| Bedrock (RAG + Claude) | $5-20 |
| DynamoDB | < $1 |
| S3 | < $1 |
| **Total** | **$15-35** |

If left running for 30 days: ~$150-300 (OpenSearch Serverless is the main cost driver).

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         CloudFront CDN           │
                    │    (richmond-website.d12345)     │
                    └────────────┬────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
    ┌─────────▼──────┐  ┌───────▼────────┐  ┌──────▼──────────┐
    │  React Website  │  │  API Gateway   │  │  AWS Connect    │
    │  (S3 Hosted)    │  │  /chat /health │  │  IVR Phone Line │
    │  RVA311 Style   │  │  /sessions     │  │  EN/ES/AR       │
    └────────────────┘  │  /dashboard    │  └───────┬─────────┘
                        │  /handoff      │          │
                        └───────┬────────┘          │
                                │                   │
                    ┌───────────▼───────────────────▼──┐
                    │     Orchestrator Lambda           │
                    │  • Bedrock KB Retrieval (RAG)     │
                    │  • Claude Haiku 3.5 Response      │
                    │  • Session Management (DynamoDB)  │
                    │  • PII Redaction (Comprehend)     │
                    │  • Conversation Logging (S3)      │
                    └──────────┬────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼─────┐ ┌───────▼──────────┐
    │  Bedrock KB    │ │  DynamoDB  │ │  Email/Handoff   │
    │  10 PDF docs   │ │  Sessions  │ │  SES → Nonprofits│
    │  Vector search │ │  Handoffs  │ │  SNS → SMS       │
    └────────────────┘ └────────────┘ └──────────────────┘
```

---

## File Structure

```
HackRVA/
├── QUICKSTART.md                    ← You are here
├── infrastructure/
│   ├── app.py                       CDK entry (5 stacks)
│   ├── stacks/
│   │   ├── storage_stack.py         S3 + DynamoDB
│   │   ├── rag_stack.py             OpenSearch + Bedrock KB
│   │   ├── api_stack.py             6 Lambdas + API Gateway
│   │   ├── connect_stack.py         IVR (multilingual)
│   │   └── web_stack.py             CloudFront + S3 website
│   └── lambdas/
│       ├── orchestrator/handler.py  Main chat engine
│       ├── redaction/handler.py     PII detection
│       ├── email_summary/handler.py Email/SMS delivery
│       ├── dashboard/handler.py     Dashboard API
│       ├── handoff/handler.py       Nonprofit handoff
│       └── doc_sync/handler.py      Document ingestion
├── website/
│   ├── src/
│   │   ├── App.jsx                  Main app with routing
│   │   ├── config.js                Categories + demo responses
│   │   ├── styles/rva311.css        RVA311-styled CSS
│   │   └── components/
│   │       ├── Sidebar.jsx          Navy sidebar nav
│   │       ├── Header.jsx           RVA311-style header
│   │       ├── CategoryGrid.jsx     Service category grid
│   │       ├── ChatInterface.jsx    AI chatbot with voice
│   │       ├── CallOption.jsx       IVR call option
│   │       ├── ConversationEnd.jsx  Satisfaction + delivery
│   │       ├── Dashboard.jsx        Public redacted view
│   │       └── AdminDashboard.jsx   Manager view (password)
│   └── package.json
├── scripts/
│   ├── deploy.sh                    One-command deploy
│   ├── destroy.sh                   Teardown (2-day cleanup)
│   ├── upload_docs.sh               PDF document ingestion
│   └── setup_aws.sh                 AWS setup helper
└── docs/                            Put your 10 PDFs here
```

---

## Manager Dashboard Access

- **Public view:** `https://<cloudfront-url>/dashboard`
  - All PII redacted (emails, phones show as [REDACTED])
  - Anyone can see interaction summaries

- **Manager view:** `https://<cloudfront-url>/dashboard/admin`
  - Password: `richmond311admin`
  - Full email/phone visible
  - CSV export available
  - Conversation detail view

---

## Troubleshooting

**CDK deploy fails with "resource already exists"**
→ The Connect instance alias must be globally unique. Edit `connect_stack.py` and change `richmond-city-assistant` to something unique.

**Bedrock returns empty responses**
→ Ensure model access is enabled AND documents have been ingested. Run `bash scripts/upload_docs.sh ./docs/` and wait 2-3 minutes.

**Website shows "Error connecting"**
→ Check your `.env` file has the correct `VITE_API_ENDPOINT` URL ending with `/prod/`

**SES emails not sending**
→ In sandbox mode, you must verify BOTH sender and recipient emails. Run `aws ses verify-email-identity --email-address ...`

---

**Built at Hack4RVA 2026 | Thriving and Inclusive Communities Pillar**
*The phone call that was a dead end is now a bridge.*
