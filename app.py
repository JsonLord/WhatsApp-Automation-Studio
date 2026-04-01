from flask import Flask, request, jsonify
from flask_cors import CORS
from wa_logic import WhatsAppAutomation
import threading
import time
import requests
import os

app = Flask(__name__)
CORS(app)

# Global automation instance
wa = WhatsAppAutomation()
wa_lock = threading.Lock()

REGISTER_ENDPOINT = "https://auxteam-plandex-backup.hf.space/register"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ready"}), 200

@app.route('/api-docs', methods=['GET'])
def api_docs():
    docs = {
        "endpoints": [
            {
                "path": "/health",
                "method": "GET",
                "purpose": "Returns HTTP 200 when the app is ready."
            },
            {
                "path": "/api-docs",
                "method": "GET",
                "purpose": "Documents all available API endpoints."
            },
            {
                "path": "/login",
                "method": "POST",
                "purpose": "Starts the Selenium browser in headless mode and captures the QR code.",
                "response": {
                    "status": "success/error",
                    "qr_code": "base64_encoded_qr_code (if success)"
                }
            },
            {
                "path": "/check-login",
                "method": "GET",
                "purpose": "Checks if the WhatsApp session is logged in."
            },
            {
                "path": "/send",
                "method": "POST",
                "purpose": "Sends a message to the currently active chat.",
                "request": {
                    "message": "The message text to send"
                }
            }
        ]
    }
    return jsonify(docs), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    global wa
    with wa_lock:
        if wa.driver:
            wa.close()

        success = wa.initialize_driver(headless=True)
        if not success:
            return jsonify({"status": "error", "message": "Failed to initialize driver"}), 500

        wa.navigate_to_whatsapp()
        qr_code = wa.get_qr_code_screenshot()

        if qr_code:
            # Forward QR code to register endpoint
            try:
                requests.post(REGISTER_ENDPOINT, json={"qr_code": qr_code}, timeout=5)
            except Exception as e:
                print(f"Error forwarding QR code: {str(e)}")

            return jsonify({"status": "success", "qr_code": qr_code}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to capture QR code"}), 500

@app.route('/check-login', methods=['GET'])
def check_login():
    global wa
    with wa_lock:
        if not wa.driver:
            return jsonify({"status": "error", "message": "Driver not initialized"}), 400

        logged_in = wa.check_login_status(timeout=5)
        return jsonify({"status": "success", "logged_in": logged_in}), 200

@app.route('/send', methods=['GET', 'POST'])
def send():
    global wa
    if request.method == 'POST':
        data = request.json or {}
        message = data.get('message')
    else:
        message = request.args.get('message')

    if not message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    with wa_lock:
        if not wa.driver:
            return jsonify({"status": "error", "message": "Driver not initialized. Please login first."}), 400

        success = wa.send_message(message)
        if success:
            return jsonify({"status": "success", "message": "Message sent"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send message"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)
