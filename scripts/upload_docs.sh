#!/bin/bash

################################################################################
# Richmond 311 After-Hours Bridge - Document Upload Script
# Hackathon: Hack4RVA 2026
#
# Uploads documents to S3 for Bedrock Knowledge Base ingestion
# Supports: PDF, TXT, DOCX, HTML, CSV, Markdown
#
# Usage:
#   ./upload_docs.sh /path/to/documents
#   ./upload_docs.sh                    # Uses current directory
#
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================
# Step 1: Setup
# ============================================================
print_header "Richmond 311 Bridge - Document Upload"

DOCS_DIR=${1:-.}
AWS_REGION=$(aws configure get region)
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="richmond-docs-${AWS_ACCOUNT}-${AWS_REGION}"
KB_NAME="richmond-city-kb"

# Verify directory exists
if [[ ! -d "$DOCS_DIR" ]]; then
    print_error "Directory not found: $DOCS_DIR"
    exit 1
fi

print_success "AWS Region: $AWS_REGION"
print_success "AWS Account: $AWS_ACCOUNT"
print_success "Destination bucket: s3://$BUCKET/documents/"
print_success "Source directory: $DOCS_DIR"

# ============================================================
# Step 2: Count documents
# ============================================================
print_header "Step 1: Scanning Documents"

TOTAL_COUNT=0
for ext in pdf txt docx html csv md; do
    COUNT=$(find "$DOCS_DIR" -name "*.${ext}" 2>/dev/null | wc -l)
    if [[ $COUNT -gt 0 ]]; then
        print_info "Found $COUNT .$ext file(s)"
        TOTAL_COUNT=$((TOTAL_COUNT + COUNT))
    fi
done

if [[ $TOTAL_COUNT -eq 0 ]]; then
    print_warning "No supported documents found in $DOCS_DIR"
    echo ""
    echo "Supported formats: PDF, TXT, DOCX, HTML, CSV, Markdown"
    exit 1
fi

print_success "Total documents to upload: $TOTAL_COUNT"

# ============================================================
# Step 3: Upload documents
# ============================================================
print_header "Step 2: Uploading Documents to S3"

UPLOADED_COUNT=0
for ext in pdf txt docx html csv md; do
    FILES=$(find "$DOCS_DIR" -name "*.${ext}" 2>/dev/null)
    for f in $FILES; do
        FILENAME=$(basename "$f")
        print_info "Uploading: $FILENAME"
        aws s3 cp "$f" "s3://$BUCKET/documents/" --quiet
        UPLOADED_COUNT=$((UPLOADED_COUNT + 1))
    done
done

print_success "Uploaded $UPLOADED_COUNT documents to S3"

# ============================================================
# Step 4: Trigger Bedrock KB ingestion
# ============================================================
print_header "Step 3: Triggering Bedrock Knowledge Base Ingestion"

# Get Knowledge Base ID and Data Source ID from CloudFormation
KB_ID=$(aws cloudformation describe-stacks --stack-name RichmondRagStack \
    --query "Stacks[0].Outputs[?OutputKey=='KnowledgeBaseId'].OutputValue" \
    --output text --region "$AWS_REGION" 2>/dev/null || echo "")

DATA_SOURCE_ID=$(aws cloudformation describe-stacks --stack-name RichmondRagStack \
    --query "Stacks[0].Outputs[?OutputKey=='DataSourceId'].OutputValue" \
    --output text --region "$AWS_REGION" 2>/dev/null || echo "")

if [[ -z "$KB_ID" ]]; then
    print_warning "Could not find Knowledge Base ID in CloudFormation outputs"
    print_info "Knowledge Base may be in another region or not yet deployed"
    print_info "Documents are uploaded to S3 and can be ingested manually:"
    echo "  1. Go to AWS Bedrock Console"
    echo "  2. Select Knowledge Bases"
    echo "  3. Select: $KB_NAME"
    echo "  4. Go to Data sources tab"
    echo "  5. Click 'Sync' to ingest documents"
    exit 0
fi

if [[ -z "$DATA_SOURCE_ID" ]]; then
    print_warning "Could not find Data Source ID"
    exit 1
fi

print_info "Knowledge Base ID: $KB_ID"
print_info "Data Source ID: $DATA_SOURCE_ID"

# Trigger ingestion job
print_info "Starting ingestion job..."
JOB_RESPONSE=$(aws bedrock-agent start-ingestion-job \
    --knowledge-base-id "$KB_ID" \
    --data-source-id "$DATA_SOURCE_ID" \
    --region "$AWS_REGION" 2>/dev/null || echo "")

if [[ -z "$JOB_RESPONSE" ]]; then
    print_warning "Could not trigger ingestion automatically"
    print_info "Ingestion may have already started or be in progress"
    print_info "Check AWS Console → Bedrock → Knowledge Bases → $KB_NAME"
    exit 0
fi

INGESTION_JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.ingestionJob.ingestionJobId' 2>/dev/null || echo "")

if [[ ! -z "$INGESTION_JOB_ID" ]]; then
    print_success "Ingestion job started: $INGESTION_JOB_ID"
fi

# ============================================================
# Step 5: Wait for ingestion and monitor progress
# ============================================================
print_header "Step 4: Monitoring Ingestion Progress"

print_info "Checking ingestion status (this may take several minutes)..."
echo ""

# Check ingestion status with timeout
MAX_WAIT=600  # 10 minutes
ELAPSED=0
CHECK_INTERVAL=10

while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    # Get all ingestion jobs for this data source
    JOBS=$(aws bedrock-agent list-ingestion-jobs \
        --knowledge-base-id "$KB_ID" \
        --data-source-id "$DATA_SOURCE_ID" \
        --region "$AWS_REGION" 2>/dev/null || echo "")

    if [[ -z "$JOBS" ]]; then
        print_warning "Could not retrieve ingestion status"
        break
    fi

    # Get the most recent job status
    STATUS=$(echo "$JOBS" | jq -r '.ingestionJobSummaries[0].status' 2>/dev/null || echo "")

    if [[ "$STATUS" == "COMPLETE" ]]; then
        print_success "Ingestion completed successfully!"
        break
    elif [[ "$STATUS" == "FAILED" ]]; then
        print_error "Ingestion failed"
        break
    elif [[ "$STATUS" == "IN_PROGRESS" ]]; then
        STATS=$(echo "$JOBS" | jq -r '.ingestionJobSummaries[0] | "\(.statistics.numberOfDocumentsProcessed)/\(.statistics.numberOfDocuments)"' 2>/dev/null)
        print_info "In progress: $STATS documents processed"
    fi

    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
    sleep $CHECK_INTERVAL
done

# ============================================================
# Step 6: Verify document count
# ============================================================
print_header "Step 5: Verification"

# Count files in S3
S3_COUNT=$(aws s3 ls "s3://$BUCKET/documents/" --recursive | wc -l)

print_success "Documents in S3: $S3_COUNT files"
print_success "Documents uploaded to: s3://$BUCKET/documents/"

# ============================================================
# Summary
# ============================================================
print_header "Upload Complete!"

echo "Documents have been uploaded and ingestion has been triggered."
echo ""
echo "Next steps:"
echo "  1. Monitor ingestion progress in AWS Console:"
echo "     https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/knowledge-bases"
echo "  2. Once complete, your Bedrock KB will have access to these documents"
echo "  3. Test queries in the Richmond 311 Bridge Chat interface"
echo ""
echo "Ingestion typically takes:"
echo "  - Small documents (< 1 MB): 1-2 minutes"
echo "  - Medium documents (1-10 MB): 5-10 minutes"
echo "  - Large documents (> 10 MB): 10-30 minutes"
echo ""
print_success "Document upload script completed!"

exit 0
