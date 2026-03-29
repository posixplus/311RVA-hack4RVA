"""
Dashboard Lambda - Provides analytics and reporting APIs for Richmond 311
Handles session browsing, statistics, and CSV export (admin only)
All PII is redacted in non-admin responses
"""

import json
import os
import boto3
import csv
from io import StringIO
from typing import Any, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
comprehend_client = boto3.client("comprehend")
s3_client = boto3.client("s3")

SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE")
LOGS_BUCKET = os.environ.get("LOGS_BUCKET")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "richmond311admin")
REGION = os.environ.get("REGION", "us-east-1")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main dashboard handler.
    Routes to appropriate endpoint based on path.
    """
    try:
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/dashboard")

        # GET /dashboard/sessions - all sessions (redacted)
        if path == "/dashboard/sessions" and http_method == "GET":
            return handle_get_sessions(event)

        # GET /dashboard/sessions/{id} - specific session
        if path.startswith("/dashboard/sessions/") and http_method == "GET" and not path.endswith("/export"):
            session_id = path.split("/")[-1]
            return handle_get_session_detail(event, session_id)

        # GET /dashboard/stats - aggregate statistics
        if path == "/dashboard/stats" and http_method == "GET":
            return handle_get_stats(event)

        # POST /dashboard/export - CSV export (admin only)
        if path == "/dashboard/export" and http_method == "POST":
            return handle_export(event)

        return error_response("Endpoint not found", 404)

    except Exception as e:
        print(f"Error in dashboard handler: {str(e)}")
        return error_response(str(e), 500)


def handle_get_sessions(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /dashboard/sessions
    Returns all sessions with PII redacted for dashboard view.
    Supports pagination with 'limit' and 'lastSessionId' query parameters.
    """
    try:
        query_params = event.get("queryStringParameters", {}) or {}
        limit = int(query_params.get("limit", "100"))
        limit = min(limit, 100)  # Cap at 100

        table = dynamodb.Table(SESSIONS_TABLE)

        # Scan with limit
        scan_kwargs = {
            "Limit": limit,
        }

        # Handle pagination
        if "lastSessionId" in query_params:
            scan_kwargs["ExclusiveStartKey"] = {"sessionId": query_params["lastSessionId"]}

        response = table.scan(**scan_kwargs)

        sessions = []
        for item in response.get("Items", []):
            session = {
                "sessionId": item.get("sessionId"),
                "category": item.get("category", "general"),
                "language": item.get("language", "en"),
                "startTime": item.get("createdAt"),
                "status": item.get("status", "active"),
                "messageCount": item.get("messageCount", 0),
                "lastActivityAt": item.get("lastActivityAt"),
            }
            sessions.append(session)

        return success_response({
            "sessions": sessions,
            "total": len(sessions),
            "hasMore": "LastEvaluatedKey" in response,
            "nextPageToken": response.get("LastEvaluatedKey", {}).get("sessionId"),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        print(f"Error in handle_get_sessions: {str(e)}")
        return error_response(str(e), 500)


def handle_get_session_detail(event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    GET /dashboard/sessions/{id}
    Returns full session detail.
    Admin (with x-admin-key header) gets unredacted data.
    Others get redacted data.
    """
    try:
        # Check for admin key
        headers = event.get("headers", {}) or {}
        admin_key = headers.get("x-admin-key") or headers.get("X-Admin-Key")
        is_admin = admin_key == ADMIN_KEY

        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id})

        if "Item" not in response:
            return error_response("Session not found", 404)

        item = response["Item"]

        # Redact conversation if not admin
        if not is_admin:
            if "conversation" in item:
                item["conversation"] = [
                    {
                        "message": redact_pii(msg.get("message", "")),
                        "response": redact_pii(msg.get("response", "")),
                        "timestamp": msg.get("timestamp"),
                    }
                    for msg in item["conversation"]
                ]
            # Hide delivery address
            item["deliveryAddress"] = "[REDACTED]" if "deliveryAddress" in item else None

        # Convert Decimal to float for JSON serialization
        item = convert_decimals(item)

        return success_response(item)

    except Exception as e:
        print(f"Error in handle_get_session_detail: {str(e)}")
        return error_response(str(e), 500)


def handle_get_stats(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /dashboard/stats
    Returns aggregate statistics about sessions.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)

        # Scan all sessions
        response = table.scan()
        items = response.get("Items", [])

        # Calculate statistics
        total_sessions = len(items)
        sessions_by_category = {}
        sessions_by_language = {}
        sessions_by_status = {}
        total_messages = 0
        messages_count = 0

        for item in items:
            # By category
            category = item.get("category", "general")
            sessions_by_category[category] = sessions_by_category.get(category, 0) + 1

            # By language
            language = item.get("language", "en")
            sessions_by_language[language] = sessions_by_language.get(language, 0) + 1

            # By status
            status = item.get("status", "active")
            sessions_by_status[status] = sessions_by_status.get(status, 0) + 1

            # Message count
            message_count = item.get("messageCount", 0)
            if isinstance(message_count, Decimal):
                message_count = int(message_count)
            total_messages += message_count
            messages_count += 1

        # Calculate averages
        avg_messages_per_session = (
            total_messages / messages_count if messages_count > 0 else 0
        )

        # Session duration stats (from createdAt to completedAt or lastActivityAt)
        session_durations = []
        for item in items:
            created_at = item.get("createdAt")
            end_time = item.get("completedAt") or item.get("lastActivityAt")

            if created_at and end_time:
                duration_ms = end_time - created_at
                session_durations.append(duration_ms)

        avg_session_duration_ms = (
            sum(session_durations) / len(session_durations)
            if session_durations
            else 0
        )

        return success_response({
            "totalSessions": total_sessions,
            "sessionsByCategory": sessions_by_category,
            "sessionsByLanguage": sessions_by_language,
            "sessionsByStatus": sessions_by_status,
            "totalMessages": total_messages,
            "averageMessagesPerSession": round(avg_messages_per_session, 2),
            "averageSessionDurationMs": int(avg_session_duration_ms),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        print(f"Error in handle_get_stats: {str(e)}")
        return error_response(str(e), 500)


def handle_export(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /dashboard/export
    Exports all sessions as CSV (admin only).
    Returns CSV content or upload URL to S3.
    """
    try:
        # Check for admin key
        headers = event.get("headers", {}) or {}
        admin_key = headers.get("x-admin-key") or headers.get("X-Admin-Key")

        if admin_key != ADMIN_KEY:
            return error_response("Unauthorized: Admin key required", 401)

        # Parse body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        include_conversation = body.get("includeConversation", False)
        upload_to_s3 = body.get("uploadToS3", False)

        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.scan()
        items = response.get("Items", [])

        # Generate CSV
        csv_content = generate_csv_export(items, include_conversation)

        if upload_to_s3:
            # Upload to S3 and return URL
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"exports/sessions_export_{timestamp}.csv"

            s3_client.put_object(
                Bucket=LOGS_BUCKET,
                Key=s3_key,
                Body=csv_content.encode("utf-8"),
                ContentType="text/csv",
            )

            s3_url = f"s3://{LOGS_BUCKET}/{s3_key}"

            return success_response({
                "message": "Export uploaded to S3",
                "s3Url": s3_url,
                "rowsExported": len(items),
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            # Return CSV content in response
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/csv",
                    "Content-Disposition": f"attachment; filename=sessions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": csv_content,
            }

    except Exception as e:
        print(f"Error in handle_export: {str(e)}")
        return error_response(str(e), 500)


def generate_csv_export(items: List[Dict[str, Any]], include_conversation: bool = False) -> str:
    """
    Generate CSV content from sessions.
    """
    try:
        output = StringIO()
        writer = None

        for i, item in enumerate(items):
            item = convert_decimals(item)

            if i == 0:
                # Write header row
                fieldnames = [
                    "sessionId",
                    "createdAt",
                    "status",
                    "category",
                    "language",
                    "messageCount",
                    "lastActivityAt",
                ]
                if include_conversation:
                    fieldnames.append("conversationSummary")

                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

            # Write data row
            row = {
                "sessionId": item.get("sessionId", ""),
                "createdAt": item.get("createdAt", ""),
                "status": item.get("status", ""),
                "category": item.get("category", ""),
                "language": item.get("language", ""),
                "messageCount": item.get("messageCount", 0),
                "lastActivityAt": item.get("lastActivityAt", ""),
            }

            if include_conversation:
                # Summarize conversation
                conversation = item.get("conversation", [])
                summary = f"({len(conversation)} interactions)"
                if conversation:
                    first_msg = conversation[0].get("message", "")[:50]
                    summary += f" Started with: {first_msg}..."
                row["conversationSummary"] = summary

            writer.writerow(row)

        return output.getvalue()

    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        return ""


def redact_pii(text: str) -> str:
    """
    Redact PII from text using AWS Comprehend.
    """
    try:
        if not text or len(text) < 5:
            return text

        # Detect PII entities
        response = comprehend_client.detect_pii_entities(
            Text=text,
            LanguageCode="en",
        )

        entities = response.get("Entities", [])

        if not entities:
            return text

        # Sort by end offset (descending)
        entities = sorted(entities, key=lambda x: x["EndOffset"], reverse=True)

        redacted = text
        for entity in entities:
            start = entity["BeginOffset"]
            end = entity["EndOffset"]
            entity_type = entity["Type"]
            placeholder = f"[{entity_type}]"
            redacted = redacted[:start] + placeholder + redacted[end:]

        return redacted

    except Exception as e:
        print(f"Error redacting PII: {str(e)}")
        return text


def convert_decimals(obj: Any) -> Any:
    """
    Convert DynamoDB Decimal objects to float/int for JSON serialization.
    """
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build HTTP success response with CORS headers."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Admin-Key",
        },
        "body": json.dumps(data, default=str),
    }


def error_response(message: str, status_code: int) -> Dict[str, Any]:
    """Build HTTP error response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Admin-Key",
        },
        "body": json.dumps({"error": message}),
    }
