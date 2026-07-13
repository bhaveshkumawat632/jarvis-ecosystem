import os
import hashlib
import structlog
import aiohttp
from configs.settings import ASSETS_DIR

logger = structlog.get_logger(__name__)

class AssetCache:
    def __init__(self):
        self.cache_dir = os.path.join(ASSETS_DIR, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_hash(self, url: str) -> str:
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    async def get_or_download(self, url: str, extension: str = ".mp4") -> str:
        file_hash = self._get_hash(url)
        cached_path = os.path.join(self.cache_dir, f"{file_hash}{extension}")
        
        if os.path.exists(cached_path):
            logger.info("asset_cache_hit", path=cached_path)
            return cached_path
            
        logger.info("asset_cache_miss_downloading", url=url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(cached_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        
        logger.info("asset_cached", path=cached_path)
        return cached_path

asset_cache = AssetCache()
