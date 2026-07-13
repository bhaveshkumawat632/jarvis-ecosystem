from typing import List
import subprocess
import structlog
import os

logger = structlog.get_logger(__name__)

class BaseNode:
    def __init__(self, file_path: str = None):
        self.file_path = file_path

class VideoNode(BaseNode):
    pass

class AudioNode(BaseNode):
    def __init__(self, file_path: str, volume: float = 1.0):
        super().__init__(file_path)
        self.volume = volume

class SubtitleNode(BaseNode):
    pass

class EffectNode(BaseNode):
    pass

class OverlayNode(BaseNode):
    pass

class TransitionNode(BaseNode):
    pass

class ExportNode:
    def __init__(self, output_path: str):
        self.output_path = output_path

class RenderGraph:
    def __init__(self):
        self.nodes: List[BaseNode] = []

    def add(self, node: BaseNode):
        self.nodes.append(node)

    def _check_cuda(self):
        try:
            res = subprocess.run(["ffmpeg", "-hide_banner", "-hwaccels"], capture_output=True, text=True)
            return "cuda" in res.stdout
        except:
            return False

    def compile(self) -> str:
        logger.info("render_graph_compile_started")
        
        inputs = []
        video_idx = -1
        audio_indices = []
        subtitle_path = None
        
        for node in self.nodes:
            if isinstance(node, VideoNode):
                inputs.extend(["-i", node.file_path])
                video_idx += 1
            elif isinstance(node, AudioNode):
                inputs.extend(["-i", node.file_path])
                video_idx += 1
                audio_indices.append((video_idx, node.volume))
            elif isinstance(node, SubtitleNode):
                subtitle_path = os.path.abspath(node.file_path)
            elif isinstance(node, ExportNode):
                self.output_path = node.output_path

        hwaccel = ["-hwaccel", "cuda"] if self._check_cuda() else []
        filter_complex = []
        
        # Audio mixing
        if len(audio_indices) > 0:
            audio_filters = []
            for i, vol in audio_indices:
                audio_filters.append(f"[{i}:a]volume={vol}[a{i}]")
            
            filter_complex.append(";".join(audio_filters))
            amix_inputs = "".join([f"[a{i}]" for i, _ in audio_indices])
            filter_complex.append(f"{amix_inputs}amix=inputs={len(audio_indices)}:duration=first:dropout_transition=2[aout]")
            audio_map = ["-map", "[aout]"]
        else:
            audio_map = []
            
        # Subtitles / Video
        if subtitle_path:
            ass_filter = f"ass='{subtitle_path}'"
            filter_complex.append(f"[0:v]{ass_filter}[vout]")
            video_map = ["-map", "[vout]"]
        else:
            video_map = ["-map", "0:v"]

        cmd = ["ffmpeg", "-y"] + hwaccel + inputs
        
        if filter_complex:
            cmd.extend(["-filter_complex", ";".join(filter_complex)])
            
        cmd.extend(video_map + audio_map)
        
        # Encoding flags
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            self.output_path
        ])

        logger.info("executing_ffmpeg_graph", cmd=" ".join(cmd))
        subprocess.run(cmd, check=True)
        logger.info("render_graph_compile_completed", output=self.output_path)
        return self.output_path
