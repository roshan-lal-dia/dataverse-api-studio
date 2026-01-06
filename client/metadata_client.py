"""
Metadata Client - Extends DataverseClient with metadata fetching capabilities
Fetches entity definitions, field metadata, and choice option labels
"""

import requests
from typing import Dict, List, Optional
from client.dataverse_client import DataverseClient
from utils.schema_cache import SchemaCache


class MetadataClient(DataverseClient):
    """Extended client with metadata discovery capabilities"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 org_url: str, cache_dir=None):
        """Initialize with optional cache directory"""
        super().__init__(tenant_id, client_id, client_secret, org_url)
        self.cache = SchemaCache(cache_dir) if cache_dir else None
    
    def fetch_entity_definitions(self, use_cache: bool = True) -> Dict:
        """
        Fetch all entity definitions from Dataverse
        Returns: {"success": bool, "entities": List[Dict]}
        """
        cache_key = f"{self.org_url}/EntityDefinitions"
        
        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {"success": True, "entities": cached_data, "from_cache": True}
        
        try:
            url = f"{self.org_url}/api/data/v9.2/EntityDefinitions"
            headers = self._get_headers()
            
            # Select only needed properties for performance
            params = {
                "$select": "LogicalName,DisplayName,SchemaName,EntitySetName,PrimaryIdAttribute,PrimaryNameAttribute"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get("value", [])
                
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, entities)
                
                return {"success": True, "entities": entities, "from_cache": False}
            else:
                return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_entity_attributes(self, entity_name: str, use_cache: bool = True) -> Dict:
        """
        Fetch attribute metadata for a specific entity
        Returns: {"success": bool, "attributes": List[Dict]}
        """
        cache_key = f"{self.org_url}/EntityDefinitions/{entity_name}/Attributes"
        
        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {"success": True, "attributes": cached_data, "from_cache": True}
        
        try:
            url = f"{self.org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')/Attributes"
            headers = self._get_headers()
            
            # Select needed properties
            params = {
                "$select": "LogicalName,DisplayName,AttributeType,IsValidForCreate,IsValidForUpdate,RequiredLevel,SchemaName"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get("value", [])
                
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, attributes)
                
                return {"success": True, "attributes": attributes, "from_cache": False}
            else:
                return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_choice_options(self, entity_name: str, attribute_name: str, 
                            use_cache: bool = True) -> Dict:
        """
        Fetch choice/picklist options with labels and values
        Returns: {"success": bool, "options": [{"label": str, "value": int}, ...]}
        """
        cache_key = f"{self.org_url}/Choice/{entity_name}/{attribute_name}"
        
        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {"success": True, "options": cached_data, "from_cache": True}
        
        try:
            # First get the attribute metadata
            url = f"{self.org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')/Attributes(LogicalName='{attribute_name}')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
            headers = self._get_headers()
            
            params = {
                "$select": "LogicalName",
                "$expand": "OptionSet($select=Options)"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                option_set = data.get("OptionSet", {})
                raw_options = option_set.get("Options", [])
                
                # Extract label and value
                options = []
                for opt in raw_options:
                    label_data = opt.get("Label", {})
                    user_localized_label = label_data.get("UserLocalizedLabel", {})
                    label = user_localized_label.get("Label", "")
                    value = opt.get("Value")
                    
                    if label and value is not None:
                        options.append({"label": label, "value": value})
                
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, options)
                
                return {"success": True, "options": options, "from_cache": False}
            else:
                return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_entity_list(self, use_cache: bool = True) -> List[str]:
        """
        Get simplified list of entity logical names
        Returns: List of entity names (e.g., ['account', 'contact', ...])
        """
        result = self.fetch_entity_definitions(use_cache)
        
        if result.get("success"):
            entities = result.get("entities", [])
            return sorted([e.get("LogicalName", "") for e in entities if e.get("LogicalName")])
        
        return []
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalidate cached metadata
        Args:
            pattern: Optional pattern to match (default: clear all)
        """
        if self.cache:
            if pattern:
                # Invalidate specific key
                cache_key = f"{self.org_url}/{pattern}"
                self.cache.invalidate(cache_key)
            else:
                # Clear all cache
                self.cache.clear_all()
