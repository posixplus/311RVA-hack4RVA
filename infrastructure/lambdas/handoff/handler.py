"""
Handoff Lambda - Manages nonprofit/department handoff requests
Records handoffs and sends notifications to target organizations
"""

import json
import os
import boto3
from typing import Any, Dict
from datetime import datetime

ses_client = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")

SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@richmond311.com")
REGION = os.environ.get("REGION", "us-east-1")

# Nonprofit organization configurations
NONPROFIT_ORGS = {
    "irc": {
        "name": "IRC Richmond",
        "email": "handoffs@ircrichmond.org",
        "description": "International Rescue Committee - Refugee Services",
        "phone": "(804) 353-5900",
    },
    "reestablish": {
        "name": "ReEstablish Richmond",
        "email": "intake@reestablishrichmond.org",
        "description": "Housing and homelessness services",
        "phone": "(804) 644-9999",
    },
    "sacred_heart": {
        "name": "Sacred Heart Center",
        "email": "info@sacredheartcenter.org",
        "description": "Comprehensive family support services",
        "phone": "(804) 780-5500",
    },
    "afghan": {
        "name": "Afghan Association of Virginia",
        "email": "info@afghansassociation.org",
        "description": "Afghan community services",
        "phone": "(804) 888-8888",
    },
    "legal_aid": {
        "name": "Central Virginia Legal Aid",
        "email": "info@cvlegalaid.org",
        "description": "Legal aid services",
        "phone": "(804) 648-1012",
    },
    "bha": {
        "name": "Richmond Housing Authority",
        "email": "intake@richmondhousing.org",
        "description": "Public housing and homelessness programs",
        "phone": "(804) 646-2950",
    },
    "crossover": {
        "name": "CrossOver Healthcare Collective",
        "email": "info@crossoverhealthcare.org",
        "description": "Primary and preventive care for uninsured",
        "phone": "(804) 819-4700",
    },
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for handoff operations.
    Routes based on HTTP method and path.
    """
    try:
        http_method = event.get("httpMethod", "POST")
        path = event.get("path", "/handoff")

        if path == "/handoff" and http_method == "POST":
            return handle_create_handoff(event)

        if path.startswith("/handoff/") and http_method == "GET":
            handoff_id = path.split("/")[-1]
            return handle_get_handoff(handoff_id)

        if path == "/handoff/organizations" and http_method == "GET":
            return handle_get_organizations()

        return error_response("Endpoint not found", 404)

    except Exception as e:
        print(f"Error in handoff handler: {str(e)}")
        return error_response(str(e), 500)


def handle_create_handoff(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /handoff
    Create a new handoff request to a nonprofit organization.
    """
    try:
        # Parse input
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        session_id = body.get("sessionId", "").strip()
        target_org = body.get("targetOrg", "").lower().strip()
        target_contact = body.get("targetContact", "").strip()
        notes = body.get("notes", "").strip()

        # Validation
        if not session_id:
            return error_response("sessionId is required", 400)

        if not target_org:
            return error_response("targetOrg is required", 400)

        if target_org not in NONPROFIT_ORGS:
            return error_response(
                f"Unknown organization: {target_org}. Valid options: {', '.join(NONPROFIT_ORGS.keys())}",
                400,
            )

        org_info = NONPROFIT_ORGS[target_org]

        # Record handoff in DynamoDB
        handoff_id = f"hoff_{session_id}_{int(datetime.utcnow().timestamp())}"
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        table = dynamodb.Table(SESSIONS_TABLE)

        # Update session with handoff info
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #status = :status, handoffTarget = :target, handoffTime = :time, handoffId = :id, handoffNotes = :notes, handoffContact = :contact",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "handed_off",
                ":target": org_info["name"],
                ":time": timestamp,
                ":id": handoff_id,
                ":notes": notes,
                ":contact": target_contact,
            },
        )

        # Send notification email to nonprofit
        send_handoff_notification(session_id, org_info, notes, target_contact)

        return success_response({
            "handoffId": handoff_id,
            "sessionId": session_id,
            "targetOrganization": org_info["name"],
            "status": "handed_off",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Session handed off to {org_info['name']}. Notification email sent.",
        })

    except Exception as e:
        print(f"Error in handle_create_handoff: {str(e)}")
        return error_response(str(e), 500)


def handle_get_handoff(handoff_id: str) -> Dict[str, Any]:
    """
    GET /handoff/{id}
    Retrieve handoff details (includes associated session info).
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)

        # Query for session with this handoff ID
        response = table.scan(
            FilterExpression="handoffId = :hid",
            ExpressionAttributeValues={":hid": handoff_id},
        )

        if not response.get("Items"):
            return error_response("Handoff not found", 404)

        item = response["Items"][0]

        return success_response({
            "handoffId": handoff_id,
            "sessionId": item.get("sessionId"),
            "targetOrganization": item.get("handoffTarget"),
            "handoffTime": item.get("handoffTime"),
            "notes": item.get("handoffNotes", ""),
            "contact": item.get("handoffContact", ""),
            "status": item.get("status"),
        })

    except Exception as e:
        print(f"Error in handle_get_handoff: {str(e)}")
        return error_response(str(e), 500)


def handle_get_organizations() -> Dict[str, Any]:
    """
    GET /handoff/organizations
    List all available nonprofit organizations for handoff.
    """
    try:
        organizations = []

        for org_id, org_info in NONPROFIT_ORGS.items():
            organizations.append({
                "id": org_id,
                "name": org_info["name"],
                "email": org_info["email"],
                "phone": org_info["phone"],
                "description": org_info["description"],
            })

        return success_response({
            "organizations": organizations,
            "total": len(organizations),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        print(f"Error in handle_get_organizations: {str(e)}")
        return error_response(str(e), 500)


def send_handoff_notification(
    session_id: str, org_info: Dict[str, str], notes: str, contact_name: str
) -> None:
    """
    Send handoff notification email to nonprofit organization.
    """
    try:
        # Retrieve session data for context
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id})
        session_data = response.get("Item", {})

        # Build email subject and body
        subject = f"New Handoff Request: Richmond 311 Session {session_id[:8]}"

        category = session_data.get("category", "General")
        language = session_data.get("language", "English")
        message_count = session_data.get("messageCount", 0)
        created_at = session_data.get("createdAt", "")

        # Format timestamp
        if created_at and isinstance(created_at, int):
            dt = datetime.fromtimestamp(created_at / 1000)
            created_at_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            created_at_str = str(created_at)

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f9f9f9;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: #001a4d;
                    color: white;
                    padding: 20px;
                    border-radius: 4px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .details {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }}
                .label {{
                    font-weight: 600;
                    color: #001a4d;
                }}
                .notes {{
                    background: #e8f4f8;
                    padding: 15px;
                    border-left: 4px solid #001a4d;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .action {{
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Handoff Request</h1>
                    <p>Richmond City 311 Service</p>
                </div>

                <p>Dear {escape_html(org_info['name'])} Team,</p>

                <p>A Richmond 311 session has been handed off to your organization. Below are the session details:</p>

                <div class="details">
                    <div class="detail-row">
                        <span class="label">Session ID:</span>
                        <span>{session_id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Category:</span>
                        <span>{escape_html(category)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Language:</span>
                        <span>{language}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Started:</span>
                        <span>{created_at_str}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Interactions:</span>
                        <span>{message_count}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Contact Name:</span>
                        <span>{escape_html(contact_name) if contact_name else 'Not provided'}</span>
                    </div>
                </div>

                {f'<div class="notes"><strong>Handoff Notes:</strong><br/>{escape_html(notes)}</div>' if notes else ''}

                <div class="action">
                    <p style="margin: 0;">
                        <strong>Next Steps:</strong> The full conversation transcript will be sent separately.
                        Please review the session details and reach out to the caller if appropriate.
                    </p>
                </div>

                <p>If you have any questions about this handoff, please contact the Richmond City 311 Service.</p>

                <div class="footer">
                    <p>This is an automated notification from Richmond City 311.</p>
                    <p>For support: <a href="mailto:support@richmond311.com">support@richmond311.com</a></p>
                    <p>Visit: <a href="https://richmond.gov">richmond.gov</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Richmond 311 - Handoff Notification

Session Details:
- Session ID: {session_id}
- Category: {category}
- Language: {language}
- Started: {created_at_str}
- Total Interactions: {message_count}
- Contact: {contact_name if contact_name else 'Not provided'}

Handoff Notes:
{notes if notes else 'None provided'}

Next Steps:
Please review the session details and reach out to the caller if appropriate.
The full conversation transcript will be sent separately.

For support: support@richmond311.com
Visit: richmond.gov
"""

        # Send email via SES
        ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                "ToAddresses": [org_info["email"]],
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
                    "Text": {
                        "Data": text_body,
                        "Charset": "UTF-8",
                    },
                },
            },
        )

        print(f"Handoff notification sent to {org_info['name']} ({org_info['email']})")

    except Exception as e:
        print(f"Error sending handoff notification: {str(e)}")
        raise


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
