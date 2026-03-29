#!/bin/bash

################################################################################
# Richmond 311 After-Hours Bridge - Complete Deployment Script
# Hackathon: Hack4RVA 2026
#
# This script automates the entire deployment of the Richmond 311 Bridge
# infrastructure on AWS, including all 5 CDK stacks.
#
# Estimated time: 15-25 minutes
# Estimated 2-day cost: ~$80-120 (well within $1000 hackathon budget)
#
# Prerequisites:
#   - AWS CLI configured with valid credentials
#   - Node.js and npm installed
#   - Python 3.12+ installed
#   - Bedrock model access enabled
#   - SES sender email verified (if not in sandbox)
#
# Usage:
#   ./deploy.sh
#
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timing
START_TIME=$(date +%s)

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
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

get_elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    printf "%02d:%02d" $minutes $seconds
}

# ============================================================
# Step 0: Welcome and confirmation
# ============================================================
print_header "Richmond 311 Bridge - AWS CDK Deployment"

echo "This script will deploy:"
echo "  1. Storage Stack (S3 + DynamoDB)"
echo "  2. RAG Stack (OpenSearch + Bedrock KB)"
echo "  3. API Stack (Lambdas + API Gateway)"
echo "  4. Connect Stack (IVR)"
echo "  5. Web Stack (S3 + CloudFront)"
echo ""
echo "Estimated cost: \$80-120 for 2-day demo"
echo "Estimated time: 15-25 minutes"
echo ""
read -p "Continue with deployment? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    print_error "Deployment cancelled"
    exit 1
fi

# ============================================================
# Step 1: Check prerequisites
# ============================================================
print_header "Step 1: Checking Prerequisites"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    echo "Visit: https://aws.amazon.com/cli/"
    exit 1
fi
print_success "AWS CLI found"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install it first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node -v)
print_success "Node.js found ($NODE_VERSION)"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install it first."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
print_success "Python 3 found ($PYTHON_VERSION)"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
print_success "AWS credentials valid (Account: $AWS_ACCOUNT, Region: $AWS_REGION)"

# ============================================================
# Step 2: Install/upgrade CDK
# ============================================================
print_header "Step 2: Installing AWS CDK"

if ! command -v cdk &> /dev/null; then
    print_info "CDK not found, installing..."
    npm install -g aws-cdk
    print_success "CDK installed"
else
    CDK_VERSION=$(cdk --version)
    print_success "CDK found ($CDK_VERSION)"
fi

# ============================================================
# Step 3: Navigate to infrastructure directory
# ============================================================
print_header "Step 3: Setting up Infrastructure Directory"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")/infrastructure"

if [[ ! -d "$INFRA_DIR" ]]; then
    print_error "Infrastructure directory not found at $INFRA_DIR"
    exit 1
fi

cd "$INFRA_DIR"
print_success "Working directory: $INFRA_DIR"

# ============================================================
# Step 4: Install Python dependencies
# ============================================================
print_header "Step 4: Installing Python Dependencies"

if [[ ! -f "requirements.txt" ]]; then
    print_error "requirements.txt not found"
    exit 1
fi

pip install -q -r requirements.txt
print_success "Python dependencies installed"

# ============================================================
# Step 5: Check Bedrock model access
# ============================================================
print_header "Step 5: Checking Bedrock Model Access"

print_info "Checking Bedrock model availability in $AWS_REGION..."

# This is a best-effort check; actual access depends on Bedrock quotas
if aws bedrock list-foundation-models --region "$AWS_REGION" &> /dev/null; then
    print_success "Bedrock models accessible"
else
    print_warning "Bedrock models may not be accessible"
    echo "  Visit: https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/models"
    echo "  Enable the Claude 3 Haiku model and any data sources you need"
    read -p "Have you enabled Bedrock models? (yes/no): " bedrock_enabled
    if [[ "$bedrock_enabled" != "yes" ]]; then
        print_error "Bedrock models must be enabled. Aborting deployment."
        exit 1
    fi
fi

# ============================================================
# Step 6: Bootstrap CDK (if needed)
# ============================================================
print_header "Step 6: Bootstrapping CDK for $AWS_ACCOUNT/$AWS_REGION"

# Check if bootstrap stack exists
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region "$AWS_REGION" &> /dev/null; then
    print_info "Running CDK bootstrap..."
    cdk bootstrap aws://"$AWS_ACCOUNT"/"$AWS_REGION"
    print_success "CDK bootstrap complete"
else
    print_success "CDK bootstrap stack already exists"
fi

# ============================================================
# Step 7: Synthesize and validate CDK app
# ============================================================
print_header "Step 7: Synthesizing CDK App"

print_info "Validating stack configuration..."
cdk synth --quiet
print_success "CDK app synthesized successfully"

# ============================================================
# Step 8: Deploy stacks in order
# ============================================================
print_header "Step 8: Deploying CloudFormation Stacks"

echo "Deploying stacks in dependency order..."
echo ""

# Deploy Storage Stack
print_info "Deploying Storage Stack..."
START_STACK=$(date +%s)
if cdk deploy RichmondStorageStack --require-approval never --quiet; then
    ELAPSED=$(($(date +%s) - START_STACK))
    print_success "Storage Stack deployed (${ELAPSED}s)"
else
    print_error "Storage Stack deployment failed"
    exit 1
fi

# Deploy RAG Stack
print_info "Deploying RAG Stack..."
START_STACK=$(date +%s)
if cdk deploy RichmondRagStack --require-approval never --quiet; then
    ELAPSED=$(($(date +%s) - START_STACK))
    print_success "RAG Stack deployed (${ELAPSED}s)"
else
    print_error "RAG Stack deployment failed"
    exit 1
fi

# Deploy API Stack
print_info "Deploying API Stack..."
START_STACK=$(date +%s)
if cdk deploy RichmondApiStack --require-approval never --quiet; then
    ELAPSED=$(($(date +%s) - START_STACK))
    print_success "API Stack deployed (${ELAPSED}s)"
else
    print_error "API Stack deployment failed"
    exit 1
fi

# Deploy Connect Stack
print_info "Deploying Connect Stack..."
START_STACK=$(date +%s)
if cdk deploy RichmondConnectStack --require-approval never --quiet; then
    ELAPSED=$(($(date +%s) - START_STACK))
    print_success "Connect Stack deployed (${ELAPSED}s)"
else
    print_error "Connect Stack deployment failed"
    exit 1
fi

# Deploy Web Stack
print_info "Deploying Web Stack..."
START_STACK=$(date +%s)
if cdk deploy RichmondWebStack --require-approval never --quiet; then
    ELAPSED=$(($(date +%s) - START_STACK))
    print_success "Web Stack deployed (${ELAPSED}s)"
else
    print_error "Web Stack deployment failed"
    exit 1
fi

# ============================================================
# Step 9: Get stack outputs
# ============================================================
print_header "Step 9: Retrieving Stack Outputs"

print_info "Fetching deployment outputs..."

# Get outputs from each stack
get_stack_output() {
    local stack_name=$1
    local output_key=$2
    aws cloudformation describe-stacks --stack-name "$stack_name" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text --region "$AWS_REGION" 2>/dev/null || echo ""
}

API_ENDPOINT=$(get_stack_output "RichmondApiStack" "ApiEndpoint")
DOCS_BUCKET=$(get_stack_output "RichmondStorageStack" "DocsBucketName")
WEBSITE_BUCKET=$(get_stack_output "RichmondStorageStack" "WebsiteBucketName")
CLOUDFRONT_URL=$(get_stack_output "RichmondWebStack" "CloudFrontURL")
CONNECT_INSTANCE=$(get_stack_output "RichmondConnectStack" "ConnectInstanceId")

# ============================================================
# Step 10: Deploy website (if exists)
# ============================================================
print_header "Step 10: Deploying Website Assets"

WEBSITE_DIR="$(dirname "$INFRA_DIR")/website"
if [[ -d "$WEBSITE_DIR" ]]; then
    cd "$WEBSITE_DIR"

    if [[ -f "package.json" ]]; then
        print_info "Building website..."
        npm install --quiet
        npm run build 2>&1 || print_warning "Website build had errors — check output above"

        if [[ -d "build" ]]; then
            print_info "Uploading website to S3..."
            aws s3 sync build "s3://$WEBSITE_BUCKET" --delete --quiet
            print_success "Website deployed to S3"

            # Invalidate CloudFront cache
            if [[ ! -z "$CLOUDFRONT_URL" ]]; then
                DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='${CLOUDFRONT_URL#https://}'].Id" --output text)
                if [[ ! -z "$DIST_ID" ]]; then
                    aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" --quiet
                    print_success "CloudFront cache invalidated"
                fi
            fi
        else
            print_warning "build/ directory not found. Run 'npm run build' manually."
        fi
    else
        print_warning "No package.json found in website directory"
    fi

    cd "$INFRA_DIR"
else
    print_warning "Website directory not found at $WEBSITE_DIR"
fi

# ============================================================
# Step 11: Upload documentation
# ============================================================
print_header "Step 11: Uploading Documentation"

DOCS_DIR="$(dirname "$INFRA_DIR")/documents"
if [[ -d "$DOCS_DIR" ]]; then
    print_info "Uploading documents to S3..."
    aws s3 sync "$DOCS_DIR" "s3://$DOCS_BUCKET/documents/" --quiet

    # Count uploaded files
    DOC_COUNT=$(aws s3 ls "s3://$DOCS_BUCKET/documents/" --recursive | wc -l)
    print_success "Uploaded documents ($DOC_COUNT files)"
else
    print_warning "Documents directory not found at $DOCS_DIR"
    print_info "To add documents later, run:"
    echo "  aws s3 sync ./documents s3://$DOCS_BUCKET/documents/"
fi

# ============================================================
# Step 12: Verify SES
# ============================================================
print_header "Step 12: SES Configuration"

SES_STATUS=$(aws ses describe-configuration-set --configuration-set-name default --region "$AWS_REGION" 2>/dev/null || echo "")

if [[ -z "$SES_STATUS" ]]; then
    print_warning "SES not fully configured for production"
    echo "  Email notifications require either:"
    echo "  1. Verified sender email address, OR"
    echo "  2. Exit SES sandbox mode"
    echo ""
    echo "  To verify sender email, run:"
    echo "  aws ses verify-email-identity --email-address your-email@example.com"
else
    print_success "SES configuration found"
fi

# ============================================================
# Step 13: Summary and next steps
# ============================================================
print_header "Deployment Complete!"

TOTAL_TIME=$(get_elapsed_time)
echo ""
echo -e "${GREEN}All stacks deployed successfully!${NC}"
echo ""
echo "Deployment Summary:"
echo "  Duration: $TOTAL_TIME"
echo "  AWS Account: $AWS_ACCOUNT"
echo "  AWS Region: $AWS_REGION"
echo ""
echo "Endpoints:"
echo "  API Gateway: $API_ENDPOINT"
echo "  Website: $CLOUDFRONT_URL"
echo ""
echo "S3 Buckets:"
echo "  Docs: s3://$DOCS_BUCKET"
echo "  Website: s3://$WEBSITE_BUCKET"
echo ""
echo "AWS Connect:"
echo "  Instance ID: $CONNECT_INSTANCE"
echo "  Console: https://console.aws.amazon.com/connect/home?region=$AWS_REGION"
echo ""
echo "Cost Information:"
echo "  2-day estimate: \$80-120"
echo "  30-day estimate: \$150-300"
echo ""
echo -e "${YELLOW}IMPORTANT: Remember to run cleanup when demo is complete!${NC}"
echo "  ./destroy.sh"
echo ""
echo "Next steps:"
echo "  1. Verify SES email: aws ses verify-email-identity --email-address <your-email>"
echo "  2. Claim a phone number in AWS Connect console"
echo "  3. Test the IVR: Call your Connect phone number"
echo "  4. Upload sample documents: aws s3 sync ./documents s3://$DOCS_BUCKET/documents/"
echo "  5. Access dashboard: $CLOUDFRONT_URL"
echo ""
print_success "Deployment script completed successfully!"

exit 0
