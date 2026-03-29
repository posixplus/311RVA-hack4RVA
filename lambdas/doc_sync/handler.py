import json
import os
import boto3
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
DATA_SOURCE_ID = os.environ["DATA_SOURCE_ID"]
REGION = os.environ.get("REGION", "us-east-1")

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)


def lambda_handler(event, context):
    """
    Triggered by S3 events when new documents are uploaded.
    Starts Bedrock Knowledge Base ingestion job.
    """
    try:
        # Parse S3 event
        records = event.get("Records", [])
        uploaded_files = []

        for record in records:
            bucket = record.get("s3", {}).get("bucket", {}).get("name", "")
            key = record.get("s3", {}).get("object", {}).get("key", "")

            if bucket and key:
                uploaded_files.append(key)
                logger.info(f"S3 upload detected: s3://{bucket}/{key}")

        if not uploaded_files:
            logger.warning("No files found in S3 event")
            return {
                "success": False,
                "error": "No files in event"
            }

        # Start ingestion job
        try:
            job_response = bedrock_agent.start_ingestion_job(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                dataSourceId=DATA_SOURCE_ID,
                clientToken=str(uuid.uuid4())
            )

            job_id = job_response.get("ingestionJobId", "unknown")
            logger.info(f"Ingestion job started: {job_id}")

            return {
                "success": True,
                "job_started": True,
                "job_id": job_id,
                "files": uploaded_files,
                "file_count": len(uploaded_files)
            }

        except bedrock_agent.exceptions.ResourceInUseException as e:
            # Ingestion already in progress
            logger.info(f"Ingestion already in progress: {str(e)}")
            return {
                "success": True,
                "job_started": False,
                "reason": "Ingestion already in progress",
                "files": uploaded_files
            }

        except Exception as e:
            logger.error(f"Failed to start ingestion job: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Unhandled exception in doc_sync handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
