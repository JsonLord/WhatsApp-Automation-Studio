import os
import time
import base64
import requests
import threading
import random
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import gradio as gr
from wa_logic import WhatsAppAutomation
from presets import PresetManager

# Global automation instance and lock
wa = WhatsAppAutomation()
wa_lock = threading.Lock()

pm = PresetManager()
presets = pm.get_presets()
preset_names = [p["name"] for p in presets]

REGISTER_ENDPOINT = "https://auxteam-plandex-backup.hf.space/register"

# Logic Functions
def perform_login():
    global wa
    with wa_lock:
        if wa.driver:
            try:
                wa.close()
            except:
                pass
        wa = WhatsAppAutomation() # Re-init
        success = wa.initialize_driver(headless=True)
        if not success:
            return None, "Failed to initialize driver"

        wa.navigate_to_whatsapp()
        # Wait for QR code to appear
        for _ in range(20):
            qr_code = wa.get_qr_code_screenshot()
            if qr_code:
                try:
                    # Forward QR code to register endpoint
                    requests.post(REGISTER_ENDPOINT, json={"qr_code": qr_code}, timeout=2)
                except:
                    pass
                return f"data:image/png;base64,{qr_code}", "QR code captured. Scan now!"
            time.sleep(1)

        return None, "Failed to capture QR code after timeout"

def check_wa_login():
    global wa
    with wa_lock:
        if not wa.driver:
            return False, "Browser not started"
        logged_in = wa.check_login_status(timeout=5)
        return logged_in, "Logged in" if logged_in else "Not logged in"

def send_wa_message(message, repeat=1, delay_min=1, delay_max=3, typing_sim=True, typing_speed=0.01):
    global wa
    if not message:
        return "No message provided"

    with wa_lock:
        if not wa.driver:
            return "Browser not started. Login first."

        # Update config dynamically
        wa.config["typing_simulation"] = typing_sim
        wa.config["typing_speed"] = typing_speed

        results = []
        for i in range(int(repeat)):
            success = wa.send_message(message)
            if success:
                results.append(f"Sent {i+1}/{repeat}")
            else:
                results.append(f"Failed at {i+1}/{repeat}")
                break
            if i < int(repeat) - 1:
                # Random delay between messages
                time.sleep(random.uniform(delay_min, delay_max))

        return "\n".join(results)

# Gradio Interface
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
                    with gr.Row():
                        repeat_count = gr.Number(value=1, label="Repeat Count", precision=0)
                        send_btn = gr.Button("▶ Start Sending", variant="primary")
                    send_status = gr.TextArea(label="Status", interactive=False)
                with gr.Column(scale=1):
                    preset_dropdown = gr.Dropdown(choices=preset_names, label="✨ Message Presets")
                    load_preset_btn = gr.Button("📥 Load Preset")

                    def load_preset(name):
                        preset = pm.get_preset_by_name(name)
                        if preset:
                            if "messages" in preset:
                                return "\n".join(preset["messages"])
                            return preset.get("message", "")
                        return ""

                    load_preset_btn.click(load_preset, inputs=preset_dropdown, outputs=msg_input)

        with gr.Tab("⚙️ Settings"):
            with gr.Group():
                typing_sim = gr.Checkbox(label="Simulate Real Typing", value=True)
                typing_spd = gr.Slider(minimum=0.001, maximum=0.1, value=0.01, label="Typing Speed (sec/char)")
                delay_min = gr.Slider(minimum=0.1, maximum=10.0, value=1.0, label="Min Delay Between Messages")
                delay_max = gr.Slider(minimum=1.0, maximum=20.0, value=3.0, label="Max Delay Between Messages")
                gr.Checkbox(label="🌙 Dark Mode", value=True)

        with gr.Tab("📋 Logs"):
            log_output = gr.TextArea(label="Activity Logs", value="Welcome to WhatsApp Automation Studio!", interactive=False, lines=15)

    # Wire up the send button with settings
    send_btn.click(
        send_wa_message,
        inputs=[msg_input, repeat_count, delay_min, delay_max, typing_sim, typing_spd],
        outputs=send_status
    )

# FastAPI integration
api_app = FastAPI()

@api_app.get("/health")
def health():
    return {"status": "ready"}

@api_app.get("/api-docs")
def api_docs():
    return {
        "endpoints": [
            {"path": "/health", "method": "GET", "purpose": "Health check"},
            {"path": "/api-docs", "method": "GET", "purpose": "API documentation"},
            {"path": "/login", "method": "POST", "purpose": "Start login and get QR code"},
            {"path": "/send", "method": "POST", "purpose": "Send message via API"}
        ]
    }

@api_app.post("/login")
def api_login():
    qr, msg = perform_login()
    if qr:
        return {"status": "success", "qr_code": qr, "message": msg}
    raise HTTPException(status_code=500, detail=msg)

@api_app.get("/check-login")
def api_check_login():
    logged_in, msg = check_wa_login()
    return {"status": "success", "logged_in": logged_in, "message": msg}

@api_app.post("/send")
async def api_send(request: Request):
    try:
        data = await request.json()
    except:
        data = {}
    res = send_wa_message(data.get("message"), repeat=data.get("repeat", 1))
    return {"status": "success" if "successfully" in res or "Sent" in res else "error", "message": res}

# Mount Gradio into FastAPI
app = gr.mount_gradio_app(api_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
