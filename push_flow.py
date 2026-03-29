#!/usr/bin/env python3
"""Push updated Connect contact flow via boto3"""
import json
import boto3

flow = json.load(open("tmp_flow_update.json"))
content = json.dumps(flow)

client = boto3.client("connect", region_name="us-east-1")
try:
    resp = client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=content
    )
    print(f"SUCCESS: {resp['ResponseMetadata']['HTTPStatusCode']}")
except Exception as e:
    print(f"ERROR: {e}")
