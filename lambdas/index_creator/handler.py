import json
import os
import boto3
import logging
import urllib.request
import urllib.parse
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INDEX_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "l2",
                    "engine": "faiss",
                    "parameters": {"ef_construction": 512, "m": 16}
                }
            },
            "text": {"type": "text"},
            "metadata": {"type": "object"}
        }
    }
}


def get_opensearch_client(host):
    """Create authenticated OpenSearch client using AWS4Auth"""
    try:
        # Get credentials from boto3
        credentials = boto3.Session().get_credentials()

        # Create AWS4Auth signer
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            boto3.Session().region_name or "us-east-1",
            "aoss"
        )

        # Create OpenSearch client
        client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

        logger.info(f"OpenSearch client created for {host}")
        return client

    except Exception as e:
        logger.error(f"Failed to create OpenSearch client: {str(e)}")
        raise


def create_index(client, index_name):
    """Create OpenSearch Serverless vector index"""
    try:
        # Check if index already exists
        if client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True

        # Create index
        response = client.indices.create(
            index=index_name,
            body=INDEX_MAPPING
        )

        logger.info(f"Index {index_name} created successfully")
        return True

    except Exception as e:
        if "resource_already_exists" in str(e).lower():
            logger.info(f"Index {index_name} already exists")
            return True
        logger.error(f"Failed to create index: {str(e)}")
        raise


def delete_index(client, index_name):
    """Delete OpenSearch index"""
    try:
        # Check if index exists
        if not client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} does not exist, skipping deletion")
            return True

        # Delete index
        response = client.indices.delete(index=index_name)
        logger.info(f"Index {index_name} deleted successfully")
        return True

    except Exception as e:
        if "index_not_found" in str(e).lower() or "not_found_exception" in str(e).lower():
            logger.info(f"Index {index_name} not found, skipping")
            return True
        logger.error(f"Failed to delete index: {str(e)}")
        raise


def cfn_response(event, context, status, reason=""):
    """Send response to CloudFormation Custom Resource"""
    try:
        response_url = event.get("ResponseURL", "")

        if not response_url:
            logger.error("No ResponseURL in event")
            return

        response_body = {
            "Status": status,
            "Reason": reason or f"See CloudWatch logs in /aws/lambda/{context.function_name}",
            "PhysicalResourceId": event.get("PhysicalResourceId") or event.get("RequestId", "unknown"),
            "StackId": event.get("StackId", ""),
            "RequestId": event.get("RequestId", ""),
            "LogicalResourceId": event.get("LogicalResourceId", ""),
            "Data": {
                "IndexName": event.get("ResourceProperties", {}).get("IndexName", ""),
                "CollectionEndpoint": event.get("ResourceProperties", {}).get("CollectionEndpoint", "")
            }
        }

        json_response = json.dumps(response_body)

        req = urllib.request.Request(
            response_url,
            data=json_response.encode("utf-8"),
            method="PUT",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(json_response))
            }
        )

        with urllib.request.urlopen(req) as response:
            logger.info(f"CloudFormation response sent: {response.status}")

    except Exception as e:
        logger.error(f"Failed to send CloudFormation response: {str(e)}", exc_info=True)


def lambda_handler(event, context):
    """
    CloudFormation Custom Resource Lambda for creating OpenSearch Serverless vector index.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        request_type = event.get("RequestType", "")
        resource_properties = event.get("ResourceProperties", {})
        collection_endpoint = resource_properties.get("CollectionEndpoint", "")
        index_name = resource_properties.get("IndexName", "bedrock-index")

        if not collection_endpoint:
            error_msg = "CollectionEndpoint not provided in ResourceProperties"
            logger.error(error_msg)
            cfn_response(event, context, "FAILED", error_msg)
            return

        logger.info(f"RequestType: {request_type}, IndexName: {index_name}, Endpoint: {collection_endpoint}")

        # Create OpenSearch client
        client = get_opensearch_client(collection_endpoint)

        if request_type == "Create":
            logger.info("Creating index")
            create_index(client, index_name)
            cfn_response(event, context, "SUCCESS", f"Index {index_name} created")

        elif request_type == "Delete":
            logger.info("Deleting index")
            delete_index(client, index_name)
            cfn_response(event, context, "SUCCESS", f"Index {index_name} deleted")

        elif request_type == "Update":
            logger.info("Update request - no action needed")
            cfn_response(event, context, "SUCCESS", "No update required")

        else:
            error_msg = f"Unknown RequestType: {request_type}"
            logger.error(error_msg)
            cfn_response(event, context, "FAILED", error_msg)

    except Exception as e:
        logger.error(f"Unhandled exception in index_creator handler: {str(e)}", exc_info=True)
        cfn_response(event, context, "FAILED", str(e))
