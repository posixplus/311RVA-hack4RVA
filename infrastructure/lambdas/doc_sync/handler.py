"""
Doc Sync Lambda - Triggers Bedrock Knowledge Base ingestion when documents are uploaded
Supports: PDF, TXT, DOCX, HTML, MD, CSV
Logs successful ingestion to CloudWatch
"""

import json
import os
import boto3
from typing import Any, Dict
from datetime import datetime

bedrock_client = boto3.client("bedrock-agent")
cloudwatch = boto3.client("cloudwatch")
logs_client = boto3.client("logs")

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID")
DATA_SOURCE_ID = os.environ.get("DATA_SOURCE_ID")

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".html", ".md", ".csv"}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle S3 document upload events and trigger Bedrock ingestion.
    Validates file types and logs ingestion jobs.
    """
    try:
        print(f"Received event: {json.dumps(event)}")

        processed_records = []
        failed_records = []

        # Parse S3 event
        if "Records" in event:
            for record in event["Records"]:
                try:
                    bucket = record["s3"]["bucket"]["name"]
                    key = record["s3"]["object"]["key"]

                    print(f"Processing document: s3://{bucket}/{key}")

                    # Validate file extension
                    if not is_supported_file(key):
                        failed_records.append({
                            "key": key,
                            "reason": f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
                        })
                        print(f"Skipped unsupported file: {key}")
                        continue

                    # Trigger ingestion job
                    ingestion_job_id = start_ingestion_job(bucket, key)
                    processed_records.append({
                        "key": key,
                        "ingestionJobId": ingestion_job_id,
                        "status": "started",
                    })

                    # Log successful ingestion start
                    log_ingestion_start(key, ingestion_job_id, bucket)

                except Exception as e:
                    print(f"Error processing record for {key}: {str(e)}")
                    failed_records.append({
                        "key": key,
                        "reason": str(e),
                    })

        # Publish metrics to CloudWatch
        publish_metrics(len(processed_records), len(failed_records))

        return success_response({
            "message": "Document ingestion processing completed",
            "processedRecords": len(processed_records),
            "failedRecords": len(failed_records),
            "processed": processed_records,
            "failed": failed_records,
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        print(f"Error in doc sync handler: {str(e)}")
        return error_response(str(e), 500)


def is_supported_file(filename: str) -> bool:
    """
    Check if file extension is supported.
    """
    for ext in SUPPORTED_EXTENSIONS:
        if filename.lower().endswith(ext):
            return True
    return False


def start_ingestion_job(bucket: str, key: str) -> str:
    """
    Start a Bedrock Knowledge Base ingestion job for the uploaded document.
    Returns the ingestion job ID.
    """
    try:
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID,
            clientToken=f"{bucket}/{key}/{datetime.utcnow().isoformat()}",
        )

        ingestion_job_id = response.get("ingestionJobId")
        print(f"Ingestion job started: {ingestion_job_id} for {key}")

        return ingestion_job_id

    except Exception as e:
        print(f"Error starting ingestion job for {key}: {str(e)}")
        raise


def log_ingestion_start(filename: str, job_id: str, bucket: str) -> None:
    """
    Log successful ingestion start to CloudWatch.
    """
    try:
        timestamp = datetime.utcnow().isoformat()

        log_message = {
            "timestamp": timestamp,
            "event": "ingestion_started",
            "filename": filename,
            "jobId": job_id,
            "bucket": bucket,
            "knowledgeBaseId": KNOWLEDGE_BASE_ID,
            "dataSourceId": DATA_SOURCE_ID,
        }

        print(f"[INGESTION_LOG] {json.dumps(log_message)}")

        # Optional: Write to CloudWatch Logs group
        try:
            log_group = f"/aws/lambda/doc-sync/{KNOWLEDGE_BASE_ID}"
            log_stream = f"ingestion-jobs"

            # Create log group and stream if they don't exist
            try:
                logs_client.create_log_group(logGroupName=log_group)
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass

            try:
                logs_client.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=log_stream,
                )
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass

            # Put log event
            logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=[
                    {
                        "timestamp": int(datetime.utcnow().timestamp() * 1000),
                        "message": json.dumps(log_message),
                    }
                ],
            )
        except Exception as e:
            print(f"Warning: Could not write to CloudWatch Logs: {str(e)}")

    except Exception as e:
        print(f"Error logging ingestion: {str(e)}")


def publish_metrics(processed: int, failed: int) -> None:
    """
    Publish metrics to CloudWatch for monitoring.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace="HackRVA/DocSync",
            MetricData=[
                {
                    "MetricName": "DocumentsProcessed",
                    "Value": processed,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "DocumentsFailed",
                    "Value": failed,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "IngestionJobStarted",
                    "Value": processed,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
            ],
        )
        print(f"CloudWatch metrics published: processed={processed}, failed={failed}")
    except Exception as e:
        print(f"Error publishing metrics: {str(e)}")


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build HTTP success response with CORS headers."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }


def error_response(message: str, status_code: int) -> Dict[str, Any]:
    """Build HTTP error response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }
