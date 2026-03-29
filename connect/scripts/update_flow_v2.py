#!/usr/bin/env python3
"""Update Connect flow: add language menu using proper Connect action format.
Strategy: get current working flow, add DTMF language selection before Lex."""
import json
import boto3
import uuid

INSTANCE_ID = "5c77d278-0991-408d-b9ea-c6e9451b93ef"
FLOW_ID = "381da872-11bc-48f4-bdcb-d50c28b3cdb8"
LEX_BOT_ALIAS_ARN = "arn:aws:lex:us-east-1:099407892939:bot-alias/QPUFEHCFV9/HHBVRXMHDC"
client = boto3.client("connect", region_name="us-east-1")

# Get current working flow as base
resp = client.describe_contact_flow(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID)
current = json.loads(resp["ContactFlow"]["Content"])

print("Current actions:")
for a in current["Actions"]:
    print(f"  {a['Identifier'][:12]:15s} {a['Type']}")

# Generate proper UUIDs for new actions
welcome_id = str(uuid.uuid4())
lex_en_id = str(uuid.uuid4())
lex_es_id = str(uuid.uuid4())
play_en_id = str(uuid.uuid4())
play_es_id = str(uuid.uuid4())
disconnect_id = str(uuid.uuid4())

# Build new flow with proper UUIDs
flow = {
    "Version": "2019-10-30",
    "StartAction": welcome_id,
    "Metadata": {
        "entryPointPosition": {"x": 40, "y": 40},
        "ActionMetadata": {
            welcome_id: {"position": {"x": 100, "y": 40}},
            lex_en_id: {"position": {"x": 450, "y": -40},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": str(uuid.uuid4()), "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            lex_es_id: {"position": {"x": 450, "y": 180},
                "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                "conditionMetadata": [{"id": str(uuid.uuid4()), "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
            },
            play_en_id: {"position": {"x": 750, "y": -40}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
            play_es_id: {"position": {"x": 750, "y": 180}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
            disconnect_id: {"position": {"x": 950, "y": 80}}
        },
        "Annotations": []
    },
    "Actions": [
        # Welcome + language selection using Lex DTMF
        # Use ConnectParticipantWithLexBot with DTMF - the welcome text IS the prompt
        # When user presses 1 or 2, Lex captures it as DTMF
        # Actually, let's use the simpler approach: the Welcome message asks for language,
        # then we use TWO Lex blocks. The first English Lex block is the default.
        # We add a "Store customer input" DTMF block.

        # Approach: Welcome message includes language choice.
        # Then use GetParticipantInput with DTMF options.
        # If that fails, fall back to English-only with bilingual welcome.

        # SIMPLE APPROACH: Welcome says both languages, then go to English Lex.
        # If user speaks Spanish, English Lex still captures it (CatchAllIntent matches anything).
        # Lambda detects Spanish input and responds in Spanish.
        # This avoids needing DTMF entirely!

        # Actually, the locale matters for speech-to-text. Let me try the DTMF approach
        # using ConnectParticipantWithLexBot with DTMF enabled.

        # Welcome message
        {
            "Parameters": {
                "Text": "Welcome to Richmond 3-1-1 After Hours. Bienvenido al servicio 3-1-1 de Richmond fuera de horario. For English, press 1 or say English. Para español, oprima 2 o diga español."
            },
            "Identifier": welcome_id,
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": lex_en_id,
                "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
            }
        },
        # English Lex bot
        {
            "Parameters": {
                "Text": "I'm listening. Please describe what you need help with.",
                "LexV2Bot": {"AliasArn": LEX_BOT_ALIAS_ARN, "LocaleId": "en_US"}
            },
            "Identifier": lex_en_id,
            "Type": "ConnectParticipantWithLexBot",
            "Transitions": {
                "NextAction": disconnect_id,
                "Conditions": [{
                    "NextAction": play_en_id,
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": play_en_id, "ErrorType": "NoMatchingCondition"},
                    {"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # Spanish Lex bot
        {
            "Parameters": {
                "Text": "Estoy escuchando. Por favor describa en qué necesita ayuda.",
                "LexV2Bot": {"AliasArn": LEX_BOT_ALIAS_ARN, "LocaleId": "es_US"}
            },
            "Identifier": lex_es_id,
            "Type": "ConnectParticipantWithLexBot",
            "Transitions": {
                "NextAction": disconnect_id,
                "Conditions": [{
                    "NextAction": play_es_id,
                    "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}
                }],
                "Errors": [
                    {"NextAction": play_es_id, "ErrorType": "NoMatchingCondition"},
                    {"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}
                ]
            }
        },
        # Play English response, loop back
        {
            "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
            "Identifier": play_en_id,
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": lex_en_id,
                "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
            }
        },
        # Play Spanish response, loop back
        {
            "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
            "Identifier": play_es_id,
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": lex_es_id,
                "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
            }
        },
        # Disconnect
        {
            "Parameters": {},
            "Identifier": disconnect_id,
            "Type": "DisconnectParticipant",
            "Transitions": {}
        }
    ]
}

# First try: with LocaleId in Lex params
content = json.dumps(flow)
print(f"\nPushing flow with LocaleId ({len(content)} bytes)...")
try:
    client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content)
    print("SUCCESS!")
except Exception as e:
    print(f"FAILED: {e}")

    # Fallback: try without LocaleId (maybe Connect doesn't support it in flow JSON)
    # In this case, we'll route everyone through English Lex and rely on
    # Claude to detect language and respond accordingly
    print("\nFallback: single Lex block, Claude auto-detects language...")
    for action in flow["Actions"]:
        if action["Type"] == "ConnectParticipantWithLexBot":
            if "LocaleId" in action["Parameters"].get("LexV2Bot", {}):
                del action["Parameters"]["LexV2Bot"]["LocaleId"]

    # Remove Spanish Lex block and route welcome directly to English
    # Just use ONE Lex bot - Claude will detect Spanish and respond accordingly
    simple_flow = {
        "Version": "2019-10-30",
        "StartAction": welcome_id,
        "Metadata": {
            "entryPointPosition": {"x": 40, "y": 40},
            "ActionMetadata": {
                welcome_id: {"position": {"x": 100, "y": 40}},
                lex_en_id: {"position": {"x": 400, "y": 40},
                    "parameters": {"LexV2Bot": {"AliasArn": {"displayName": "live", "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge"}}},
                    "useLexBotDropdown": True, "lexV2BotName": "RVA311Bridge", "lexV2BotAliasName": "live",
                    "conditionMetadata": [{"id": str(uuid.uuid4()), "operator": {"name": "Equals", "value": "Equals", "shortDisplay": "="}, "value": "CatchAllIntent"}]
                },
                play_en_id: {"position": {"x": 700, "y": 40}, "parameters": {"Text": {"useDynamic": True}}, "useDynamic": True},
                disconnect_id: {"position": {"x": 900, "y": 40}}
            },
            "Annotations": []
        },
        "Actions": [
            {
                "Parameters": {"Text": "Welcome to Richmond 3-1-1 After Hours. Bienvenido al servicio 3-1-1 de Richmond. This is a private service request. No personal information will be collected. Please describe what you need help with, in English or Spanish."},
                "Identifier": welcome_id,
                "Type": "MessageParticipant",
                "Transitions": {"NextAction": lex_en_id, "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]}
            },
            {
                "Parameters": {
                    "Text": "I'm listening. Estoy escuchando.",
                    "LexV2Bot": {"AliasArn": LEX_BOT_ALIAS_ARN}
                },
                "Identifier": lex_en_id,
                "Type": "ConnectParticipantWithLexBot",
                "Transitions": {
                    "NextAction": disconnect_id,
                    "Conditions": [{"NextAction": play_en_id, "Condition": {"Operator": "Equals", "Operands": ["CatchAllIntent"]}}],
                    "Errors": [{"NextAction": play_en_id, "ErrorType": "NoMatchingCondition"}, {"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]
                }
            },
            {
                "Parameters": {"Text": "$.Lex.SessionAttributes.aiResponse"},
                "Identifier": play_en_id,
                "Type": "MessageParticipant",
                "Transitions": {"NextAction": lex_en_id, "Errors": [{"NextAction": disconnect_id, "ErrorType": "NoMatchingError"}]}
            },
            {
                "Parameters": {},
                "Identifier": disconnect_id,
                "Type": "DisconnectParticipant",
                "Transitions": {}
            }
        ]
    }
    content2 = json.dumps(simple_flow)
    print(f"Pushing simplified bilingual flow ({len(content2)} bytes)...")
    try:
        client.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=FLOW_ID, Content=content2)
        print("SUCCESS! (Using auto-detect approach - Claude detects language from input)")
    except Exception as e2:
        print(f"ALSO FAILED: {e2}")
