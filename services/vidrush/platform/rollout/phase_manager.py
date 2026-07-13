import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class RolloutPhaseManager:
    """Strictly enforces the Go-Live Phase Transition Gates."""
    def __init__(self):
        self.current_phase = "closed_alpha"
        self.metrics_state = {
            "workflow_completion_rate": 82.0,
            "render_failure_rate": 6.5,
            "infrastructure_margin": 45.0,
            "creator_satisfaction": 6.8
        }

    def attempt_phase_escalation(self, target_phase: str):
        logger.info("rollout_escalation_attempted", current=self.current_phase, target=target_phase)
        
        if target_phase == "controlled_beta":
            # HARD GATES FOR CLOSED ALPHA -> CONTROLLED BETA
            if self.metrics_state["workflow_completion_rate"] < 85.0:
                raise Exception("Escalation Denied: Workflow completion rate < 85%")
            if self.metrics_state["render_failure_rate"] > 5.0:
                raise Exception("Escalation Denied: Render failure rate > 5%")
            if self.metrics_state["creator_satisfaction"] < 7.0:
                raise Exception("Escalation Denied: Creator satisfaction < 7.0")
                
            self.current_phase = "controlled_beta"
            logger.info("rollout_escalated_successfully", new_phase=self.current_phase)
            return True

phase_manager = RolloutPhaseManager()
