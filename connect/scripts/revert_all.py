#!/usr/bin/env python3
"""Revert to the last known working state:
- Lex alias -> version 5 (confirmed working with fulfillment)
- Connect flow -> original structure with original UUIDs
"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"
LEX_BOT_ALIAS_ARN = "arn:aws:lex:us-east-1:099407892939:bot-alias/QPUFEHCFV9/HHBVRXMHDC"

lex = boto3.client("lexv2-models", region_name="us-east-1")
connect = boto3.client("connect", region_name="us-east-1")

# Step 1: Revert Lex alias to version 5
print("Step 1: Reverting Lex alias to version 5...")
lex.update_bot_alias(
    botId=BOT_ID, botAliasId=ALIAS_ID, botAliasName="live",
    botVersion="5",
    botAliasLocaleSettings={
        "en_US": {
            "enabled": True,
            "codeHookSpecification": {
                "lambdaCodeHook": {
                    "lambdaARN": LAMBDA_ARN,
                    "codeHookInterfaceVersion": "1.0"
                }
            }
        }
    }
)
print("  Lex alias reverted to version 5")

# Step 2: Restore Connect flow with original UUIDs
# This is the flow structure that was working (user confirmed "I got the response")
print("Step 2: Restoring Connect flow...")
flow = {
    "Version": "2019-10-30",
    "StartAction": "e0fbcc28-5c3f-4412-8c0b-07ad048491a2",
    "Metadata": {
        "entryPointPosition": {"x": 40, "y": 40},
        "ActionMetadata": {
            "e0fbcc28-5c3f-4412-8c0b-07ad048491a2": {"position": {"x": 135.2, "y": -67.2}},
            "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4": {
                "position": {"x": 428, "y": -80},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": "11196d0e-13a9-46aa-9e68-a683a8c66dac", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            "d9a6fb55-dbce-4c3c-9c91-d86799d97696": {"position": {"x": 700, "y": -78.4}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
            "564504c5-ae2d-49e6-b81b-868ab53df225": {"position": {"x": 950, "y": 80}}
        },
        "Annotations": []
    },
    "Actions": [
        # Welcome message
        {
            "Parameters": {"Text": "Welcome to Richmond 3-1-1 After Hours. This is a private service request. No personal information will be collected without your consent. Please describe what you need help with."},
            "Identifier": "e0fbcc28-5c3f-4412-8c0b-07ad048491a2",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4",
                "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
            }
        },
        # Lex bot (en_US)
        {
            "Parameters": {
                "Text": "I'm listening",
                "LexV2Bot": {"AliasArn": LEX_BOT_ALIAS_ARN}
            },
            "Identifier": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4",
            "Type": "ConnectParticipantWithLexBot",
            "Transitions": {
                "NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225",
                "Conditions": [{
                    "NextAction": "d9a6fb55-dbce-4c3c-9c91-d86799d97696",
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": "d9a6fb55-dbce-4c3c-9c91-d86799d97696", "ErrorType": "NoMatchingCondition"},
                    {"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # Play AI response from Lex session attributes, then loop
        {
            "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
            "Identifier": "d9a6fb55-dbce-4c3c-9c91-d86799d97696",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4",
                "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
            }
        },
        # Disconnect
        {
            "Parameters": {},
            "Identifier": "564504c5-ae2d-49e6-b81b-868ab53df225",
            "Type": "DisconnectParticipant",
            "Transitions": {}
        }
    ]
}

content = json.dumps(flow)
try:
    connect.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
    print("  Connect flow restored!")
except Exception as e:
    print(f"  FAILED: {e}")

# Verify
print("\nVerification:")
alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"  Lex alias version: {alias['botVersion']}")

resp = connect.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
vf = json.loads(resp["ContactFlow"]["Content"])
print(f"  Flow actions: {len(vf['Actions'])}")
for a in vf["Actions"]:
    print(f"    {a['Type']:30s} {a['Identifier'][:12]}")
print("\nDONE - reverted to working state")
