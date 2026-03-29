#!/usr/bin/env python3
"""Apply Connect flow fix in sequential steps"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
client = boto3.client("connect", region_name="us-east-1")

def get_flow():
    resp = client.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
    return json.loads(resp["ContactFlow"]["Content"])

def push_flow(flow, label):
    content = json.dumps(flow)
    try:
        client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
        print(f"  {label}: SUCCESS")
        return True
    except Exception as e:
        print(f"  {label}: FAILED - {e}")
        return False

# Step 1: Remove LambdaInvocationAttributes
print("Step 1: Remove LambdaInvocationAttributes...")
flow = get_flow()
for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        if "LambdaInvocationAttributes" in action["Parameters"]:
            del action["Parameters"]["LambdaInvocationAttributes"]
if "dynamicMetadata" in flow["Metadata"]["ActionMetadata"].get("5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e", {}):
    del flow["Metadata"]["ActionMetadata"]["5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"]["dynamicMetadata"]
if not push_flow(flow, "Step 1"):
    exit(1)

# Step 2: Add SetContactAttributes action (orphan for now)
print("Step 2: Add SetContactAttributes action...")
flow = get_flow()
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
        "NextAction": "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e",
        "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
    }
}
flow["Actions"].append(new_action)
flow["Metadata"]["ActionMetadata"][new_action_id] = {"position": {"x": 556, "y": -77}}
if not push_flow(flow, "Step 2"):
    exit(1)

# Step 3: Reroute CatchAllIntent only
print("Step 3: Reroute CatchAllIntent -> SetAttributes...")
flow = get_flow()
for action in flow["Actions"]:
    if action["Identifier"] == "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4":
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = new_action_id
if not push_flow(flow, "Step 3"):
    print("  Trying alternative: reroute NoMatchingCondition only...")
    flow = get_flow()
    for action in flow["Actions"]:
        if action["Identifier"] == "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4":
            for err in action["Transitions"].get("Errors", []):
                if err["ErrorType"] == "NoMatchingCondition":
                    err["NextAction"] = new_action_id
    push_flow(flow, "Step 3 alt")

# Step 4: Reroute NoMatchingCondition too
print("Step 4: Reroute NoMatchingCondition -> SetAttributes...")
flow = get_flow()
for action in flow["Actions"]:
    if action["Identifier"] == "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4":
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = new_action_id
if not push_flow(flow, "Step 4"):
    print("  NoMatchingCondition reroute failed, but CatchAllIntent should still work")

# Final verification
print("\nFinal flow state:")
flow = get_flow()
for a in flow["Actions"]:
    t = a["Transitions"]
    next_a = t.get("NextAction", "none")
    conds = [f"{c['Condition']['Operands'][0]}->{c['NextAction'][:8]}" for c in t.get("Conditions", [])]
    errs = [f"{e['ErrorType']}->{e['NextAction'][:8]}" for e in t.get("Errors", [])]
    print(f"  {a['Type']:30s} {a['Identifier'][:8]} -> {str(next_a)[:8]:8s} cond={conds} err={errs}")
