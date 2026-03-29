#!/usr/bin/env python3
"""
Richmond 311 After-Hours Bridge - AWS CDK Application
Hackathon: Hack4RVA 2026

Deploys 6 interconnected stacks. RagKBStack must be deployed AFTER
creating the OpenSearch index manually (see scripts/create_index.py).
"""

import os
from aws_cdk import App, Tags, Environment
from stacks.storage_stack import StorageStack
from stacks.rag_stack import RagStack
from stacks.rag_kb_stack import RagKBStack
from stacks.api_stack import ApiStack
from stacks.connect_stack import ConnectStack
from stacks.web_stack import WebStack


def main():
    app = App()

    aws_account = os.environ.get("AWS_ACCOUNT_ID") or app.node.try_get_context("account")
    aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    if not aws_account:
        aws_account = "000000000000"

    env = Environment(
        account=aws_account,
        region=aws_region,
    )

    common_tags = {
        "Project": "Richmond311Bridge",
        "Hackathon": "Hack4RVA2026",
        "ManagedBy": "CDK",
    }

    # 1. Storage Stack
    storage_stack = StorageStack(
        app, id="RichmondStorageStack", env=env,
        description="Storage: S3 docs/logs, DynamoDB sessions & handoffs"
    )
    for k, v in common_tags.items():
        Tags.of(storage_stack).add(k, v)

    # 2. RAG Collection Stack (OpenSearch Serverless + policies)
    rag_stack = RagStack(
        app, id="RichmondRagStack", storage_stack=storage_stack, env=env,
        description="RAG: OpenSearch Serverless collection and policies"
    )
    rag_stack.add_dependency(storage_stack)
    for k, v in common_tags.items():
        Tags.of(rag_stack).add(k, v)

    # 3. RAG KB Stack (Bedrock KB + Data Source) — deploy AFTER index creation
    rag_kb_stack = RagKBStack(
        app, id="RichmondRagKBStack", rag_stack=rag_stack, env=env,
        description="RAG: Bedrock Knowledge Base and S3 Data Source"
    )
    rag_kb_stack.add_dependency(rag_stack)
    for k, v in common_tags.items():
        Tags.of(rag_kb_stack).add(k, v)

    # 4. API Stack (Lambdas + API Gateway)
    api_stack = ApiStack(
        app, id="RichmondApiStack",
        storage_stack=storage_stack, rag_stack=rag_kb_stack, env=env,
        description="API: Lambdas + API Gateway with all routes"
    )
    api_stack.add_dependency(storage_stack)
    api_stack.add_dependency(rag_kb_stack)
    for k, v in common_tags.items():
        Tags.of(api_stack).add(k, v)

    # 5. Connect Stack (AWS Connect IVR)
    connect_stack = ConnectStack(
        app, id="RichmondConnectStack", api_stack=api_stack, env=env,
        description="Contact Center: Amazon Connect with multilingual IVR"
    )
    connect_stack.add_dependency(api_stack)
    for k, v in common_tags.items():
        Tags.of(connect_stack).add(k, v)

    # 6. Web Stack (S3 + CloudFront)
    web_stack = WebStack(
        app, id="RichmondWebStack", env=env,
        description="Web hosting: S3 + CloudFront for static website"
    )
    for k, v in common_tags.items():
        Tags.of(web_stack).add(k, v)

    app.synth()


if __name__ == "__main__":
    main()
