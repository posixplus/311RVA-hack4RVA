# CDK Infrastructure Validation Checklist

## Pre-Deployment Validation

Run this checklist before deploying to ensure all files and configurations are correct.

### 1. File Structure Validation

```bash
cd HackRVA/infrastructure

# Verify all required files exist
test -f app.py && echo "✓ app.py" || echo "✗ app.py MISSING"
test -f cdk.json && echo "✓ cdk.json" || echo "✗ cdk.json MISSING"
test -f requirements.txt && echo "✓ requirements.txt" || echo "✗ requirements.txt MISSING"

# Verify stacks directory
test -f stacks/__init__.py && echo "✓ stacks/__init__.py" || echo "✗ stacks/__init__.py MISSING"
test -f stacks/storage_stack.py && echo "✓ stacks/storage_stack.py" || echo "✗ stacks/storage_stack.py MISSING"
test -f stacks/rag_stack.py && echo "✓ stacks/rag_stack.py" || echo "✗ stacks/rag_stack.py MISSING"
test -f stacks/api_stack.py && echo "✓ stacks/api_stack.py" || echo "✗ stacks/api_stack.py MISSING"
test -f stacks/connect_stack.py && echo "✓ stacks/connect_stack.py" || echo "✗ stacks/connect_stack.py MISSING"

# Verify Lambda directories
for lambda in orchestrator redaction email_summary doc_sync index_creator; do
  test -f lambdas/$lambda/handler.py && echo "✓ lambdas/$lambda/handler.py" || echo "✗ lambdas/$lambda/handler.py MISSING"
done
```

### 2. Python Syntax Validation

```bash
cd HackRVA/infrastructure

# Check for syntax errors
python3 -m py_compile app.py
python3 -m py_compile stacks/storage_stack.py
python3 -m py_compile stacks/rag_stack.py
python3 -m py_compile stacks/api_stack.py
python3 -m py_compile stacks/connect_stack.py

# Check Lambda handlers
for handler in lambdas/*/handler.py; do
  python3 -m py_compile "$handler" && echo "✓ $handler" || echo "✗ $handler SYNTAX ERROR"
done
```

### 3. CDK Validation

```bash
cd HackRVA/infrastructure

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk

# Validate CDK stacks
cdk list
# Should output:
# RichmondStorage
# RichmondRag
# RichmondApi
# RichmondConnect

# Synthesize CloudFormation templates
cdk synth
# Should produce CloudFormation JSON without errors
```

### 4. AWS Account Validation

```bash
# Check AWS credentials
aws sts get-caller-identity
# Should return: UserId, Account, Arn

# Get account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Check region
export AWS_DEFAULT_REGION=$(aws configure get region)
echo "AWS Region: $AWS_DEFAULT_REGION"

# Verify Bedrock model availability
aws bedrock list-foundation-models --region $AWS_DEFAULT_REGION | grep claude

# Verify OpenSearch Serverless is available
aws opensearchserverless list-collections --region $AWS_DEFAULT_REGION 2>/dev/null || echo "OpenSearch Serverless available"

# Verify AWS Connect is available
aws connect describe-instance --region $AWS_DEFAULT_REGION 2>/dev/null || echo "Connect available"
```

### 5. Environment Variable Validation

```bash
# Required environment variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Optional but recommended
export NONPROFIT_EMAILS="nonprofit1@example.com,nonprofit2@example.com"

# Verify
echo "Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_DEFAULT_REGION"
echo "Non-profits: $NONPROFIT_EMAILS"
```

### 6. SES Setup Validation

```bash
# Verify SES is available in your region
aws ses list-verified-email-addresses --region $AWS_DEFAULT_REGION

# Verify sender email is configured
aws ses verify-email-identity \
  --email-address noreply@richmond-assistant.com \
  --region $AWS_DEFAULT_REGION

# Check SES sandbox status
aws ses get-account-sending-enabled --region $AWS_DEFAULT_REGION
# Returns: SendingEnabled: true/false
```

### 7. Code Quality Checks

```bash
cd HackRVA/infrastructure

# Check imports are correct
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

# Verify imports work
try:
    from stacks.storage_stack import StorageStack
    print("✓ StorageStack imports")
except Exception as e:
    print(f"✗ StorageStack import error: {e}")

try:
    from stacks.rag_stack import RagStack
    print("✓ RagStack imports")
except Exception as e:
    print(f"✗ RagStack import error: {e}")

try:
    from stacks.api_stack import ApiStack
    print("✓ ApiStack imports")
except Exception as e:
    print(f"✗ ApiStack import error: {e}")

try:
    from stacks.connect_stack import ConnectStack
    print("✓ ConnectStack imports")
except Exception as e:
    print(f"✗ ConnectStack import error: {e}")
EOF
```

### 8. Lambda Code Validation

```bash
cd HackRVA/infrastructure

# Verify Lambda handlers have required elements
python3 << 'EOF'
import os
import json

handlers = {
    "lambdas/orchestrator/handler.py": ["lambda_handler", "retrieve_from_kb", "generate_response"],
    "lambdas/redaction/handler.py": ["lambda_handler", "redact_pii"],
    "lambdas/email_summary/handler.py": ["lambda_handler", "send_email"],
    "lambdas/doc_sync/handler.py": ["lambda_handler", "start_ingestion_job"],
    "lambdas/index_creator/handler.py": ["lambda_handler"],
}

for filepath, required_functions in handlers.items():
    if os.path.exists(filepath):
        with open(filepath) as f:
            content = f.read()

        missing = [fn for fn in required_functions if f"def {fn}" not in content]
        if missing:
            print(f"✗ {filepath} missing: {missing}")
        else:
            print(f"✓ {filepath} has all required functions")
    else:
        print(f"✗ {filepath} NOT FOUND")
EOF
```

### 9. Stack Dependencies Validation

```bash
cd HackRVA/infrastructure

# Verify stack dependency order
python3 << 'EOF'
from aws_cdk import App
from stacks.storage_stack import StorageStack
from stacks.rag_stack import RagStack
from stacks.api_stack import ApiStack
from stacks.connect_stack import ConnectStack

app = App()

# Try to create stacks
try:
    storage = StorageStack(app, "TestStorage")
    rag = RagStack(app, "TestRag", storage_stack=storage)
    api = ApiStack(app, "TestApi", storage_stack=storage, rag_stack=rag)
    connect = ConnectStack(app, "TestConnect", api_stack=api)

    print("✓ All stacks can be instantiated")
    print("✓ Stack dependencies are correct")
except Exception as e:
    print(f"✗ Stack instantiation error: {e}")
EOF
```

### 10. JSON Validation

```bash
# Validate cdk.json is valid JSON
python3 -c "import json; json.load(open('cdk.json'))" && echo "✓ cdk.json is valid" || echo "✗ cdk.json is invalid"
```

---

## Deployment Validation Checklist

After deployment, verify:

### Post-Deployment Checks

```bash
# Check stack creation
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE \
  --region $AWS_DEFAULT_REGION | grep -i richmond

# Verify S3 buckets
aws s3 ls | grep richmond-

# Verify DynamoDB table
aws dynamodb list-tables --region $AWS_DEFAULT_REGION | grep richmond

# Verify Lambda functions
aws lambda list-functions --region $AWS_DEFAULT_REGION | grep richmond

# Verify API Gateway
aws apigateway get-rest-apis --region $AWS_DEFAULT_REGION | grep richmond

# Verify Connect instance
aws connect list-instances --region $AWS_DEFAULT_REGION | grep richmond
```

### Manual Testing

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name RichmondApi \
  --region $AWS_DEFAULT_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"

# Test /health endpoint
curl $API_ENDPOINT/health

# Test /chat endpoint
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

---

## Common Issues & Fixes

### Issue: "User is not authorized to perform: bedrock:..."
**Fix**: Ensure IAM user has Bedrock permissions
```bash
# Add policy
aws iam attach-user-policy \
  --user-name YOUR_USER \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### Issue: "Could not find cfnresponse module"
**Fix**: cfnresponse is built-in for CloudFormation custom resources
- Ensure index_creator/handler.py has: `import cfnresponse`
- Lambda runtime must be Python 3.12

### Issue: "OpenSearch collection not found"
**Fix**: Collections take 1-2 minutes to initialize
- Wait 2-3 minutes after stack creation
- Check status: `aws opensearchserverless list-collections`

### Issue: "Contact Flow JSON validation error"
**Fix**: Ensure Connect flow JSON is valid
- Verify all transitions have NextAction
- Check that all Actions are defined
- Use AWS Connect console to validate flow JSON

### Issue: "SES email not sending"
**Fix**: Verify SES setup
```bash
# Check SES status
aws ses get-account-sending-enabled

# Verify sender email
aws ses list-verified-email-addresses

# Add verified recipient (sandbox mode)
aws ses verify-email-identity --email-address recipient@example.com
```

---

## Validation Summary Template

Copy and fill this out before deployment:

```
Pre-Deployment Validation Results
===================================

Date: ________________
AWS Account ID: ________________
Region: ________________
User: ________________

File Structure:       [ ] PASS  [ ] FAIL
Python Syntax:       [ ] PASS  [ ] FAIL
CDK Validation:      [ ] PASS  [ ] FAIL
AWS Credentials:     [ ] PASS  [ ] FAIL
Environment Vars:    [ ] PASS  [ ] FAIL
SES Setup:          [ ] PASS  [ ] FAIL
Code Quality:       [ ] PASS  [ ] FAIL
Lambda Functions:   [ ] PASS  [ ] FAIL
Stack Dependencies: [ ] PASS  [ ] FAIL
JSON Validation:    [ ] PASS  [ ] FAIL

Overall Status: [ ] READY FOR DEPLOYMENT  [ ] NOT READY - ISSUES FOUND

Issues Found:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

Approved By: ________________  Date: ________________
```

---

**Validation Checklist for Richmond City 24/7 Resource Assistant**
**Last Updated**: March 27, 2026
