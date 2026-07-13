import subprocess
import structlog
import shutil

logger = structlog.get_logger(__name__)

class GPUResourceManager:
    def __init__(self):
        self.cuda_available = self._detect_cuda()
        self.nvenc_available = self._detect_nvenc()

    def _detect_cuda(self) -> bool:
        if not shutil.which("nvidia-smi"):
            return False
        try:
            res = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            return res.returncode == 0
        except:
            return False

    def _detect_nvenc(self) -> bool:
        try:
            res = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
            return "hevc_nvenc" in res.stdout or "h264_nvenc" in res.stdout
        except:
            return False

    def get_vram_usage(self) -> dict:
        if not self.cuda_available:
            return {"status": "no_gpu"}
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"],
                capture_output=True, text=True
            )
            used, total = map(int, res.stdout.strip().split(", "))
            return {"used_mb": used, "total_mb": total, "percent": (used / total) * 100}
        except:
            return {"status": "error"}

    def wait_for_vram(self, required_mb: int = 2000):
        """Throttle renders if VRAM is overflowing."""
        import time
        while True:
            usage = self.get_vram_usage()
            if usage.get("status") in ["no_gpu", "error"]:
                break
            
            free_mb = usage["total_mb"] - usage["used_mb"]
            if free_mb >= required_mb:
                break
                
            logger.warning("vram_overflow_waiting", free_mb=free_mb, required=required_mb)
            time.sleep(5)

gpu_manager = GPUResourceManager()
