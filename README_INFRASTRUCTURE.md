# Richmond City 24/7 Resource Assistant - Infrastructure

Complete AWS CDK infrastructure for a hackathon project providing 24/7 citizen resource assistance via phone, combining AWS Connect IVR, Bedrock Knowledge Bases, Claude Haiku 3.5, and Amazon Comprehend PII redaction.

## Quick Start

```bash
cd infrastructure

# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk

# Configure
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_DEFAULT_REGION=us-east-1

# Deploy
cdk bootstrap aws://${AWS_ACCOUNT_ID}/us-east-1
cdk deploy --all --require-approval never
```

## What You Get

### 4 CDK Stacks

1. **StorageStack** - S3 buckets + DynamoDB
2. **RagStack** - OpenSearch Serverless + Bedrock Knowledge Base
3. **ApiStack** - Lambda functions + API Gateway
4. **ConnectStack** - AWS Connect instance + IVR contact flow

### 5 Lambda Functions

- **orchestrator** - Main conversational handler (Claude Haiku 3.5)
- **redaction** - PII detection via AWS Comprehend
- **email_summary** - Sends summaries to non-profit partners via SES
- **doc_sync** - Auto-ingests documents to Bedrock KB
- **index_creator** - Initializes OpenSearch vector index

### Key Features

- **Voice IVR**: AWS Connect with intelligent call routing
- **RAG (Retrieval-Augmented Generation)**: Bedrock KB + OpenSearch Serverless
- **Claude Haiku 3.5**: Fast, cost-effective LLM responses
- **PII Redaction**: Automatic PII detection and redaction
- **Non-profit Integration**: Email summaries of calls to partner organizations
- **Serverless**: Auto-scaling, pay-per-use, no capacity management

## Files

```
infrastructure/
├── app.py                 # CDK entry point
├── cdk.json              # CDK config
├── requirements.txt      # Python dependencies
├── VALIDATION.md         # Pre-deployment checklist
│
├── stacks/
│   ├── storage_stack.py      # S3 + DynamoDB
│   ├── rag_stack.py          # OpenSearch + Bedrock KB
│   ├── api_stack.py          # Lambdas + API Gateway
│   └── connect_stack.py      # AWS Connect + IVR
│
└── lambdas/
    ├── orchestrator/         # Conversational AI
    ├── redaction/            # PII detection
    ├── email_summary/        # Non-profit summaries
    ├── doc_sync/             # Document ingestion
    └── index_creator/        # Vector index creation
```

## Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- **IMPLEMENTATION_SUMMARY.md** - Technical architecture details
- **VALIDATION.md** - Pre-deployment validation checklist

## Architecture

```
User Call
  ↓
AWS Connect (IVR)
  ↓
Contact Flow (JSON)
  ├→ Welcome Message
  ├→ Voice Input Collection
  ├→ Orchestrator Lambda
  │  ├→ Bedrock KB Retrieval
  │  ├→ Claude Haiku Response
  │  ├→ PII Redaction
  │  └→ DynamoDB + S3 Logging
  ├→ Response Playback
  ├→ Follow-up Question
  └→ Email Summary (async)
       └→ SES to Non-profits
```

## Costs

**Estimated Monthly** (100 calls, 3 min avg):
- AWS Connect: $26
- OpenSearch Serverless: $25-100
- Bedrock API: $10-20
- Other services: <$10
- **Total: $60-150/month**

## Next Steps

1. Read DEPLOYMENT_GUIDE.md for detailed instructions
2. Run VALIDATION.md checklist
3. Deploy: `cdk deploy --all`
4. Test voice flow with claimed phone number
5. Upload knowledge base documents
6. Monitor CloudWatch logs

## Support

See documentation files for:
- Troubleshooting
- Cost optimization
- Production hardening
- Architecture decisions
- Testing checklist

---

**Project**: Richmond City 24/7 Citizen Resource Assistant
**Type**: AWS CDK Infrastructure as Code
**Language**: Python 3.12
**Status**: Production-Ready for Hackathon
