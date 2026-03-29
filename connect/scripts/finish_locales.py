#!/usr/bin/env python3
"""Finalize: create bot version with en_US + es_US, update alias"""
import json
import boto3
import time

BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"
lex = boto3.client("lexv2-models", region_name="us-east-1")

# Create version with en_US + es_US
print("Creating bot version with en_US + es_US...")
ver = lex.create_bot_version(
    botId=BOT_ID,
    botVersionLocaleSpecification={
        "en_US": {"sourceBotVersion": "DRAFT"},
        "es_US": {"sourceBotVersion": "DRAFT"},
    }
)
new_ver = ver["botVersion"]
print(f"  Version: {new_ver}")
for i in range(20):
    time.sleep(3)
    v = lex.describe_bot_version(botId=BOT_ID, botVersion=new_ver)
    print(f"  Status: {v['botStatus']}")
    if v["botStatus"] == "Available":
        break

# Update alias with both locales + Lambda
print(f"\nUpdating alias to version {new_ver}...")
lex.update_bot_alias(
    botId=BOT_ID, botAliasId=ALIAS_ID, botAliasName="live",
    botVersion=new_ver,
    botAliasLocaleSettings={
        "en_US": {
            "enabled": True,
            "codeHookSpecification": {
                "lambdaCodeHook": {"lambdaARN": LAMBDA_ARN, "codeHookInterfaceVersion": "1.0"}
            }
        },
        "es_US": {
            "enabled": True,
            "codeHookSpecification": {
                "lambdaCodeHook": {"lambdaARN": LAMBDA_ARN, "codeHookInterfaceVersion": "1.0"}
            }
        }
    }
)

# Add Lambda permission for es_US
lam = boto3.client("lambda", region_name="us-east-1")
try:
    lam.add_permission(
        FunctionName="richmond-orchestrator",
        StatementId="lex-fulfillment-es-US",
        Action="lambda:InvokeFunction",
        Principal="lexv2.amazonaws.com",
        SourceArn=f"arn:aws:lex:us-east-1:099407892939:bot-alias/{BOT_ID}/{ALIAS_ID}"
    )
    print("  Added Lambda permission for es_US")
except Exception as e:
    if "ResourceConflict" in str(type(e).__name__):
        print("  Lambda permission already exists")
    else:
        print(f"  {e}")

alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"\nAlias version: {alias['botVersion']}")
for loc, s in alias["botAliasLocaleSettings"].items():
    print(f"  {loc}: enabled={s['enabled']}, lambda={'codeHookSpecification' in s}")
print("\nDONE!")
