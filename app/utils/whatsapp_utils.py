import logging
import json
import re
import requests
from flask import current_app, jsonify
from app.services.openai_service import generate_response

def log_http_response(response):
    """
    Log HTTP response details
    
    :param response: HTTP response object
    """
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def get_text_message_input(recipient, text):
    """
    Prepare JSON payload for WhatsApp text message
    
    :param recipient: Recipient's phone number
    :param text: Message text
    :return: JSON-formatted message payload
    """
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    })

def send_message(data):
    """
    Send message via WhatsApp API
    
    :param data: Prepared message data
    :return: HTTP response or error
    """
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        log_http_response(response)
        return response

def process_text_for_whatsapp(text):
    """
    Process text to be WhatsApp-compatible
    
    :param text: Input text
    :return: Formatted WhatsApp text
    """
    # Remove brackets
    text = re.sub(r"\【.*?\】", "", text).strip()

    # Convert double asterisks to single asterisks for WhatsApp formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

    return text

def process_whatsapp_message(body):
    """
    Process incoming WhatsApp message
    
    :param body: Webhook request body
    """
    # Extract sender details
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    # Get the message body
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # Generate AI response
    response = generate_response(message_body, wa_id, name)

    # Format response for WhatsApp
    processed_response = process_text_for_whatsapp(response)

    # Send response back to sender
    data = get_text_message_input(wa_id, processed_response)
    send_message(data)

def is_valid_whatsapp_message(body):
    """
    Validate incoming WhatsApp message structure
    
    :param body: Webhook request body
    :return: Boolean indicating message validity
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )