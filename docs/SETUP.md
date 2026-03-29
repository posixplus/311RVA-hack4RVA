# Richmond City Safety Net — Setup Guide

## Prerequisites

Before deploying, ensure you have:

- **AWS Account** with billing enabled (will incur ~$25/day during active deployment)
- **AWS CLI** configured with credentials (`aws configure`)
- **Python 3.9+** (`python3 --version`)
- **Node.js 18+** (`node --version`)
- **AWS CDK v2** (`npm install -g aws-cdk` or `npx cdk`)
- **Bedrock Model Access** — Claude Haiku 3.5 and Titan Embeddings V2 enabled in your region

---

## Step 1: Enable Bedrock Models (5 min)

1. Open [AWS Bedrock Console](https://console.aws.amazon.com/bedrock) (ensure region is **us-east-1**)
2. Navigate to **Model access** (left sidebar)
3. Click **Manage model access** button
4. Search for and enable:
   - **Claude 3.5 Haiku** (by Anthropic)
   - **Titan Embeddings V2** (by AWS)
5. Click **Save changes**
6. Verify status shows "Access granted" for both models

---

## Step 2: Verify SES Email Identity (5 min)

Run this command to verify an email address for sending notifications:

```bash
aws ses verify-email-identity --email-address YOUR_EMAIL@domain.com --region us-east-1
```

Check your email for an AWS verification link and click it.

**Note:** For production, verify a domain instead using `aws ses verify-domain-identity`.

---

## Step 3: Deploy Everything (15-20 min)

Set your region and deploy:

```bash
export AWS_DEFAULT_REGION=us-east-1
./scripts/deploy.sh
```

This script will:
1. Check AWS CLI, Node.js, and Python 3 are installed
2. Bootstrap AWS CDK (one-time setup)
3. Deploy 4 CloudFormation stacks in order:
   - **RichmondStorage** (S3 bucket for documents)
   - **RichmondRag** (OpenSearch + Bedrock Knowledge Base) — *Takes 10-15 min*
   - **RichmondApi** (Lambda + API Gateway)
   - **RichmondConnect** (Amazon Connect IVR)
4. Display stack outputs (API URL, Connect instance ID, etc.)

**Important:** The OpenSearch collection can take 10-15 minutes to provision. The script will complete while it deploys in the background.

---

## Step 4: Upload Richmond City Documents

Create a folder with your Richmond city documentation (PDFs, Word docs, spreadsheets, etc.):

```bash
mkdir -p ./docs/richmond-manuals
# Copy your Richmond city documents here
cp /path/to/your/docs/*.pdf ./docs/richmond-manuals/
```

Then upload them for RAG indexing:

```bash
./scripts/upload_docs.sh ./docs/richmond-manuals/
```

Supported formats: `.pdf`, `.txt`, `.docx`, `.html`, `.csv`, `.md`

**Note:** Bedrock Knowledge Base indexing happens automatically. Check progress in AWS Console:
- AWS Bedrock → Knowledge Bases → **richmond-city-kb** → Sync Status

---

## Step 5: Configure the Website

Update the frontend with your API endpoint:

```bash
cd website
cp .env.example .env.local
# Edit .env.local and replace:
#   NEXT_PUBLIC_API_URL=https://YOUR_API_GATEWAY_URL_HERE
nano .env.local
```

Then start the development server:

```bash
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

---

## Step 6: Configure Amazon Connect Phone Number

Amazon Connect requires manual phone number routing setup:

1. Go to [AWS Connect Console](https://console.aws.amazon.com/connect)
2. Click your instance **richmond-city-safety-net**
3. Navigate to **Phone Numbers** (left sidebar)
4. Select the phone number ending in the last 4 digits from deploy output
5. Under "Contact flows," select **Richmond City Main Flow**
6. Click **Save**

Now incoming calls will route to your IVR flow.

**Testing:** Call the phone number to hear the greeting and interact with the chatbot.

---

## Cost Summary

| Service | Daily Cost | Notes |
|---------|-----------|-------|
| OpenSearch Collection | ~$23 | Largest cost; stops when you run `destroy.sh` |
| Lambda | ~$1-2 | Scales with usage; included free tier generous |
| API Gateway | ~$0.50 | $3.50 per million requests |
| S3 Documents | <$0.10 | Storage only; minimal unless you store GBs |
| Bedrock (Claude calls) | ~$1-3 | On demand; varies with query volume |
| SES (email) | ~$0.10 | 62k free per month; $0.10 per 1k after |
| Amazon Connect | ~$1 | Pay-per-minute when call is active |
| **TOTAL DAILY** | **~$25-30** | |

**After Hackathon:** Run `./scripts/destroy.sh` to delete all resources and stop charges.

---

## Make Scripts Executable

After cloning, make all deployment scripts executable:

```bash
chmod +x scripts/*.sh
```

---

## Troubleshooting

### OpenSearch Collection ACTIVE but KB Still CREATING
- **Issue:** Knowledge Base status shows CREATING long after deploy.sh finishes
- **Solution:** Wait 5-10 more minutes, then refresh AWS Console. Large document uploads take time to index.
- **Check:** `./scripts/check_status.sh` to see current status

### Lambda Timeout Error (502 Bad Gateway)
- **Issue:** API returns 502 after deploy
- **Solution:** Lambda execution time too short. Increase timeout in Lambda console:
  1. Console → Lambda → richmond-city-api-handler
  2. Configuration → General settings → Timeout: **30 seconds**
  3. Save and retry

### CORS Error in Browser Console
- **Issue:** "Access to XMLHttpRequest blocked by CORS policy"
- **Solution:** Update API Gateway CORS in CloudFormation:
  1. Console → CloudFormation → RichmondApi → Outputs
  2. Add website origin (http://localhost:3000 for dev) to CORS allowed origins
  3. Or temporarily allow `*` for hackathon (not production-safe)

### SES Sandbox Mode (Can't Send Email)
- **Issue:** Email sending fails; account in SES Sandbox
- **Solution:** AWS SES starts all accounts in "Sandbox" (test mode). You must verify recipient emails:
  ```bash
  # Verify your email
  aws ses verify-email-identity --email-address your-email@example.com
  # Verify any recipient email you want to send to during hackathon
  aws ses verify-email-identity --email-address recipient@example.com
  ```
  OR request production access: AWS Console → SES → Sandbox → Request production access

### Bedrock Model Access Not Showing
- **Issue:** Claude Haiku not available in Bedrock dropdown
- **Solution:** 
  1. Confirm you're in **us-east-1** region
  2. Go to Bedrock → Model access → Manage model access
  3. Make sure you clicked **Save changes** after enabling models
  4. Wait 1-2 minutes and refresh the console

### Deploy Script Fails: "CDK not found"
- **Issue:** `command not found: cdk`
- **Solution:**
  ```bash
  npm install -g aws-cdk
  # Or use npx (no install needed):
  npx cdk --version
  ```

### Destroy Script Won't Delete Resources
- **Issue:** Some resources fail to delete
- **Solution:** Run destroy script again (idempotent), or manually delete in AWS Console:
  - CloudFormation → Stacks → Select each stack → Delete
  - Amazon Connect → Instances → Delete (manual step; not automated)

---

## Quick Health Check

Run this anytime to verify all systems are live:

```bash
./scripts/check_status.sh
```

Output shows:
- API Gateway health (HTTP 200 = healthy)
- Bedrock Knowledge Base status
- OpenSearch Collection status (and daily cost warning)
- Amazon Connect instance ID

---

## Next Steps After Deployment

1. **Test the IVR:** Call your Amazon Connect phone number
2. **Test the Website:** Open http://localhost:3000 (after starting dev server)
3. **Upload Real Docs:** Replace placeholder docs with actual Richmond city materials
4. **Invite Users:** Get phone number from Connect console output and share
5. **Monitor Costs:** Check [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/home) daily
6. **Cleanup:** Run `./scripts/destroy.sh` at end of hackathon

---

## Support & Debugging

If something breaks, check in this order:
1. Run `./scripts/check_status.sh` to diagnose
2. Check AWS CloudFormation → Events for deploy errors
3. Check Lambda CloudWatch logs: Console → Lambda → richmond-city-api-handler → Logs
4. Check Bedrock KB sync status: Bedrock → Knowledge Bases → richmond-city-kb

---

**Happy Hacking! 🏙️**
