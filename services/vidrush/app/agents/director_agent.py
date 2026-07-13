import json
from groq import Groq
from configs.settings import GROQ_API_KEY

class DirectorAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        
    def direct(self, topic: str):
        prompt = f"""
        You are an expert YouTube Director. Analyze the topic '{topic}' and decide the creative direction.
        Output MUST be valid JSON only, without any markdown:
        {{
            "emotion": "fear | tension | sadness | excitement | curiosity",
            "pace": "fast | medium | slow",
            "music": "cinematic | suspense | upbeat | ambient",
            "style": "documentary | reddit | fast_paced"
        }}
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        import re
        from app.schemas.master_schema import DirectorOutput
        match = re.search(r"\{.*\}", content, re.DOTALL)
        try:
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(content)
            return DirectorOutput(**data).model_dump()
        except:
            fallback = {"emotion": "excitement", "pace": "fast", "music": "upbeat", "style": "reddit"}
            return DirectorOutput(**fallback).model_dump()

if __name__ == "__main__":
    agent = DirectorAgent()
    print(agent.direct("I Found My Wife Secret Life"))
