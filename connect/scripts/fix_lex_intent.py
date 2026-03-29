#!/usr/bin/env python3
"""Fix CatchAllIntent: remove dialog code hook, use only fulfillment"""
import json
import boto3
import time

BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
INTENT_ID = "4BDNOO5GF7"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"

lex = boto3.client("lexv2-models", region_name="us-east-1")
lex_runtime = boto3.client("lexv2-runtime", region_name="us-east-1")

# Step 1: Get current intent
intent = lex.describe_intent(
    botId=BOT_ID, botVersion="DRAFT", localeId="en_US", intentId=INTENT_ID
)
print(f"Current initialResponseSetting: {json.dumps(intent.get('initialResponseSetting', 'NONE'), indent=2, default=str)}")
print(f"Current fulfillmentCodeHook: {json.dumps(intent.get('fulfillmentCodeHook', 'NONE'), indent=2, default=str)}")

# Step 2: Update intent - ONLY fulfillment, NO dialog code hook
print("\nUpdating intent: remove initialResponseSetting, keep fulfillment...")
lex.update_intent(
    botId=BOT_ID,
    botVersion="DRAFT",
    localeId="en_US",
    intentId=INTENT_ID,
    intentName="CatchAllIntent",
    sampleUtterances=intent["sampleUtterances"],
    fulfillmentCodeHook={
        "enabled": True,
        "active": True,
        "postFulfillmentStatusSpecification": {
            "successNextStep": {"dialogAction": {"type": "EndConversation"}},
            "failureNextStep": {"dialogAction": {"type": "EndConversation"}},
            "timeoutNextStep": {"dialogAction": {"type": "EndConversation"}}
        }
    }
    # NO initialResponseSetting = removes dialog code hook
)
print("  Intent updated")

# Step 3: Build
print("\nBuilding bot...")
lex.build_bot_locale(botId=BOT_ID, botVersion="DRAFT", localeId="en_US")
for i in range(30):
    time.sleep(3)
    status = lex.describe_bot_locale(botId=BOT_ID, botVersion="DRAFT", localeId="en_US")
    s = status["botLocaleStatus"]
    print(f"  {s}")
    if s in ("Built", "ReadyExpressTesting"):
        break
    if s == "Failed":
        print(f"  FAILED: {status.get('failureReasons')}")
        exit(1)

# Step 4: Create new version
print("\nCreating version...")
ver = lex.create_bot_version(
    botId=BOT_ID,
    botVersionLocaleSpecification={"en_US": {"sourceBotVersion": "DRAFT"}}
)
new_ver = ver["botVersion"]
print(f"  Version {new_ver}")
for i in range(20):
    time.sleep(2)
    v = lex.describe_bot_version(botId=BOT_ID, botVersion=new_ver)
    if v["botStatus"] == "Available":
        print(f"  Version {new_ver} available")
        break

# Step 5: Update alias
print(f"\nUpdating alias to version {new_ver}...")
lex.update_bot_alias(
    botId=BOT_ID,
    botAliasId=ALIAS_ID,
    botAliasName="live",
    botVersion=new_ver,
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
print("  Alias updated")

# Step 6: Test
print("\nTesting Lex bot...")
time.sleep(2)
try:
    resp = lex_runtime.recognize_text(
        botId=BOT_ID,
        botAliasId=ALIAS_ID,
        localeId="en_US",
        sessionId="test-fix-456",
        text="I need help finding food assistance"
    )
    intent_name = resp.get("sessionState", {}).get("intent", {}).get("name", "NONE")
    intent_state = resp.get("sessionState", {}).get("intent", {}).get("state", "NONE")
    session_attrs = resp.get("sessionState", {}).get("sessionAttributes", {})
    messages = resp.get("messages", [])
    print(f"  Intent: {intent_name}")
    print(f"  State: {intent_state}")
    print(f"  Session attrs keys: {list(session_attrs.keys())}")
    if "aiResponse" in session_attrs:
        print(f"  aiResponse (first 200 chars): {session_attrs['aiResponse'][:200]}")
    print(f"  Messages: {json.dumps(messages[:1], indent=2)[:500]}")

    if intent_state == "Fulfilled" and "aiResponse" in session_attrs:
        print("\n*** SUCCESS! Lex fulfillment is working! ***")
    elif intent_state == "ReadyForFulfillment":
        print("\n*** STILL NOT CALLING LAMBDA - fulfillment not active ***")
    else:
        print(f"\n*** Unexpected state: {intent_state} ***")
except Exception as e:
    print(f"  Error: {e}")
