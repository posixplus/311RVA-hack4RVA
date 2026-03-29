# Richmond City 24/7 Resource Assistant - Deployment Guide

A complete AWS CDK infrastructure implementation for a 24/7 citizen resource assistant using AWS Connect IVR, Bedrock Knowledge Bases, Claude Haiku 3.5, and Amazon Comprehend PII redaction.

## Project Structure

```
HackRVA/infrastructure/
├── app.py                          # CDK app entry point
├── cdk.json                        # CDK configuration
├── requirements.txt                # Python dependencies
├── stacks/
│   ├── __init__.py
│   ├── storage_stack.py           # S3 + DynamoDB
│   ├── rag_stack.py               # OpenSearch + Bedrock KB
│   ├── api_stack.py               # Lambda functions + API Gateway
│   └── connect_stack.py           # AWS Connect + Contact Flow
└── lambdas/
    ├── orchestrator/              # Main conversational handler
    ├── redaction/                 # PII detection via Comprehend
    ├── email_summary/             # Non-profit email summaries
    ├── doc_sync/                  # Document ingestion trigger
    └── index_creator/             # OpenSearch index initialization
```

## Stack Overview

### 1. StorageStack (RichmondStorage)
- **S3 Doc Bucket**: `richmond-docs-{account}-{region}`
  - Versioned, CORS-enabled for demo site, 30-day lifecycle
  - Contains knowledge base documents (PDFs, TXT, DOCX)

- **S3 Logs Bucket**: `richmond-logs-{account}-{region}`
  - Stores call transcripts and conversation logs
  - Used for non-profit partner summaries

- **DynamoDB Table**: `richmond-call-sessions`
  - Tracks active call sessions (7-day TTL)
  - Partition key: sessionId | Sort key: timestamp

### 2. RagStack (RichmondRag)
**Depends on**: StorageStack

- **OpenSearch Serverless Collection**: `richmond-kb`
  - Type: VECTORSEARCH
  - Stores vector embeddings for semantic search
  - Encryption + Network policies configured

- **Bedrock Knowledge Base**: `richmond-city-kb`
  - Model: Titan Embed Text v2 (embeddings)
  - Retrieves context for Claude responses

- **Bedrock Data Source**: `richmond-docs-source`
  - Syncs documents from S3 to KB
  - Chunking: Fixed 512-token chunks with 20% overlap

- **Custom Lambda**: Index Creator
  - Initializes OpenSearch vector index during deployment

### 3. ApiStack (RichmondApi)
**Depends on**: StorageStack, RagStack

- **Orchestrator Lambda** (`richmond-orchestrator`)
  - Runtime: Python 3.12 | Timeout: 30s | Memory: 512MB
  - Routes user input → KB retrieval → Claude response
  - Calls redaction + email Lambdas

- **Redaction Lambda** (`richmond-redaction`)
  - Detects PII using AWS Comprehend
  - Returns redacted text + entity detection

- **Email Summary Lambda** (`richmond-email-summary`)
  - Sends call summaries to non-profit partners via SES
  - Retrieves conversation logs from S3
  - Generates HTML email reports

- **Doc Sync Lambda** (`richmond-doc-sync`)
  - S3 event trigger: `documents/*.pdf|txt|docx`
  - Initiates Bedrock KB ingestion jobs

- **API Gateway REST API**: `richmond-api`
  - **POST /chat**: Send message → get Claude response
  - **GET /health**: Status check
  - CORS enabled (all origins for demo)
  - Deploy stage: `prod`

### 4. ConnectStack (RichmondConnect)
**Depends on**: ApiStack

- **AWS Connect Instance**: `richmond-city-assistant`
  - Identity management: CONNECT_MANAGED
  - Inbound calls enabled

- **Contact Flow**: `Richmond City Main Flow`
  - Welcomes caller
  - Collects voice input via IVR
  - Invokes Orchestrator Lambda
  - Plays Claude response
  - Asks follow-up question
  - Sends conversation summary to non-profits
  - Disconnects

- **Phone Number**: DID (Direct Inward Dialing)
  - Cost: ~$1/month + $0.018/minute for calls
  - Routed to contact flow

## Prerequisites

### AWS Account Setup
1. **AWS Account** with sufficient permissions
2. **IAM User** with CDK deployment permissions
   - Policy: `AdministratorAccess` (or custom with CDK+Bedrock+Connect permissions)
3. **AWS CLI** configured: `aws configure`
4. **Python 3.9+** installed
5. **Node.js 14+** installed (for AWS CDK CLI)

### AWS Service Permissions
- Bedrock KB and Model creation
- OpenSearch Serverless access
- AWS Connect instance creation
- SES email sending (requires verified sender address)
- DynamoDB, S3, Lambda, API Gateway access

### SES Email Verification (CRITICAL)
Before deploying, verify sender email in SES:
```bash
# In the AWS Console or CLI
aws ses verify-email-identity --email-address noreply@richmond-assistant.com --region us-east-1

# OR verify domain
aws ses verify-domain-identity --domain richmond-assistant.com --region us-east-1
```

**Note**: In SES sandbox mode, recipients must also be verified individually.

## Installation & Deployment

### 1. Install CDK and Dependencies
```bash
# Install AWS CDK CLI globally
npm install -g aws-cdk

# Navigate to infrastructure directory
cd HackRVA/infrastructure

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Required AWS credentials (from aws configure)
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_DEFAULT_REGION=us-east-1  # Or your preferred region

# Optional: Set non-profit email recipients
export NONPROFIT_EMAILS="nonprofit1@example.com,nonprofit2@example.com"
```

### 3. Bootstrap CDK (first time only)
```bash
cdk bootstrap aws://${AWS_ACCOUNT_ID}/us-east-1
```

### 4. Validate Stacks
```bash
# Check that CDK files are valid Python
cdk synth

# Or list stacks
cdk list
```

### 5. Deploy Stacks
```bash
# Deploy all stacks (with dependency order automatically handled)
cdk deploy --all --require-approval never

# OR deploy individual stacks in order
cdk deploy RichmondStorage
cdk deploy RichmondRag
cdk deploy RichmondApi
cdk deploy RichmondConnect
```

**Note**: Deployment takes 10-20 minutes (OpenSearch Serverless takes the longest).

### 6. Retrieve Outputs
After deployment, note the outputs:
```bash
# API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name RichmondApi \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)

# Connect instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks --stack-name RichmondConnect \
  --query 'Stacks[0].Outputs[?OutputKey==`ConnectInstanceId`].OutputValue' --output text)

echo "API: $API_ENDPOINT"
echo "Instance: $INSTANCE_ID"
```

## Post-Deployment Configuration

### 1. Update Connect Instance Alias (IMPORTANT)
The default instance alias `richmond-city-assistant` must be globally unique. If deployment fails:
1. Edit `/HackRVA/infrastructure/stacks/connect_stack.py`
2. Change `instance_alias="richmond-city-assistant"` to unique value
3. Redeploy: `cdk deploy RichmondConnect`

### 2. Claim a Phone Number
1. Go to AWS Connect console
2. Select the `richmond-city-assistant` instance
3. **Phone numbers** → **Claim a number**
4. Choose country (US), type (DID), assign to `Richmond City Main Flow`
5. Costs: ~$1/month + $0.018/minute

### 3. Upload Knowledge Base Documents
```bash
# Upload sample documents to S3
aws s3 cp sample_housing.pdf s3://richmond-docs-${AWS_ACCOUNT_ID}-us-east-1/documents/
aws s3 cp sample_food_assistance.txt s3://richmond-docs-${AWS_ACCOUNT_ID}-us-east-1/documents/

# Doc Sync Lambda automatically triggers Bedrock KB ingestion
# Check status in Bedrock console: Data sources → richmond-docs-source → Ingestion jobs
```

### 4. Verify SES Setup
```bash
# Send test email
aws ses send-email \
  --from noreply@richmond-assistant.com \
  --to nonprofit1@example.com \
  --subject "Test Email" \
  --text "Test message"

# Check send quota
aws ses get-account-sending-enabled
```

### 5. Test the API
```bash
# Test /chat endpoint
curl -X POST ${API_ENDPOINT}chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I need help with housing"}'

# Test /health endpoint
curl ${API_ENDPOINT}health
```

## Usage

### Voice Call Flow
1. **Call the claimed phone number**
2. IVR welcomes caller and asks for help
3. Caller speaks their question
4. **Orchestrator Lambda**:
   - Retrieves relevant documents from Bedrock KB
   - Generates response using Claude Haiku 3.5
   - Detects PII via Comprehend
5. **Claude response** played back to caller
6. IVR asks follow-up question
7. Conversation log saved to S3
8. **Email Summary Lambda** sends summary to non-profits
9. Call disconnects

### API Requests
```bash
# Chat request
POST /chat
{
  "message": "I need emergency housing assistance",
  "sessionId": "optional-session-id"
}

Response:
{
  "response": "Based on emergency housing in Richmond...",
  "sessionId": "auto-generated-id",
  "context": "Retrieved knowledge base context"
}
```

## Monitoring & Logs

### CloudWatch Logs
```bash
# Orchestrator Lambda logs
aws logs tail /aws/lambda/richmond-orchestrator --follow

# API Gateway logs
aws logs tail /aws/apigateway/richmond-api --follow

# Connect activity logs
# View in AWS Connect console → Contact flows → Richmond City Main Flow
```

### DynamoDB Sessions
```bash
# Query active sessions
aws dynamodb scan --table-name richmond-call-sessions \
  --scan-index-forward false | head -10
```

### S3 Logs
```bash
# List conversation logs
aws s3 ls s3://richmond-logs-${AWS_ACCOUNT_ID}-us-east-1/logs/ --recursive
```

## Cleanup

### Remove All Resources
```bash
# Delete all stacks (reverse order)
cdk destroy --all --force

# Manually delete any resources not managed by CDK:
# - Phone number (AWS Connect console)
# - SES verified email addresses (if created separately)
```

**Warning**: This deletes S3 buckets, DynamoDB tables, and all data. Ensure backups are taken.

## Cost Estimation

### Monthly Costs (Hackathon Scale: ~100 calls)
| Service | Quantity | Cost/Unit | Monthly |
|---------|----------|-----------|---------|
| AWS Connect instance | 1 | $20 | $20 |
| Phone number | 1 | $1 | $1 |
| Inbound calls | 100 | $0.018/min (avg 3 min) | $5.40 |
| OpenSearch Serverless | 1 | $25-100 | $25-100 |
| Bedrock API calls | 100 | $0.00035/input token | ~$10-20 |
| Lambda (5GB-s) | 5 | $0.0000002/GB-s | <$1 |
| DynamoDB (on-demand) | - | $1.25/million WCU | <$1 |
| S3 (1GB storage) | 1 | $0.023/GB | <$1 |
| SES (100 emails) | 100 | $0.10/1000 | <$1 |
| **Total** | | | **$60-150/month** |

Actual costs depend on usage patterns and region.

## Troubleshooting

### CDK Deployment Fails
**Error**: "User: ... is not authorized to perform: bedrock:..."
- Solution: Ensure IAM user has Bedrock permissions
- Update IAM policy or use root account (dev only)

**Error**: "Could not locate cfnresponse"
- Solution: Custom resource Lambda needs cfnresponse module
- Already included in index_creator/handler.py

### OpenSearch Index Not Created
- Check Lambda logs: `/aws/lambda/richmond-index-creator`
- Ensure collection endpoint is reachable
- Verify data access policy includes index creator role

### SES Emails Not Sending
- Verify sender email address is verified in SES
- Check SES quota: `aws ses get-account-sending-enabled`
- Ensure recipient email addresses are verified (if in sandbox mode)
- Review SES Suppression List for bounced addresses

### Contact Flow Not Invoked
- Verify Lambda integration in Connect console
- Check Lambda invoke permission for Connect service
- Review Contact Flow history in Connect dashboard
- Test Lambda directly: `aws lambda invoke --function-name richmond-orchestrator ...`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Connect (IVR)                       │
│                   richmond-city-assistant                   │
│                    [+1-XXX-XXX-XXXX]                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │    Contact Flow JSON         │
          │  - Welcome/Input/Process     │
          │  - Invoke Orchestrator       │
          │  - Play Response             │
          │  - Email to Non-profits      │
          └────────────┬─────────────────┘
                       │
         ┌─────────────▼──────────────┐
         │  Orchestrator Lambda       │
         │  richmond-orchestrator     │
         │  Python 3.12 | 512MB       │
         │  - Retrieve from KB        │
         │  - Call Claude Haiku       │
         │  - Store session/logs      │
         │  - Async email trigger     │
         └────────┬────────┬──────────┘
                  │        │
         ┌────────▼──┐  ┌──▼──────────────┐
         │  Bedrock  │  │  DynamoDB Table │
         │     KB    │  │  (sessions)     │
         │  + Claude │  │                 │
         │  Haiku    │  │  S3 Logs Bucket │
         └───────────┘  └─────────────────┘

      ┌─────────────────────────────────┐
      │   Email Summary Lambda          │
      │   richmond-email-summary        │
      │                                 │
      │   Retrieves logs from S3        │
      │   Sends via SES to Non-profits  │
      └─────────────────────────────────┘
```

## Support & Next Steps

### For Hackathon Completion
1. Deploy stacks and test voice flow
2. Upload sample knowledge base documents
3. Process sample calls and verify email summaries
4. Document lessons learned

### For Production Hardening
1. Implement authentication for API
2. Add rate limiting and request validation
3. Set up CloudWatch alarms for Lambda errors
4. Implement database backups and snapshots
5. Use VPC endpoints for OpenSearch (remove public access)
6. Add CloudFront distribution for API
7. Implement call recording and compliance logging

### References
- [AWS Connect Developer Guide](https://docs.aws.amazon.com/connect/latest/adminguide/)
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-bases.html)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Claude Haiku API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)

---

**Project**: Richmond City 24/7 Citizen Resource Assistant
**Hackathon**: HackRVA 2026
**Last Updated**: March 27, 2026
