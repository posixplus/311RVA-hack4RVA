"""
API Stack - Enhanced Lambda functions, API Gateway, and orchestration
Includes: Orchestrator, Redaction, Email Summary, Doc Sync, Dashboard, and Handoff Lambdas
API Gateway with all routes (chat, health, sessions, dashboard, handoff) with CORS
"""

import os
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    aws_sns as sns,
    Duration,
    CfnOutput,
)
from constructs import Construct
from stacks.storage_stack import StorageStack
from stacks.rag_kb_stack import RagKBStack


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        storage_stack: StorageStack,
        rag_stack: "RagKBStack",
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        region = self.region
        account = self.account

        docs_bucket = storage_stack.docs_bucket
        logs_bucket = storage_stack.logs_bucket
        sessions_table = storage_stack.sessions_table
        handoffs_table = storage_stack.handoffs_table

        # Admin key for dashboard authentication
        admin_key = "richmond311admin"

        # Non-profit email addresses - can be overridden via environment variable
        nonprofit_emails = os.environ.get(
            "NONPROFIT_EMAILS", "nonprofit1@example.com,nonprofit2@example.com"
        )

        # SNS topic for alerts
        self.alerts_topic = sns.Topic(
            self,
            "AlertsTopic",
            topic_name="richmond-311-alerts",
            display_name="Richmond 311 Alerts"
        )

        # ============================================================
        # 1. Orchestrator Lambda - main conversational handler
        # ============================================================
        self.orchestrator_lambda = lambda_.Function(
            self,
            "OrchestratorLambda",
            function_name="richmond-orchestrator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/orchestrator"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "KNOWLEDGE_BASE_ID": rag_stack.knowledge_base_id,
                "SESSIONS_TABLE": sessions_table.table_name,
                "LOGS_BUCKET": logs_bucket.bucket_name,
                "BEDROCK_MODEL_ID": "anthropic.claude-3-5-haiku-20241022-v1:0",
                "BEDROCK_REGION": region,
                "REGION": region,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant Lambda permissions
        sessions_table.grant_read_write_data(self.orchestrator_lambda)
        logs_bucket.grant_write(self.orchestrator_lambda)

        # Allow invocation of Bedrock
        self.orchestrator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:Retrieve"],
                resources=["*"],
            )
        )
        self.orchestrator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:RetrieveAndGenerate"],
                resources=["*"],
            )
        )

        # ============================================================
        # 2. Redaction Lambda - PII detection via Comprehend
        # ============================================================
        self.redaction_lambda = lambda_.Function(
            self,
            "RedactionLambda",
            function_name="richmond-redaction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/redaction"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(15),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        self.redaction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["comprehend:DetectPiiEntities"],
                resources=["*"],
            )
        )

        # ============================================================
        # 3. Email Summary Lambda - sends summaries to non-profits
        # ============================================================
        self.email_lambda = lambda_.Function(
            self,
            "EmailSummaryLambda",
            function_name="richmond-email-summary",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/email_summary"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "SENDER_EMAIL": "noreply@richmond-assistant.com",
                "NONPROFIT_EMAILS": nonprofit_emails,
                "LOGS_BUCKET": logs_bucket.bucket_name,
                "ALERTS_TOPIC_ARN": self.alerts_topic.topic_arn,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant SES, S3, and SNS permissions
        self.email_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )
        logs_bucket.grant_read(self.email_lambda)
        self.alerts_topic.grant_publish(self.email_lambda)

        # Allow orchestrator to invoke email Lambda
        email_lambda_arn = self.email_lambda.function_arn
        self.orchestrator_lambda.add_environment("EMAIL_LAMBDA_ARN", email_lambda_arn)
        self.email_lambda.grant_invoke(self.orchestrator_lambda)

        # ============================================================
        # 4. Document Sync Lambda - triggers Bedrock KB ingestion
        # ============================================================
        self.doc_sync_lambda = lambda_.Function(
            self,
            "DocSyncLambda",
            function_name="richmond-doc-sync",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/doc_sync"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "KNOWLEDGE_BASE_ID": rag_stack.knowledge_base_id,
                "DATA_SOURCE_ID": rag_stack.data_source_id,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        self.doc_sync_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:StartIngestionJob"],
                resources=["*"],
            )
        )

        # NOTE: S3 event notifications for auto-sync removed to avoid CDK dependency cycle.
        # Document ingestion is triggered manually via: aws bedrock-agent start-ingestion-job
        # or by invoking the doc_sync Lambda directly after uploading documents.
        docs_bucket.grant_read(self.doc_sync_lambda)

        # ============================================================
        # 5. Dashboard Lambda - session analytics and export
        # ============================================================
        self.dashboard_lambda = lambda_.Function(
            self,
            "DashboardLambda",
            function_name="richmond-dashboard",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/dashboard"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "SESSIONS_TABLE": sessions_table.table_name,
                "LOGS_BUCKET": logs_bucket.bucket_name,
                "ADMIN_KEY": admin_key,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant DynamoDB and S3 read permissions
        sessions_table.grant_read_data(self.dashboard_lambda)
        logs_bucket.grant_read(self.dashboard_lambda)

        # ============================================================
        # 6. Handoff Lambda - manages escalations and agent handoffs
        # ============================================================
        self.handoff_lambda = lambda_.Function(
            self,
            "HandoffLambda",
            function_name="richmond-handoff",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambdas/handoff"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "HANDOFFS_TABLE": handoffs_table.table_name,
                "ALERTS_TOPIC_ARN": self.alerts_topic.topic_arn,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant DynamoDB and SNS permissions
        handoffs_table.grant_read_write_data(self.handoff_lambda)
        self.alerts_topic.grant_publish(self.handoff_lambda)

        # ============================================================
        # 7. API Gateway REST API with ALL routes
        # ============================================================
        api = apigateway.RestApi(
            self,
            "RichmondApi",
            rest_api_name="richmond-api",
            description="Richmond 311 After-Hours Bridge API",
            deploy_options={
                "stage_name": "prod",
                "logging_level": apigateway.MethodLoggingLevel.INFO,
                "data_trace_enabled": False,
            },
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization", "X-Admin-Key"],
            ),
        )

        # ---- /chat endpoint (POST)
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.orchestrator_lambda,
                proxy=True,
            ),
        )

        # ---- /health endpoint (GET)
        health_resource = api.root.add_resource("health")
        health_integration = apigateway.LambdaIntegration(
            self.orchestrator_lambda,
            proxy=True,
        )
        health_resource.add_method("GET", health_integration)

        # ---- /sessions endpoint (GET - list all sessions)
        sessions_resource = api.root.add_resource("sessions")
        sessions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                self.dashboard_lambda,
                proxy=True,
            ),
        )

        # ---- /sessions/{id} endpoint (GET - get specific session)
        session_id_resource = sessions_resource.add_resource("{id}")
        session_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                self.dashboard_lambda,
                proxy=True,
            ),
        )

        # ---- /dashboard/stats endpoint (GET)
        dashboard_resource = api.root.add_resource("dashboard")
        stats_resource = dashboard_resource.add_resource("stats")
        stats_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                self.dashboard_lambda,
                proxy=True,
            ),
        )

        # ---- /dashboard/export endpoint (POST)
        export_resource = dashboard_resource.add_resource("export")
        export_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.dashboard_lambda,
                proxy=True,
            ),
        )

        # ---- /handoff endpoint (POST)
        handoff_resource = api.root.add_resource("handoff")
        handoff_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.handoff_lambda,
                proxy=True,
            ),
        )

        # ============================================================
        # Outputs
        # ============================================================
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="Richmond 311 Bridge API endpoint",
            export_name="RichmondApiEndpoint",
        )

        CfnOutput(
            self,
            "OrchestratorLambdaArn",
            value=self.orchestrator_lambda.function_arn,
            description="Orchestrator Lambda ARN"
        )

        CfnOutput(
            self,
            "DashboardLambdaArn",
            value=self.dashboard_lambda.function_arn,
            description="Dashboard Lambda ARN"
        )

        CfnOutput(
            self,
            "HandoffLambdaArn",
            value=self.handoff_lambda.function_arn,
            description="Handoff Lambda ARN"
        )

        self.api_url = api.url
