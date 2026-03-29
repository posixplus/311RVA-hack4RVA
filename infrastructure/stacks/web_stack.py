"""
Web Stack - S3 website hosting and CloudFront CDN
Hosts the Richmond 311 Bridge dashboard and admin interface with global CDN distribution
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    CfnOutput,
)
from constructs import Construct


class WebStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        account = self.account
        region = self.region

        # Website S3 bucket - created here to avoid cross-stack dependency cycles
        website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            bucket_name=f"richmond-website-{account}-{region}",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # ============================================================
        # 1. Create Origin Access Identity for CloudFront
        # ============================================================
        oai = cloudfront.OriginAccessIdentity(
            self,
            "WebsiteOAI",
            comment="OAI for Richmond 311 Bridge website bucket"
        )

        # Grant CloudFront access to the website bucket
        website_bucket.grant_read(oai)

        # ============================================================
        # 2. Create CloudFront Distribution
        # ============================================================
        distribution = cloudfront.Distribution(
            self,
            "WebsiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    website_bucket,
                    origin_access_identity=oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                # SPA routing: 404 errors go to index.html
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                # 403 errors (Forbidden) also route to index.html for SPA routing
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
        )

        # ============================================================
        # 3. Outputs
        # ============================================================
        CfnOutput(
            self,
            "WebsiteBucketName",
            value=website_bucket.bucket_name,
            description="S3 bucket for website static assets"
        )

        CfnOutput(
            self,
            "CloudFrontDomainName",
            value=distribution.domain_name,
            description="CloudFront distribution domain"
        )

        CfnOutput(
            self,
            "CloudFrontURL",
            value=f"https://{distribution.domain_name}",
            description="CloudFront URL for website access"
        )

        CfnOutput(
            self,
            "DeploymentInstructions",
            value=f"Build your website and deploy with: aws s3 sync ./build s3://{website_bucket.bucket_name} --delete && aws cloudfront create-invalidation --distribution-id {distribution.distribution_id} --paths '/*'",
            description="Command to deploy website and invalidate cache"
        )

        # Store references for later use
        self.website_bucket = website_bucket
        self.distribution = distribution
        self.cloudfront_url = f"https://{distribution.domain_name}"
