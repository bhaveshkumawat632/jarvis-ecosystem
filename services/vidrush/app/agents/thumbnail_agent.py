from PIL import Image, ImageDraw, ImageFont
import os
from configs.settings import OUTPUT_DIR

class ThumbnailAgent:
    def generate_thumbnail(self, title: str, emotion: str):
        # Image dimensions 1280x720
        img = Image.new("RGB", (1280, 720), color=(15, 15, 15))
        draw = ImageDraw.Draw(img)
        
        # Color mapping based on emotion
        colors = {
            "fear": (255, 0, 0),
            "tension": (255, 50, 50),
            "sadness": (0, 100, 255),
            "excitement": (255, 200, 0),
            "neutral": (255, 255, 255)
        }
        main_color = colors.get(emotion, (255, 255, 255))
        
        # Draw a placeholder face ellipse in the center
        draw.ellipse([440, 160, 840, 560], fill=(50, 50, 50), outline=main_color, width=10)
        
        # We don't have an exact font file path, use default if PIL allows or draw standard text
        # For a real implementation, you'd load a TTF here: ImageFont.truetype("impact.ttf", 80)
        try:
            font = ImageFont.load_default() # Fallback
        except:
            font = None
            
        # Add bold text at the bottom
        short_title = title[:30] + ("..." if len(title) > 30 else "")
        draw.text((100, 600), short_title.upper(), fill=main_color, font=font, stroke_width=2, stroke_fill=(0,0,0))
        
        output_path = os.path.join(OUTPUT_DIR, f"thumbnail_{emotion}.jpg")
        img.save(output_path)
        return output_path

if __name__ == "__main__":
    agent = ThumbnailAgent()
    print("Thumbnail saved to:", agent.generate_thumbnail("Secret Life Revealed", "fear"))
