from abc import ABC, abstractmethod
from typing import Dict, Any

class PluginManifest:
    def __init__(self, name: str, version: str, author: str, target_hooks: list):
        self.name = name
        self.version = version
        self.author = author
        self.target_hooks = target_hooks

class BasePlugin(ABC):
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest

    @abstractmethod
    def register(self):
        """Called upon plugin load to hook into the EventBus or Orchestrator."""
        pass

class PluginLoader:
    def __init__(self):
        self.active_plugins: Dict[str, BasePlugin] = {}

    def load_plugin(self, plugin: BasePlugin):
        plugin.register()
        self.active_plugins[plugin.manifest.name] = plugin
        
plugin_loader = PluginLoader()
