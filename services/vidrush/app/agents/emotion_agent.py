import json
from groq import Groq
from configs.settings import GROQ_API_KEY

class EmotionAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        
    def analyze(self, text_segment: str):
        prompt = f"""
        Analyze the following script segment and detect the primary emotion.
        Segment: "{text_segment}"
        
        Choose strictly from: fear, tension, sadness, excitement, neutral.
        Output MUST be valid JSON only:
        {{
            "emotion": "selected_emotion",
            "suggested_color": "red | yellow | blue | white",
            "zoom_effect": "fast_in | slow_in | none"
        }}
        (fear=red, excitement=yellow, sadness=blue, neutral=white)
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        import re
        from app.schemas.master_schema import EmotionOutput
        match = re.search(r"\{.*\}", content, re.DOTALL)
        try:
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(content)
            return EmotionOutput(**data).model_dump()
        except:
            fallback = {"emotion": "neutral", "suggested_color": "white", "zoom_effect": "none"}
            return EmotionOutput(**fallback).model_dump()

if __name__ == "__main__":
    agent = EmotionAgent()
    print(agent.analyze("I opened the hard drive and my blood ran cold."))
