import logging
import json
from flask import Blueprint, request, jsonify, current_app
from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Create webhook blueprint
webhook_blueprint = Blueprint("webhook", __name__)

def handle_message():
    """
    Handle incoming WhatsApp webhook events
    
    :return: JSON response and HTTP status code
    """
    body = request.get_json()
    logging.info(f"Received request body: {body}")

    # Check for WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

def verify():
    """
    Verify webhook configuration
    
    :return: Verification challenge or error response
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

# Webhook routes
@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()