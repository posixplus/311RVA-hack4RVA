#!/bin/bash
# Quick health check for all deployed resources

AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🏙️  Richmond Safety Net — Status Check"
echo "========================================"
echo ""

# API Gateway
API_URL=$(aws cloudformation describe-stacks --stack-name RichmondApi \
  --query "Stacks[0].Outputs[?OutputKey=='RichmondApiUrl'].OutputValue" \
  --output text 2>/dev/null)

if [ -n "$API_URL" ]; then
  echo "✅ API Gateway: $API_URL"
  # Health check
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}health" 2>/dev/null || echo "ERR")
  echo "   Health check: HTTP $STATUS"
else
  echo "❌ API Gateway: Not deployed"
fi

echo ""

# Bedrock KB
KB_STATUS=$(aws bedrock list-knowledge-bases \
  --query "knowledgeBaseSummaries[?name=='richmond-city-kb'].status" \
  --output text 2>/dev/null)
echo "🧠 Bedrock Knowledge Base: ${KB_STATUS:-Not found}"

# OpenSearch Collection
COLL_STATUS=$(aws opensearchserverless list-collections \
  --query "collectionSummaries[?name=='richmond-kb'].status" \
  --output text 2>/dev/null)
echo "🔍 OpenSearch Collection: ${COLL_STATUS:-Not found}"
[ "$COLL_STATUS" = "ACTIVE" ] && echo "   💰 Cost: ~$23/day while ACTIVE"

echo ""

# Connect
CONNECT_ID=$(aws cloudformation describe-stacks --stack-name RichmondConnect \
  --query "Stacks[0].Outputs[?OutputKey=='ConnectInstanceId'].OutputValue" \
  --output text 2>/dev/null)
if [ -n "$CONNECT_ID" ]; then
  echo "📞 Amazon Connect: Instance $CONNECT_ID"
else
  echo "❌ Amazon Connect: Not deployed"
fi

echo ""
echo "💡 Tip: Run ./scripts/destroy.sh when done demoing to stop all charges."
