#!/usr/bin/env python3
"""Test Lex bot directly to see if fulfillment Lambda gets called"""
import json
import boto3

lex_runtime = boto3.client("lexv2-runtime", region_name="us-east-1")

try:
    resp = lex_runtime.recognize_text(
        botId="QPUFEHCFV9",
        botAliasId="HHBVRXMHDC",
        localeId="en_US",
        sessionId="test-session-123",
        text="I need help finding food assistance"
    )
    print("Lex response:")
    print(f"  Intent: {resp.get('sessionState', {}).get('intent', {}).get('name', 'NONE')}")
    print(f"  State: {resp.get('sessionState', {}).get('intent', {}).get('state', 'NONE')}")
    print(f"  Session attrs: {json.dumps(resp.get('sessionState', {}).get('sessionAttributes', {}), indent=2)}")
    print(f"  Messages: {json.dumps(resp.get('messages', []), indent=2)}")
    print(f"  Interpretations: {[i['intent']['name'] for i in resp.get('interpretations', [])]}")
except Exception as e:
    print(f"Error: {e}")
