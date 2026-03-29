#!/usr/bin/env python3
"""Update Connect flow: remove Play Prompt, Lex handles response + barge-in.
Flow: Welcome -> Lex (fulfillment plays response, listens for next input) -> loop"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
LEX_BOT_ALIAS_ARN = "arn:aws:lex:us-east-1:099407892939:bot-alias/QPUFEHCFV9/HHBVRXMHDC"
connect = boto3.client("connect", region_name="us-east-1")

# Simplified flow: Welcome -> Lex (loops to itself)
# Lex fulfillment plays response with barge-in, then ElicitIntent keeps listening
flow = {
    "Version": "2019-10-30",
    "StartAction": "e0fbcc28-5c3f-4412-8c0b-07ad048491a2",
    "Metadata": {
        "entryPointPosition": {"x": 40, "y": 40},
        "ActionMetadata": {
            "e0fbcc28-5c3f-4412-8c0b-07ad048491a2": {"position": {"x": 135, "y": -67}},
            "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4": {
                "position": {"x": 428, "y": -80},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": "11196d0e-13a9-46aa-9e68-a683a8c66dac", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            "564504c5-ae2d-49e6-b81b-868ab53df225": {"position": {"x": 700, "y": 80}}
        },
        "Annotations": []
    },
    "Actions": [
        # Welcome
        {
            "Parameters": {"Text": "Welcome to Richmond 3-1-1 After Hours. This is a private service request. No personal information will be collected without your consent. Please describe what you need help with."},
            "Identifier": "e0fbcc28-5c3f-4412-8c0b-07ad048491a2",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4",
                "Errors": [{"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}]
            }
        },
        # Lex bot - fulfillment plays response with barge-in, ElicitIntent loops
        # CatchAllIntent and NoMatchingCondition both loop back to Lex
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
                    "NextAction": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4",
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": "2353dfd3-61bd-438b-9ec8-0d8c9380b9d4", "ErrorType": "NoMatchingCondition"},
                    {"NextAction": "564504c5-ae2d-49e6-b81b-868ab53df225", "ErrorType": "NoMatchingError"}
                ]
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
print(f"Pushing barge-in flow ({len(content)} bytes)...")
try:
    connect.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
    print("SUCCESS!")
except Exception as e:
    print(f"FAILED: {e}")
