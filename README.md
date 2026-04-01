---
title: WhatsApp Automation Studio
sdk: docker
app_port: 7860
---

# WhatsApp Automation Studio

Professional WhatsApp Web automation for seamless messaging, now running on Hugging Face Spaces.

## API Documentation

- **`/health`**: Returns HTTP 200 when the app is ready.
- **`/api-docs`**: Documents all available API endpoints.
- **`/login`**: Starts the Selenium browser in headless mode and captures the QR code.
- **`/check-login`**: Checks if the WhatsApp session is logged in.
- **`/send`**: Sends a message to the currently active chat.

## Usage

1. Call `/login` (POST) to start the browser and get the QR code.
2. Scan the QR code with your WhatsApp app.
3. Call `/check-login` (GET) to verify login success.
4. Call `/send` (POST) with `{"message": "Your text"}` to send messages.
