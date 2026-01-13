import ollama
import random

class BotBrain:
    def __init__(self, model="llama3.2"):
        self.model = model

    async def generate_response(self, context_messages, user_message=None):
        """
        Generates a response based on learned messages.
        If user_message is provided, it acts as a trigger/topic.
        """
        
        # Build the system prompt using learned context
        context_str = "\n".join([f"- {msg}" for msg in context_messages])
        
        system_prompt = f"""
You are a funny, slightly chaotic Discord bot. 
You learn from what users say. Here are some snippets of things you've learned lately:
{context_str}

Your goal is to send a short, funny message that fits the "vibe" of these messages. 
Don't be a generic assistant. Be a Discord user. 
Keep it short (1-2 sentences). 
Do not use emojis unless the learned messages use them.
Do not use quotation marks around your response.
"""

        prompt = "Say something funny based on what you've learned."
        if user_message:
            prompt = f"Someone just said: '{user_message}'. Respond to it in a funny way, reflecting the vibe of what you've learned."

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None

    def should_trigger(self, base_chance=0.05):
        """
        Determines if the bot should spontaneously send a message.
        base_chance 0.05 means 5% of the time.
        """
        return random.random() < base_chance
