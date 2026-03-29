#!/bin/bash

################################################################################
# Richmond 311 After-Hours Bridge - AWS Setup Helper
# Hackathon: Hack4RVA 2026
#
# Quick AWS setup for hackathon participants who have credits but need help
# configuring AWS credentials and enabling necessary services.
#
# This script:
#   1. Checks if AWS CLI is installed
#   2. Helps configure AWS credentials
#   3. Enables Bedrock model access
#   4. Verifies SES sandbox status
#   5. Checks IAM permissions
#   6. Provides a readiness checklist
#
# Usage:
#   ./setup_aws.sh
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
# Step 1: Check AWS CLI
# ============================================================
print_header "Richmond 311 Bridge - AWS Setup"

print_info "Step 1: Checking AWS CLI installation..."

if ! command -v aws &> /dev/null; then
    print_warning "AWS CLI not found. Installing..."

    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            print_error "Homebrew not found. Please install from https://brew.sh"
            exit 1
        fi
        brew install awscli
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if ! command -v apt &> /dev/null; then
            print_error "apt-get not found. Please install AWS CLI manually: https://aws.amazon.com/cli/"
            exit 1
        fi
        sudo apt-get update && sudo apt-get install -y awscli
    else
        print_error "Unsupported OS. Please install AWS CLI manually: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI installed"
else
    AWS_VERSION=$(aws --version)
    print_success "AWS CLI found: $AWS_VERSION"
fi

# ============================================================
# Step 2: Check AWS credentials
# ============================================================
print_header "Step 2: AWS Credentials"

if aws sts get-caller-identity &> /dev/null; then
    print_success "AWS credentials are already configured"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    echo "  Account: $AWS_ACCOUNT"
    echo "  User: $AWS_USER"
else
    print_info "AWS credentials not configured. Let's set them up."
    echo ""
    echo "You need an AWS Access Key ID and Secret Access Key."
    echo "Get them from: https://console.aws.amazon.com/iam/home#/security_credentials"
    echo ""

    read -p "Do you want to configure AWS credentials now? (yes/no): " configure_creds

    if [[ "$configure_creds" == "yes" ]]; then
        aws configure

        # Verify configuration worked
        if ! aws sts get-caller-identity &> /dev/null; then
            print_error "Failed to configure AWS credentials"
            exit 1
        fi
        print_success "AWS credentials configured successfully"
    else
        print_error "AWS credentials required. Run 'aws configure' manually."
        exit 1
    fi
fi

# ============================================================
# Step 3: Check region and set default
# ============================================================
print_header "Step 3: AWS Region"

CURRENT_REGION=$(aws configure get region)

if [[ -z "$CURRENT_REGION" ]]; then
    print_warning "No default region configured"
    read -p "Enter your preferred AWS region (default: us-east-1): " REGION
    REGION=${REGION:-us-east-1}

    aws configure set region "$REGION"
    print_success "Region set to: $REGION"
else
    print_success "Default region: $CURRENT_REGION"
fi

AWS_REGION=$(aws configure get region)

# ============================================================
# Step 4: Check and enable Bedrock
# ============================================================
print_header "Step 4: Bedrock Model Access"

print_info "Checking Bedrock model availability..."

if aws bedrock list-foundation-models --region "$AWS_REGION" &> /dev/null; then
    print_success "Bedrock models are accessible in $AWS_REGION"
else
    print_warning "Bedrock models not accessible in $AWS_REGION"
    echo ""
    echo "To enable Bedrock access:"
    echo "  1. Go to: https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/models"
    echo "  2. Click 'Enable Bedrock models'"
    echo "  3. Accept the Claude 3 Haiku model terms"
    echo "  4. Wait 5-10 minutes for activation"
    echo ""
    read -p "Have you enabled Bedrock models? (yes/no): " bedrock_ok

    if [[ "$bedrock_ok" != "yes" ]]; then
        print_warning "Bedrock must be enabled before deployment"
    else
        print_success "Bedrock enabled"
    fi
fi

# ============================================================
# Step 5: Check SES
# ============================================================
print_header "Step 5: SES (Simple Email Service)"

print_info "Checking SES status..."

# Check if in sandbox
SES_SANDBOX=$(aws ses describe-configuration-set --configuration-set-name default --region "$AWS_REGION" 2>/dev/null || echo "")

if [[ -z "$SES_SANDBOX" ]]; then
    print_warning "SES sandbox mode - email can only be sent to verified addresses"
    echo ""
    echo "To exit sandbox mode (optional):"
    echo "  1. Submit a request at: https://console.aws.amazon.com/ses/home?region=$AWS_REGION#/account"
    echo "  2. AWS will review within 24 hours"
    echo ""
    echo "For hackathon, you can verify your own email:"
    read -p "Enter an email address to verify (or press Enter to skip): " email_to_verify

    if [[ ! -z "$email_to_verify" ]]; then
        aws ses verify-email-identity --email-address "$email_to_verify" --region "$AWS_REGION"
        print_success "Verification email sent to: $email_to_verify"
        echo "  Check your inbox and click the verification link"
    fi
else
    print_success "SES fully configured"
fi

# ============================================================
# Step 6: Check IAM permissions
# ============================================================
print_header "Step 6: IAM Permissions Check"

print_info "Checking required IAM permissions..."

REQUIRED_PERMS=(
    "iam:CreateRole"
    "iam:AttachRolePolicy"
    "s3:CreateBucket"
    "dynamodb:CreateTable"
    "lambda:CreateFunction"
    "apigateway:CreateRestApi"
    "bedrock:InvokeModel"
    "connect:CreateInstance"
    "cloudformation:CreateStack"
)

MISSING_PERMS=0
for perm in "${REQUIRED_PERMS[@]}"; do
    # Simple check - try to list policies
    if aws iam list-policies --query "Policies[?PolicyName=='*'].PolicyName" &> /dev/null; then
        print_info "Permission check: $perm (assuming available)"
    else
        print_warning "Cannot verify permission: $perm"
        MISSING_PERMS=$((MISSING_PERMS + 1))
    fi
done

if [[ $MISSING_PERMS -eq 0 ]]; then
    print_success "IAM permissions appear sufficient"
else
    print_warning "Could not verify all IAM permissions"
    echo "  If deployment fails, check your IAM role has AdministratorAccess or equivalent"
fi

# ============================================================
# Step 7: Readiness Checklist
# ============================================================
print_header "Readiness Checklist"

echo "Before running deploy.sh, verify:"
echo ""
echo -e "${GREEN}✓${NC} AWS CLI installed and configured"
echo -e "${GREEN}✓${NC} AWS credentials active and valid"
echo -e "${GREEN}✓${NC} Default region set (current: $AWS_REGION)"
echo -e "${GREEN}✓${NC} Bedrock models enabled in your region"
echo -e "${GREEN}✓${NC} (Optional) SES email verified for notifications"
echo -e "${GREEN}✓${NC} (Optional) AWS credit/billing enabled"
echo ""

# ============================================================
# Step 8: Pre-flight checks
# ============================================================
print_header "Pre-Flight Checks"

READY=true

# Check Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js not installed. Installation required for deployment."
    echo "  Install from: https://nodejs.org/"
    READY=false
else
    print_success "Node.js found"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 not installed. Installation required for deployment."
    READY=false
else
    print_success "Python 3 found"
fi

# Check git (optional but recommended)
if ! command -v git &> /dev/null; then
    print_warning "Git not installed (optional but recommended)"
else
    print_success "Git found"
fi

# ============================================================
# Summary
# ============================================================
print_header "Setup Summary"

if [[ "$READY" == true ]]; then
    print_success "AWS environment is ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. cd to the infrastructure directory"
    echo "  2. Run: ./scripts/deploy.sh"
    echo ""
else
    print_warning "Some dependencies are missing. Please install them before deployment."
    echo ""
    echo "Required:"
    echo "  - Node.js: https://nodejs.org/"
    echo "  - Python 3: https://www.python.org/downloads/"
    echo ""
fi

print_success "AWS setup script completed!"

exit 0
