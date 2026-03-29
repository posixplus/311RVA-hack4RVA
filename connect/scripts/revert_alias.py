#!/usr/bin/env python3
"""Revert alias to version 5 (which was confirmed working) with Lambda"""
import json
import boto3

BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"
lex = boto3.client("lexv2-models", region_name="us-east-1")

# Check current alias
alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"Current alias version: {alias['botVersion']}")
print(f"Current locales: {json.dumps(alias['botAliasLocaleSettings'], indent=2)}")

# Revert to version 5 with en_US only (the version that was working)
print("\nReverting alias to version 5...")
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

alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"Reverted alias version: {alias['botVersion']}")
print(f"Locales: {list(alias['botAliasLocaleSettings'].keys())}")
print("DONE")
