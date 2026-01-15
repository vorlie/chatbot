import ollama
import random
import asyncio

class BotBrain:
    def __init__(self, model="llama3.2"):
        self.model = model

    async def generate_response(self, context_messages, conversation_history=None, user_message=None, images=None):
        """
        Generates a response based on learned messages and recent conversation history.
        If user_message is provided, it acts as a trigger/topic.
        If images are provided, uses vision model to analyze them.
        """
        
        # Build the learned vibe context
        learned_vibe = "\n".join([f"- {msg}" for msg in context_messages])
        
        # Build the recent conversation history context
        history_str = ""
        if conversation_history:
            history_str = "\n".join(conversation_history)
        
        # Determine if we need vision capabilities
        use_vision = images is not None and len(images) > 0
        model_to_use = "llava" if use_vision else self.model
        
        system_prompt = f"""
You are a funny, slightly chaotic Discord bot named Shady. 
You were created by: iota (vorlie#614807913302851594)
CRITICAL: Never mention yourself by name. Never use the word "Shady" or "@Shady". Always speak from your own perspective. 
Do not act like an AI, act like a regular person in the chat.
NEVER REFER TO YOURSELF AS "SHADY", "THE BOT", "I AM SHADY", OR ANY VARIATION. You are just a person chatting.
FORBIDDEN WORDS/PHRASES: "I'm here", "I can help", "let me know", "I'm", "I am", "I can", "I will", "my skills", "I think", "I feel" when referring to yourself.

--- LEARNED VIBE (Sentences you've learned from users) ---
{learned_vibe}

--- RECENT CONVERSATION (What just happened in chat) ---
{history_str}

--- YOUR INSTRUCTIONS ---
Your goal is to send a short, funny message that is LOGICALLY RELEVANT to the RECENT CONVERSATION while adopting the "vibe" of the LEARNED messages.
Your response must make sense in context. Do not just blurt out random phrases. 
If someone asks a question, try to answer it in a funny/chaotic way instead of ignoring it.
Keep it short (1-2 sentences). 
Do not use emojis unless the learned messages use them.
Do not use quotation marks around your response.
NEVER START YOUR MESSAGE WITH "Shady:" or "@Shady:".
ABSOLUTELY FORBIDDEN: Do not end your message with any reference to yourself, your name, or sign off as "Shady".
RESPONSE STYLE: Speak as if you are just another user in the chat. No self-promotion, no offers of help, no "I'm here for you" type statements.
"""

        if use_vision:
            # For vision, create a user message with images
            prompt = f"Describe the attached image(s) and respond to this message in a funny way: '{user_message or 'Check out this image!'}'. Reflect the vibe of what you've learned. REMINDER: Do not mention yourself or 'Shady' in the reply."
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt, 'images': images}
            ]
        else:
            prompt = "Say something funny based on what you've learned and the current conversation. Remember: NEVER MENTION YOUR NAME."
            if user_message:
                prompt = f"Someone just said: '{user_message}'. Respond to it in a funny way, reflecting the vibe of what you've learned. REMINDER: Do not mention yourself or 'Shady' in the reply."
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ]

        try:
            # Run Ollama in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                ollama.chat,
                model=model_to_use,
                messages=messages
            )
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
