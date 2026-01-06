"""
Plugin System - Lightweight plugin loader
Discovers and loads plugins from plugins/ folder
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
import traceback


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    module_path: Path
    module: Any = None
    error: Optional[str] = None


class PluginInterface:
    """Base interface that plugins should implement"""
    
    @staticmethod
    def get_plugin_info() -> Dict[str, str]:
        """
        Return plugin metadata
        Returns:
            {
                "name": "Plugin Name",
                "version": "1.0.0",
                "description": "Plugin description",
                "author": "Author Name"
            }
        """
        raise NotImplementedError
    
    @staticmethod
    def register_tabs(main_window) -> List[Any]:
        """
        Register custom tabs
        Args:
            main_window: MainWindow instance
        Returns:
            List of tab widgets to add
        """
        return []
    
    @staticmethod
    def register_actions(main_window) -> List[Any]:
        """
        Register custom menu actions
        Args:
            main_window: MainWindow instance
        Returns:
            List of QAction instances
        """
        return []
    
    @staticmethod
    def on_initialize(main_window):
        """
        Called when plugin is initialized
        Args:
            main_window: MainWindow instance
        """
        pass
    
    @staticmethod
    def on_client_connected(client):
        """
        Called when Dataverse client connects
        Args:
            client: MetadataClient instance
        """
        pass


class PluginManager:
    """Discover and manage plugins"""
    
    def __init__(self, plugins_dir: Path):
        """
        Initialize plugin manager
        Args:
            plugins_dir: Path to plugins directory
        """
        self.plugins_dir = plugins_dir
        self.plugins: List[PluginInfo] = []
        self.loaded_modules: Dict[str, Any] = {}
        
        # Ensure plugins directory exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Add plugins dir to path
        if str(self.plugins_dir) not in sys.path:
            sys.path.insert(0, str(self.plugins_dir))
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover all plugins in plugins directory
        Returns:
            List of PluginInfo objects
        """
        self.plugins = []
        
        # Look for Python files in plugins directory
        for plugin_file in self.plugins_dir.glob("*.py"):
            # Skip __init__.py and private files
            if plugin_file.name.startswith("_"):
                continue
            
            plugin_info = self._load_plugin(plugin_file)
            self.plugins.append(plugin_info)
        
        return self.plugins
    
    def _load_plugin(self, plugin_path: Path) -> PluginInfo:
        """
        Load a single plugin
        Args:
            plugin_path: Path to plugin file
        Returns:
            PluginInfo object
        """
        module_name = plugin_path.stem
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                return PluginInfo(
                    name=module_name,
                    version="0.0.0",
                    description="Failed to load",
                    author="Unknown",
                    module_path=plugin_path,
                    error="Invalid module spec"
                )
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get plugin info
            if hasattr(module, 'get_plugin_info'):
                info_dict = module.get_plugin_info()
                
                plugin_info = PluginInfo(
                    name=info_dict.get("name", module_name),
                    version=info_dict.get("version", "0.0.0"),
                    description=info_dict.get("description", "No description"),
                    author=info_dict.get("author", "Unknown"),
                    module_path=plugin_path,
                    module=module
                )
                
                self.loaded_modules[module_name] = module
                return plugin_info
            else:
                return PluginInfo(
                    name=module_name,
                    version="0.0.0",
                    description="Invalid plugin (missing get_plugin_info)",
                    author="Unknown",
                    module_path=plugin_path,
                    error="Missing get_plugin_info function"
                )
        
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            return PluginInfo(
                name=module_name,
                version="0.0.0",
                description="Failed to load",
                author="Unknown",
                module_path=plugin_path,
                error=error_msg
            )
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get list of successfully loaded plugins"""
        return [p for p in self.plugins if p.error is None]
    
    def get_failed_plugins(self) -> List[PluginInfo]:
        """Get list of failed plugins"""
        return [p for p in self.plugins if p.error is not None]
    
    def register_plugin_tabs(self, main_window) -> List[Any]:
        """
        Register tabs from all loaded plugins
        Args:
            main_window: MainWindow instance
        Returns:
            List of (tab_widget, tab_name) tuples
        """
        tabs = []
        
        for plugin in self.get_loaded_plugins():
            try:
                if hasattr(plugin.module, 'register_tabs'):
                    plugin_tabs = plugin.module.register_tabs(main_window)
                    tabs.extend(plugin_tabs)
            except Exception as e:
                print(f"Error registering tabs for plugin {plugin.name}: {str(e)}")
                traceback.print_exc()
        
        return tabs
    
    def register_plugin_actions(self, main_window) -> List[Any]:
        """
        Register menu actions from all loaded plugins
        Args:
            main_window: MainWindow instance
        Returns:
            List of QAction instances
        """
        actions = []
        
        for plugin in self.get_loaded_plugins():
            try:
                if hasattr(plugin.module, 'register_actions'):
                    plugin_actions = plugin.module.register_actions(main_window)
                    actions.extend(plugin_actions)
            except Exception as e:
                print(f"Error registering actions for plugin {plugin.name}: {str(e)}")
                traceback.print_exc()
        
        return actions
    
    def initialize_plugins(self, main_window):
        """
        Initialize all loaded plugins
        Args:
            main_window: MainWindow instance
        """
        for plugin in self.get_loaded_plugins():
            try:
                if hasattr(plugin.module, 'on_initialize'):
                    plugin.module.on_initialize(main_window)
            except Exception as e:
                print(f"Error initializing plugin {plugin.name}: {str(e)}")
                traceback.print_exc()
    
    def notify_client_connected(self, client):
        """
        Notify all plugins that client has connected
        Args:
            client: MetadataClient instance
        """
        for plugin in self.get_loaded_plugins():
            try:
                if hasattr(plugin.module, 'on_client_connected'):
                    plugin.module.on_client_connected(client)
            except Exception as e:
                print(f"Error notifying plugin {plugin.name}: {str(e)}")
                traceback.print_exc()
    
    def reload_plugins(self):
        """Reload all plugins (for development)"""
        # Clear loaded modules
        for module_name in list(self.loaded_modules.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        self.loaded_modules.clear()
        self.plugins.clear()
        
        # Rediscover
        self.discover_plugins()
