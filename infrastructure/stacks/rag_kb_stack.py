"""
RAG KB Stack - Bedrock Knowledge Base and Data Source.
Deploy AFTER creating the OpenSearch index (via create_index.py).
"""

from aws_cdk import (
    Stack,
    aws_bedrock as bedrock,
    CfnOutput,
)
from constructs import Construct
from stacks.rag_stack import RagStack


class RagKBStack(Stack):
    def __init__(
        self, scope: Construct, id: str, rag_stack: RagStack, **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        region = self.region

        # ============================================================
        # 1. Bedrock Knowledge Base
        # ============================================================
        knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "BedrockKB",
            name="richmond-city-kb",
            role_arn=rag_stack.kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0",
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=rag_stack.collection_arn,
                    vector_index_name="richmond-kb-index",
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        vector_field="embedding",
                        text_field="text",
                        metadata_field="metadata",
                    ),
                ),
            ),
        )

        # ============================================================
        # 2. Bedrock Data Source
        # ============================================================
        data_source = bedrock.CfnDataSource(
            self,
            "DocumentsDataSource",
            knowledge_base_id=knowledge_base.attr_knowledge_base_id,
            name="richmond-docs-source",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=rag_stack.docs_bucket.bucket_arn,
                    inclusion_prefixes=["documents/"],
                ),
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=512,
                        overlap_percentage=20,
                    ),
                ),
            ),
        )

        # ============================================================
        # Outputs
        # ============================================================
        self.knowledge_base_id = knowledge_base.attr_knowledge_base_id
        self.data_source_id = data_source.attr_data_source_id

        CfnOutput(self, "KnowledgeBaseId",
                  value=knowledge_base.attr_knowledge_base_id,
                  description="Bedrock Knowledge Base ID")

        CfnOutput(self, "DataSourceId",
                  value=data_source.attr_data_source_id,
                  description="Bedrock Data Source ID")
