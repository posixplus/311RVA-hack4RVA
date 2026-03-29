import json
import os
import boto3
import logging
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@richmond-resources.org")
NONPROFIT_EMAILS = os.environ.get("NONPROFIT_EMAILS", "").split(",")
LOGS_BUCKET = os.environ.get("LOGS_BUCKET", "")

ses_client = boto3.client("ses")
s3_client = boto3.client("s3")


def extract_resources(response_text):
    """
    Parse assistant responses to extract resources, phone numbers, addresses.
    Returns a list of resource references found.
    """
    resources = []

    # Simple phone number pattern
    phone_pattern = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phones = re.findall(phone_pattern, response_text)
    for phone in phones:
        resources.append(f"Phone: {phone}")

    # Simple address pattern (contains numbers and common street types)
    address_pattern = r'\d+\s+[A-Z][a-z]+\s+(Street|Street|Ave|Avenue|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Circle|Ct)'
    addresses = re.findall(address_pattern, response_text)
    for address in addresses:
        if address not in resources:
            resources.append(f"Address: {address}")

    # Richmond.gov reference
    if "richmond.gov" in response_text.lower():
        resources.append("Reference: richmond.gov")

    # 311 reference
    if "311" in response_text:
        resources.append("Reference: Richmond 311")

    return resources


def build_html_email(session_id, channel, conversation, caller_info):
    """Build HTML email content"""
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    resources = []
    for msg in conversation:
        if msg.get("role") == "assistant":
            resources.extend(extract_resources(msg.get("text", "")))

    # Remove duplicates while preserving order
    seen = set()
    unique_resources = []
    for r in resources:
        if r not in seen:
            seen.add(r)
            unique_resources.append(r)

    phone_last4 = caller_info.get("phone_last4", "****") if caller_info else "****"

    resources_html = ""
    if unique_resources:
        resources_html = "<h3>Resources Mentioned:</h3><ul>"
        for resource in unique_resources:
            resources_html += f"<li>{resource}</li>"
        resources_html += "</ul>"

    conversation_html = "<h3>Conversation Transcript:</h3><div style='background-color: #f5f5f5; padding: 15px; border-radius: 5px;'>"
    for msg in conversation:
        role = msg.get("role", "unknown").upper()
        text = msg.get("text", "").replace("\n", "<br>")
        timestamp = msg.get("timestamp", "")

        if role == "USER":
            conversation_html += f"<p><strong>Caller:</strong> {text}</p>"
        else:
            conversation_html += f"<p><strong>Assistant:</strong> {text}</p>"

    conversation_html += "</div>"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 20px 0; }}
            .summary {{ background-color: #e8f1f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .footer {{ color: #777; font-size: 12px; text-align: center; margin-top: 30px; }}
            h3 {{ color: #1e3a8a; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Richmond City Resource Assistant</h1>
                <p>Call Summary</p>
            </div>

            <div class="content">
                <div class="summary">
                    <p><strong>Date:</strong> {date_str}</p>
                    <p><strong>Time:</strong> {time_str}</p>
                    <p><strong>Channel:</strong> {channel.upper()}</p>
                    <p><strong>Session ID:</strong> {session_id}</p>
                    <p><strong>Caller:</strong> ...{phone_last4}</p>
                </div>

                {conversation_html}

                {resources_html}

                <div class="footer">
                    <p>This summary was auto-generated to help connect residents with local resources.</p>
                    <p>Richmond City 311 | www.richmond.gov</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def send_email(recipient, subject, html_content):
    """Send email via SES"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient

        part = MIMEText(html_content, 'html')
        msg.attach(part)

        response = ses_client.send_raw_email(
            Source=SENDER_EMAIL,
            Destinations=[recipient],
            RawMessage={'Data': msg.as_string()}
        )
        logger.info(f"Email sent to {recipient}, MessageId: {response.get('MessageId')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return False


def save_to_s3(session_id, html_content):
    """Save summary to S3"""
    try:
        now = datetime.now()
        date_path = now.strftime("%Y-%m-%d")
        key = f"summaries/{date_path}/{session_id}.html"

        s3_client.put_object(
            Bucket=LOGS_BUCKET,
            Key=key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html'
        )
        logger.info(f"Summary saved to S3: s3://{LOGS_BUCKET}/{key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save summary to S3: {str(e)}")
        return False


def lambda_handler(event, context):
    """
    Email summary Lambda handler.
    Receives session data and sends structured call summaries to non-profit partners.
    """
    try:
        session_id = event.get("session_id", "unknown")
        contact_id = event.get("contact_id", "")
        channel = event.get("channel", "web")
        conversation = event.get("conversation", [])
        caller_info = event.get("caller_info", {})

        logger.info(f"Processing email summary for session {session_id}, channel {channel}")

        if not conversation:
            logger.warning(f"No conversation data for session {session_id}")
            return {
                "success": False,
                "error": "No conversation data"
            }

        # Build HTML content
        html_content = build_html_email(session_id, channel, conversation, caller_info)

        # Save to S3
        if LOGS_BUCKET:
            save_to_s3(session_id, html_content)

        # Send emails to nonprofit partners
        emails_sent = 0
        subject = f"Richmond City Resource Assistant - Call Summary [{datetime.now().strftime('%m/%d/%Y')}]"

        for recipient in NONPROFIT_EMAILS:
            recipient = recipient.strip()
            if recipient and "@" in recipient:
                if send_email(recipient, subject, html_content):
                    emails_sent += 1

        logger.info(f"Email summary complete: {emails_sent} emails sent")

        return {
            "success": True,
            "emails_sent": emails_sent,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Unhandled exception in email_summary handler: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
