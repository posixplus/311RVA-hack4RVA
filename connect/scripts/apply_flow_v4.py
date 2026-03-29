#!/usr/bin/env python3
"""Fix: Set dynamicMetadata to true so $.Lex.InputTranscript resolves"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
LAMBDA_ID = "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"
client = boto3.client("connect", region_name="us-east-1")

resp = client.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
flow = json.loads(resp["ContactFlow"]["Content"])

# The key insight: dynamicMetadata was {"InputTranscript": false}
# false = treat as literal string, true = resolve dynamic reference!
# Fix: Set LambdaInvocationAttributes with $.Lex.InputTranscript AND
# set dynamicMetadata to true so Connect resolves the reference

for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"]["LambdaInvocationAttributes"] = {
            "InputTranscript": "$.Lex.InputTranscript"
        }
        print(f"Set LambdaInvocationAttributes: {action['Parameters']['LambdaInvocationAttributes']}")

# Set dynamicMetadata to TRUE
flow["Metadata"]["ActionMetadata"][LAMBDA_ID]["dynamicMetadata"] = {
    "InputTranscript": True
}
print("Set dynamicMetadata.InputTranscript = true")

content = json.dumps(flow)
try:
    client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
    print("\nSUCCESS! Flow updated with dynamic Lex transcript resolution.")
except Exception as e:
    print(f"\nFAILED: {e}")

    # Fallback: try without metadata change, just the param
    print("\nFallback: try with dynamic metadata but different attribute format...")
    flow2 = json.loads(resp["ContactFlow"]["Content"])
    for action in flow2["Actions"]:
        if action["Type"] == "InvokeLambdaFunction":
            action["Parameters"]["LambdaInvocationAttributes"] = {
                "userInput": "$.Lex.InputTranscript"
            }
    flow2["Metadata"]["ActionMetadata"][LAMBDA_ID]["dynamicMetadata"] = {
        "userInput": True
    }
    try:
        client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=json.dumps(flow2))
        print("  Fallback SUCCESS!")
    except Exception as e2:
        print(f"  Fallback FAILED: {e2}")
