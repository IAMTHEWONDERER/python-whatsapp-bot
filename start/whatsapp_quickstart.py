import json
from dotenv import load_dotenv
import os
import requests
import aiohttp
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# --------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------
load_dotenv()

# Configuration variables
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION", "v18.0")

# --------------------------------------------------------------
# Synchronous WhatsApp Message Sending Functions
# --------------------------------------------------------------

def get_text_message_input(recipient, text):
    """
    Prepare JSON payload for sending a text message via WhatsApp.
    
    :param recipient: Phone number of the recipient
    :param text: Message body
    :return: JSON-formatted message payload
    """
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    })

def send_whatsapp_message(recipient, text):
    """
    Send a WhatsApp message synchronously.
    
    :param recipient: Phone number of the recipient
    :param text: Message body
    :return: Response from WhatsApp API
    """
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = get_text_message_input(recipient, text)
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        logging.info(f"Message sent successfully to {recipient}")
        logging.info(f"Status: {response.status_code}")
        logging.info(f"Response: {response.json()}")
        
        return response
    except requests.RequestException as e:
        logging.error(f"Error sending message: {e}")
        return None

# --------------------------------------------------------------
# Asynchronous WhatsApp Message Sending Functions
# --------------------------------------------------------------

async def send_whatsapp_message_async(recipient, text):
    """
    Send a WhatsApp message asynchronously.
    
    :param recipient: Phone number of the recipient
    :param text: Message body
    """
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    data = get_text_message_input(recipient, text)
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    logging.info(f"Async message sent successfully to {recipient}")
                    html = await response.text()
                    logging.info(f"Response: {html}")
                else:
                    logging.error(f"Failed to send async message. Status: {response.status}")
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection Error: {e}")

# Example async message sending
async def main():
    recipient = os.getenv("TEST_RECIPIENT")  # Example recipient from .env
    await send_whatsapp_message_async(recipient, "Hello from async WhatsApp!")

if __name__ == "__main__":
    # Uncomment to test async messaging
    asyncio.run(main())
    pass