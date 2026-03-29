#!/usr/bin/env python3
"""Debug: isolate exactly what breaks the flow update"""
import json
import boto3

client = boto3.client("connect", region_name="us-east-1")

resp = client.describe_contact_flow(
    InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
    ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8"
)
current_content = resp["ContactFlow"]["Content"]

# Test A: Parse and re-serialize with NO changes
print("Test A: Parse + re-serialize, no changes...")
flow = json.loads(current_content)
reserialized = json.dumps(flow)
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=reserialized
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")
    # Check diff
    print(f"  Original length: {len(current_content)}")
    print(f"  Reserialized length: {len(reserialized)}")
    if current_content == reserialized:
        print("  Strings are identical")
    else:
        print("  Strings differ!")
        # Find first difference
        for i, (a, b) in enumerate(zip(current_content, reserialized)):
            if a != b:
                print(f"  First diff at pos {i}: orig='{current_content[max(0,i-20):i+20]}' vs new='{reserialized[max(0,i-20):i+20]}'")
                break

# Test B: Only change Lambda timeout (keep LambdaInvocationAttributes)
print("\nTest B: Only change Lambda timeout, keep everything else...")
flow2 = json.loads(current_content)
for action in flow2["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"]["InvocationTimeLimitSeconds"] = "25"
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=json.dumps(flow2)
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")

# Test C: Only remove LambdaInvocationAttributes
print("\nTest C: Only remove LambdaInvocationAttributes...")
flow3 = json.loads(current_content)
for action in flow3["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        if "LambdaInvocationAttributes" in action["Parameters"]:
            del action["Parameters"]["LambdaInvocationAttributes"]
        # Also clean metadata
if "dynamicMetadata" in flow3["Metadata"]["ActionMetadata"].get("5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e", {}):
    del flow3["Metadata"]["ActionMetadata"]["5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"]["dynamicMetadata"]
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=json.dumps(flow3)
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")

# Test D: Only add the SetContactAttributes action (no rerouting)
print("\nTest D: Add SetContactAttributes action, no routing changes...")
flow4 = json.loads(current_content)
new_action = {
    "Parameters": {
        "Attributes": {
            "userMessage": "$.Lex.InputTranscript"
        }
    },
    "Identifier": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "Type": "UpdateContactAttributes",
    "Transitions": {
        "NextAction": "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e",
        "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
    }
}
flow4["Actions"].append(new_action)
flow4["Metadata"]["ActionMetadata"]["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"] = {"position": {"x": 556, "y": -77}}
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=json.dumps(flow4)
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")
