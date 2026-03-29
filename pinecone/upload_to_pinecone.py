import json
import boto3
import os
import base64
from urllib.parse import parse_qs
import logging
from pinecone import Pinecone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Initialize Clients ---
bedrock_runtime = boto3.client('bedrock-runtime')

# Initialize Pinecone
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME')
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0" 
CLAUDE_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'

def get_embedding(text):
    """Turns the caller's spoken words into a vector using Titan."""
    body = json.dumps({"inputText": text, "dimensions": 1536, "normalize": True})
    response = bedrock_runtime.invoke_model(
        body=body, modelId=EMBEDDING_MODEL_ID, accept='application/json', contentType='application/json'
    )
    return json.loads(response.get('body').read()).get('embedding')

def lambda_handler(event, context):
    # Parse Twilio's incoming form data
    body = event.get('body', '')
    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body).decode('utf-8')
    parsed_body = parse_qs(body)
    
    speech_result = parsed_body.get('SpeechResult', [None])[0]

    # Start of call greeting
    if not speech_result:
        return generate_twiml("Welcome to the Richmond 3 1 1 after-hours assistant. How can I help you?")

    logger.info(f"User Speech: {speech_result}")

    try:
        # 1. Embed the user's question
        query_vector = get_embedding(speech_result)
        
        # 2. Search Pinecone for the top 3 most relevant document chunks
        search_results = index.query(
            vector=query_vector,
            top_k=3,
            include_metadata=True
        )
        
        # 3. Extract the text from those chunks to build our context
        retrieved_context = ""
        for match in search_results['matches']:
            retrieved_context += match['metadata']['text'] + "\n\n"

        # 4. Ask Claude to answer the question using ONLY the retrieved context
        system_prompt = (
            "You are a Helpful Richmond Municipal Assistant answering an after-hours 311 call. "
            "Provide clear, concise, and empathetic answers based ONLY on the <context> provided. "
            "If the answer is not in the context, say you don't know. "
            "Keep your answers short, as they will be read aloud over the phone. "
            "Under no circumstances should you ask for personal identifiers like names or addresses."
        )
        
        user_prompt = f"<context>\n{retrieved_context}\n</context>\n\nCaller Question: {speech_result}"

        # 5. Call Claude 3 Haiku via Messages API
        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
                "temperature": 0.1
            })
        )
        
        response_body = json.loads(response.get('body').read())
        generated_answer = response_body['content'][0]['text']
        
        return generate_twiml(generated_answer)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return generate_twiml("I am having trouble accessing the city manuals right now. Please try again.")

def generate_twiml(message):
    """Formats the response so Twilio reads it aloud and waits for the user to reply."""
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather input="speech" action="" timeout="3" speechTimeout="auto" language="en-US">
            <Say voice="Polly.Joanna-Neural">{message}</Say>
        </Gather>
    </Response>"""
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/xml"},
        "body": twiml
    }