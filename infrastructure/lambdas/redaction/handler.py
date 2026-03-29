"""
Redaction Lambda - PII detection and redaction using AWS Comprehend
Supports single text redaction and bulk mode processing
"""

import json
import boto3
from typing import Any, Dict, List

comprehend_client = boto3.client("comprehend")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for PII redaction.
    Supports single text or bulk texts mode.
    """
    try:
        # Parse input
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # Check for bulk mode
        if "texts" in body:
            return handle_bulk_redaction(body.get("texts", []))
        else:
            text = body.get("text", "")
            if not text:
                return error_response("No text provided", 400)
            return handle_single_redaction(text)

    except Exception as e:
        print(f"Error in redaction handler: {str(e)}")
        return error_response(str(e), 500)


def handle_single_redaction(text: str) -> Dict[str, Any]:
    """
    Redact PII from a single text string.
    """
    try:
        if not text:
            return success_response(
                {
                    "original_text": "",
                    "redacted_text": "",
                    "entities_found": [],
                    "entity_count": 0,
                }
            )

        # Detect PII entities
        pii_response = comprehend_client.detect_pii_entities(
            Text=text,
            LanguageCode="en",
        )

        entities = pii_response.get("Entities", [])

        # Redact PII
        redacted_text = redact_pii(text, entities)

        # Build entity details
        entities_found = []
        for entity in entities:
            entities_found.append(
                {
                    "type": entity["Type"],
                    "score": float(entity["Score"]),
                    "offset": entity["BeginOffset"],
                    "length": entity["EndOffset"] - entity["BeginOffset"],
                    "value": text[entity["BeginOffset"] : entity["EndOffset"]],
                }
            )

        return success_response(
            {
                "original_text": text,
                "redacted_text": redacted_text,
                "entities_found": entities_found,
                "entity_count": len(entities),
            }
        )

    except Exception as e:
        print(f"Error in single redaction: {str(e)}")
        return error_response(str(e), 500)


def handle_bulk_redaction(texts: List[str]) -> Dict[str, Any]:
    """
    Redact PII from multiple texts.
    Returns array of redacted texts in same order.
    """
    try:
        if not texts:
            return success_response(
                {
                    "redacted_texts": [],
                    "total_processed": 0,
                    "errors": [],
                }
            )

        redacted_texts = []
        errors = []

        for i, text in enumerate(texts):
            try:
                if not text:
                    redacted_texts.append("")
                    continue

                # Detect PII
                pii_response = comprehend_client.detect_pii_entities(
                    Text=text,
                    LanguageCode="en",
                )

                entities = pii_response.get("Entities", [])
                redacted = redact_pii(text, entities)
                redacted_texts.append(redacted)

            except Exception as e:
                print(f"Error redacting text at index {i}: {str(e)}")
                errors.append({"index": i, "error": str(e)})
                redacted_texts.append(text)  # Return original if error

        return success_response(
            {
                "redacted_texts": redacted_texts,
                "total_processed": len(texts),
                "errors": errors if errors else [],
            }
        )

    except Exception as e:
        print(f"Error in bulk redaction: {str(e)}")
        return error_response(str(e), 500)


def redact_pii(text: str, entities: List[Dict[str, Any]]) -> str:
    """
    Redact PII entities in text by replacing with type-specific placeholders.
    Handles: NAME, ADDRESS, PHONE, EMAIL, SSN, DATE_OF_BIRTH, DRIVER_ID,
             PASSPORT_NUMBER, CREDIT_DEBIT_NUMBER, BANK_ACCOUNT_NUMBER, IP_ADDRESS
    """
    if not entities:
        return text

    # Sort by end offset (descending) to avoid offset issues during replacement
    entities = sorted(entities, key=lambda x: x["EndOffset"], reverse=True)

    result = text
    for entity in entities:
        pii_type = entity["Type"]
        start = entity["BeginOffset"]
        end = entity["EndOffset"]

        # Map entity types to redaction strings
        type_map = {
            "NAME": "[NAME]",
            "ADDRESS": "[ADDRESS]",
            "PHONE": "[PHONE]",
            "EMAIL": "[EMAIL]",
            "SSN": "[SSN]",
            "DATE_OF_BIRTH": "[DOB]",
            "DRIVER_ID": "[DRIVER_ID]",
            "PASSPORT_NUMBER": "[PASSPORT]",
            "CREDIT_DEBIT_NUMBER": "[CARD_NUMBER]",
            "BANK_ACCOUNT_NUMBER": "[ACCOUNT_NUMBER]",
            "IP_ADDRESS": "[IP_ADDRESS]",
        }

        placeholder = type_map.get(pii_type, f"[{pii_type}]")
        result = result[:start] + placeholder + result[end:]

    return result


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build HTTP success response with CORS headers."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }


def error_response(message: str, status_code: int) -> Dict[str, Any]:
    """Build HTTP error response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }
