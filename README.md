# Shady - Discord Learning Bot

A chaotic, funny Discord bot that learns from your messages (with permission) and responds spontaneously using AI. Features image analysis, community learning, and privacy-first design.

## ✨ Features

- **AI-Powered Responses**: Uses Llama 3.2 for generating funny, context-aware messages
- **Image Vision**: Analyzes images using LLaVA and responds with witty commentary (toggleable)
- **Learning System**: Learns from opted-in users to match your community's vibe
- **Privacy-First**: Only learns from users who explicitly opt-in
- **Random Responses**: Occasional spontaneous replies (configurable chance)
- **Bot Interactions**: Can respond to other bots for cross-bot conversations
- **Statistics**: View learning stats and top contributors
- **Data Management**: Owner commands to clear messages by date ranges
- **Owner Controls**: Administrative commands for bot management

## Prerequisites

1. **Ollama**: Must be installed and running on your system.
   - Download from [ollama.ai](https://ollama.ai)
   - `ollama serve`
   - `ollama pull llama3.2:3b` (main model)
   - `ollama pull llava` (for image vision)

2. **uv**: Recommended for Python environment management.
   - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

3. **Discord Bot Token**: Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)

## Setup

1. **Clone & Install**:
   ```bash
   git clone https://github.com/vorlie/chatbot
   cd chatbot
   uv sync
   ```

2. **Configure Environment**:
   Create a `.env` file:
   ```env
   DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
   RESPONSE_CHANCE=0.05  # Chance to respond randomly (0.05 = 5%)
   OLLAMA_MODEL=llama3.2:3b
   BOT_OWNER_ID=YOUR_DISCORD_USER_ID  # For admin commands
   ```

3. **Run the Bot**:
   ```bash
   uv run bot.py
   ```

## Usage

### For Users

- **Opt-in to Learning**: `/allow_learning allow:True`
- **Check Privacy Status**: `/privacy_status`
- **View Bot Stats**: `/stats`

The bot will:
- Learn from your messages (if opted-in)
- Occasionally respond with funny messages
- Analyze images you post and comment on them
- Respond to mentions and other bots

### For Bot Owner

- **Pull Vision Model**: `/pull_vision_model` (downloads LLaVA)
- **Toggle Vision**: `/toggle_vision` (enable/disable image processing)
- **Vision Status**: `/vision_status` (check if vision is enabled)
- **Clear All Messages**: `/clear_all_messages`
- **Clear Messages Before Date**: `/clear_messages_before timestamp:2026-01-01`
- **Clear Messages After Date**: `/clear_messages_after timestamp:2026-01-01`

## How It Works

1. **Learning Phase**: Bot collects messages from opted-in users
2. **Context Building**: Uses recent chat history + learned messages for personality
3. **Response Generation**: Llama 3.2 generates funny, relevant responses
4. **Image Analysis**: LLaVA processes images and incorporates them into responses
5. **Privacy Protection**: All data handling respects user opt-in preferences

## Configuration

- **Response Chance**: Adjust `RESPONSE_CHANCE` in `.env` (0.01-0.10 recommended)
- **Model Selection**: Change `OLLAMA_MODEL` for different AI personalities
- **Vision Model**: Automatically switches to LLaVA for image processing

## Privacy & Ethics

- Only learns from users who explicitly opt-in
- Images are processed locally (no external API calls)
- Owner can clear data at any time
- No data is shared or stored externally

## Performance

- **VRAM Usage**: ~6GB with both models loaded (on RX 7600)
- **Response Time**: Fast generation with local AI
- **Image Limits**: 1MB max per image for processing

## Contributing

Created by: iota (vorlie#614807913302851594)

Feel free to fork and modify! Just update the creator credit if you deploy your own version.
