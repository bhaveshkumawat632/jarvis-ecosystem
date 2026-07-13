from groq import Groq
from configs.settings import GROQ_API_KEY

class ScriptAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        
    def write_script(self, topic: str, hook: str):
        prompt = f"""
        Write a highly engaging script for a YouTube video about '{topic}'.
        Start with this precise hook: "{hook}"
        
        The script MUST follow this exact structure:
        1. Hook (already provided, just include it)
        2. Buildup
        3. Conflict
        4. Reveal
        5. Ending
        6. CTA (Call To Action)
        
        Do NOT write scene directions. ONLY write the spoken narration text.
        Make it around 800 words total.
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

if __name__ == "__main__":
    agent = ScriptAgent()
    print(agent.write_script("I Found My Wife Secret Life", "I thought my wife was a normal accountant, until I found the hidden hard drive."))
