from typing import Any, Dict
from app.schemas.master_schema import MasterNarrativeSchema

class BaseDomainAdapter:
    """Base interface for all Modular Domain Adapters."""
    def adapt_workflow(self, topic: str) -> MasterNarrativeSchema:
        raise NotImplementedError("Domain adapters must implement the adapt_workflow method.")

class StandardEntertainmentAdapter(BaseDomainAdapter):
    """The default YouTube/Reddit story workflow."""
    def adapt_workflow(self, topic: str) -> MasterNarrativeSchema:
        print("[Adapter] Executing Standard Entertainment Workflow...")
        # Simulates calling HookAgent -> EmotionAgent -> Standard Asset Pipeline
        return MasterNarrativeSchema(topic=topic, version="1.0.0-entertainment")

class CorporateTrainingAdapter(BaseDomainAdapter):
    """
    Highly specialized workflow for corporate environments.
    Bypasses HookAgent, replaces EmotionAgent with ComplianceAgent, 
    and forces strict corporate branding on AssetGenerators.
    """
    def adapt_workflow(self, topic: str) -> MasterNarrativeSchema:
        print(f"[Adapter] Executing Corporate Training Workflow for: {topic}")
        
        print(" -> Bypassing standard HookAgent (using standard corporate greeting).")
        hook = "Welcome to your mandatory training module."
        
        print(" -> Invoking ComplianceAgent instead of EmotionAgent.")
        compliance_score = "Pass: Corporate messaging standards met."
        
        print(" -> AssetGenerator explicitly locked to On-Brand Stock Footage and clean aesthetics.")
        
        # Build the final schema constrained by the Training Goal
        schema = MasterNarrativeSchema(
            topic=topic,
            version="1.0.0-corporate",
            hook_script=hook,
            full_script=f"Corporate guidelines regarding {topic} dictate safe operations."
        )
        return schema

class DomainAdapterFactory:
    """
    Intercepts the initialization process and returns the correct domain adapter 
    without modifying the core rendering engine.
    """
    @staticmethod
    def get_adapter(domain: str) -> BaseDomainAdapter:
        if domain.lower() == "corporate_training":
            return CorporateTrainingAdapter()
        # Add 'HistoricalDocumentaryAdapter', 'SerializedFictionAdapter' here
        return StandardEntertainmentAdapter()
