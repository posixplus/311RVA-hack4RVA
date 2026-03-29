import json
import boto3
import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client("comprehend")

# PII entity types to redact completely
REDACT_TYPES = {"SSN", "CREDIT_DEBIT_NUMBER", "BANK_ACCOUNT_NUMBER", "PASSPORT_NUMBER", "DRIVER_ID"}
# Partially redact these (show last 4)
PARTIAL_REDACT_TYPES = {"PHONE", "ADDRESS"}

# Max length for Comprehend API
MAX_TEXT_LENGTH = 5000


def chunk_text(text, chunk_size=5000):
    """Split text into chunks for Comprehend processing"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def process_chunk(chunk):
    """Process a single text chunk through Comprehend"""
    try:
        response = comprehend.detect_pii_entities(
            Text=chunk,
            LanguageCode="en"
        )
        return response.get("Entities", []), None
    except Exception as e:
        logger.warning(f"Comprehend error processing chunk: {str(e)}")
        return [], str(e)


def redact_text(text):
    """
    Redact PII from text using Amazon Comprehend.

    Returns: (redacted_text, pii_found, entity_types)
    """
    if not text:
        return text, False, []

    all_entities = []
    entity_types_found = set()
    error_occurred = False

    # Process in chunks
    if len(text) > MAX_TEXT_LENGTH:
        logger.info(f"Text exceeds {MAX_TEXT_LENGTH} chars, chunking")
        chunks = chunk_text(text, MAX_TEXT_LENGTH)
        offset = 0

        for chunk in chunks:
            entities, error = process_chunk(chunk)
            error_occurred = error_occurred or (error is not None)

            # Adjust entity offsets for multi-chunk processing
            for entity in entities:
                entity["BeginOffset"] = entity.get("BeginOffset", 0) + offset
                entity["EndOffset"] = entity.get("EndOffset", 0) + offset
                all_entities.append(entity)

            offset += len(chunk)
    else:
        all_entities, error = process_chunk(text)
        error_occurred = error is not None

    if error_occurred and not all_entities:
        logger.warning("Comprehend failed and no entities found, returning original text")
        return text, False, []

    # Collect entity types found
    for entity in all_entities:
        entity_types_found.add(entity.get("Type", "UNKNOWN"))

    # Sort by offset descending to avoid offset invalidation during replacement
    all_entities.sort(key=lambda e: e.get("BeginOffset", 0), reverse=True)

    redacted_text = text
    replacements_made = 0

    for entity in all_entities:
        entity_type = entity.get("Type", "")
        begin = entity.get("BeginOffset", 0)
        end = entity.get("EndOffset", 0)

        if begin >= end or begin < 0 or end > len(redacted_text):
            logger.warning(f"Invalid entity offset: {begin}-{end} for text length {len(redacted_text)}")
            continue

        if entity_type in REDACT_TYPES:
            replacement = "[REDACTED]"
            redacted_text = redacted_text[:begin] + replacement + redacted_text[end:]
            replacements_made += 1

        elif entity_type in PARTIAL_REDACT_TYPES:
            original = redacted_text[begin:end]
            if len(original) > 4:
                replacement = "[***" + original[-4:] + "]"
            else:
                replacement = "[***" + original + "]"
            redacted_text = redacted_text[:begin] + replacement + redacted_text[end:]
            replacements_made += 1

    pii_found = len(all_entities) > 0
    logger.info(f"Redaction complete: {replacements_made} replacements, types: {entity_types_found}")

    return redacted_text, pii_found, list(entity_types_found)


def lambda_handler(event, context):
    """
    Lambda handler for PII redaction.
    Expected event format: {"text": "..."}
    """
    try:
        text = event.get("text", "")

        if not text:
            return {
                "redacted_text": "",
                "pii_found": False,
                "entity_types": []
            }

        redacted_text, pii_found, entity_types = redact_text(text)

        return {
            "redacted_text": redacted_text,
            "pii_found": pii_found,
            "entity_types": entity_types
        }

    except Exception as e:
        logger.error(f"Unhandled exception in redaction handler: {str(e)}", exc_info=True)
        return {
            "redacted_text": event.get("text", ""),
            "pii_found": False,
            "entity_types": [],
            "error": str(e)
        }
