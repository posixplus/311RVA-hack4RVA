#!/usr/bin/env python3
"""Configure Lex bot to use Lambda fulfillment for CatchAllIntent"""
import json
import boto3
import time

BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
INTENT_ID = "4BDNOO5GF7"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"
REGION = "us-east-1"

lex = boto3.client("lexv2-models", region_name=REGION)

# Step 1: Update CatchAllIntent to use fulfillment code hook
print("Step 1: Update CatchAllIntent with fulfillment code hook...")
intent = lex.describe_intent(
    botId=BOT_ID, botVersion="DRAFT", localeId="en_US", intentId=INTENT_ID
)

# Update the intent with fulfillment code hook
update_params = {
    "botId": BOT_ID,
    "botVersion": "DRAFT",
    "localeId": "en_US",
    "intentId": INTENT_ID,
    "intentName": "CatchAllIntent",
    "sampleUtterances": intent["sampleUtterances"],
    "fulfillmentCodeHook": {
        "enabled": True,
        "active": True,
        "postFulfillmentStatusSpecification": {
            "successNextStep": {"dialogAction": {"type": "EndConversation"}},
            "failureNextStep": {"dialogAction": {"type": "EndConversation"}},
            "timeoutNextStep": {"dialogAction": {"type": "EndConversation"}}
        }
    },
}
# Preserve initialResponseSetting if it exists
if "initialResponseSetting" in intent:
    update_params["initialResponseSetting"] = intent["initialResponseSetting"]
lex.update_intent(**update_params)
print("  Intent updated with fulfillment code hook")

# Step 2: Build the bot
print("Step 2: Building bot...")
build_resp = lex.build_bot_locale(
    botId=BOT_ID, botVersion="DRAFT", localeId="en_US"
)
print(f"  Build status: {build_resp['botLocaleStatus']}")

# Wait for build
for i in range(30):
    time.sleep(3)
    status = lex.describe_bot_locale(
        botId=BOT_ID, botVersion="DRAFT", localeId="en_US"
    )
    s = status["botLocaleStatus"]
    print(f"  Build status: {s}")
    if s in ("Built", "ReadyExpressTesting"):
        break
    if s == "Failed":
        print(f"  Build failed: {status.get('failureReasons', 'unknown')}")
        exit(1)

# Step 3: Create new bot version
print("Step 3: Creating bot version...")
version_resp = lex.create_bot_version(
    botId=BOT_ID,
    botVersionLocaleSpecification={
        "en_US": {"sourceBotVersion": "DRAFT"}
    }
)
new_version = version_resp["botVersion"]
print(f"  Created version: {new_version}")

# Wait for version to be available
for i in range(20):
    time.sleep(2)
    v = lex.describe_bot_version(botId=BOT_ID, botVersion=new_version)
    vs = v["botStatus"]
    print(f"  Version {new_version} status: {vs}")
    if vs == "Available":
        break

# Step 4: Update alias with Lambda and new version
print("Step 4: Updating bot alias with Lambda function...")
lex.update_bot_alias(
    botId=BOT_ID,
    botAliasId=ALIAS_ID,
    botAliasName="live",
    botVersion=new_version,
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
print(f"  Alias updated to version {new_version} with Lambda fulfillment")

# Verify
alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"\nVerification:")
print(f"  Alias version: {alias['botVersion']}")
print(f"  Locale settings: {json.dumps(alias['botAliasLocaleSettings'], indent=2)}")
print("\nDONE! Lex bot now calls Lambda directly for fulfillment.")
