"""
Orchestrator Lambda - Main conversational handler
Routes user input through Bedrock KB retrieval and Claude Haiku for response generation
Manages conversation history, session lifecycle, and handoffs to nonprofits
"""

import json
import os
import boto3
import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

bedrock_client = boto3.client("bedrock-runtime")
bedrock_agent_client = boto3.client("bedrock-agent-runtime")
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
lambda_client = boto3.client("lambda")
comprehend_client = boto3.client("comprehend")

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID")
SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE")
LOGS_BUCKET = os.environ.get("LOGS_BUCKET")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
REGION = os.environ.get("REGION", "us-east-1")
EMAIL_LAMBDA_ARN = os.environ.get("EMAIL_LAMBDA_ARN")
REDACTION_LAMBDA_ARN = os.environ.get("REDACTION_LAMBDA_ARN")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "richmond311admin")

PRIVACY_NOTICE = """This is a private service request and will not be posted publicly. It is not mandatory but you can create an account or sign in with your existing account, both of which can be done by continuing on with your request. If you do not sign in, you will only receive email notifications for changes in request status. There will be no PII collected."""

NONPROFIT_ORGS = {
    "irc": {"name": "IRC Richmond", "contact": "info@ircrichmond.org"},
    "reestablish": {"name": "ReEstablish Richmond", "contact": "contact@reestablishrichmond.org"},
    "sacred_heart": {"name": "Sacred Heart Center", "contact": "info@sacredheartcenter.org"},
    "afghan": {"name": "Afghan Association of Virginia", "contact": "info@afghansassociation.org"},
    "legal_aid": {"name": "Central Virginia Legal Aid", "contact": "info@cvlegalaid.org"},
    "bha": {"name": "Richmond BHA", "contact": "info@richmondoha.org"},
    "crossover": {"name": "CrossOver Healthcare", "contact": "info@crossoverhealthcare.org"},
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for orchestrator Lambda.
    Routes requests based on HTTP method and path.
    """
    try:
        http_method = event.get("httpMethod", "POST")
        path = event.get("path", "/chat")

        # Health check
        if path == "/health" and http_method == "GET":
            return success_response({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

        # GET /sessions - dashboard view of all sessions (redacted)
        if path == "/sessions" and http_method == "GET":
            return handle_get_sessions(event)

        # GET /sessions/{id} - admin view of specific session
        if path.startswith("/sessions/") and http_method == "GET" and not path.endswith("/handoff"):
            session_id = path.split("/")[-1]
            return handle_get_session(event, session_id)

        # POST /sessions/{id}/handoff - handoff to nonprofit
        if path.endswith("/handoff") and http_method == "POST":
            session_id = path.split("/")[-2]
            return handle_handoff(event, session_id)

        # POST /chat - main conversation handler
        if path == "/chat" and http_method == "POST":
            return handle_chat(event)

        return error_response("Endpoint not found", 404)

    except Exception as e:
        print(f"Error in orchestrator: {str(e)}")
        return error_response(str(e), 500)


def handle_chat(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle chat messages with action routing.
    """
    try:
        # Parse input
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        message = body.get("message", "").strip()
        session_id = body.get("sessionId") or str(uuid.uuid4())
        language = body.get("language", "en")
        category = body.get("category", "general")
        action = body.get("action", "chat")

        if not message:
            return error_response("No message provided", 400)

        # Route based on action
        if action == "end_conversation":
            return handle_end_conversation(session_id)
        elif action == "deliver_summary":
            return handle_deliver_summary(session_id, body)
        elif action == "handoff":
            return handle_handoff_request(session_id, body)
        else:  # Default: chat action
            history = body.get("history", [])
            return handle_message(session_id, message, language, category, history)

    except Exception as e:
        print(f"Error in handle_chat: {str(e)}")
        return error_response(str(e), 500)


def handle_message(
    session_id: str, message: str, language: str, category: str, history: list = None
) -> Dict[str, Any]:
    """
    Process a chat message: retrieve KB context, generate response, store history.
    """
    try:
        # Initialize session if needed
        init_session(session_id, language, category)

        # Retrieve context from knowledge base
        retrieval_results = retrieve_from_kb(message)
        sources = retrieval_results.get("sources", [])

        # Generate response with Claude Haiku 4.5, passing conversation history
        response_text = generate_response(message, retrieval_results, session_id, history or [])

        # Redact PII from message and response before storage
        redacted_message = redact_pii_sync(message)
        redacted_response = redact_pii_sync(response_text)

        # Store conversation to DynamoDB
        store_conversation_history(session_id, message, response_text)

        # Store conversation to S3 with redaction
        store_log_to_s3(session_id, redacted_message, redacted_response, sources)

        # Update session metadata
        update_session_metadata(session_id, category)

        return success_response(
            {
                "response": response_text,
                "sessionId": session_id,
                "sources": sources,
                "status": "active",
                "messageCount": get_message_count(session_id),
                "privacyNotice": PRIVACY_NOTICE,
            }
        )

    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        return error_response(str(e), 500)


def handle_end_conversation(session_id: str) -> Dict[str, Any]:
    """
    Mark a conversation as complete and trigger email summary.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)

        # Update session status to completed
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET #status = :status, completedAt = :timestamp",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "completed",
                ":timestamp": int(datetime.utcnow().timestamp() * 1000),
            },
        )

        # Trigger email summary asynchronously
        if EMAIL_LAMBDA_ARN:
            trigger_email_lambda(session_id)

        # Log the action
        store_log_to_s3(session_id, "[SYSTEM]", "Conversation ended by user", [])

        return success_response(
            {
                "sessionId": session_id,
                "status": "completed",
                "message": "Conversation ended. A summary will be sent to your email.",
            }
        )

    except Exception as e:
        print(f"Error in handle_end_conversation: {str(e)}")
        return error_response(str(e), 500)


def handle_deliver_summary(session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deliver conversation summary to email or phone.
    """
    try:
        delivery_method = body.get("deliveryMethod", "email")
        delivery_address = body.get("deliveryAddress", "").strip()
        is_nonprofit = body.get("isNonprofit", False)

        if not delivery_address:
            return error_response("No delivery address provided", 400)

        # Validate email or phone format
        if delivery_method == "email" and not validate_email(delivery_address):
            return error_response("Invalid email address", 400)
        elif delivery_method == "sms" and not validate_phone(delivery_address):
            return error_response("Invalid phone number", 400)

        # Trigger email lambda
        payload = {
            "sessionId": session_id,
            "deliveryMethod": delivery_method,
            "deliveryAddress": delivery_address,
            "isNonprofit": is_nonprofit,
        }

        lambda_client.invoke(
            FunctionName=EMAIL_LAMBDA_ARN,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Update session with delivery info
        table = dynamodb.Table(SESSIONS_TABLE)
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET deliveryMethod = :method, deliveryAddress = :address",
            ExpressionAttributeValues={
                ":method": delivery_method,
                ":address": delivery_address,
            },
        )

        return success_response(
            {
                "sessionId": session_id,
                "deliveryMethod": delivery_method,
                "message": f"Summary will be delivered to {delivery_address}",
            }
        )

    except Exception as e:
        print(f"Error in handle_deliver_summary: {str(e)}")
        return error_response(str(e), 500)


def handle_handoff_request(session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle handoff request to a nonprofit organization.
    """
    try:
        target_org = body.get("targetOrg", "").lower()
        target_contact = body.get("targetContact", "")
        notes = body.get("notes", "")

        if target_org not in NONPROFIT_ORGS:
            return error_response(f"Unknown organization: {target_org}", 400)

        org_info = NONPROFIT_ORGS[target_org]

        # Record handoff in DynamoDB
        table = dynamodb.Table(SESSIONS_TABLE)
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET #status = :status, handoffTarget = :target, handoffTime = :time, handoffNotes = :notes",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "handed_off",
                ":target": org_info["name"],
                ":time": int(datetime.utcnow().timestamp() * 1000),
                ":notes": notes,
            },
        )

        # Store handoff event to S3
        store_log_to_s3(
            session_id,
            "[SYSTEM]",
            f"Handoff initiated to {org_info['name']}",
            [],
        )

        return success_response(
            {
                "sessionId": session_id,
                "status": "handed_off",
                "handoffTarget": org_info["name"],
                "message": f"Session handed off to {org_info['name']}",
            }
        )

    except Exception as e:
        print(f"Error in handle_handoff_request: {str(e)}")
        return error_response(str(e), 500)


def handle_get_sessions(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /sessions - Return all sessions with PII redacted for dashboard.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.scan()

        sessions = []
        for item in response.get("Items", []):
            session = {
                "sessionId": item.get("sessionId"),
                "category": item.get("category", "general"),
                "language": item.get("language", "en"),
                "startTime": item.get("createdAt"),
                "status": item.get("status", "active"),
                "messageCount": item.get("messageCount", 0),
            }

            # Include summary if available (will be redacted client-side if needed)
            if "summary" in item:
                session["summary_redacted"] = redact_pii_sync(item["summary"])

            sessions.append(session)

        return success_response(
            {
                "sessions": sessions,
                "total": len(sessions),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        print(f"Error in handle_get_sessions: {str(e)}")
        return error_response(str(e), 500)


def handle_get_session(event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    GET /sessions/{id} - Return full session detail (admin only if unredacted).
    """
    try:
        # Check admin key
        headers = event.get("headers", {})
        admin_key = headers.get("x-admin-key") or headers.get("X-Admin-Key")
        is_admin = admin_key == ADMIN_KEY

        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id, "timestamp": 0})

        if "Item" not in response:
            return error_response("Session not found", 404)

        item = response["Item"]

        # Redact if not admin
        if not is_admin:
            item["conversation"] = [
                {
                    "message": redact_pii_sync(msg.get("message", "")),
                    "response": redact_pii_sync(msg.get("response", "")),
                    "timestamp": msg.get("timestamp"),
                }
                for msg in item.get("conversation", [])
            ]

        return success_response(item)

    except Exception as e:
        print(f"Error in handle_get_session: {str(e)}")
        return error_response(str(e), 500)


def handle_handoff(event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    POST /sessions/{id}/handoff - Perform handoff to nonprofit.
    """
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        target_org = body.get("targetOrg", "").lower()
        notes = body.get("notes", "")

        if target_org not in NONPROFIT_ORGS:
            return error_response(f"Unknown organization: {target_org}", 400)

        org_info = NONPROFIT_ORGS[target_org]

        # Record handoff
        table = dynamodb.Table(SESSIONS_TABLE)
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET #status = :status, handoffTarget = :target, handoffTime = :time",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "handed_off",
                ":target": org_info["name"],
                ":time": int(datetime.utcnow().timestamp() * 1000),
            },
        )

        return success_response(
            {
                "sessionId": session_id,
                "status": "handed_off",
                "handoffTarget": org_info["name"],
            }
        )

    except Exception as e:
        print(f"Error in handle_handoff: {str(e)}")
        return error_response(str(e), 500)


def init_session(session_id: str, language: str, category: str) -> None:
    """
    Initialize a new session in DynamoDB if it doesn't exist.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        # Use update to only create if doesn't exist
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET createdAt = if_not_exists(createdAt, :ts), #status = if_not_exists(#status, :active), #language = if_not_exists(#language, :lang), category = if_not_exists(category, :cat), conversation = if_not_exists(conversation, :conv), messageCount = if_not_exists(messageCount, :zero), #ttl = :ttl",
            ExpressionAttributeNames={
                "#status": "status",
                "#language": "language",
                "#ttl": "ttl",
            },
            ExpressionAttributeValues={
                ":ts": timestamp,
                ":active": "active",
                ":lang": language,
                ":cat": category,
                ":conv": [],
                ":zero": 0,
                ":ttl": int(datetime.utcnow().timestamp()) + (7 * 24 * 3600),  # 7 days
            },
        )
    except Exception as e:
        print(f"Error initializing session: {str(e)}")


def retrieve_from_kb(query: str) -> Dict[str, Any]:
    """
    Retrieve relevant documents from Bedrock Knowledge Base using RetrieveAndGenerate.
    Returns context and source information.
    """
    try:
        response = bedrock_agent_client.retrieve_and_generate(
            input={
                "text": query,
            },
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": f"arn:aws:bedrock:{BEDROCK_REGION}:099407892939:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
                },
            },
        )

        # Extract retrieved documents with sources
        sources = []
        context_parts = []

        if "sessionId" in response:
            # Get citations and context from the response
            citations = response.get("citations", [])

            for citation in citations:
                source = {
                    "title": citation.get("generatedResponsePart", {}).get("textResponsePart", {}).get("text", "Knowledge Base"),
                    "excerpt": citation.get("retrievedReferences", [{}])[0].get("content", {}).get("text", "")[:200],
                }
                if source["excerpt"]:
                    sources.append(source)
                    context_parts.append(source["excerpt"])

        context_str = "\n".join(context_parts) if context_parts else ""

        return {
            "context": context_str,
            "sources": sources,
        }
    except Exception as e:
        print(f"KB Retrieval error: {str(e)}")
        return {"context": "", "sources": []}


def generate_response(
    user_input: str, retrieval_results: Dict[str, Any], session_id: str, history: list = None
) -> str:
    """
    Generate response using Claude Haiku 4.5 with retrieved context and conversation history.
    Includes privacy notice and source citations.
    """
    try:
        context = retrieval_results.get("context", "")
        sources = retrieval_results.get("sources", [])

        # Build system prompt
        system_prompt = f"""You are a compassionate Richmond City 24/7 Resource Assistant.
You help connect citizens with food assistance, housing support, healthcare resources, and other critical services.

IMPORTANT: You MUST only use the knowledge base context provided. Do not make up resources or information.
Be empathetic, clear, and actionable in your responses.
When providing information, cite the document sources.
If you don't know something or the knowledge base doesn't cover it, be honest and suggest contacting local non-profit organizations.

Privacy Notice:
{PRIVACY_NOTICE}

Focus on:
- Understanding the caller's immediate needs
- Providing actionable next steps
- Connecting them with verified local resources
- Being respectful of their situation
- Maintaining context from the conversation history"""

        # Build user message with context
        source_citations = ""
        if sources:
            source_citations = "\n\nSource Information:\n"
            for i, source in enumerate(sources, 1):
                source_citations += f"{i}. {source['title']}: {source['excerpt']}\n"

        user_message = f"""Context from knowledge base:
{context}
{source_citations}

User question: {user_input}

Provide a helpful, compassionate, and concise response (2-3 sentences max).
If you cite information, reference the source number."""

        # Build messages array with conversation history for context
        messages = []
        if history:
            for msg in history[-8:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({
                        "role": role,
                        "content": [{"text": content}],
                    })

        # Add current user message
        messages.append({
            "role": "user",
            "content": [{"text": user_message}],
        })

        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 512},
        )

        # Parse response
        response_text = response["output"]["message"]["content"][0]["text"]

        return response_text

    except Exception as e:
        print(f"Response generation error: {str(e)}")
        return "I apologize, I'm having difficulty processing your request. Please try again or contact Richmond Services at 311."


def store_conversation_history(session_id: str, user_message: str, assistant_response: str) -> None:
    """
    Store full conversation history in DynamoDB.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        # Append to conversation array
        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET conversation = list_append(if_not_exists(conversation, :empty), :msg), messageCount = if_not_exists(messageCount, :zero) + :one, lastMessageAt = :ts",
            ExpressionAttributeValues={
                ":empty": [],
                ":msg": [
                    {
                        "timestamp": timestamp,
                        "message": user_message,
                        "response": assistant_response,
                    }
                ],
                ":one": 1,
                ":zero": 0,
                ":ts": timestamp,
            },
        )
    except Exception as e:
        print(f"Error storing conversation history: {str(e)}")


def store_log_to_s3(
    session_id: str, user_message: str, assistant_response: str, sources: List[Dict[str, str]]
) -> None:
    """
    Store conversation log to S3 for analytics and audit trails.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "sessionId": session_id,
            "timestamp": timestamp,
            "userMessage": user_message,
            "assistantResponse": assistant_response,
            "sources": sources,
        }

        key = f"logs/{session_id}/{timestamp.replace(':', '-')}.json"
        s3_client.put_object(
            Bucket=LOGS_BUCKET,
            Key=key,
            Body=json.dumps(log_entry),
            ContentType="application/json",
        )
    except Exception as e:
        print(f"Error storing log to S3: {str(e)}")


def update_session_metadata(session_id: str, category: str) -> None:
    """
    Update session metadata like category and last activity timestamp.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        table.update_item(
            Key={"sessionId": session_id, "timestamp": 0},
            UpdateExpression="SET category = :cat, lastActivityAt = :ts",
            ExpressionAttributeValues={
                ":cat": category,
                ":ts": timestamp,
            },
        )
    except Exception as e:
        print(f"Error updating session metadata: {str(e)}")


def redact_pii_sync(text: str) -> str:
    """
    Synchronously redact PII using AWS Comprehend.
    Falls back to text if Comprehend fails.
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

        # Sort by end offset (descending) to avoid offset issues
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


def trigger_email_lambda(session_id: str) -> None:
    """
    Trigger email summary Lambda asynchronously.
    """
    if not EMAIL_LAMBDA_ARN:
        return

    try:
        lambda_client.invoke(
            FunctionName=EMAIL_LAMBDA_ARN,
            InvocationType="Event",
            Payload=json.dumps({"sessionId": session_id}),
        )
    except Exception as e:
        print(f"Error triggering email lambda: {str(e)}")


def get_message_count(session_id: str) -> int:
    """
    Get the current message count for a session.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={"sessionId": session_id, "timestamp": 0})
        return response.get("Item", {}).get("messageCount", 0)
    except Exception as e:
        print(f"Error getting message count: {str(e)}")
        return 0


def validate_email(email: str) -> bool:
    """
    Simple email validation.
    """
    return "@" in email and "." in email.split("@")[-1]


def validate_phone(phone: str) -> bool:
    """
    Simple phone validation (10+ digits).
    """
    digits = "".join(c for c in phone if c.isdigit())
    return len(digits) >= 10


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
