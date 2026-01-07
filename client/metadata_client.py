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
        
        except requests.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
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
        
        except requests.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def fetch_choice_options(self, entity_name: str, attribute_name: str, 
                            use_cache: bool = True) -> Dict:
        """
        Fetch choice/picklist options with labels and values
        Handles nested JSON structures robustly
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
                options = self._parse_choice_options(data)
                
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, options)
                
                return {"success": True, "options": options, "from_cache": False}
            else:
                return {"success": False, "error": response.text}
        
        except requests.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def _parse_choice_options(self, metadata: Dict) -> List[Dict]:
        """
        Parse choice options from nested JSON metadata structure
        Handles various formats and missing fields gracefully
        """
        options = []
        
        try:
            # Navigate nested structure
            option_set = metadata.get("OptionSet", {})
            raw_options = option_set.get("Options", [])
            
            for opt in raw_options:
                # Extract label with fallback logic
                label = self._extract_label(opt)
                
                # Extract value
                value = opt.get("Value")
                
                # Only add if we have both label and value
                if label and value is not None:
                    options.append({
                        "label": label,
                        "value": value,
                        "description": self._extract_description(opt)
                    })
        
        except Exception as e:
            # Log error but don't fail - return empty list
            print(f"Warning: Error parsing choice options: {str(e)}")
        
        return options
    
    def _extract_label(self, option: Dict) -> str:
        """Extract label from option with multiple fallback strategies"""
        # Try UserLocalizedLabel first
        label_data = option.get("Label", {})
        
        if isinstance(label_data, dict):
            user_localized = label_data.get("UserLocalizedLabel")
            if user_localized and isinstance(user_localized, dict):
                label = user_localized.get("Label", "")
                if label:
                    return label
            
            # Fallback to LocalizedLabels array
            localized_labels = label_data.get("LocalizedLabels", [])
            if localized_labels and isinstance(localized_labels, list) and len(localized_labels) > 0:
                first_label = localized_labels[0]
                if isinstance(first_label, dict):
                    label = first_label.get("Label", "")
                    if label:
                        return label
        
        # Last resort: use Value as label
        value = option.get("Value")
        if value is not None:
            return str(value)
        
        return ""
    
    def _extract_description(self, option: Dict) -> str:
        """Extract description from option if available"""
        desc_data = option.get("Description", {})
        
        if isinstance(desc_data, dict):
            user_localized = desc_data.get("UserLocalizedLabel")
            if user_localized and isinstance(user_localized, dict):
                return user_localized.get("Label", "")
        
        return ""
    
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
    
    def get_entity_set_name(self, entity_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Get EntitySetName (collection name) for an entity
        Args:
            entity_name: Logical name of the entity (e.g., 'opportunity')
            use_cache: Whether to use cached metadata
        Returns:
            EntitySetName (e.g., 'opportunities') or None if not found
        """
        result = self.fetch_entity_definitions(use_cache)
        
        if result.get("success"):
            entities = result.get("entities", [])
            for entity in entities:
                if entity.get("LogicalName") == entity_name:
                    return entity.get("EntitySetName")
        
        return None
    
    def get_entity_metadata_map(self, use_cache: bool = True) -> Dict[str, Dict]:
        """
        Get a map of entity logical names to their full metadata
        Returns: Dict mapping LogicalName -> entity metadata dict
        """
        result = self.fetch_entity_definitions(use_cache)
        
        if result.get("success"):
            entities = result.get("entities", [])
            return {
                e.get("LogicalName"): e 
                for e in entities 
                if e.get("LogicalName")
            }
        
        return {}
    
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
    
    def fetch_entity_relationships(self, entity_name: str, use_cache: bool = True) -> Dict:
        """
        Fetch relationship metadata for an entity (for navigation)
        Returns: {"success": bool, "relationships": List[Dict]}
        """
        cache_key = f"{self.org_url}/EntityDefinitions/{entity_name}/Relationships"
        
        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {"success": True, "relationships": cached_data, "from_cache": True}
        
        try:
            # Fetch both one-to-many and many-to-one relationships
            url = f"{self.org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')"
            headers = self._get_headers()
            
            params = {
                "$select": "LogicalName",
                # Include navigation property names for resolution when needed
                "$expand": (
                    "ManyToOneRelationships($select=ReferencedEntity,ReferencedAttribute,ReferencingAttribute,SchemaName,"
                    "ReferencedEntityNavigationPropertyName),"
                    "OneToManyRelationships($select=ReferencedEntity,ReferencedAttribute,ReferencingAttribute,ReferencingEntity,SchemaName,"
                    "ReferencingEntityNavigationPropertyName,ReferencedEntityNavigationPropertyName)"
                )
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                relationships = {
                    "many_to_one": data.get("ManyToOneRelationships", []),
                    "one_to_many": data.get("OneToManyRelationships", [])
                }
                
                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, relationships)
                
                return {"success": True, "relationships": relationships, "from_cache": False}
            else:
                return {"success": False, "error": response.text}
        
        except requests.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
