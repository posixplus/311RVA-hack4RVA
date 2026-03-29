#!/usr/bin/env python3
"""Apply the full Connect flow fix"""
import json
import boto3

client = boto3.client("connect", region_name="us-east-1")

resp = client.describe_contact_flow(
    InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
    ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8"
)
flow = json.loads(resp["ContactFlow"]["Content"])

# 1. Remove LambdaInvocationAttributes from Lambda action
for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        if "LambdaInvocationAttributes" in action["Parameters"]:
            del action["Parameters"]["LambdaInvocationAttributes"]
            print("Removed LambdaInvocationAttributes")

# 2. Clean dynamicMetadata from Lambda action metadata
lambda_id = "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"
if "dynamicMetadata" in flow["Metadata"]["ActionMetadata"].get(lambda_id, {}):
    del flow["Metadata"]["ActionMetadata"][lambda_id]["dynamicMetadata"]
    print("Removed dynamicMetadata from Lambda metadata")

# 3. Add SetContactAttributes action to store Lex transcript
new_action_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
new_action = {
    "Parameters": {
        "Attributes": {
            "userMessage": "$.Lex.InputTranscript"
        }
    },
    "Identifier": new_action_id,
    "Type": "UpdateContactAttributes",
    "Transitions": {
        "NextAction": lambda_id,  # -> Lambda
        "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
    }
}
flow["Actions"].append(new_action)
flow["Metadata"]["ActionMetadata"][new_action_id] = {"position": {"x": 556, "y": -77}}
print("Added SetContactAttributes action")

# 4. Reroute Lex bot transitions through SetContactAttributes
lex_id = "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4"
for action in flow["Actions"]:
    if action["Identifier"] == lex_id:
        # CatchAllIntent -> SetAttributes (was -> Lambda directly)
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                old = cond["NextAction"]
                cond["NextAction"] = new_action_id
                print(f"Rerouted CatchAllIntent: {old[:8]}... -> {new_action_id[:8]}...")
        # NoMatchingCondition -> SetAttributes (was -> Lambda directly)
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                old = err["NextAction"]
                err["NextAction"] = new_action_id
                print(f"Rerouted NoMatchingCondition: {old[:8]}... -> {new_action_id[:8]}...")

# 5. Push the updated flow
content = json.dumps(flow)
print(f"\nPushing updated flow ({len(content)} bytes)...")
try:
    client.update_contact_flow_content(
        InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
        ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8",
        Content=content
    )
    print("SUCCESS! Flow updated.")
except Exception as e:
    print(f"FAILED: {e}")

# 6. Verify by re-reading
print("\nVerifying...")
verify = client.describe_contact_flow(
    InstanceId="5c77d278-0991-408d-b9ea-c6e9451b93ef",
    ContactFlowId="381da872-11bc-48f4-bdcb-d50c28b3cdb8"
)
verified_flow = json.loads(verify["ContactFlow"]["Content"])
print("Updated flow actions:")
for a in verified_flow["Actions"]:
    t = a["Transitions"]
    next_action = t.get("NextAction", "none")
    conditions = [c["Condition"]["Operands"][0] + "->" + c["NextAction"][:8] for c in t.get("Conditions", [])]
    errors = [e["ErrorType"] + "->" + e["NextAction"][:8] for e in t.get("Errors", [])]
    print(f"  [{a['Type']}] {a['Identifier'][:8]}... -> next={next_action[:8] if next_action else 'none'}  cond={conditions}  err={errors}")
