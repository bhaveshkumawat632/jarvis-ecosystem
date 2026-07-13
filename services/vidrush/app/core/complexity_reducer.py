import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class ComplexityReducer:
    """Audits active microservices and agents, disabling any that do not generate measurable value."""
    def __init__(self):
        self.active_modules = ["NarrativeAgent", "VisualDirector", "AudiencePsychologist"]

    def audit_architecture(self):
        logger.info("complexity_audit_started")
        
        # Example logic finding an over-engineered layer
        value_metrics = {"AudiencePsychologist": 0.5} # Low value score
        
        for module, score in value_metrics.items():
            if score < 1.0:
                self.active_modules.remove(module)
                logger.warning("module_deprecated", module=module, reason="Failed measurable value audit")
                event_bus.publish_sync("COMPLEXITY_REDUCTION_APPLIED", payload={"removed": module})

reducer = ComplexityReducer()
