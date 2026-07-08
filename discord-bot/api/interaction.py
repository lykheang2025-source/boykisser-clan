import os
import json
import random
import time
import nacl.bindings
import nacl.signing
import nacl.exceptions
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─── Environment ──────────────────────────────────────────────────────────────
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
TOKEN = os.environ.get("DISCORD_TOKEN", "")
OWNER_ID = os.environ.get("OWNER_ID", "")

# ─── Storage ──────────────────────────────────────────────────────────────────
import storage as store
CLAIM_COOLDOWN = 3600
DAILY_COOLDOWN = 86400  # 24h
OWNER_ID = os.environ.get("OWNER_ID", "")

get_user_data = store.get_user
update_user_data = lambda uid, **kw: store.set_user(uid, **kw) if kw else None
get_user_rank = store.get_user_rank

# ─── Verify Discord interaction signature ────────────────────────────────────
def verify_signature(raw_body: bytes, signature: str, timestamp: str) -> bool:
    if not signature or not timestamp or not DISCORD_PUBLIC_KEY:
        return False
    try:
        message = timestamp.encode() + raw_body
        sig_bytes = bytes.fromhex(signature)
        pub_key_bytes = bytes.fromhex(DISCORD_PUBLIC_KEY)
        verify_key = nacl.signing.VerifyKey(pub_key_bytes)
        verify_key.verify(message, sig_bytes)
        return True
    except nacl.exceptions.BadSignatureError:
        return False
    except Exception:
        try:
            nacl.bindings.crypto_sign_verify_detached(sig_bytes, message, pub_key_bytes)
            return True
        except Exception:
            return False

# ─── Command handlers ─────────────────────────────────────────────────────────
def handle_claim(user_id: str) -> dict:
    user_data = get_user_data(user_id)
    now = time.time()
    time_since = now - user_data["last_claim"]
    if time_since < CLAIM_COOLDOWN:
        remaining = int(CLAIM_COOLDOWN - time_since)
        h, rem = divmod(remaining, 3600)
        m, s = divmod(rem, 60)
        return {"type": 4, "data": {"embeds": [{"title": "Cooldown!", "description": f"You need to wait **{h}h {m}m {s}s** before claiming again!", "color": 0xFFA500}], "flags": 64}}
    reward = random.randint(10, 1000)
    new_balance = user_data["coins"] + reward
    update_user_data(user_id, coins=new_balance, last_claim=int(now))
    return {"type": 4, "data": {"embeds": [{"title": "Coins Claimed!", "description": f"You claimed **{reward}** coins! Your new balance: **{new_balance}** coins", "color": 0x00FF00, "footer": {"text": "Come back in 1 hour to claim again!"}}]}}

def handle_spin(user_id: str, amount: int) -> dict:
    user_data = get_user_data(user_id)
    balance = user_data["coins"]
    if balance < amount:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": f"You only have **{balance}** coins, but you tried to bet **{amount}**!", "color": 0xFF0000}], "flags": 64}}
    won = random.choice([True, False])
    if won:
        new_balance = balance + amount
        update_user_data(user_id, coins=new_balance)
        embed = {"title": "SPIN RESULT - YOU WIN!", "description": f"**You spun and WON!**\n\nBet: **{amount}** coins\nPayout: **+{amount}** coins **(2x)**\nNew balance: **{new_balance}** coins", "color": 0xFFD700}
    else:
        new_balance = balance - amount
        update_user_data(user_id, coins=new_balance)
        embed = {"title": "SPIN RESULT - YOU LOSE!", "description": f"**You spun and LOST...**\n\nBet: **{amount}** coins\nLost: **-{amount}** coins\nNew balance: **{new_balance}** coins", "color": 0x8B0000}
    return {"type": 4, "data": {"embeds": [embed]}}

def handle_balance(user_id: str) -> dict:
    user_data = get_user_data(user_id)
    return {"type": 4, "data": {"embeds": [{"title": "Your Balance", "description": f"You have **{user_data['coins']}** coins.", "color": 0x3498DB}]}}

def handle_profile(user_id: str, target_id: str = None, caller_name: str = "User", caller_avatar: str = "") -> dict:
    show_id = target_id if target_id else user_id
    show_name = caller_name
    show_avatar = caller_avatar

    if target_id and target_id != user_id:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://discord.com/api/v10/users/{target_id}",
                headers={"Authorization": f"Bot {TOKEN}"}
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                show_name = data.get("global_name") or data.get("username", "Unknown")
                avatar_hash = data.get("avatar", "")
                if avatar_hash:
                    ext = "gif" if avatar_hash.startswith("a_") else "png"
                    show_avatar = f"https://cdn.discordapp.com/avatars/{target_id}/{avatar_hash}.{ext}"
                else:
                    show_avatar = f"https://cdn.discordapp.com/embed/avatars/{int(target_id) % 5}.png"
        except Exception:
            pass

    user_data = get_user_data(show_id)
    coins = user_data["coins"]

    if coins >= 50000:
        rank = "Diamond"
    elif coins >= 10000:
        rank = "Platinum"
    elif coins >= 5000:
        rank = "Gold"
    elif coins >= 1000:
        rank = "Silver"
    elif coins >= 100:
        rank = "Bronze"
    else:
        rank = "Peasant"

    top = get_user_rank(show_id)
    coin_str = str(coins).zfill(4)

    embed = {
        "title": "PF",
        "color": 15564031,
        "fields": [
            {"name": "**Name : **", "value": f"**{show_name}**", "inline": False},
            {"name": "**Rank : **", "value": f"**{rank}**\n**Top : {top} **", "inline": False},
            {"name": "**Cloin : **", "value": f"**{coin_str}**", "inline": False}
        ],
        "image": {
            "url": "https://cdn.discordapp.com/attachments/1518976980270448761/1524347198803017738/mauzymice-mauzy.gif?ex=6a4f6a75&is=6a4e18f5&hm=a7b877b6193965c05a0c466354cee39ca9d52d44946eaba5d0179c612988b30e&"
        },
        "thumbnail": {
            "url": show_avatar
        }
    }
    return {"type": 4, "data": {"embeds": [embed]}}

def handle_givecloin(user_id: str, target_id: str, amount: int) -> dict:
    if target_id == user_id:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "You can't give coins to yourself!", "color": 0xFF0000}], "flags": 64}}
    if amount < 1:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "Amount must be at least 1!", "color": 0xFF0000}], "flags": 64}}

    sender_data = get_user_data(user_id)
    if sender_data["coins"] < amount:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": f"You only have **{sender_data['coins']}** coins, but you tried to give **{amount}**!", "color": 0xFF0000}], "flags": 64}}

    receiver_data = get_user_data(target_id)
    update_user_data(user_id, coins=sender_data["coins"] - amount)
    update_user_data(target_id, coins=receiver_data["coins"] + amount)

    return {"type": 4, "data": {"embeds": [{"title": "Transfer Complete!", "description": f"You gave **{amount}** coins to <@{target_id}>!\n\nYour balance: **{sender_data['coins'] - amount}** coins\nTheir balance: **{receiver_data['coins'] + amount}** coins", "color": 0x00FF00}]}}

def handle_setcloin(user_id: str, target_id: str, amount: int) -> dict:
    if not OWNER_ID or user_id != OWNER_ID:
        return {"type": 4, "data": {"embeds": [{"title": "Access Denied!", "description": "Only the bot owner can use this command!", "color": 0xFF0000}], "flags": 64}}
    if amount < 0:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "Amount must be 0 or more!", "color": 0xFF0000}], "flags": 64}}

    update_user_data(target_id, coins=amount)
    return {"type": 4, "data": {"embeds": [{"title": "Coins Set!", "description": f"Set <@{target_id}>'s balance to **{amount}** coins!", "color": 0x00FF00}]}}

# ─── New Game Commands ─────────────────────────────────────────────────────────

def handle_slots(user_id: str, amount: int) -> dict:
    user_data = get_user_data(user_id)
    balance = user_data["coins"]
    if balance < amount:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": f"You only have **{balance}** coins, but you tried to bet **{amount}**!", "color": 0xFF0000}], "flags": 64}}

    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐", "7️⃣"]
    r1 = random.choice(symbols)
    r2 = random.choice(symbols)
    r3 = random.choice(symbols)

    payout = 0
    if r1 == r2 == r3:
        # Jackpot - 3 matching
        multiplier = 5 if r1 == "7️⃣" else 4
        payout = amount * multiplier
        result_text = f"**JACKPOT!** {r1} {r2} {r3}"
    elif r1 == r2 or r1 == r3 or r2 == r3:
        payout = amount * 1  # 1x (get bet back)
        result_text = f"**Small win!** {r1} {r2} {r3}"
    else:
        payout = 0
        result_text = f"**You lost!** {r1} {r2} {r3}"

    profit = payout - amount
    new_balance = balance + profit
    update_user_data(user_id, coins=new_balance)

    if profit > 0:
        embed = {"title": "🎰 SLOTS", "description": f"{result_text}\n\nBet: **{amount}**\nPayout: **+{profit}**\nBalance: **{new_balance}**", "color": 0xFFD700}
    elif profit == 0:
        embed = {"title": "🎰 SLOTS", "description": f"{result_text}\n\nBet: **{amount}**\nPayout: **0** (tied!)\nBalance: **{new_balance}**", "color": 0x3498DB}
    else:
        embed = {"title": "🎰 SLOTS", "description": f"{result_text}\n\nBet: **{amount}**\nLost: **-{amount}**\nBalance: **{new_balance}**", "color": 0x8B0000}

    return {"type": 4, "data": {"embeds": [embed]}}

def handle_dice(user_id: str, amount: int) -> dict:
    user_data = get_user_data(user_id)
    balance = user_data["coins"]
    if balance < amount:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": f"You only have **{balance}** coins, but you tried to bet **{amount}**!", "color": 0xFF0000}], "flags": 64}}

    roll = random.randint(1, 6)
    if roll >= 4:
        multiplier = 2 if roll == 6 else 1.5
        profit = int(amount * multiplier) - amount
        new_balance = balance + profit
        update_user_data(user_id, coins=new_balance)
        embed = {"title": f"🎲 DICE - {roll}", "description": f"**You won!**\n\nBet: **{amount}**\nRoll: **{roll}**\nPayout: **+{profit}**\nBalance: **{new_balance}**", "color": 0xFFD700}
    else:
        new_balance = balance - amount
        update_user_data(user_id, coins=new_balance)
        embed = {"title": f"🎲 DICE - {roll}", "description": f"**You lost!**\n\nBet: **{amount}**\nRoll: **{roll}**\nLost: **-{amount}**\nBalance: **{new_balance}**", "color": 0x8B0000}

    return {"type": 4, "data": {"embeds": [embed]}}

def handle_coinflip(user_id: str, amount: int, choice: str) -> dict:
    user_data = get_user_data(user_id)
    balance = user_data["coins"]
    if balance < amount:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": f"You only have **{balance}** coins, but you tried to bet **{amount}**!", "color": 0xFF0000}], "flags": 64}}

    result = random.choice(["heads", "tails"])
    won = choice == result

    if won:
        new_balance = balance + amount
        update_user_data(user_id, coins=new_balance)
        embed = {"title": "🪙 COINFLIP", "description": f"**You won!** 🎉\n\nCalled: **{choice}**\nResult: **{result}**\nBet: **{amount}**\nPayout: **+{amount}**\nBalance: **{new_balance}**", "color": 0xFFD700}
    else:
        new_balance = balance - amount
        update_user_data(user_id, coins=new_balance)
        embed = {"title": "🪙 COINFLIP", "description": f"**You lost!** 💀\n\nCalled: **{choice}**\nResult: **{result}**\nBet: **{amount}**\nLost: **-{amount}**\nBalance: **{new_balance}**", "color": 0x8B0000}

    return {"type": 4, "data": {"embeds": [embed]}}

def handle_daily(user_id: str) -> dict:
    user_data = get_user_data(user_id)
    now = time.time()
    time_since = now - user_data.get("last_daily", 0)
    if time_since < DAILY_COOLDOWN:
        remaining = int(DAILY_COOLDOWN - time_since)
        h, rem = divmod(remaining, 3600)
        m, s = divmod(rem, 60)
        return {"type": 4, "data": {"embeds": [{"title": "Daily Cooldown!", "description": f"Come back in **{h}h {m}m {s}s** for your daily bonus!", "color": 0xFFA500}], "flags": 64}}

    reward = random.randint(50, 500)
    new_balance = user_data["coins"] + reward
    store.set_user(user_id, coins=new_balance, last_claim=user_data["last_claim"], last_daily=int(now))
    return {"type": 4, "data": {"embeds": [{"title": "Daily Reward!", "description": f"You claimed your daily **{reward}** coins! 🎉\n\nBalance: **{new_balance}** coins", "color": 0x00FF00, "footer": {"text": "Come back in 24 hours for more!"}}]}}

def handle_leaderboard(user_id: str) -> dict:
    try:
        all_data = store.get_all_users()
        entries = [(uid, u["coins"]) for uid, u in all_data.items()]
        entries.sort(key=lambda x: x[1], reverse=True)
        top10 = entries[:10]

        description_lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, coins) in enumerate(top10):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description_lines.append(f"{medal} <@{uid}> — **{coins}** coins")

        embed = {
            "title": "🏆 Leaderboard",
            "description": "\n".join(description_lines) if description_lines else "No users yet!",
            "color": 0xFFD700,
            "footer": {"text": "Top 10 richest users"}
        }
        return {"type": 4, "data": {"embeds": [embed]}}
    except Exception:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "Could not load leaderboard.", "color": 0xFF0000}], "flags": 64}}

def handle_rob(user_id: str, target_id: str) -> dict:
    if target_id == user_id:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "You can't rob yourself!", "color": 0xFF0000}], "flags": 64}}

    target_data = get_user_data(target_id)
    if target_data["coins"] <= 0:
        return {"type": 4, "data": {"embeds": [{"title": "Error!", "description": "That user has 0 coins! Nothing to rob...", "color": 0xFF0000}], "flags": 64}}

    user_data = get_user_data(user_id)
    if user_data["coins"] < 25:
        return {"type": 4, "data": {"embeds": [{"title": "Not Enough Coins!", "description": "You need at least **25** coins to attempt a robbery (bail money)!", "color": 0xFF0000}], "flags": 64}}

    success = random.random() < 0.4  # 40% chance

    if success:
        steal_pct = random.uniform(0.15, 0.30)
        stolen = max(1, int(target_data["coins"] * steal_pct))
        update_user_data(user_id, coins=user_data["coins"] + stolen)
        update_user_data(target_id, coins=target_data["coins"] - stolen)
        embed = {"title": "💰 ROBBERY SUCCESS!", "description": f"You robbed <@{target_id}> and got **{stolen}** coins! 💀\n\nYour balance: **{user_data['coins'] + stolen}**\nTheir balance: **{target_data['coins'] - stolen}**", "color": 0x00FF00}
    else:
        penalty = random.randint(25, 75)
        new_balance = max(0, user_data["coins"] - penalty)
        update_user_data(user_id, coins=new_balance)
        embed = {"title": "🚔 ROBBERY FAILED!", "description": f"You got caught trying to rob <@{target_id}>! Paid **{penalty}** coins as bail! 💀\n\nYour balance: **{new_balance}**", "color": 0xFF0000}

    return {"type": 4, "data": {"embeds": [embed]}}

# ─── Routes ──────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return "Boykisser Game Bot is running on Vercel!"

@app.route("/", methods=["POST"])
def interaction():
    """Main Discord interaction endpoint."""
    raw_body = request.get_data()
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")

    if signature and timestamp:
        if not verify_signature(raw_body, signature, timestamp):
            return "Invalid signature", 401
    else:
        try:
            payload = json.loads(raw_body)
            if payload.get("type") == 1:
                return jsonify({"type": 1})
        except Exception:
            pass
        return "Missing signature headers", 401

    try:
        payload = json.loads(raw_body)

        if payload.get("type") == 1:
            return jsonify({"type": 1})

        if payload.get("type") == 2:
            data = payload.get("data", {})
            command_name = data.get("name", "")
            member = payload.get("member", {})
            user = member.get("user", {}) or payload.get("user", {})
            user_id = user.get("id", "")
            caller_name = user.get("global_name") or user.get("username", "User")
            avatar_hash = user.get("avatar", "")
            if avatar_hash:
                ext = "gif" if avatar_hash.startswith("a_") else "png"
                caller_avatar = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}"
            else:
                caller_avatar = f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png"
            options = {opt["name"]: opt["value"] for opt in data.get("options", [])}

            if command_name == "claim":
                resp = handle_claim(user_id)
            elif command_name == "spin":
                resp = handle_spin(user_id, int(options.get("amount", 1)))
            elif command_name == "balance":
                resp = handle_balance(user_id)
            elif command_name == "profile":
                target_id = options.get("user", None)
                resp = handle_profile(user_id, target_id, caller_name, caller_avatar)
            elif command_name == "givecloin":
                target_id = str(options.get("user", ""))
                amount = int(options.get("amount", 1))
                resp = handle_givecloin(user_id, target_id, amount)
            elif command_name == "setcloin":
                target_id = str(options.get("user", ""))
                amount = int(options.get("amount", 0))
                resp = handle_setcloin(user_id, target_id, amount)
            elif command_name == "slots":
                resp = handle_slots(user_id, int(options.get("amount", 1)))
            elif command_name == "dice":
                resp = handle_dice(user_id, int(options.get("amount", 1)))
            elif command_name == "coinflip":
                resp = handle_coinflip(user_id, int(options.get("amount", 1)), options.get("choice", "heads"))
            elif command_name == "daily":
                resp = handle_daily(user_id)
            elif command_name == "leaderboard":
                resp = handle_leaderboard(user_id)
            elif command_name == "rob":
                target_id = str(options.get("user", ""))
                resp = handle_rob(user_id, target_id)
            else:
                resp = {"type": 4, "data": {"content": f"Unknown command: {command_name}", "flags": 64}}

            return jsonify(resp)

        return jsonify({"error": "Unknown interaction type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/interaction", methods=["POST"])
def interaction_alt():
    return interaction()
