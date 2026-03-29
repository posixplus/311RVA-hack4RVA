#!/usr/bin/env python3
"""Add Spanish (es_US) and Arabic (ar_001) locales to Lex bot with CatchAllIntent + Lambda fulfillment"""
import json
import boto3
import time

BOT_ID = "QPUFEHCFV9"
ALIAS_ID = "HHBVRXMHDC"
LAMBDA_ARN = "arn:aws:lambda:us-east-1:099407892939:function:richmond-orchestrator"
lex = boto3.client("lexv2-models", region_name="us-east-1")

LOCALES = {
    "es_US": {
        "name": "Spanish (US)",
        "nlu_confidence": 0.10,
        "utterances": [
            {"utterance": "necesito ayuda"},
            {"utterance": "ayuda"},
            {"utterance": "necesito comida"},
            {"utterance": "vivienda"},
            {"utterance": "refugio"},
            {"utterance": "emergencia"},
            {"utterance": "ayuda con inmigración"},
            {"utterance": "salud"},
            {"utterance": "ayuda legal"},
            {"utterance": "necesito asistencia"},
            {"utterance": "dónde puedo encontrar ayuda"},
            {"utterance": "tengo una pregunta"},
            {"utterance": "servicios de la ciudad"},
            {"utterance": "beneficios"},
            {"utterance": "SNAP"},
            {"utterance": "necesito un doctor"},
            {"utterance": "asistencia con renta"},
            {"utterance": "asistencia de vivienda"},
            {"utterance": "hola"},
            {"utterance": "sí"},
            {"utterance": "no"},
            {"utterance": "gracias"},
            {"utterance": "necesito información"},
            {"utterance": "quiero reportar algo"},
            {"utterance": "licencia de negocio"},
        ]
    },
    "ar_001": {
        "name": "Arabic",
        "nlu_confidence": 0.10,
        "utterances": [
            {"utterance": "أحتاج مساعدة"},
            {"utterance": "مساعدة"},
            {"utterance": "أحتاج طعام"},
            {"utterance": "سكن"},
            {"utterance": "مأوى"},
            {"utterance": "طوارئ"},
            {"utterance": "مساعدة هجرة"},
            {"utterance": "صحة"},
            {"utterance": "مساعدة قانونية"},
            {"utterance": "أحتاج مساعدة"},
            {"utterance": "أين يمكنني العثور على مساعدة"},
            {"utterance": "لدي سؤال"},
            {"utterance": "خدمات المدينة"},
            {"utterance": "مزايا"},
            {"utterance": "أحتاج طبيب"},
            {"utterance": "مساعدة إيجار"},
            {"utterance": "مساعدة سكنية"},
            {"utterance": "مرحبا"},
            {"utterance": "نعم"},
            {"utterance": "لا"},
            {"utterance": "شكرا"},
            {"utterance": "أحتاج معلومات"},
            {"utterance": "أريد الإبلاغ عن شيء"},
        ]
    }
}

for locale_id, config in LOCALES.items():
    print(f"\n{'='*50}")
    print(f"Setting up {config['name']} ({locale_id})")
    print(f"{'='*50}")

    # Step 1: Create locale
    print(f"  Creating locale...")
    try:
        lex.create_bot_locale(
            botId=BOT_ID,
            botVersion="DRAFT",
            localeId=locale_id,
            nluIntentConfidenceThreshold=config["nlu_confidence"]
        )
        print(f"  Locale created")
    except Exception as e:
        if "ConflictException" in str(type(e).__name__) or "already exists" in str(e).lower():
            print(f"  Locale already exists, continuing...")
        else:
            print(f"  Error: {e}")
            continue

    # Wait for locale to be ready
    for i in range(10):
        time.sleep(2)
        status = lex.describe_bot_locale(botId=BOT_ID, botVersion="DRAFT", localeId=locale_id)
        s = status["botLocaleStatus"]
        if s in ("NotBuilt", "Built", "ReadyExpressTesting"):
            break

    # Step 2: Create CatchAllIntent for this locale
    print(f"  Creating CatchAllIntent...")
    try:
        intent_resp = lex.create_intent(
            botId=BOT_ID,
            botVersion="DRAFT",
            localeId=locale_id,
            intentName="CatchAllIntent",
            sampleUtterances=config["utterances"],
            fulfillmentCodeHook={
                "enabled": True,
                "active": True,
                "postFulfillmentStatusSpecification": {
                    "successNextStep": {"dialogAction": {"type": "EndConversation"}},
                    "failureNextStep": {"dialogAction": {"type": "EndConversation"}},
                    "timeoutNextStep": {"dialogAction": {"type": "EndConversation"}}
                }
            }
        )
        print(f"  CatchAllIntent created: {intent_resp['intentId']}")
    except Exception as e:
        if "ConflictException" in str(type(e).__name__):
            print(f"  CatchAllIntent already exists, updating...")
            # List intents to find ID
            intents = lex.list_intents(botId=BOT_ID, botVersion="DRAFT", localeId=locale_id)
            for i in intents["intentSummaries"]:
                if i["intentName"] == "CatchAllIntent":
                    lex.update_intent(
                        botId=BOT_ID, botVersion="DRAFT", localeId=locale_id,
                        intentId=i["intentId"], intentName="CatchAllIntent",
                        sampleUtterances=config["utterances"],
                        fulfillmentCodeHook={
                            "enabled": True, "active": True,
                            "postFulfillmentStatusSpecification": {
                                "successNextStep": {"dialogAction": {"type": "EndConversation"}},
                                "failureNextStep": {"dialogAction": {"type": "EndConversation"}},
                                "timeoutNextStep": {"dialogAction": {"type": "EndConversation"}}
                            }
                        }
                    )
                    print(f"  CatchAllIntent updated")
                    break
        else:
            print(f"  Error: {e}")
            continue

    # Step 3: Build the locale
    print(f"  Building locale...")
    lex.build_bot_locale(botId=BOT_ID, botVersion="DRAFT", localeId=locale_id)
    for i in range(30):
        time.sleep(3)
        status = lex.describe_bot_locale(botId=BOT_ID, botVersion="DRAFT", localeId=locale_id)
        s = status["botLocaleStatus"]
        print(f"    {s}")
        if s in ("Built", "ReadyExpressTesting"):
            break
        if s == "Failed":
            print(f"    FAILED: {status.get('failureReasons')}")
            break

# Step 4: Create new bot version with all 3 locales
print(f"\n{'='*50}")
print("Creating bot version with all locales...")
ver = lex.create_bot_version(
    botId=BOT_ID,
    botVersionLocaleSpecification={
        "en_US": {"sourceBotVersion": "DRAFT"},
        "es_US": {"sourceBotVersion": "DRAFT"},
        "ar_001": {"sourceBotVersion": "DRAFT"},
    }
)
new_ver = ver["botVersion"]
print(f"  Version {new_ver}")
for i in range(20):
    time.sleep(3)
    v = lex.describe_bot_version(botId=BOT_ID, botVersion=new_ver)
    print(f"    {v['botStatus']}")
    if v["botStatus"] == "Available":
        break

# Step 5: Update alias with all 3 locales + Lambda
print(f"\nUpdating alias to version {new_ver} with all locales...")
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
        },
        "es_US": {
            "enabled": True,
            "codeHookSpecification": {
                "lambdaCodeHook": {
                    "lambdaARN": LAMBDA_ARN,
                    "codeHookInterfaceVersion": "1.0"
                }
            }
        },
        "ar_001": {
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
print("  Alias updated!")

# Verify
alias = lex.describe_bot_alias(botId=BOT_ID, botAliasId=ALIAS_ID)
print(f"\nFinal alias config:")
print(f"  Version: {alias['botVersion']}")
for loc, settings in alias["botAliasLocaleSettings"].items():
    has_lambda = "codeHookSpecification" in settings
    print(f"  {loc}: enabled={settings['enabled']}, lambda={has_lambda}")

print("\nDONE! Lex bot now supports en_US, es_US, and ar_001")
