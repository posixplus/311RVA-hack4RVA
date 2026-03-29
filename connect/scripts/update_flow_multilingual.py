#!/usr/bin/env python3
"""Update Connect flow with language selection menu (DTMF) and Spanish Lex bot"""
import json
import boto3

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
LEX_BOT_ALIAS_ARN = "arn:aws:lex:us-east-1:099407892939:bot-alias/QPUFEHCFV9/HHBVRXMHDC"
client = boto3.client("connect", region_name="us-east-1")

# Build the new flow from scratch for clarity
# Flow: Welcome -> Language Menu (DTMF) -> Lex (en or es) -> Play Response -> Loop to Lex
flow = {
    "Version": "2019-10-30",
    "StartAction": "welcome-msg",
    "Metadata": {
        "entryPointPosition": {"x": 40, "y": 40},
        "ActionMetadata": {
            "welcome-msg": {"position": {"x": 100, "y": 40}},
            "lang-menu": {"position": {"x": 350, "y": 40},
                "conditionMetadata": [
                    {"id": "cond-en", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "1"},
                    {"id": "cond-es", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "2"}
                ]
            },
            "lex-en": {"position": {"x": 600, "y": -40},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": "cond-catch-en", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            "lex-es": {"position": {"x": 600, "y": 140},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": "cond-catch-es", "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            "play-en": {"position": {"x": 850, "y": -40}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
            "play-es": {"position": {"x": 850, "y": 140}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
            "disconnect": {"position": {"x": 1100, "y": 80}}
        },
        "Annotations": []
    },
    "Actions": [
        # 1. Welcome message with language options
        {
            "Parameters": {
                "Text": "Welcome to Richmond 3-1-1 After Hours. This is a private service request. No personal information will be collected without your consent. For English, press 1. Para español, oprima 2."
            },
            "Identifier": "welcome-msg",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "lang-menu",
                "Errors": [{"NextAction": "disconnect", "ErrorType": "NoMatchingError"}]
            }
        },
        # 2. DTMF language menu - get keypress
        {
            "Parameters": {
                "Text": "Press 1 for English. Para español, oprima 2.",
                "DTMFConfiguration": {
                    "InputTimeLimitSeconds": "8",
                    "MaxDigits": 1
                },
                "StoreInput": "True",
                "InputTimeLimitSeconds": "8"
            },
            "Identifier": "lang-menu",
            "Type": "GetParticipantInput",
            "Transitions": {
                "NextAction": "lex-en",
                "Conditions": [
                    {
                        "NextAction": "lex-en",
                        "Condition": {"Operator": "Equals", "Operands": ["1"]}
                    },
                    {
                        "NextAction": "lex-es",
                        "Condition": {"Operator": "Equals", "Operands": ["2"]}
                    }
                ],
                "Errors": [
                    {"NextAction": "lex-en", "ErrorType": "NoMatchingCondition"},
                    {"NextAction": "lex-en", "ErrorType": "InputTimeLimitExceeded"},
                    {"NextAction": "disconnect", "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # 3. Lex bot - English
        {
            "Parameters": {
                "Text": "I'm listening. Please describe what you need help with.",
                "LexV2Bot": {
                    "AliasArn": LEX_BOT_ALIAS_ARN,
                    "LocaleId": "en_US"
                }
            },
            "Identifier": "lex-en",
            "Type": "ConnectParticipantWithLexBot",
            "Transitions": {
                "NextAction": "disconnect",
                "Conditions": [{
                    "NextAction": "play-en",
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": "play-en", "ErrorType": "NoMatchingCondition"},
                    {"NextAction": "disconnect", "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # 4. Lex bot - Spanish
        {
            "Parameters": {
                "Text": "Estoy escuchando. Por favor describa en qué necesita ayuda.",
                "LexV2Bot": {
                    "AliasArn": LEX_BOT_ALIAS_ARN,
                    "LocaleId": "es_US"
                }
            },
            "Identifier": "lex-es",
            "Type": "ConnectParticipantWithLexBot",
            "Transitions": {
                "NextAction": "disconnect",
                "Conditions": [{
                    "NextAction": "play-es",
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": "play-es", "ErrorType": "NoMatchingCondition"},
                    {"NextAction": "disconnect", "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # 5. Play AI response - English, then loop back to English Lex
        {
            "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
            "Identifier": "play-en",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "lex-en",
                "Errors": [{"NextAction": "disconnect", "ErrorType": "NoMatchingError"}]
            }
        },
        # 6. Play AI response - Spanish, then loop back to Spanish Lex
        {
            "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
            "Identifier": "play-es",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "lex-es",
                "Errors": [{"NextAction": "disconnect", "ErrorType": "NoMatchingError"}]
            }
        },
        # 7. Disconnect
        {
            "Parameters": {},
            "Identifier": "disconnect",
            "Type": "DisconnectParticipant",
            "Transitions": {}
        }
    ]
}

content = json.dumps(flow)
print(f"Pushing multilingual flow ({len(content)} bytes)...")
try:
    client.update_contact_flow_content(
        InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content
    )
    print("SUCCESS!")
except Exception as e:
    print(f"FAILED: {e}")
    # If DTMF GetParticipantInput fails, try without it
    # Maybe Connect doesn't support that action type name
    print("\nDumping flow for debug...")
    print(content[:2000])
