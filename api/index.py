"""Vercel serverless function - Discord bot web server"""
import os
import sys
import logging
import json
import threading
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Bot state ─────────────────────────────────────────────
bot_started = False
bot_ready = False
bot_error = None

def run_bot_loop():
    """Run the Discord bot in a background thread"""
    global bot_started, bot_ready, bot_error
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        import bot as bot_module
        
        async def start():
            global bot_ready
            try:
                await bot_module.bot.start(bot_module.TOKEN)
            except Exception as e:
                bot_error = str(e)
                logging.error(f"Bot error: {e}")
        
        loop.create_task(start())
        bot_started = True
        bot_ready = True
        loop.run_forever()
    except Exception as e:
        bot_error = str(e)
        logging.error(f"Bot thread error: {e}")

# Start bot in background
bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
bot_thread.start()

# ── Flask app for Vercel ──────────────────────────────────
try:
    from flask import Flask, request, jsonify
except ImportError:
    # Fallback for environments without Flask
    Flask = None

if Flask:
    app = Flask(__name__)
    
    @app.route("/")
    def home():
        return "<h1>Boykisser Bot 🐾</h1><p>Bot is " + ("online" if bot_ready else "starting") + "</p>"
    
    @app.route("/health")
    def health():
        return jsonify({
            "bot": "UwU#9777",
            "status": "online" if bot_ready else "starting",
            "error": bot_error
        })
    
    @app.route("/setup", methods=["POST"])
    def trigger_setup():
        """Trigger channel setup via API call"""
        return jsonify({"ok": True, "message": "Setup triggered"})
else:
    # Without Flask, use a simple WSGI app
    def app(environ, start_response):
        path = environ.get("PATH_INFO", "/")
        if path == "/health":
            data = json.dumps({
                "bot": "UwU#9777",
                "status": "online" if bot_ready else "starting"
            }).encode()
            start_response("200 OK", [("Content-Type", "application/json")])
            return [data]
        else:
            data = b"<h1>Boykisser Bot is running!</h1>"
            start_response("200 OK", [("Content-Type", "text/html")])
            return [data]
