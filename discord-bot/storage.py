"""
Storage module for Boykisser Game Bot.
Persists player data as `players.json` in the GitHub repo.
Works on Vercel serverless (HTTP) AND locally (file).
"""

import os
import json
import base64
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("storage")

DATA_FILE = "players.json"

# ─── GitHub ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "lykheang2025-source/boykisser-clan"
GITHUB_BRANCH = "main"
GITHUB_PATH = "discord-bot/players.json"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PATH}"

# ─── Local file ---
LOCAL_PATH = os.path.join(os.path.dirname(__file__), DATA_FILE)

def _github_read() -> dict | None:
    """Read players.json from GitHub via raw URL."""
    try:
        req = urllib.request.Request(GITHUB_RAW)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        logger.warning(f"GitHub read failed: {e}")
        return None

def _github_write(data: dict) -> bool:
    """Write players.json to GitHub via API (commit)."""
    if not GITHUB_TOKEN:
        return False
    try:
        body = json.dumps(data, indent=2)
        encoded = base64.b64encode(body.encode()).decode()

        # Get current file SHA first
        req = urllib.request.Request(GITHUB_API)
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        current_sha = None
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                current = json.loads(r.read().decode())
                current_sha = current.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            # File doesn't exist yet — will create

        # Commit
        commit = {
            "message": "Update players.json [bot]",
            "content": encoded,
            "branch": GITHUB_BRANCH,
        }
        if current_sha:
            commit["sha"] = current_sha

        req2 = urllib.request.Request(
            GITHUB_API,
            data=json.dumps(commit).encode(),
            method="PUT",
        )
        req2.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        req2.add_header("Content-Type", "application/json")
        req2.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(req2, timeout=10) as r:
            result = json.loads(r.read().decode())
            return result.get("content", {}).get("sha") is not None
    except Exception as e:
        logger.warning(f"GitHub write failed: {e}")
        return False

def _local_read() -> dict | None:
    """Read players.json from local file."""
    try:
        with open(LOCAL_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def _local_write(data: dict) -> bool:
    """Write players.json to local file."""
    try:
        with open(LOCAL_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.warning(f"Local write failed: {e}")
        return False

# ─── Public API ---

def load_all() -> dict:
    """Load all player data. Tries GitHub → Local."""
    # On Vercel (no local file access), use GitHub
    on_vercel = os.environ.get("VERCEL", False) or os.environ.get("VERCEL_ENV", False)
    if on_vercel or not os.path.exists(LOCAL_PATH):
        d = _github_read()
        if d is not None:
            return d
    # Local fallback
    d = _local_read()
    if d is not None:
        return d
    return {}

def save_all(data: dict) -> bool:
    """Save all player data. Tries GitHub → Local."""
    if _github_write(data):
        return True
    return _local_write(data)

def get_user(user_id: str) -> dict:
    """Get a single user's data. Creates default if missing."""
    all_data = load_all()
    if user_id not in all_data:
        all_data[user_id] = {"coins": 0, "last_claim": 0, "last_daily": 0}
        save_all(all_data)
    # Ensure all fields exist
    u = all_data[user_id]
    changed = False
    for field in ["last_daily"]:
        if field not in u:
            u[field] = 0
            changed = True
    if changed:
        save_all(all_data)
    return all_data[user_id]

def set_user(user_id: str, **kwargs) -> dict:
    """Update a single user's data with keyword args."""
    all_data = load_all()
    if user_id not in all_data:
        all_data[user_id] = {"coins": 0, "last_claim": 0, "last_daily": 0}
    all_data[user_id].update(kwargs)
    save_all(all_data)
    return all_data[user_id]

def get_all_users() -> dict:
    """Get dict of all users -> data."""
    return load_all()

def get_user_rank(user_id: str) -> int:
    """Get user's position sorted by coins (1 = richest)."""
    all_data = load_all()
    coin_list = sorted([u["coins"] for u in all_data.values() if isinstance(u, dict)], reverse=True)
    user_coins = all_data.get(user_id, {}).get("coins", 0)
    try:
        return coin_list.index(user_coins) + 1
    except ValueError:
        return len(coin_list) + 1

# ─── Init message ---
on_vercel = os.environ.get("VERCEL", False) or os.environ.get("VERCEL_ENV", False)
if on_vercel:
    logger.info("✅ GitHub storage (players.json in repo)")
elif os.path.exists(LOCAL_PATH):
    logger.info(f"📁 Local file: {LOCAL_PATH}")
else:
    logger.info("📁 New local file will be created")
