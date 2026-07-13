from typing import List, Optional
import structlog

logger = structlog.get_logger(__name__)

class Clip:
    def __init__(self, file_path: str, start: float = 0, duration: float = None):
        self.file_path = file_path
        self.start = start
        self.duration = duration

class AudioLayer:
    def __init__(self, file_path: str, volume: float = 1.0, ducking: bool = False):
        self.file_path = file_path
        self.volume = volume
        self.ducking = ducking

class Transition:
    def __init__(self, type: str = "crossfade", duration: float = 1.0):
        self.type = type
        self.duration = duration

class Track:
    def __init__(self, type: str):
        self.type = type # 'video' or 'audio' or 'subtitle'
        self.clips: List[Clip] = []
        self.transitions: List[Transition] = []

class TimelineComposer:
    def __init__(self):
        self.video_track = Track("video")
        self.audio_tracks: List[AudioLayer] = []
        self.subtitle_track: Optional[Track] = None

    def add_video_clip(self, clip: Clip, transition: Optional[Transition] = None):
        self.video_track.clips.append(clip)
        if transition:
            self.video_track.transitions.append(transition)

    def add_audio_layer(self, layer: AudioLayer):
        self.audio_tracks.append(layer)

    def set_subtitles(self, clip: Clip):
        self.subtitle_track = Track("subtitle")
        self.subtitle_track.clips.append(clip)

    def compile_to_graph(self) -> dict:
        """Converts the Timeline Premiere-style logic into RenderGraph Nodes"""
        logger.info("timeline_composer_compiled", video_clips=len(self.video_track.clips), audio_layers=len(self.audio_tracks))
        return {
            "video_clips": [c.file_path for c in self.video_track.clips],
            "audio_layers": [{"path": a.file_path, "vol": a.volume, "duck": a.ducking} for a in self.audio_tracks],
            "subtitles": self.subtitle_track.clips[0].file_path if self.subtitle_track else None
        }
