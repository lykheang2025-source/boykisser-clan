import json
import os
import random
import time
import discord
from discord import app_commands
from discord.ext import commands

DATA_FILE = "data.json"
CLAIM_COOLDOWN = 3600  # 1 hour in seconds

OWNER_ID = os.getenv("OWNER_ID", "")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_data(user_id: str):
    data = load_data()
    if user_id not in data:
        data[user_id] = {"coins": 0, "last_claim": 0}
        save_data(data)
    return data[user_id]

def update_user_data(user_id: str, coins: int = None, last_claim: int = None):
    data = load_data()
    if user_id not in data:
        data[user_id] = {"coins": 0, "last_claim": 0}
    if coins is not None:
        data[user_id]["coins"] = coins
    if last_claim is not None:
        data[user_id]["last_claim"] = last_claim
    save_data(data)

def get_user_rank(user_id: str) -> int:
    data = load_data()
    coin_list = sorted([u["coins"] for u in data.values()], reverse=True)
    user_coins = get_user_data(user_id)["coins"]
    return coin_list.index(user_coins) + 1 if user_coins in coin_list else len(coin_list) + 1

class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="claim", description="Claim a random amount of coins (10–1000)!")
    async def claim(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)

        now = time.time()
        time_since_last_claim = now - user_data["last_claim"]

        if time_since_last_claim < CLAIM_COOLDOWN:
            remaining = int(CLAIM_COOLDOWN - time_since_last_claim)
            hours, rem = divmod(remaining, 3600)
            minutes, seconds = divmod(rem, 60)
            embed = discord.Embed(
                title="⏳ Cooldown!",
                description=(
                    f"You need to wait **{hours}h {minutes}m {seconds}s** "
                    "before claiming again!"
                ),
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        reward = random.randint(10, 1000)
        new_balance = user_data["coins"] + reward

        update_user_data(user_id, coins=new_balance, last_claim=int(now))

        embed = discord.Embed(
            title="💰 Coins Claimed!",
            description=(
                f"You claimed **{reward}** coins! 🎉\n"
                f"Your new balance: **{new_balance}** coins"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Come back in 1 hour to claim again!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spin", description="Spin to win! Double your bet or lose it all.")
    @app_commands.describe(amount="How many coins you want to bet")
    async def spin(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1]):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        balance = user_data["coins"]

        if balance < amount:
            embed = discord.Embed(
                title="❌ Not Enough Coins!",
                description=(
                    f"You only have **{balance}** coins, "
                    f"but you tried to bet **{amount}**!"
                ),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 50/50 win or lose
        won = random.choice([True, False])

        if won:
            profit = amount  # win = get 2x (original bet + profit = 2x)
            new_balance = balance + profit
            update_user_data(user_id, coins=new_balance)

            embed = discord.Embed(
                title="🎰 SPIN RESULT — YOU WIN!",
                description=(
                    f"**You spun and WON!** 🎉\n\n"
                    f"Bet: **{amount}** coins\n"
                    f"Payout: **+{profit}** coins **(2×)**\n"
                    f"New balance: **{new_balance}** coins"
                ),
                color=discord.Color.gold()
            )
        else:
            new_balance = balance - amount
            update_user_data(user_id, coins=new_balance)

            embed = discord.Embed(
                title="🎰 SPIN RESULT — YOU LOSE!",
                description=(
                    f"**You spun and LOST...** 💀\n\n"
                    f"Bet: **{amount}** coins\n"
                    f"Lost: **-{amount}** coins\n"
                    f"New balance: **{new_balance}** coins"
                ),
                color=discord.Color.dark_red()
            )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Check your coin balance!")
    async def balance(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        balance = user_data["coins"]

        embed = discord.Embed(
            title="💳 Your Balance",
            description=f"You have **{balance}** coins.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show your profile or another user's profile with coins and rank!")
    @app_commands.describe(user="User to look up (leave blank for yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        target_id = str(target.id)
        user_data = get_user_data(target_id)
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

        top = get_user_rank(target_id)
        coin_str = str(coins).zfill(4)

        embed = discord.Embed(
            title="PF",
            color=15564031
        )
        embed.add_field(name="**Name : **", value=f"**{target.display_name}**", inline=False)
        embed.add_field(name="**Rank : **", value=f"**{rank}**\n**Top : {top} **", inline=False)
        embed.add_field(name="**Cloin : **", value=f"**{coin_str}**", inline=False)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1518976980270448761/1524347198803017738/mauzymice-mauzy.gif?ex=6a4f6a75&is=6a4e18f5&hm=a7b877b6193965c05a0c466354cee39ca9d52d44946eaba5d0179c612988b30e&")
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="givecloin", description="Give coins to another user!")
    @app_commands.describe(user="User to give coins to", amount="Amount of coins to give")
    async def givecloin(self, interaction: discord.Interaction, user: discord.User, amount: app_commands.Range[int, 1]):
        user_id = str(interaction.user.id)
        target_id = str(user.id)

        if target_id == user_id:
            embed = discord.Embed(title="Error!", description="You can't give coins to yourself!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        sender_data = get_user_data(user_id)
        if sender_data["coins"] < amount:
            embed = discord.Embed(title="Not Enough Coins!", description=f"You only have **{sender_data['coins']}** coins, but you tried to give **{amount}**!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        receiver_data = get_user_data(target_id)
        update_user_data(user_id, coins=sender_data["coins"] - amount)
        update_user_data(target_id, coins=receiver_data["coins"] + amount)

        embed = discord.Embed(
            title="Transfer Complete!",
            description=f"You gave **{amount}** coins to {user.mention}!\n\nYour balance: **{sender_data['coins'] - amount}** coins\nTheir balance: **{receiver_data['coins'] + amount}** coins",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setcloin", description="[OP ONLY] Set a user's coin balance")
    @app_commands.describe(user="User to set coins for", amount="Amount of coins to set")
    async def setcloin(self, interaction: discord.Interaction, user: discord.User, amount: app_commands.Range[int, 0]):
        user_id = str(interaction.user.id)

        if not OWNER_ID or user_id != OWNER_ID:
            embed = discord.Embed(title="Access Denied!", description="Only the bot owner can use this command!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_id = str(user.id)
        update_user_data(target_id, coins=amount)

        embed = discord.Embed(
            title="Coins Set!",
            description=f"Set {user.mention}'s balance to **{amount}** coins!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Spin the slot machine! Match 3 to win big!")
    @app_commands.describe(amount="Coins to bet")
    async def slots(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1]):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        if user_data["coins"] < amount:
            embed = discord.Embed(title="Not Enough Coins!", description=f"You only have **{user_data['coins']}** coins!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐", "7️⃣"]
        r1, r2, r3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        if r1 == r2 == r3:
            multi = 5 if r1 == "7️⃣" else 4
            profit = amount * multi
            result_text = f"**JACKPOT!** {r1} {r2} {r3}"
            color = discord.Color.gold()
        elif r1 == r2 or r1 == r3 or r2 == r3:
            profit = amount * 1
            result_text = f"**Small win!** {r1} {r2} {r3}"
            color = discord.Color.blue()
        else:
            profit = 0
            result_text = f"**You lost!** {r1} {r2} {r3}"
            color = discord.Color.dark_red()
        net = profit - amount
        new_bal = user_data["coins"] + net
        update_user_data(user_id, coins=new_bal)
        embed = discord.Embed(title="🎰 SLOTS", description=f"{result_text}\n\nBet: **{amount}**\nNet: **{net:+d}**\nBalance: **{new_bal}**", color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll a 6-sided die! Roll 4+ to win!")
    @app_commands.describe(amount="Coins to bet")
    async def dice(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1]):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        if user_data["coins"] < amount:
            embed = discord.Embed(title="Not Enough Coins!", description=f"You only have **{user_data['coins']}** coins!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        roll = random.randint(1, 6)
        if roll >= 4:
            multi = 2 if roll == 6 else 1.5
            profit = int(amount * multi)
            net = profit - amount
            new_bal = user_data["coins"] + net
            update_user_data(user_id, coins=new_bal)
            embed = discord.Embed(title=f"🎲 DICE - {roll}", description=f"**You won!**\n\nBet: **{amount}**\nRoll: **{roll}**\nPayout: **+{net}**\nBalance: **{new_bal}**", color=discord.Color.gold())
        else:
            new_bal = user_data["coins"] - amount
            update_user_data(user_id, coins=new_bal)
            embed = discord.Embed(title=f"🎲 DICE - {roll}", description=f"**You lost!**\n\nBet: **{amount}**\nRoll: **{roll}**\nLost: **-{amount}**\nBalance: **{new_bal}**", color=discord.Color.dark_red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Bet on heads or tails!")
    @app_commands.describe(amount="Coins to bet", choice="Heads or tails?")
    @app_commands.choices(choice=[app_commands.Choice(name="Heads", value="heads"), app_commands.Choice(name="Tails", value="tails")])
    async def coinflip(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1], choice: str):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        if user_data["coins"] < amount:
            embed = discord.Embed(title="Not Enough Coins!", description=f"You only have **{user_data['coins']}** coins!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        result = random.choice(["heads", "tails"])
        won = choice == result
        if won:
            new_bal = user_data["coins"] + amount
            update_user_data(user_id, coins=new_bal)
            embed = discord.Embed(title="🪙 COINFLIP", description=f"**You won!** 🎉\n\nCalled: **{choice}**\nResult: **{result}**\nPayout: **+{amount}**\nBalance: **{new_bal}**", color=discord.Color.gold())
        else:
            new_bal = user_data["coins"] - amount
            update_user_data(user_id, coins=new_bal)
            embed = discord.Embed(title="🪙 COINFLIP", description=f"**You lost!** 💀\n\nCalled: **{choice}**\nResult: **{result}**\nLost: **-{amount}**\nBalance: **{new_bal}**", color=discord.Color.dark_red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily bonus (50-500 coins)!")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user_data(user_id)
        now = time.time()
        time_since = now - user_data.get("last_daily", 0)
        if time_since < 86400:
            remaining = int(86400 - time_since)
            h, rem = divmod(remaining, 3600)
            m, s = divmod(rem, 60)
            embed = discord.Embed(title="Daily Cooldown!", description=f"Come back in **{h}h {m}m {s}s**!", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        reward = random.randint(50, 500)
        new_bal = user_data["coins"] + reward
        update_user_data(user_id, coins=new_bal)
        data = load_data()
        data[user_id]["last_daily"] = int(now)
        save_data(data)
        embed = discord.Embed(title="Daily Reward!", description=f"You got **{reward}** coins! 🎉\n\nBalance: **{new_bal}**", color=discord.Color.green())
        embed.set_footer(text="Come back in 24 hours!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the top 10 richest users!")
    async def leaderboard(self, interaction: discord.Interaction):
        data = load_data()
        if not data:
            embed = discord.Embed(title="🏆 Leaderboard", description="No users yet!", color=discord.Color.gold())
            await interaction.response.send_message(embed=embed)
            return
        sorted_users = sorted(data.items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, udata) in enumerate(sorted_users):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            lines.append(f"{medal} <@{uid}> — **{udata['coins']}** coins")
        embed = discord.Embed(title="🏆 Leaderboard", description="\n".join(lines), color=discord.Color.gold())
        embed.set_footer(text="Top 10 richest users")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rob", description="Try to rob another user! High risk, high reward!")
    @app_commands.describe(user="User to rob")
    async def rob(self, interaction: discord.Interaction, user: discord.User):
        user_id = str(interaction.user.id)
        target_id = str(user.id)
        if target_id == user_id:
            embed = discord.Embed(title="Error!", description="You can't rob yourself!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        target_data = get_user_data(target_id)
        if target_data["coins"] <= 0:
            embed = discord.Embed(title="Error!", description="That user has 0 coins! Nothing to rob...", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        user_data = get_user_data(user_id)
        if user_data["coins"] < 25:
            embed = discord.Embed(title="Not Enough Coins!", description="You need at least **25** coins to attempt a robbery (bail money)!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        success = random.random() < 0.4
        if success:
            steal_pct = random.uniform(0.15, 0.30)
            stolen = max(1, int(target_data["coins"] * steal_pct))
            update_user_data(user_id, coins=user_data["coins"] + stolen)
            update_user_data(target_id, coins=target_data["coins"] - stolen)
            embed = discord.Embed(title="💰 ROBBERY SUCCESS!", description=f"You robbed {user.mention} and got **{stolen}** coins! 💀\n\nYour balance: **{user_data['coins'] + stolen}**\nTheir balance: **{target_data['coins'] - stolen}**", color=discord.Color.green())
        else:
            penalty = random.randint(25, 75)
            new_bal = max(0, user_data["coins"] - penalty)
            update_user_data(user_id, coins=new_bal)
            embed = discord.Embed(title="🚔 ROBBERY FAILED!", description=f"You got caught! Paid **{penalty}** coins bail! 💀\n\nYour balance: **{new_bal}**", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
