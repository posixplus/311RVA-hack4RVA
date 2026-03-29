"""
Storage Stack - S3 buckets and DynamoDB tables for Richmond 311 Bridge
Manages documentation bucket, logs bucket, website bucket, and session data tables.
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        account = self.account
        region = self.region

        # Documentation S3 bucket - versioned, CORS enabled, lifecycle management
        self.docs_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"richmond-docs-{account}-{region}",
            versioned=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=86400,
                )
            ],
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(30),
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # Logs S3 bucket - for call recordings and transcripts
        self.logs_bucket = s3.Bucket(
            self,
            "LogsBucket",
            bucket_name=f"richmond-logs-{account}-{region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(30),
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # DynamoDB table for call sessions
        self.sessions_table = dynamodb.Table(
            self,
            "SessionsTable",
            table_name="richmond-call-sessions",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl",
        )

        # DynamoDB table for handoffs between agents and escalations
        self.handoffs_table = dynamodb.Table(
            self,
            "HandoffsTable",
            table_name="richmond-handoffs",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl",
        )

        # Export bucket names and table names for downstream stacks
        self.docs_bucket_name = self.docs_bucket.bucket_name
        self.logs_bucket_name = self.logs_bucket.bucket_name
        self.sessions_table_name = self.sessions_table.table_name
        self.handoffs_table_name = self.handoffs_table.table_name

        # Outputs
        CfnOutput(
            self,
            "DocsBucketName",
            value=self.docs_bucket_name,
            description="S3 bucket for RAG documents"
        )
        CfnOutput(
            self,
            "LogsBucketName",
            value=self.logs_bucket_name,
            description="S3 bucket for logs and recordings"
        )
        CfnOutput(
            self,
            "SessionsTableName",
            value=self.sessions_table_name,
            description="DynamoDB table for session data"
        )
        CfnOutput(
            self,
            "HandoffsTableName",
            value=self.handoffs_table_name,
            description="DynamoDB table for handoff data"
        )
