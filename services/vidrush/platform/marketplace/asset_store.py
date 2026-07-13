import structlog

logger = structlog.get_logger(__name__)

class CreatorAssetStore:
    """Marketplace logic enabling creators to sell custom subtitle packs, VFX transitions, and AI presets."""
    def __init__(self):
        self.listed_assets = []

    def publish_asset(self, creator_id: str, asset_type: str, price: float, payload: dict):
        logger.info("marketplace_asset_published", creator=creator_id, type=asset_type, price=price)
        asset = {
            "creator_id": creator_id,
            "asset_type": asset_type, # "subtitle_style", "voice_clone", "timeline_template"
            "price": price,
            "payload": payload
        }
        self.listed_assets.append(asset)
        return {"status": "success", "asset_id": f"asset_{len(self.listed_assets)}"}

    def purchase_asset(self, buyer_id: str, asset_id: str):
        logger.info("creator_marketplace_purchased", buyer=buyer_id, asset=asset_id)
        # Handle 70/30 revenue split simulation
        return {"status": "purchased", "license_granted": True}

asset_store = CreatorAssetStore()
