"""
Email Summary Lambda - Sends call summaries via email/SMS to users and nonprofits
Uses AWS SES for email and SNS for SMS delivery
Includes PII redaction for nonprofit recipients
"""

import json
import os
import boto3
import re
from typing import Any, Dict, List
from datetime import datetime

ses_client = boto3.client("ses")
sns_client = boto3.client("sns")
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
comprehend_client = boto3.client("comprehend")

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@richmond311.com")
LOGS_BUCKET = os.environ.get("LOGS_BUCKET")
SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE")
REGION = os.environ.get("REGION", "us-east-1")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle email/SMS delivery of conversation summaries.
    Supports both user and nonprofit delivery.
    """
    try:
        # Parse input (handle both API Gateway and direct invocation)
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event if isinstance(event, dict) else {}

        session_id = body.get("sessionId")
        delivery_method = body.get("deliveryMethod", "email")
        delivery_address = body.get("deliveryAddress", "").strip()
        is_nonprofit = body.get("isNonprofit", False)

        if not session_id:
            return error_response("No sessionId provided", 400)

        if not delivery_address:
            return error_response("No delivery address provided", 400)

        # Retrieve session from DynamoDB
        session_data = retrieve_session(session_id)
        if not session_data:
            return error_response("Session not found", 404)

        # Generate summary
        summary = generate_summary(session_id, session_data)

        # Redact if delivering to nonprofit
        if is_nonprofit:
            summary = redact_pii_summary(summary)

        # Send via requested method
        if delivery_method == "sms":
            send_sms(delivery_address, summary)
        else:  # email
            send_email(delivery_address, session_id, summary, is_nonprofit)

        # Update session with delivery info
        update_session_delivery(session_id, delivery_method, delivery_address)

        return success_response(
            {
                "sessionId": session_id,
                "deliveryMethod": delivery_method,
                "deliveryAddress": delivery_address,
                "message": f"Summary delivered via {delivery_method}",
            }
        )

    except Exception as e:
        print(f"Error in email summary handler: {str(e)}")
        return error_response(str(e), 500)


def retrieve_session(session_id: str) -> Dict[str, Any]:
    """
    Retrieve full session data from DynamoDB.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id})
        return response.get("Item")
    except Exception as e:
        print(f"Error retrieving session: {str(e)}")
        return None


def generate_summary(session_id: str, session_data: Dict[str, Any]) -> str:
    """
    Generate a text summary of the conversation.
    """
    try:
        conversation = session_data.get("conversation", [])

        if not conversation:
            return "No conversation history available."

        summary_parts = []
        summary_parts.append(f"SESSION SUMMARY - {session_id}\n")
        summary_parts.append(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        summary_parts.append(f"Total Interactions: {len(conversation)}\n")
        summary_parts.append(f"Language: {session_data.get('language', 'English')}\n")
        summary_parts.append(f"Category: {session_data.get('category', 'General')}\n")
        summary_parts.append("\n--- CONVERSATION TRANSCRIPT ---\n")

        for i, exchange in enumerate(conversation, 1):
            timestamp = exchange.get("timestamp", "")
            if timestamp and isinstance(timestamp, int):
                # Convert milliseconds to ISO format
                dt = datetime.fromtimestamp(timestamp / 1000)
                timestamp_str = dt.strftime("%H:%M:%S")
            else:
                timestamp_str = str(timestamp)

            summary_parts.append(f"\n[{timestamp_str}] USER:\n")
            summary_parts.append(exchange.get("message", "") + "\n")

            summary_parts.append(f"\n[{timestamp_str}] RESPONSE:\n")
            summary_parts.append(exchange.get("response", "") + "\n")

        summary = "".join(summary_parts)
        return summary

    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Unable to generate summary. Please contact support."


def generate_html_email(session_id: str, session_data: Dict[str, Any], summary: str, is_nonprofit: bool) -> str:
    """
    Generate HTML email with RVA311 branding (navy blue header).
    """
    try:
        conversation = session_data.get("conversation", [])
        message_count = len(conversation)
        category = session_data.get("category", "General")
        language = session_data.get("language", "English")

        conversation_html = ""
        for i, exchange in enumerate(conversation, 1):
            timestamp = exchange.get("timestamp", "")
            if timestamp and isinstance(timestamp, int):
                dt = datetime.fromtimestamp(timestamp / 1000)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)

            conversation_html += f"""
            <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-left: 4px solid #001a4d;">
                <p style="margin: 0 0 10px 0; font-size: 0.95em; color: #666;">
                    <strong style="color: #001a4d;">Interaction #{i}</strong> • {timestamp_str}
                </p>
                <p style="margin: 0 0 8px 0;"><strong style="color: #001a4d;">You asked:</strong></p>
                <p style="margin: 0 0 12px 0; padding: 10px; background: white; border-radius: 4px;">
                    {escape_html(exchange.get("message", ""))}
                </p>
                <p style="margin: 0 0 8px 0;"><strong style="color: #001a4d;">Response:</strong></p>
                <p style="margin: 0; padding: 10px; background: white; border-radius: 4px;">
                    {escape_html(exchange.get("response", ""))}
                </p>
            </div>
            """

        nonprofit_section = ""
        if is_nonprofit:
            nonprofit_section = """
            <div style="margin-top: 30px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">
                <p style="margin: 0; color: #856404;">
                    <strong>Non-profit Partners:</strong> This summary has been redacted of personally identifiable information (PII) to protect caller privacy.
                </p>
            </div>
            """

        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f9f9f9;
                }}
                .container {{
                    max-width: 650px;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #001a4d 0%, #002966 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                    border-bottom: 4px solid #ff6b35;
                }}
                .header h1 {{
                    margin: 0 0 5px 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .header p {{
                    margin: 0;
                    font-size: 14px;
                    opacity: 0.95;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .section {{
                    margin-bottom: 25px;
                }}
                .section h2 {{
                    color: #001a4d;
                    font-size: 18px;
                    border-bottom: 2px solid #001a4d;
                    padding-bottom: 10px;
                    margin: 0 0 15px 0;
                }}
                .meta {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .meta-item {{
                    padding: 12px;
                    background: #f5f5f5;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                .meta-label {{
                    font-weight: 600;
                    color: #001a4d;
                    display: block;
                    margin-bottom: 4px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .footer a {{
                    color: #001a4d;
                    text-decoration: none;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    background: #e8f4f8;
                    color: #001a4d;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-right: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Richmond 311</h1>
                    <p>Conversation Summary</p>
                </div>

                <div class="content">
                    <div class="section">
                        <h2>Session Information</h2>
                        <div class="meta">
                            <div class="meta-item">
                                <span class="meta-label">Session ID</span>
                                {session_id}
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Total Interactions</span>
                                {message_count}
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Category</span>
                                <span class="badge">{escape_html(category)}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Language</span>
                                {escape_html(language)}
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h2>Conversation Transcript</h2>
                        {conversation_html}
                    </div>

                    {nonprofit_section}

                    <div class="section" style="background: #e8f4f8; padding: 15px; border-radius: 4px; margin-top: 20px;">
                        <h2 style="margin-top: 0;">Next Steps</h2>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Review the conversation transcript above</li>
                            <li>Take any necessary follow-up actions</li>
                            <li>Document this interaction in your system if applicable</li>
                            <li>Coordinate with other organizations if needed</li>
                        </ul>
                    </div>

                    <div class="footer">
                        <p>This is an automated report from the Richmond City 24/7 Resource Assistant.</p>
                        <p>For questions or support, visit <a href="https://richmond.gov">richmond.gov</a> or call Richmond Services at 311.</p>
                        <p style="margin-top: 15px; font-size: 11px; color: #999;">
                            Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return email_html

    except Exception as e:
        print(f"Error generating HTML email: {str(e)}")
        return f"<html><body><p>Session ID: {session_id}</p><p>{escape_html(summary)}</p></body></html>"


def send_email(recipient: str, session_id: str, summary: str, is_nonprofit: bool) -> None:
    """
    Send email via SES with HTML template.
    """
    try:
        # Retrieve session for HTML generation
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id})
        session_data = response.get("Item", {})

        # Generate HTML email
        html_body = generate_html_email(session_id, session_data, summary, is_nonprofit)

        # Determine subject
        recipient_type = "Non-profit Partners" if is_nonprofit else "You"
        subject = f"Richmond 311 - Conversation Summary for {session_id[:8]}"

        ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                "ToAddresses": [recipient],
            },
            Message={
                "Subject": {
                    "Data": subject,
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Html": {
                        "Data": html_body,
                        "Charset": "UTF-8",
                    },
                },
            },
        )

        print(f"Email sent successfully to {recipient}")

    except Exception as e:
        print(f"Error sending email to {recipient}: {str(e)}")
        raise


def send_sms(phone_number: str, summary: str) -> None:
    """
    Send SMS summary via SNS.
    Truncates summary to fit SMS character limits.
    """
    try:
        # Keep SMS under 1600 characters (multiple messages supported)
        message_text = summary[:1600]

        sns_client.publish(
            PhoneNumber=phone_number,
            Message=message_text,
            MessageAttributes={
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": "Richmond311",
                },
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                },
            },
        )

        print(f"SMS sent successfully to {phone_number}")

    except Exception as e:
        print(f"Error sending SMS to {phone_number}: {str(e)}")
        raise


def redact_pii_summary(text: str) -> str:
    """
    Redact PII from summary text using AWS Comprehend.
    """
    try:
        if not text:
            return text

        # Detect PII entities
        response = comprehend_client.detect_pii_entities(
            Text=text,
            LanguageCode="en",
        )

        entities = response.get("Entities", [])

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


def update_session_delivery(session_id: str, delivery_method: str, delivery_address: str) -> None:
    """
    Update session with delivery information.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET deliveryMethod = :method, deliveryAddress = :address, summaryDeliveredAt = :ts",
            ExpressionAttributeValues={
                ":method": delivery_method,
                ":address": delivery_address,
                ":ts": timestamp,
            },
        )
    except Exception as e:
        print(f"Error updating session delivery info: {str(e)}")


def escape_html(text: str) -> str:
    """
    Escape HTML special characters.
    """
    if not text:
        return ""

    escapes = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }

    for char, escape in escapes.items():
        text = text.replace(char, escape)

    return text


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build HTTP success response with CORS headers."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
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
        },
        "body": json.dumps({"error": message}),
    }
