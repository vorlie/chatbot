# Discord Learning Bot

A bot that learns from your messages (with permission) and uses Llama 3.2 to send spontaneous, funny messages in the style of your community.

## Prerequisites

1. **Ollama**: Must be installed and running on your system.
   - `ollama serve`
   - `ollama pull llama3.2:3b`
2. **uv**: Recommended for python environment management.

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Configure Token**:
   Create a `.env` file (one has been created for you) and paste your Discord Bot Token:
   ```env
   DISCORD_TOKEN=YOUR_TOKEN_HERE
   RESPONSE_CHANCE=0.05
   OLLAMA_MODEL=llama3.2:3b
   ```

3. **Run the Bot**:
   ```bash
   uv run bot.py
   ```

## Usage

- Use `/allow_learning allow:True` in Discord to opt-in.
- Once enough messages are learned, the bot will occasionally respond to messages with something funny!
- Current chance is set to 5% (`0.05`) in `.env`.
