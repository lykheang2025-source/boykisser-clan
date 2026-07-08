"""Slash command registration endpoint for Vercel.
Call this once after deployment to register commands with Discord."""

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.environ.get("DISCORD_TOKEN", "")
APPLICATION_ID = os.environ.get("APPLICATION_ID", "")

COMMANDS = [
    {
        "name": "claim",
        "description": "Claim a random amount of coins (10–1000)!",
    },
    {
        "name": "spin",
        "description": "Spin to win! Double your bet or lose it all.",
        "options": [
            {
                "type": 4,  # INTEGER
                "name": "amount",
                "description": "How many coins you want to bet",
                "required": True,
                "min_value": 1,
            }
        ],
    },
    {
        "name": "balance",
        "description": "Check your coin balance!",
    },
]

@app.route("/", methods=["GET"])
def health():
    return "Command sync endpoint — POST /sync to register commands"

@app.route("/sync", methods=["POST"])
def sync_commands():
    """Register all slash commands with Discord."""
    # Simple auth check — require a secret key
    auth_key = request.headers.get("X-Sync-Key", "")
    expected = os.environ.get("SYNC_SECRET", "")
    if expected and auth_key != expected:
        return jsonify({"error": "Unauthorized"}), 401

    if not TOKEN or not APPLICATION_ID:
        return jsonify({"error": "DISCORD_TOKEN and APPLICATION_ID must be set"}), 500

    url = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
    }

    results = []
    for cmd in COMMANDS:
        r = requests.post(url, headers=headers, json=cmd)
        results.append({
            "command": cmd["name"],
            "status": r.status_code,
            "response": r.json() if r.status_code == 201 else r.text,
        })

    return jsonify({"synced": len(results), "results": results})
