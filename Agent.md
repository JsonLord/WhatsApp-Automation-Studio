# WhatsApp Automation Studio Deployment

This application is deployed on a Hugging Face Space using a Docker SDK.

## Deployment Configuration

### Target Space
- **Profile:** `AUXteam`
- **Space:** `Plandex_backup`
- **Full Identifier:** `AUXteam/Plandex_backup`
- **Frontend Port:** `7860` (mandatory for all Hugging Face Spaces)

### Deployment Method
- **Docker SDK**

### Features & Logic
- The app runs a headless Selenium Chrome browser.
- QR code is captured and forwarded to `https://auxteam-plandex-backup.hf.space/register`.
- Provides a REST API for message automation.

## API Documentation

- **`/health`**: Returns HTTP 200 when the app is ready.
- **`/api-docs`**: Documents all available API endpoints.
- **`/login`**: Starts the Selenium browser in headless mode and captures the QR code.
- **`/check-login`**: Checks if the WhatsApp session is logged in.
- **`/send`**: Sends a message to the currently active chat.

### `/predict` (Example Placeholder)
- Method: POST
- Purpose: Run model inference (if any)
- Request: `{"text": "hello world"}`
- Response: `{"prediction": "…"}`

All endpoints listed here **must** appear in `/api-docs`.

## Ongoing Deployment Best Practices

- Always ensure the Docker image includes necessary browser dependencies for Selenium.
- Headless Chrome requires certain arguments like `--no-sandbox` and `--disable-dev-shm-usage` when running in Docker.
- Monitor logs regularly using the provided build and run log endpoints.
- Port binding must be on `7860`.
