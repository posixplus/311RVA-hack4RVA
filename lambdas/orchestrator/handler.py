import json
import os
import boto3
import uuid
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
SESSIONS_TABLE = os.environ["SESSIONS_TABLE"]
LOGS_BUCKET = os.environ["LOGS_BUCKET"]
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")
REGION = os.environ.get("REGION", "us-east-1")
EMAIL_LAMBDA_ARN = os.environ.get("EMAIL_LAMBDA_ARN", "")

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")
sessions_table = dynamodb.Table(SESSIONS_TABLE)

SYSTEM_PROMPT = """You are a helpful, compassionate assistant for Richmond City, Virginia.
Your role is to help residents find city services, non-profit resources, and community support.
You have access to Richmond City municipal guides and resource manuals.

Guidelines:
- Be warm, clear, and concise (responses should be 2-4 sentences for voice, up to 8 for web)
- Focus on actionable information: addresses, phone numbers, hours, eligibility
- If you don't have specific info, direct them to call 311 or visit richmond.gov
- Always maintain caller privacy - never repeat back sensitive info like SSNs
- For emergencies: direct to 911
- Available resources: housing assistance, food banks, healthcare, legal aid, utility assistance, job training, mental health services

Channel: {channel}
"""

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json"
}


def retrieve_and_respond(user_input, session_id, channel, contact_id=None):
    """
    Retrieve context from knowledge base and generate response.
    Falls back to direct Bedrock invoke if RAG fails.

    Returns: (response_text, sources_list)
    """
    sources = []
    response_text = None

    try:
        # Try RAG with Bedrock Agent
        logger.info(f"Attempting RAG retrieve for session {session_id}")

        rag_result = bedrock_agent.retrieve_and_generate(
            input={"text": user_input},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{BEDROCK_MODEL_ID}",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 3
                        }
                    },
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": SYSTEM_PROMPT.format(channel=channel) + "\n\nContext: $search_results$\n\nUser: " + user_input + "\n\nAssistant:"
                        }
                    }
                }
            }
        )

        response_text = rag_result["output"]["text"]

        # Extract citations/sources
        if "citations" in rag_result:
            for citation in rag_result.get("citations", []):
                if "location" in citation:
                    sources.append(citation["location"].get("s3Location", {}).get("uri", ""))

        logger.info(f"RAG succeeded. Sources: {len(sources)}")

    except Exception as e:
        logger.warning(f"RAG failed, falling back to direct invoke: {str(e)}")

        # Fall back to direct Bedrock invoke
        try:
            messages = [
                {
                    "role": "user",
                    "content": user_input
                }
            ]

            system = SYSTEM_PROMPT.format(channel=channel)

            invoke_result = bedrock_runtime.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                system=system,
                messages=messages
            )

            response_body = json.loads(invoke_result["body"].read().decode("utf-8"))
            response_text = response_body["content"][0]["text"]
            logger.info("Direct invoke succeeded (fallback)")

        except Exception as fallback_error:
            logger.error(f"Direct invoke also failed: {str(fallback_error)}")
            response_text = "I apologize, I'm having trouble processing your request right now. Please try again in a moment, or call Richmond City 311 for immediate assistance."

    return response_text, sources


def get_or_create_session(session_id=None):
    """Get or create a session ID"""
    if session_id:
        return session_id
    return str(uuid.uuid4())


def save_session(session_id, user_input, response_text, channel, contact_id=None):
    """Save conversation turn to DynamoDB"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl = int(time.time()) + (86400 * 7)  # 7-day retention

        sessions_table.put_item(
            Item={
                "session_id": session_id,
                "timestamp": timestamp,
                "user_input": user_input,
                "response": response_text,
                "channel": channel,
                "contact_id": contact_id or "N/A",
                "ttl": ttl
            }
        )
        logger.info(f"Saved session turn for {session_id}")
    except Exception as e:
        logger.error(f"Failed to save session: {str(e)}")


def get_session_history(session_id):
    """Retrieve full session history from DynamoDB"""
    try:
        response = sessions_table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id},
            ScanIndexForward=True  # chronological order
        )
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"Failed to retrieve session history: {str(e)}")
        return []


def trigger_email_summary(session_id, contact_id, channel):
    """Trigger email summary Lambda asynchronously"""
    if not EMAIL_LAMBDA_ARN:
        logger.warning("EMAIL_LAMBDA_ARN not configured, skipping email summary")
        return

    try:
        history = get_session_history(session_id)

        if not history:
            logger.warning(f"No history found for session {session_id}")
            return

        # Convert DynamoDB items to conversation format
        conversation = []
        for item in history:
            conversation.append({
                "role": "user",
                "text": item.get("user_input", ""),
                "timestamp": item.get("timestamp", "")
            })
            conversation.append({
                "role": "assistant",
                "text": item.get("response", ""),
                "timestamp": item.get("timestamp", "")
            })

        payload = {
            "session_id": session_id,
            "contact_id": contact_id,
            "channel": channel,
            "conversation": conversation,
            "caller_info": {
                "phone_last4": contact_id[-4:] if contact_id and len(contact_id) >= 4 else "****"
            }
        }

        lambda_client.invoke(
            FunctionName=EMAIL_LAMBDA_ARN,
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        logger.info(f"Triggered email summary for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to trigger email summary: {str(e)}")


def lambda_handler(event, context):
    """
    Main handler for both Amazon Connect IVR and web API Gateway requests.
    """
    try:
        channel = None
        user_input = None
        session_id = None
        contact_id = None
        is_disconnect = False

        # Detect Amazon Connect IVR
        if "Details" in event:
            logger.info("Detected Amazon Connect IVR request")
            channel = "ivr"

            details = event["Details"]
            parameters = details.get("Parameters", {})
            contact_data = details.get("ContactData", {})

            user_input = parameters.get("userInput", "").strip()
            contact_id = contact_data.get("ContactId", "")

            # Check for disconnect trigger
            is_disconnect = parameters.get("disconnect", False) or parameters.get("callDisconnected", False)

            # Get or create session from contact ID
            session_id = parameters.get("sessionId")
            if not session_id:
                session_id = get_or_create_session()

            logger.info(f"Connect call: contact_id={contact_id}, session_id={session_id}, disconnect={is_disconnect}")

        # Detect web API Gateway
        elif "body" in event:
            logger.info("Detected web API Gateway request")
            channel = "web"

            try:
                body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "Invalid JSON in request body"})
                }

            user_input = body.get("message", "").strip()
            session_id = body.get("sessionId")
            session_id = get_or_create_session(session_id)

            logger.info(f"Web request: session_id={session_id}")

        else:
            logger.error("Unable to determine request type")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Invalid request format"})
            }

        # Validate input
        if not user_input:
            error_msg = "No user input provided"
            logger.warning(error_msg)
            if channel == "web":
                return {
                    "statusCode": 400,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": error_msg})
                }
            else:
                return {
                    "response": error_msg,
                    "sessionId": session_id
                }

        # Get response
        response_text, sources = retrieve_and_respond(user_input, session_id, channel, contact_id)

        # Save to session log
        save_session(session_id, user_input, response_text, channel, contact_id)

        # Handle disconnect for IVR
        if is_disconnect and channel == "ivr":
            trigger_email_summary(session_id, contact_id, channel)

        # Return appropriate format
        if channel == "ivr":
            return {
                "response": response_text,
                "sessionId": session_id
            }
        else:  # web
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "response": response_text,
                    "sessionId": session_id,
                    "sources": [s for s in sources if s]
                })
            }

    except Exception as e:
        logger.error(f"Unhandled exception in lambda_handler: {str(e)}", exc_info=True)

        error_response = "I encountered an error processing your request. Please try again."

        if channel == "web":
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": error_response})
            }
        else:
            return {
                "response": error_response,
                "sessionId": session_id or "unknown"
            }
