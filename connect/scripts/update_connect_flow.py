#!/usr/bin/env python3
"""Update Connect flow: Lex now calls Lambda directly via fulfillment.
Flow becomes: Welcome -> Lex (which calls Lambda) -> Play Lex response -> Loop"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
client = boto3.client("connect", region_name="us-east-1")

resp = client.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
flow = json.loads(resp["ContactFlow"]["Content"])

print("Current flow actions:")
for a in flow["Actions"]:
    print(f"  {a['Identifier'][:8]} {a['Type']}")

# Key changes:
# 1. Lex CatchAllIntent -> Play Prompt (skip Lambda invocation, Lex already called it)
# 2. Play Prompt text: $.Lex.SessionAttributes.aiResponse (instead of $.External.response)
# 3. Keep Lambda block but make it unreachable (or remove it)

lex_id = "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4"
play_id = "d9a6fb55-dbce-4c3c-9c91-d86799d97696"
lambda_id = "5d00ef30-b0f6-4dbc-bf3b-33e39d284f2e"
disconnect_id = "564504c5-ae2d-49e6-b81b-868ab53df225"

for action in flow["Actions"]:
    # Route Lex CatchAllIntent directly to Play Prompt (skip Lambda)
    if action["Identifier"] == lex_id:
        for cond in action["Transitions"].get("Conditions", []):
            if cond["Condition"]["Operands"] == ["CatchAllIntent"]:
                cond["NextAction"] = play_id
                print(f"Rerouted CatchAllIntent -> Play Prompt")
        for err in action["Transitions"].get("Errors", []):
            if err["ErrorType"] == "NoMatchingCondition":
                err["NextAction"] = play_id
                print(f"Rerouted NoMatchingCondition -> Play Prompt")

    # Update Play Prompt to use Lex session attributes
    if action["Identifier"] == play_id:
        action["Parameters"]["Text"] = "$.Lex.SessionAttributes.aiResponse"
        print(f"Updated Play Prompt text to $.Lex.SessionAttributes.aiResponse")

# Update metadata for Play Prompt to mark it as dynamic
flow["Metadata"]["ActionMetadata"][play_id]["parameters"] = {
    "Text": {"useDynamic": True}
}
flow["Metadata"]["ActionMetadata"][play_id]["useDynamic"] = True

content = json.dumps(flow)
print(f"\nPushing updated flow ({len(content)} bytes)...")
try:
    client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
    print("SUCCESS!")
except Exception as e:
    print(f"FAILED: {e}")

    # If rerouting from Lex fails again, try keeping Lambda in the path
    # but have Lambda read from Lex session attributes
    print("\nFallback: Keep Lex->Lambda path, but update Play Prompt...")
    flow2 = json.loads(resp["ContactFlow"]["Content"])
    # Only change the Play Prompt text
    for action in flow2["Actions"]:
        if action["Identifier"] == play_id:
            action["Parameters"]["Text"] = "$.Lex.SessionAttributes.aiResponse"
    flow2["Metadata"]["ActionMetadata"][play_id]["parameters"] = {
        "Text": {"useDynamic": True}
    }
    try:
        client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=json.dumps(flow2))
        print("  Fallback SUCCESS! (Play Prompt reads Lex session attrs, Lambda still in path)")
    except Exception as e2:
        print(f"  Fallback FAILED: {e2}")

# Verify
print("\nVerifying flow:")
v = client.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
vf = json.loads(v["ContactFlow"]["Content"])
for a in vf["Actions"]:
    t = a["Transitions"]
    conds = [f"{c['Condition']['Operands'][0]}->{c['NextAction'][:8]}" for c in t.get("Conditions", [])]
    params = {k: str(v)[:50] for k, v in a.get("Parameters", {}).items() if k != "LexV2Bot"}
    print(f"  {a['Type']:30s} {a['Identifier'][:8]} params={params} cond={conds}")
