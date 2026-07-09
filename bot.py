import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN environment variable is not set!")

# OP user IDs that can use /set
OP_IDS = set()

# Join links pool
JOIN_LINKS = [
    "https://shorturl.asia/aJeTF",
    "https://shorturl.asia/GlgZK",
    "https://shorturl.asia/g1OVP",
    "https://shorturl.asia/LQ7AP",
    "https://shorturl.asia/iLv5t"
]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# ===================== VIEWS =====================

class GameDMView(discord.ui.View):
    """View sent in DM with a random Join Game link"""
    def __init__(self):
        super().__init__(timeout=None)
        link = random.choice(JOIN_LINKS)
        self.add_item(discord.ui.Button(label="Join Game", url=link, style=discord.ButtonStyle.link))


class GameButtonsView(discord.ui.View):
    """Persistent view with the 7 game buttons in #game"""
    def __init__(self):
        super().__init__(timeout=None)
        game_buttons = [
            "Fun Combat", "Sword Fight", "Goat", "V4",
            "Goat 2P", "V4 2P", "Sword Fight 2P"
        ]
        for btn_name in game_buttons:
            cid = f"gamebtn_{btn_name.lower().replace(' ', '_')}"
            button = discord.ui.Button(
                label=btn_name,
                style=discord.ButtonStyle.primary,
                custom_id=cid
            )
            button.callback = self._make_callback(btn_name)
            self.add_item(button)

    def _make_callback(self, label: str):
        async def callback(interaction: discord.Interaction):
            await self._handle_game_click(interaction)
        return callback

    async def _handle_game_click(self, interaction: discord.Interaction):
        """DM the user with game embed + random join link"""
        player_count = random.randint(20, 100)
        embed = discord.Embed(
            title="Game Condo 24/7",
            description=f"**Click a Button Join Game**\n**Game Player : {player_count} player**",
            color=0xFDBF00
        )
        embed.set_image(
            url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExejc5ZzFxZTN0bng4cjVmdjJ6NjE3b3FoOGtzaW9zd21vMTkzZTF4aCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wsOUK1nwE7gWCWvgj3/giphy.gif"
        )
        view = GameDMView()
        try:
            await interaction.user.send(embed=embed, view=view)
            await interaction.response.send_message(
                "📬 Check your DMs! Sent the game link there nya~",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I can't DM you! Please enable DMs from server members (Privacy Settings).",
                ephemeral=True
            )


class JoinGameLinkView(discord.ui.View):
    """View with a Join Game link button (random link)"""
    def __init__(self):
        super().__init__(timeout=None)
        link = random.choice(JOIN_LINKS)
        self.add_item(discord.ui.Button(
            label="Join Game",
            url=link,
            style=discord.ButtonStyle.link
        ))


# ===================== BOT EVENTS =====================

@bot.event
async def on_ready():
    logging.info(f"✅ Bot is ready! Logged in as {bot.user}")

    # Sync slash commands
    await bot.tree.sync()
    logging.info("✅ Slash commands synced!")

    # Register persistent views so they survive restarts
    bot.add_view(GameButtonsView())
    bot.add_view(JoinGameLinkView())

    # Setup channels in all guilds the bot is in
    if not bot.guilds:
        logging.warning("⚠️ Bot is not in any server! Invite the bot to a server first.")
    else:
        for guild in bot.guilds:
            logging.info(f"🔧 Setting up guild: {guild.name} (ID: {guild.id})")
            await setup_guild_channels(guild)

    logging.info("✅ Setup complete!")


async def setup_guild_channels(guild):
    """Create channels if they don't exist and send the embeds"""
    channel_names = ["game", "gemeral", "verify", "redeem"]
    channels = {}

    for name in channel_names:
        existing = discord.utils.get(guild.channels, name=name)
        if existing is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    send_messages=False,
                    read_messages=True,
                    view_channel=True
                )
            }
            channel = await guild.create_text_channel(name, overwrites=overwrites)
            channels[name] = channel
            logging.info(f"✅ Created channel #{name}")
        else:
            channels[name] = existing
            logging.info(f"✅ Found existing channel #{name}")

    # ─── Game channel ─────────────────────────────────
    game_ch = channels.get("game")
    if game_ch:
        # Embed 1: Game Condo 24/7 with 7 buttons
        embed1 = discord.Embed(
            title="Game Condo 24/7",
            description=(
                "**Click a Button To Join Game**\n"
                "**Game 24/7**\n"
                "**Bypass No Fucking banned**\n"
                "**Key : ** **```HelloWorld(\"Print\")```**"
            ),
            color=0xFDBF00  # 16632319
        )
        embed1.set_image(
            url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExc2duNWFtMGRuZGh4NzZmZ3YxMnVvNjF2bXY5enBvYXByM3BmOWJyNiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/lLGzvSHi8vrl6nRUlt/giphy.gif"
        )
        await game_ch.send(embed=embed1, view=GameButtonsView())

        # Embed 2: Game Condo with player count text + link button
        embed2 = discord.Embed(
            title="Game Condo 24/7",
            description="**Click a Button Join Game**\n**Game Player : make it random 20-100 player**",
            color=16632319
        )
        embed2.set_image(
            url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExejc5ZzFxZTN0bng4cjVmdjJ6NjE3b3FoOGtzaW9zd21vMTkzZTF4aCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wsOUK1nwE7gWCWvgj3/giphy.gif"
        )
        await game_ch.send(embed=embed2, view=JoinGameLinkView())

        logging.info("✅ Sent messages to #game")

    # ─── Redeem channel ────────────────────────────
    redeem_ch = channels.get("redeem")
    if redeem_ch:
        embed = discord.Embed(
            title="Redeem <:robux:1520275610998407278>",
            description=(
                "# Invite <:invite:1520275996748546210>\n"
                "**2 Invite <:invite:1520275996748546210> Redeem 80 <:robux:1520275610998407278>** \n"
                "**5 Invite <:invite:1520275996748546210> Redeem 400 <:robux:1520275610998407278>** \n"
                "**10 Invite <:invite:1520275996748546210> Redeem 800 <:robux:1520275610998407278>** \n"
                "# Boost <:nitro:1520276118739882115> \n"
                "**1 Boost <:nitro:1520276118739882115> Redeem 400 <:robux:1520275610998407278>** \n"
                "**2 Boost <:nitro:1520276118739882115> Redeem 1,000 <:robux:1520275610998407278>** \n"
                "**3 Boost <:nitro:1520276118739882115> Redeem 2,200 <:robux:1520275610998407278>** \n"
                "**5 Boost <:nitro:1520276118739882115> Redeem 4,500 <:robux:1520275610998407278>**"
            ),
            color=0xE4C3FF  # 14988799
        )
        embed.set_image(
            url="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExODlkbnI1bmp0aWRwNHM5a3plODM2cjRwazJsb3lubmNheXZkbjhpZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/lLGzvSHi8vrl6nRUlt/giphy.gif"
        )
        await redeem_ch.send(embed=embed)
        logging.info("✅ Sent message to #redeem")


async def reset_and_setup_channels(guild):
    """Delete existing channels and recreate them fresh with embeds"""
    channel_names = ["game", "gemeral", "verify", "redeem"]
    channels = {}

    # ── Delete existing channels ─────────────────────
    for name in channel_names:
        existing = discord.utils.get(guild.channels, name=name)
        if existing is not None:
            await existing.delete()
            logging.info(f"🗑️ Deleted channel #{name}")
            await asyncio.sleep(0.5)  # Rate-limit safety

    # ── Create fresh channels ────────────────────────
    for name in channel_names:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                read_messages=True,
                view_channel=True
            )
        }
        channel = await guild.create_text_channel(name, overwrites=overwrites)
        channels[name] = channel
        logging.info(f"✅ Created channel #{name}")
        await asyncio.sleep(0.5)

    # ─── Game channel ─────────────────────────────────
    game_ch = channels.get("game")
    if game_ch:
        embed1 = discord.Embed(
            title="Game Condo 24/7",
            description=(
                "**Click a Button To Join Game**\n"
                "**Game 24/7**\n"
                "**Bypass No Fucking banned**\n"
                "**Key : ** **```HelloWorld(\"Print\")```**"
            ),
            color=0xFDBF00
        )
        embed1.set_image(
            url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExc2duNWFtMGRuZGh4NzZmZ3YxMnVvNjF2bXY5enBvYXByM3BmOWJyNiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/lLGzvSHi8vrl6nRUlt/giphy.gif"
        )
        await game_ch.send(embed=embed1, view=GameButtonsView())

        embed2 = discord.Embed(
            title="Game Condo 24/7",
            description="**Click a Button Join Game**\n**Game Player : make it random 20-100 player**",
            color=16632319
        )
        embed2.set_image(
            url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExejc5ZzFxZTN0bng4cjVmdjJ6NjE3b3FoOGtzaW9zd21vMTkzZTF4aCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wsOUK1nwE7gWCWvgj3/giphy.gif"
        )
        await game_ch.send(embed=embed2, view=JoinGameLinkView())
        logging.info("✅ Sent messages to #game")

    # ─── Redeem channel ────────────────────────────
    redeem_ch = channels.get("redeem")
    if redeem_ch:
        embed = discord.Embed(
            title="Redeem <:robux:1520275610998407278>",
            description=(
                "# Invite <:invite:1520275996748546210>\n"
                "**2 Invite <:invite:1520275996748546210> Redeem 80 <:robux:1520275610998407278>** \n"
                "**5 Invite <:invite:1520275996748546210> Redeem 400 <:robux:1520275610998407278>** \n"
                "**10 Invite <:invite:1520275996748546210> Redeem 800 <:robux:1520275610998407278>** \n"
                "# Boost <:nitro:1520276118739882115> \n"
                "**1 Boost <:nitro:1520276118739882115> Redeem 400 <:robux:1520275610998407278>** \n"
                "**2 Boost <:nitro:1520276118739882115> Redeem 1,000 <:robux:1520275610998407278>** \n"
                "**3 Boost <:nitro:1520276118739882115> Redeem 2,200 <:robux:1520275610998407278>** \n"
                "**5 Boost <:nitro:1520276118739882115> Redeem 4,500 <:robux:1520275610998407278>**"
            ),
            color=0xE4C3FF
        )
        embed.set_image(
            url="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExODlkbnI1bmp0aWRwNHM5a3plODM2cjRwazJsb3lubmNheXZkbjhpZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/lLGzvSHi8vrl6nRUlt/giphy.gif"
        )
        await redeem_ch.send(embed=embed)
        logging.info("✅ Sent message to #redeem")


# ===================== SLASH COMMANDS =====================

@bot.tree.command(name="set", description="Configure bot settings (Owner/OP only)")
@app_commands.describe(
    action="What to do: addop / removeop / listop / setup",
    user="User to add/remove as OP (only for addop/removeop)"
)
async def set_command(
    interaction: discord.Interaction,
    action: str,
    user: discord.User = None
):
    """Admin command - only bot owner or OP users can use this"""
    # ── Permission check ──────────────────────────
    app_info = await bot.application_info()
    is_owner = interaction.user.id == app_info.owner.id
    is_op = interaction.user.id in OP_IDS

    if not (is_owner or is_op):
        await interaction.response.send_message(
            "❌ Only the bot owner or an OP can use this command!",
            ephemeral=True
        )
        return

    action_lower = action.lower().strip()

    # ── addop ────────────────────────────────────
    if action_lower == "addop":
        if user is None:
            await interaction.response.send_message(
                "❌ You must specify a user to add as OP!",
                ephemeral=True
            )
            return
        OP_IDS.add(user.id)
        await interaction.response.send_message(
            f"✅ Added {user.mention} as OP!",
            ephemeral=True
        )
        logging.info(f"OP added: {user} (ID: {user.id})")

    # ── removeop ────────────────────────────────
    elif action_lower == "removeop":
        if user is None:
            await interaction.response.send_message(
                "❌ You must specify a user to remove from OP!",
                ephemeral=True
            )
            return
        OP_IDS.discard(user.id)
        await interaction.response.send_message(
            f"✅ Removed {user.mention} from OP!",
            ephemeral=True
        )
        logging.info(f"OP removed: {user} (ID: {user.id})")

    # ── listop ──────────────────────────────────
    elif action_lower == "listop":
        if not OP_IDS:
            await interaction.response.send_message(
                "📋 No OP users configured.",
                ephemeral=True
            )
            return
        lines = [f"<@{uid}> (`{uid}`)" for uid in OP_IDS]
        await interaction.response.send_message(
            f"📋 **OP Users:**\n" + "\n".join(lines),
            ephemeral=True
        )

    # ── setup (delete old channels + recreate fresh) ─────
    elif action_lower == "setup":
        await interaction.response.send_message(
            "🔄 Resetting all channels — deleting old ones and recreating fresh!",
            ephemeral=True
        )
        for guild in bot.guilds:
            await reset_and_setup_channels(guild)
            break
        await interaction.followup.send(
            "✅ Full reset complete! All channels have been deleted and recreated with fresh embeds.",
            ephemeral=True
        )

    else:
        await interaction.response.send_message(
            "❌ Unknown action. Use: `addop`, `removeop`, `listop`, or `setup`",
            ephemeral=True
        )


@set_command.autocomplete("action")
async def set_action_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    actions = ["addop", "removeop", "listop", "setup"]
    return [
        app_commands.Choice(name=a, value=a)
        for a in actions if current.lower() in a.lower()
    ]


# ===================== RUN =====================

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logging.error("❌ Invalid token! Check your bot token.")
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
