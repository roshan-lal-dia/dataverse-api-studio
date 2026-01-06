"""
Configuration management for Dataverse API Studio
Loads environment variables and extracts available environments
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional


class Config:
    """Manage application configuration and environment variables"""
    
    def __init__(self, env_file: str = ".env"):
        """Initialize configuration from .env file"""
        self.env_file = env_file
        self._load_environment()
        
    def _load_environment(self):
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)
        if env_path.exists():
            load_dotenv(env_path)
    
    def get_tenant_id(self) -> Optional[str]:
        """Get Azure tenant ID"""
        return os.getenv("TENANT_ID")
    
    def get_client_id(self) -> Optional[str]:
        """Get Azure client ID"""
        return os.getenv("CLIENT_ID")
    
    def get_client_secret(self) -> Optional[str]:
        """Get Azure client secret"""
        return os.getenv("CLIENT_SECRET")
    
    def get_available_environments(self) -> Dict[str, str]:
        """
        Extract available environments from ORG_URL_* variables
        Returns: Dict mapping environment names to URLs
        Example: {"DEV": "https://org-dev.crm.dynamics.com", ...}
        """
        environments = {}
        
        for key, value in os.environ.items():
            if key.startswith("ORG_URL_"):
                env_name = key.replace("ORG_URL_", "")
                environments[env_name] = value
        
        return environments
    
    def get_org_url(self, environment: str) -> Optional[str]:
        """Get organization URL for specific environment"""
        return os.getenv(f"ORG_URL_{environment}")
    
    def get_cache_directory(self) -> Path:
        """Get cache directory path"""
        cache_dir = Path.cwd() / ".cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    def get_templates_directory(self) -> Path:
        """Get templates directory path"""
        templates_dir = Path.cwd() / "templates"
        templates_dir.mkdir(exist_ok=True)
        return templates_dir
