import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from database import DatabaseManager
from brain import BotBrain
import aiohttp
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DiscordBot")

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RESPONSE_CHANCE = float(os.getenv("RESPONSE_CHANCE", 0.05))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))  # Replace with actual owner ID

class LearningBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read messages for learning
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

        # 1. Privacy First: Check if we should learn from this message
        is_opted_in = await self.db.is_opted_in(message.author.id)
        if is_opted_in:
            # Clean up message (strip pings etc maybe)
            content = message.clean_content
            if content.strip():
                await self.db.log_message(message.author.id, content)
                # logger.info(f"Learned from {message.author.name}")

        is_mentioned = self.user.mentioned_in(message) and not message.mention_everyone
        is_other_bot = message.author.id == 1336477279110561802  # Respond to miku
        random_roll = self.brain.should_trigger(self.response_chance)
        
        # Check for images (only if user is opted in for privacy)
        images = []
        if is_opted_in and message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status == 200:
                                    image_data = await resp.read()
                                    # Limit to 1MB to avoid issues
                                    if len(image_data) <= 1024 * 1024:
                                        b64_image = base64.b64encode(image_data).decode('utf-8')
                                        images.append(b64_image)
                                    else:
                                        logger.warning(f"Image too large from {message.author.name}: {len(image_data)} bytes")
                    except Exception as e:
                        logger.error(f"Error downloading image: {e}")
        
        # Combine them into one clear variable
        should_respond = is_mentioned or is_other_bot or random_roll or (len(images) > 0 and is_opted_in)

        if should_respond:
            context = await self.db.get_random_learned_messages(limit=15)
            
            # Fetch recent history for more context
            history = []
            try:
                # Fetch last 10 messages, excluding the current one
                async for msg in message.channel.history(limit=11):
                    if msg.id == message.id:
                        continue
                    # Format as "[Username]: [Message]"
                    history.append(f"{msg.author.name}: {msg.clean_content}")
                
                # Reverse to get chronological order (top to bottom)
                history.reverse()
            except Exception as e:
                logger.error(f"Error fetching history: {e}")

            if context:
                async with message.channel.typing():
                    response = await self.brain.generate_response(
                        context, 
                        conversation_history=history,
                        user_message=message.clean_content,
                        images=images if images else None
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

@bot.tree.command(name="clear_all_messages", description="⚠️ Delete ALL learned messages (owner only)")
async def clear_all_messages(interaction: discord.Interaction):
    # Check if user is bot owner
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("❌ You need to be the bot owner to use this command.", ephemeral=True)
        return
    
    await bot.db.clear_all_messages()
    await interaction.response.send_message("🧹 All learned messages have been cleared!", ephemeral=True)

@bot.tree.command(name="clear_messages_before", description="⚠️ Delete messages before a specific date (owner only)")
@app_commands.describe(timestamp="Timestamp in format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
async def clear_messages_before(interaction: discord.Interaction, timestamp: str):
    # Check if user is bot owner
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("❌ You need to be the bot owner to use this command.", ephemeral=True)
        return
    
    count = await bot.db.clear_messages_before(timestamp)
    await interaction.response.send_message(f"🧹 Deleted {count} messages from before {timestamp}!", ephemeral=True)

@bot.tree.command(name="clear_messages_after", description="⚠️ Delete messages after a specific date (owner only)")
@app_commands.describe(timestamp="Timestamp in format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
async def clear_messages_after(interaction: discord.Interaction, timestamp: str):
    # Check if user is bot owner
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("❌ You need to be the bot owner to use this command.", ephemeral=True)
        return
    
    count = await bot.db.clear_messages_after(timestamp)
    await interaction.response.send_message(f"🧹 Deleted {count} messages from after {timestamp}!", ephemeral=True)
@bot.tree.command(name="pull_vision_model", description="Pull the LLaVA vision model for image analysis (owner only)")
async def pull_vision_model(interaction: discord.Interaction):
    # Check if user is bot owner
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("❌ You need to be the bot owner to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer()
    try:
        import ollama
        await interaction.followup.send("🔄 Pulling LLaVA model... This may take a while.")
        ollama.pull("llava")
        await interaction.followup.send("✅ LLaVA model pulled successfully!")
    except Exception as e:
        await interaction.followup.send(f"❌ Error pulling model: {e}")
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("No discord token found in .env! Please set it.")
    else:
        bot.run(DISCORD_TOKEN)