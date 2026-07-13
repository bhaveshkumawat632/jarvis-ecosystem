import os
from faster_whisper import WhisperModel

def format_time(seconds):
    # Convert seconds to ASS time format: H:MM:SS.cs
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

class SubtitleEngine:
    def __init__(self, model_size="tiny.en"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
    def generate_ass(self, audio_path, output_ass, emotion="neutral"):
        color_map = {
            "fear": ("&H000000FF&", "😱"),    # Red
            "tension": ("&H000000FF&", "😨"), # Red
            "sadness": ("&H00FF0000&", "😢"), # Blue
            "excitement": ("&H0000FFFF&", "🔥"), # Yellow
            "happy": ("&H0000FFFF&", "😊"),    # Yellow
            "neutral": ("&H00FFFFFF&", "")     # White
        }
        
        primary_color, emoji = color_map.get(emotion, ("&H00FFFFFF&", ""))
        
        segments, info = self.model.transcribe(audio_path, word_timestamps=True)
        
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,140,{primary_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,4,5,10,10,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(output_ass, "w", encoding="utf-8") as f:
            f.write(ass_header)
            
            for segment in segments:
                for word in segment.words:
                    start = format_time(word.start)
                    end = format_time(word.end)
                    text = word.word.strip()
                    # Add emoji randomly or at end of phrase (just prepend to first word for simplicity if there's an emoji)
                    # For a bounce effect: start at scale 150%, shrink to 100% over 150ms
                    # {\fscx150\fscy150\t(0,150,\fscx100\fscy100)}
                    
                    dialogue = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\fscx150\\fscy150\\t(0,150,\\fscx100\\fscy100)}}{text} {emoji}\n"
                    f.write(dialogue)

if __name__ == "__main__":
    import sys
    engine = SubtitleEngine()
    if len(sys.argv) > 1:
        engine.generate_ass(sys.argv[1], "test.ass", "excitement")
