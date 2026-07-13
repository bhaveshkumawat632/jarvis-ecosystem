class RenderPresets:
    """Locked, known-good presets to guarantee alpha consistency."""
    
    PRESETS = {
        "reddit_story": {
            "pacing": "fast",
            "subtitle_style": "word_by_word_centered",
            "music_profile": "suspenseful_ambient",
            "visual_source": "gta_parkour_loop",
            "hook_structure": "curiosity_gap"
        },
        "horror_short": {
            "pacing": "slow_build",
            "subtitle_style": "fade_in_bottom",
            "music_profile": "eerie_drone",
            "visual_source": "dark_aesthetic_broll",
            "hook_structure": "disturbing_fact"
        },
        "motivational": {
            "pacing": "hyper_fast",
            "subtitle_style": "bold_yellow_stroke",
            "music_profile": "epic_orchestral",
            "visual_source": "luxury_lifestyle_loop",
            "hook_structure": "direct_challenge"
        }
    }
    
    @classmethod
    def get_preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Preset '{name}' is not authorized during closed alpha.")
        return cls.PRESETS[name]
