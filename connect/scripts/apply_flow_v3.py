#!/usr/bin/env python3
"""Apply Connect flow fix - combined approach"""
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

new_action_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
lambda_id = "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"
lex_id = "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4"
disconnect_id = "564504c5-ae2d-49e6-b81b-868ab53df225"

# Approach 1: All changes at once on original flow
print("Approach 1: All changes in single push...")
flow = get_flow()

# Remove LambdaInvocationAttributes
for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"].pop("LambdaInvocationAttributes", None)
flow["Metadata"]["ActionMetadata"].get(lambda_id, {}).pop("dynamicMetadata", None)

# Add SetContactAttributes
flow["Actions"].append({
    "Parameters": {"Attributes": {"userMessage": "$.Lex.InputTranscript"}},
    "Identifier": new_action_id,
    "Type": "UpdateContactAttributes",
    "Transitions": {
        "NextAction": lambda_id,
        "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
    }
})
flow["Metadata"]["ActionMetadata"][new_action_id] = {"position": {"x": 556, "y": -77}}

# Reroute Lex
for action in flow["Actions"]:
    if action["Identifier"] == lex_id:
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = new_action_id
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = new_action_id

push_flow(flow, "All-in-one")

# Approach 2: Keep LambdaInvocationAttributes but add SetAttributes + reroute
print("\nApproach 2: Keep LambdaInvocationAttributes, add SetAttributes + reroute...")
flow = get_flow()

# Add SetContactAttributes
flow["Actions"].append({
    "Parameters": {"Attributes": {"userMessage": "$.Lex.InputTranscript"}},
    "Identifier": new_action_id,
    "Type": "UpdateContactAttributes",
    "Transitions": {
        "NextAction": lambda_id,
        "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
    }
})
flow["Metadata"]["ActionMetadata"][new_action_id] = {"position": {"x": 556, "y": -77}}

# Reroute Lex
for action in flow["Actions"]:
    if action["Identifier"] == lex_id:
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = new_action_id
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = new_action_id

push_flow(flow, "Keep-Lambda-Attrs")

# Approach 3: Different action type name? Maybe "SetAttributes"
print("\nApproach 3: Use 'SetAttributes' type instead of 'UpdateContactAttributes'...")
flow = get_flow()
flow["Actions"].append({
    "Parameters": {"Attributes": {"userMessage": "$.Lex.InputTranscript"}},
    "Identifier": new_action_id,
    "Type": "SetAttributes",
    "Transitions": {
        "NextAction": lambda_id,
        "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
    }
})
flow["Metadata"]["ActionMetadata"][new_action_id] = {"position": {"x": 556, "y": -77}}
for action in flow["Actions"]:
    if action["Identifier"] == lex_id:
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = new_action_id
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = new_action_id
push_flow(flow, "SetAttributes-type")

# Approach 4: Use Lex session attributes instead - set in Lex bot config
# Skip the SetContactAttributes entirely, just reroute and let Lambda
# get the transcript from a different source
print("\nApproach 4: Just reroute Lex->Lambda directly, no SetAttrs...")
flow = get_flow()
# Remove LambdaInvocationAttributes only
for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"].pop("LambdaInvocationAttributes", None)
flow["Metadata"]["ActionMetadata"].get(lambda_id, {}).pop("dynamicMetadata", None)
push_flow(flow, "Just-remove-LambdaAttrs")

# Approach 5: Replace LambdaInvocationAttributes value with static test
print("\nApproach 5: Set LambdaInvocationAttributes to static value...")
flow = get_flow()
for action in flow["Actions"]:
    if action["Type"] == "InvokeLambdaFunction":
        action["Parameters"]["LambdaInvocationAttributes"] = {
            "source": "connect-lex"
        }
push_flow(flow, "Static-LambdaAttrs")
