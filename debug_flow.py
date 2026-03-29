#!/usr/bin/env python3
"""Debug: try pushing original flow back, then try with fix"""
import json
import boto3

client = boto3.client("connect", region_name="us-east-1")

# First get current flow
resp = client.describe_contact_flow(
    InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
    ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8"
)
current_content = resp["ContactFlow"]["Content"]
current_flow = json.loads(current_content)

print("Current flow action types:")
for action in current_flow["Actions"]:
    print(f"  {action['Identifier'][:8]}... -> {action['Type']}")

# Test 1: Can we re-push the current flow as-is?
print("\nTest 1: Re-pushing current flow...")
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=current_content
    )
    print("  SUCCESS - current flow re-pushed OK")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 2: Minimal change - just fix Lambda timeout
print("\nTest 2: Only change Lambda timeout to 25...")
test_flow = json.loads(current_content)
for action in test_flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"]["InvocationTimeLimitSeconds"] = "25"
        # Also remove the problematic LambdaInvocationAttributes
        if "LambdaInvocationAttributes" in action["Parameters"]:
            del action["Parameters"]["LambdaInvocationAttributes"]
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=json.dumps(test_flow)
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 3: Add UpdateContactAttributes block
print("\nTest 3: Add SetContactAttributes + reroute Lex...")
test_flow2 = json.loads(current_content)

# Add new action: store Lex transcript as contact attribute
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
test_flow2["Actions"].append(new_action)

# Add metadata for new action
test_flow2["Metadata"]["ActionMetadata"]["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"] = {
    "position": {"x": 556, "y": -77}
}

# Reroute Lex CatchAllIntent and NoMatchingCondition to new action
for action in test_flow2["Actions"]:
    if action["Identifier"] == "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4":
        # CatchAllIntent -> SetAttributes
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        # NoMatchingCondition -> SetAttributes
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # Fix Lambda: remove LambdaInvocationAttributes, increase timeout
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"]["InvocationTimeLimitSeconds"] = "25"
        if "LambdaInvocationAttributes" in action["Parameters"]:
            del action["Parameters"]["LambdaInvocationAttributes"]

try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=json.dumps(test_flow2)
    )
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")
    # Try with different attribute reference format
    print("\nTest 4: Try with $.Attributes.userMessage reference pattern...")
    # Maybe we need to use Lex session attributes differently
    # Let's check if we can set it as a user-defined attribute
    for action in test_flow2["Actions"]:
        if action["Identifier"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee":
            # Try the Set contact attributes format
            action["Parameters"] = {
                "Attributes": {
                    "userMessage": "$.Lex.InputTranscript"
                }
            }
    try:
        client.update_contact_flow_content(
            InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
            ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
            Content=json.dumps(test_flow2)
        )
        print("  SUCCESS")
    except Exception as e2:
        print(f"  FAILED: {e2}")
        print("\nDumping test_flow2 for inspection...")
        print(json.dumps(test_flow2, indent=2)[:3000])
