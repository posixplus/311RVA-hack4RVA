#!/usr/bin/env python3
"""
Create OpenSearch Serverless vector index for Bedrock Knowledge Base.
Run this AFTER the RichmondRagStack has been deployed.

Usage:
    python3 scripts/create_index.py
"""

import json
import sys
import time
import boto3
import urllib.request
import ssl
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

REGION = "us-east-1"
INDEX_NAME = "richmond-kb-index"
VECTOR_DIMENSION = 1024


def get_collection_endpoint():
    """Get the collection endpoint from CloudFormation outputs."""
    cf = boto3.client("cloudformation", region_name=REGION)
    resp = cf.describe_stacks(StackName="RichmondRagStack")
    outputs = resp["Stacks"][0]["Outputs"]
    for o in outputs:
        if o["OutputKey"] == "CollectionEndpoint":
            return o["OutputValue"]
    raise Exception("CollectionEndpoint not found in stack outputs")


def signed_request(method, url, body=None):
    """Make a SigV4-signed request to OpenSearch Serverless."""
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    headers = {"Content-Type": "application/json"}
    request = AWSRequest(method=method, url=url, data=body, headers=headers)
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


def main():
    endpoint = sys.argv[1] if len(sys.argv) > 1 else get_collection_endpoint()
    if not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}"

    # Show current identity for debugging
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"AWS Identity: {identity['Arn']}")
    print(f"Collection endpoint: {endpoint}")
    print(f"Index name: {INDEX_NAME}")
    print(f"Vector dimension: {VECTOR_DIMENSION}")

    # Index body for Bedrock KB
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

    # Retry loop — data access policies can take several minutes to propagate
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")

        # Check if index already exists
        status, body = signed_request("GET", f"{endpoint}/{INDEX_NAME}")
        if status == 200:
            print(f"✅ Index '{INDEX_NAME}' already exists!")
            return

        if status == 403:
            print(f"⏳ GET returned 403 — data access policy still propagating...")
            if attempt < max_attempts:
                print(f"   Waiting 30 seconds before retry...")
                time.sleep(30)
                continue
            else:
                print(f"❌ Still 403 after {max_attempts} attempts.")
                print(f"   Your identity: {identity['Arn']}")
                print(f"   Verify this ARN is in the OpenSearch data access policy.")
                sys.exit(1)

        # Got non-403 on GET (likely 404 = index doesn't exist) — try to create
        print(f"GET returned {status} — index does not exist, creating...")
        status, body = signed_request("PUT", f"{endpoint}/{INDEX_NAME}", index_body)
        print(f"PUT response (status={status}): {body}")

        if status in (200, 201):
            print(f"\n✅ Index '{INDEX_NAME}' created successfully!")
            return
        elif status == 403:
            print(f"⏳ PUT returned 403 — data access policy still propagating...")
            if attempt < max_attempts:
                print(f"   Waiting 30 seconds before retry...")
                time.sleep(30)
                continue
        else:
            print(f"\n❌ Unexpected error creating index (status={status})")
            sys.exit(1)

    print(f"\n❌ Failed after {max_attempts} attempts")
    sys.exit(1)


if __name__ == "__main__":
    main()
