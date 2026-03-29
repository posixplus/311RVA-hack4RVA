"""
RAG Collection Stack - OpenSearch Serverless collection and policies only.
Deploy this first, then create the index, then deploy RagKBStack.
"""

import json
from aws_cdk import (
    Stack,
    aws_opensearchserverless as aoss,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
from stacks.storage_stack import StorageStack


class RagStack(Stack):
    def __init__(
        self, scope: Construct, id: str, storage_stack: StorageStack, **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        region = self.region
        account = self.account

        docs_bucket = storage_stack.docs_bucket

        # ============================================================
        # 1. IAM Role for Bedrock Knowledge Base Service
        # ============================================================
        self.kb_role = iam.Role(
            self,
            "BedrockKBRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Bedrock Knowledge Base to access S3 and OpenSearch",
        )

        docs_bucket.grant_read(self.kb_role)

        self.kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["aoss:APIAccessAll"],
                resources=["*"],
            )
        )

        self.kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0"
                ],
            )
        )

        # ============================================================
        # 2. OpenSearch Serverless Collection
        # ============================================================

        # Encryption policy
        encryption_policy = aoss.CfnSecurityPolicy(
            self,
            "EncryptionPolicy",
            name="richmond-enc-policy",
            type="encryption",
            policy=json.dumps(
                {
                    "Rules": [
                        {
                            "Resource": ["collection/richmond-kb"],
                            "ResourceType": "collection",
                        }
                    ],
                    "AWSOwnedKey": True,
                }
            ),
        )

        # Network policy
        network_policy = aoss.CfnSecurityPolicy(
            self,
            "NetworkPolicy",
            name="richmond-net-policy",
            type="network",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "ResourceType": "collection",
                                "Resource": ["collection/richmond-kb"],
                            },
                            {
                                "ResourceType": "dashboard",
                                "Resource": ["collection/richmond-kb"],
                            },
                        ],
                        "AllowFromPublic": True,
                    },
                ]
            ),
        )

        # Create the collection
        collection = aoss.CfnCollection(
            self,
            "KBCollection",
            name="richmond-kb",
            type="VECTORSEARCH",
            description="Richmond City knowledge base vector search collection",
        )
        collection.add_dependency(encryption_policy)
        collection.add_dependency(network_policy)

        # Data access policy
        data_access_policy = aoss.CfnAccessPolicy(
            self,
            "DataAccessPolicy",
            name="richmond-data-policy",
            type="data",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "Resource": ["collection/richmond-kb"],
                                "Permission": [
                                    "aoss:CreateCollectionItems",
                                    "aoss:DeleteCollectionItems",
                                    "aoss:UpdateCollectionItems",
                                    "aoss:DescribeCollectionItems",
                                ],
                                "ResourceType": "collection",
                            },
                            {
                                "Resource": ["index/richmond-kb/*"],
                                "Permission": [
                                    "aoss:CreateIndex",
                                    "aoss:DeleteIndex",
                                    "aoss:UpdateIndex",
                                    "aoss:DescribeIndex",
                                    "aoss:ReadDocument",
                                    "aoss:WriteDocument",
                                ],
                                "ResourceType": "index",
                            },
                        ],
                        "Principal": [
                            self.kb_role.role_arn,
                            f"arn:aws:iam::{account}:user/backend_deploy_run",
                            f"arn:aws:iam::{account}:root",
                        ],
                    }
                ]
            ),
        )
        data_access_policy.add_dependency(collection)

        # Store refs for KB stack
        self.collection = collection
        self.collection_arn = collection.attr_arn
        self.collection_endpoint = collection.attr_collection_endpoint
        self.docs_bucket = docs_bucket

        # ============================================================
        # Outputs
        # ============================================================
        CfnOutput(self, "CollectionEndpoint",
                  value=collection.attr_collection_endpoint,
                  description="OpenSearch Serverless collection endpoint")

        CfnOutput(self, "CollectionArn",
                  value=collection.attr_arn,
                  description="OpenSearch Serverless collection ARN")

        CfnOutput(self, "KBRoleArn",
                  value=self.kb_role.role_arn,
                  description="Bedrock KB role ARN")
