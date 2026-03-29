"""
Index Creator Lambda - Custom resource handler to create OpenSearch vector index.
Uses only boto3/botocore (built into Lambda runtime) - no external deps needed.
Includes retry logic for data access policy propagation delays.
"""

import json
import os
import time
import urllib.request
import ssl
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

COLLECTION_ENDPOINT = os.environ.get("COLLECTION_ENDPOINT", "")
INDEX_NAME = os.environ.get("INDEX_NAME", "richmond-kb-index")
VECTOR_DIMENSION = int(os.environ.get("VECTOR_DIMENSION", "1024"))
REGION = os.environ.get("AWS_REGION", "us-east-1")


def lambda_handler(event, context):
    """
    Handle CloudFormation custom resource request via CDK Provider framework.
    Returns a dict (Provider handles CFN response).
    """
    print(f"Received event: {json.dumps(event)}")
    request_type = event.get("RequestType", "Create")

    if request_type == "Create":
        return create_index()
    elif request_type == "Update":
        return {"PhysicalResourceId": INDEX_NAME}
    elif request_type == "Delete":
        return {"PhysicalResourceId": INDEX_NAME}
    else:
        return {"PhysicalResourceId": INDEX_NAME}


def signed_request(method, url, body=None):
    """Make a SigV4-signed request to OpenSearch Serverless."""
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    headers = {"Content-Type": "application/json"}
    request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers=headers,
    )
    SigV4Auth(credentials, "aoss", REGION).add_auth(request)

    req = urllib.request.Request(
        url=url,
        data=body.encode("utf-8") if body else None,
        headers=dict(request.headers),
        method=method,
    )

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def create_index():
    """Create OpenSearch vector index with retries for policy propagation."""
    endpoint = COLLECTION_ENDPOINT
    if not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}"

    print(f"Creating vector index:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Index Name: {INDEX_NAME}")
    print(f"  Vector Dimension: {VECTOR_DIMENSION}")

    # Create vector index with Bedrock KB-compatible mappings
    index_body = json.dumps({
        "settings": {
            "index.knn": True,
            "number_of_shards": 2,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": VECTOR_DIMENSION,
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw",
                        "space_type": "l2",
                    },
                },
                "text": {"type": "text"},
                "metadata": {"type": "text"},
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "text"},
            }
        },
    })

    # Retry with exponential backoff - data access policies take time to propagate
    max_retries = 6
    for attempt in range(max_retries):
        wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s, 120s, 150s, 180s
        print(f"Attempt {attempt + 1}/{max_retries}: waiting {wait_time}s for policies to propagate...")
        time.sleep(wait_time)

        # Check if index already exists
        status, body = signed_request("GET", f"{endpoint}/{INDEX_NAME}")
        if status == 200:
            print(f"Index {INDEX_NAME} already exists")
            return {"PhysicalResourceId": INDEX_NAME, "Data": {"IndexName": INDEX_NAME, "Status": "EXISTS"}}

        # Try to create the index
        status, body = signed_request("PUT", f"{endpoint}/{INDEX_NAME}", index_body)
        print(f"Attempt {attempt + 1} - PUT response (status={status}): {body}")

        if status in (200, 201):
            print(f"Index {INDEX_NAME} created successfully!")
            return {
                "PhysicalResourceId": INDEX_NAME,
                "Data": {"IndexName": INDEX_NAME, "Status": "CREATED"},
            }

        if status == 403:
            print(f"Got 403 - data access policy not yet propagated, will retry...")
            continue

        # Other errors are unexpected
        raise Exception(f"Unexpected error creating index: status={status}, body={body}")

    raise Exception(f"Failed to create index after {max_retries} attempts - data access policy did not propagate in time")
