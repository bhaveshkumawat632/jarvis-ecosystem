from groq import Groq
from configs.settings import GROQ_API_KEY

class HookAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        
    def generate_hook(self, topic: str):
        prompt = f"""
        Generate ONLY the first 5 seconds of spoken hook for a YouTube video about: '{topic}'.
        Make it high-tension and immediately shocking.
        Do not write anything else. Just the hook sentence. Maximum 10 words.
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        return response.choices[0].message.content.strip()

if __name__ == "__main__":
    agent = HookAgent()
    print(agent.generate_hook("I Found My Wife Secret Life"))
