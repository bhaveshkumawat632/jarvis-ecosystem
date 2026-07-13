import json
from groq import Groq
from configs.settings import GROQ_API_KEY

class SEOAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        
    def generate_seo_package(self, topic: str):
        prompt = f"""
        Act as an elite YouTube SEO expert. Generate a complete SEO package for a video about '{topic}'.
        Output MUST be valid JSON only:
        {{
            "title": "Ultra-viral CTR optimized title",
            "description": "500-word highly engaging description full of SEO keywords",
            "hashtags": ["#tag1", "#tag2", "... 30 hashtags total"],
            "tags": ["tag1", "tag2", "... 20 tags total"],
            "best_upload_time": "e.g., Friday 4:00 PM EST"
        }}
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        content = response.choices[0].message.content.strip()
        import re
        from app.schemas.master_schema import SEOOutput
        match = re.search(r"\{.*\}", content, re.DOTALL)
        try:
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(content)
            return SEOOutput(**data).model_dump()
        except:
            fallback = {"title": topic, "description": "Auto generated", "hashtags": ["#viral"], "tags": ["viral"], "best_upload_time": "Now"}
            return SEOOutput(**fallback).model_dump()

if __name__ == "__main__":
    agent = SEOAgent()
    print(agent.generate_seo_package("I Found My Wife Secret Life"))
