import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from database import DatabaseManager
from brain import BotBrain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DiscordBot")

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RESPONSE_CHANCE = float(os.getenv("RESPONSE_CHANCE", 0.05))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

class LearningBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.db = DatabaseManager()
        self.brain = BotBrain(model=OLLAMA_MODEL)
        self.response_chance = RESPONSE_CHANCE

    async def setup_hook(self):
        # Initialize database
        await self.db.initialize()
        # Sync slash commands
        await self.tree.sync()
        logger.info("Bot setup complete and slash commands synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return

        # 1. Privacy First: Check if user is opted-in
        is_opted_in = await self.db.is_opted_in(message.author.id)
        if is_opted_in:
            # Clean up message (strip pings etc maybe)
            content = message.clean_content
            if content.strip():
                await self.db.log_message(message.author.id, content)
                # logger.info(f"Learned from {message.author.name}")

        is_mentioned = self.user.mentioned_in(message) and not message.mention_everyone
        random_roll = self.brain.should_trigger(self.response_chance)
        
        # Combine them into one clear variable
        should_respond = is_mentioned or random_roll

        if should_respond:
            context = await self.db.get_random_learned_messages(limit=15)
            if context:
                async with message.channel.typing():
                    response = await self.brain.generate_response(
                        context, 
                        user_message=message.clean_content
                    )
                    
                    if response:
                        response = response.strip().strip('"').strip("'")
                        
                        # Use the logic from earlier to decide how to send it
                        if is_mentioned:
                            await message.reply(response)
                        else:
                            await message.channel.send(response)

        # Process prefix commands (if any)
        await self.process_commands(message)

bot = LearningBot()

@bot.tree.command(name="allow_learning", description="Allow or disallow the bot to learn from your messages (for funny responses)")
@app_commands.describe(allow="Set to True to let the bot learn from you, False to stop.")
async def allow_learning(interaction: discord.Interaction, allow: bool):
    await bot.db.set_opt_in(interaction.user.id, allow)
    status = "enabled" if allow else "disabled"
    msg = f"Learning has been **{status}** for your messages! Thank you for contributing to my brain."
    if not allow:
        msg = "I will no longer learn from your messages. Your privacy is respected!"
    
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="privacy_status", description="Check if the bot is currently learning from you")
async def privacy_status(interaction: discord.Interaction):
    is_opted_in = await bot.db.is_opted_in(interaction.user.id)
    status = "Learning is **active**" if is_opted_in else "Learning is **disabled**"
    await interaction.response.send_message(f"Current status: {status}", ephemeral=True)

@bot.tree.command(name="stats", description="Show bot learning statistics")
async def stats(interaction: discord.Interaction):
    opted_in, total_msgs, top_users = await bot.db.get_stats()
    embed = discord.Embed(
        title="🧠 Brain Statistics",
        color=discord.Color.blue()
    )
    leaderboard_lines = []
    for i, (user_id, count) in enumerate(top_users, 1):
        leaderboard_lines.append(f"**{i}.** <@{user_id}> — `{count} msgs`")
    leaderboard_text = "\n".join(leaderboard_lines) if leaderboard_lines else "No one yet."
    embed.description = f"**Top stupid morons of all time I've learned from:**\n{leaderboard_text}"
    embed.add_field(name="Opted-in Users", value=f"👤 `{opted_in}`", inline=True)
    embed.add_field(name="Total Memory", value=f"💬 `{total_msgs}`", inline=True)
    embed.set_footer(text=f"Requested by {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("No discord token found in .env! Please set it.")
    else:
        bot.run(DISCORD_TOKEN)