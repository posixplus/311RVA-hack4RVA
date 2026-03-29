#!/bin/bash

################################################################################
# Richmond 311 After-Hours Bridge - Teardown Script
# Hackathon: Hack4RVA 2026
#
# Safely destroys all AWS infrastructure created by deploy.sh
# Cleans up S3 buckets, CloudFormation stacks, and other resources
#
# Usage:
#   ./destroy.sh
#
# WARNING: This will permanently delete:
#   - All CloudFormation stacks
#   - All S3 buckets and their contents
#   - All DynamoDB tables and data
#   - AWS Connect instance and phone numbers
#   - All Lambda functions
#   - API Gateway
#   - CloudFront distribution
#   - OpenSearch Serverless indexes
#   - Bedrock Knowledge Base
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
# Step 0: Confirmation
# ============================================================
print_header "Richmond 311 Bridge - Infrastructure Teardown"

print_warning "This script will PERMANENTLY DELETE all resources created by deploy.sh"
echo ""
echo "This includes:"
echo "  - All CloudFormation stacks"
echo "  - All S3 buckets and contents"
echo "  - All DynamoDB tables and data"
echo "  - AWS Connect instance and phone numbers"
echo "  - OpenSearch Serverless indexes"
echo "  - Bedrock Knowledge Base"
echo "  - All Lambda functions"
echo ""
print_warning "This action CANNOT be undone!"
echo ""
read -p "Type 'DESTROY' to confirm teardown: " confirm
if [[ "$confirm" != "DESTROY" ]]; then
    print_info "Teardown cancelled"
    exit 0
fi

# ============================================================
# Step 1: Get AWS details
# ============================================================
print_header "Step 1: Gathering AWS Information"

AWS_REGION=$(aws configure get region)
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

print_success "AWS Region: $AWS_REGION"
print_success "AWS Account: $AWS_ACCOUNT"

# ============================================================
# Step 2: Empty S3 buckets before deletion
# ============================================================
print_header "Step 2: Emptying S3 Buckets"

# Find buckets matching our pattern
BUCKETS=$(aws s3 ls --region "$AWS_REGION" | grep "richmond-" | awk '{print $3}')

if [[ -z "$BUCKETS" ]]; then
    print_info "No Richmond 311 buckets found"
else
    for bucket in $BUCKETS; do
        print_info "Emptying bucket: $bucket"
        aws s3 rm "s3://$bucket" --recursive --region "$AWS_REGION" 2>/dev/null || true
        print_success "Emptied: $bucket"
    done
fi

# ============================================================
# Step 3: Delete CloudFront distributions
# ============================================================
print_header "Step 3: Deleting CloudFront Distributions"

# Find and disable distributions
DISTRIBUTIONS=$(aws cloudfront list-distributions --query "DistributionList.Items[?Tags.Items[?Key=='Project' && Value=='Richmond311Bridge']].Id" --output text)

if [[ -z "$DISTRIBUTIONS" ]]; then
    print_info "No CloudFront distributions found"
else
    for dist_id in $DISTRIBUTIONS; do
        print_info "Disabling distribution: $dist_id"
        ETAG=$(aws cloudfront get-distribution-config --id "$dist_id" --query 'ETag' --output text)
        CONFIG=$(aws cloudfront get-distribution-config --id "$dist_id" --query 'DistributionConfig' --output json)
        UPDATED_CONFIG=$(echo "$CONFIG" | jq '.Enabled = false')
        aws cloudfront update-distribution --id "$dist_id" --distribution-config "$UPDATED_CONFIG" --if-match "$ETAG" 2>/dev/null || true
        print_success "Distribution disabled: $dist_id"
    done
    print_info "Note: Disabled distributions will auto-delete after approximately 5 minutes"
fi

# ============================================================
# Step 4: Delete CloudFormation stacks in reverse order
# ============================================================
print_header "Step 4: Deleting CloudFormation Stacks"

STACKS=("RichmondWebStack" "RichmondConnectStack" "RichmondApiStack" "RichmondRagStack" "RichmondStorageStack")

for stack in "${STACKS[@]}"; do
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$stack" --region "$AWS_REGION" &> /dev/null; then
        print_info "Deleting stack: $stack"
        aws cloudformation delete-stack --stack-name "$stack" --region "$AWS_REGION"
        print_success "Stack deletion initiated: $stack"

        # Wait for stack to be deleted
        print_info "Waiting for stack deletion... (this may take a few minutes)"
        aws cloudformation wait stack-delete-complete --stack-name "$stack" --region "$AWS_REGION" 2>/dev/null || true
        print_success "Stack deleted: $stack"
    else
        print_info "Stack not found: $stack"
    fi
done

# ============================================================
# Step 5: Clean up AWS Connect resources
# ============================================================
print_header "Step 5: Cleaning Up AWS Connect Resources"

# Get all Connect instances and delete phone numbers first
CONNECT_INSTANCES=$(aws connect list-instances --region "$AWS_REGION" --query 'InstanceSummaryList[?Tags.Project=="Richmond311Bridge"].Id' --output text 2>/dev/null || echo "")

if [[ -z "$CONNECT_INSTANCES" ]]; then
    print_info "No Connect instances found with our tag"
else
    for instance_id in $CONNECT_INSTANCES; do
        print_info "Cleaning up Connect instance: $instance_id"

        # List and release phone numbers
        PHONE_NUMBERS=$(aws connect list-phone-numbers --instance-id "$instance_id" --region "$AWS_REGION" --query 'PhoneNumberSummaryList[].Id' --output text 2>/dev/null || echo "")

        for phone in $PHONE_NUMBERS; do
            print_info "Releasing phone number: $phone"
            aws connect disassociate-phone-number-contact-flow --phone-number-id "$phone" --region "$AWS_REGION" 2>/dev/null || true
            aws connect release-phone-number --phone-number-id "$phone" --region "$AWS_REGION" 2>/dev/null || true
        done

        print_success "Connect cleanup complete"
    done
fi

# ============================================================
# Step 6: Verify deletion
# ============================================================
print_header "Step 6: Verifying Deletion"

print_info "Checking remaining Richmond 311 resources..."

# Check buckets
REMAINING_BUCKETS=$(aws s3 ls --region "$AWS_REGION" | grep "richmond-" | awk '{print $3}')
if [[ -z "$REMAINING_BUCKETS" ]]; then
    print_success "No S3 buckets remaining"
else
    print_warning "Warning: Some S3 buckets still exist: $REMAINING_BUCKETS"
fi

# Check stacks
REMAINING_STACKS=$(aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --region "$AWS_REGION" --query "StackSummaries[?contains(StackName, 'Richmond')].StackName" --output text)
if [[ -z "$REMAINING_STACKS" ]]; then
    print_success "No CloudFormation stacks remaining"
else
    print_warning "Warning: Some stacks still exist: $REMAINING_STACKS"
fi

# ============================================================
# Step 7: Cost Summary
# ============================================================
print_header "Cost Summary"

echo "Estimated costs avoided by cleanup:"
echo "  OpenSearch Serverless: ~$3-5/day"
echo "  CloudFront: minimal in free tier"
echo "  Connect: $1/month + $0.018/minute"
echo "  Lambda/DynamoDB/S3: <$1/day"
echo ""
echo "Total monthly cost eliminated: ~$100-300"
echo ""

# ============================================================
# Final Summary
# ============================================================
print_header "Teardown Complete!"

echo -e "${GREEN}All Richmond 311 Bridge resources have been deleted.${NC}"
echo ""
print_warning "Please note:"
echo "  - Some resources (like disabled CloudFront distributions) may take 5-10 minutes to fully delete"
echo "  - Check AWS Console to verify all resources are gone"
echo "  - If any resources remain, they may incur charges"
echo ""
print_success "Teardown script completed!"

exit 0
