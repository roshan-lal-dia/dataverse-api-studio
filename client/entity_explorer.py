"""
Entity Explorer Client - Comprehensive entity record exploration
Fetches all entity metadata, attribute values, relationships, and related records
"""

import requests
from typing import Dict, List, Optional, Any, Tuple
from client.metadata_client import MetadataClient


class EntityExplorer(MetadataClient):
    """Extended client for comprehensive entity record exploration"""
    
    def fetch_complete_entity_metadata(self, entity_name: str, use_cache: bool = True) -> Dict:
        """
        Fetch comprehensive entity metadata including attributes and all relationship types
        Args:
            entity_name: Logical name of the entity (e.g., 'lmdm_location')
            use_cache: Whether to use cached metadata
        Returns:
            {
                "success": bool,
                "entity": {
                    "LogicalName": str,
                    "DisplayName": str,
                    "SchemaName": str,
                    "EntitySetName": str,
                    "PrimaryIdAttribute": str,
                    "PrimaryNameAttribute": str
                },
                "attributes": [...],
                "relationships": {
                    "many_to_one": [...],
                    "one_to_many": [...],
                    "many_to_many": [...]
                }
            }
        """
        try:
            # Fetch entity definition
            url = f"{self.org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')"
            headers = self._get_headers()
            
            params = {
                "$select": "LogicalName,DisplayName,SchemaName,EntitySetName,PrimaryIdAttribute,PrimaryNameAttribute",
                "$expand": (
                    "Attributes($select=LogicalName,DisplayName,SchemaName,AttributeType,RequiredLevel,"
                    "IsValidForCreate,IsValidForUpdate,Description,MaxLength,Format,PrecisionSource,MaxValue,MinValue),"
                    "ManyToOneRelationships($select=ReferencedEntity,ReferencedAttribute,ReferencingAttribute,SchemaName,"
                    "ReferencedEntityNavigationPropertyName,ReferencingEntityNavigationPropertyName,IsCustomRelationship),"
                    "OneToManyRelationships($select=ReferencedEntity,ReferencedAttribute,ReferencingAttribute,ReferencingEntity,SchemaName,"
                    "ReferencingEntityNavigationPropertyName,ReferencedEntityNavigationPropertyName,IsCustomRelationship),"
                    "ManyToManyRelationships($select=Entity1LogicalName,Entity2LogicalName,IntersectEntityName,Entity1NavigationPropertyName,"
                    "Entity2NavigationPropertyName,SchemaName,IsCustomRelationship)"
                )
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "success": True,
                    "entity": {
                        "LogicalName": data.get("LogicalName"),
                        "DisplayName": data.get("DisplayName", {}).get("UserLocalizedLabel", {}).get("Label", ""),
                        "SchemaName": data.get("SchemaName"),
                        "EntitySetName": data.get("EntitySetName"),
                        "PrimaryIdAttribute": data.get("PrimaryIdAttribute"),
                        "PrimaryNameAttribute": data.get("PrimaryNameAttribute")
                    },
                    "attributes": data.get("Attributes", []),
                    "relationships": {
                        "many_to_one": data.get("ManyToOneRelationships", []),
                        "one_to_many": data.get("OneToManyRelationships", []),
                        "many_to_many": data.get("ManyToManyRelationships", [])
                    }
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error fetching metadata: {str(e)}"}
    
    def fetch_record_with_attributes(self, entity_name: str, record_id: str, 
                                    attribute_list: Optional[List[str]] = None) -> Dict:
        """
        Fetch a single record with specified attributes
        Args:
            entity_name: Logical name of the entity
            record_id: GUID of the record
            attribute_list: Specific attributes to fetch (None = all)
        Returns:
            {
                "success": bool,
                "record": {...},
                "entity_set_name": str
            }
        """
        try:
            # Get entity set name
            entity_set = self.get_entity_set_name(entity_name)
            if not entity_set:
                return {"success": False, "error": f"Entity '{entity_name}' not found"}
            
            url = f"{self.org_url}/api/data/v9.2/{entity_set}({record_id})"
            headers = self._get_headers()
            
            params = {}
            if attribute_list:
                params["$select"] = ",".join(attribute_list)
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "record": response.json(),
                    "entity_set_name": entity_set
                }
            elif response.status_code == 404:
                return {"success": False, "error": f"Record with ID '{record_id}' not found"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error fetching record: {str(e)}"}
    
    def fetch_related_records(self, entity_name: str, record_id: str, 
                             relationship_name: str, nav_property: str,
                             attributes: Optional[List[str]] = None,
                             max_records: int = 100) -> Dict:
        """
        Fetch related records through a relationship
        Args:
            entity_name: Logical name of the base entity
            record_id: GUID of the base record
            relationship_name: Name of the relationship
            nav_property: Navigation property name
            attributes: Specific attributes to fetch from related records
            max_records: Maximum records to return
        Returns:
            {
                "success": bool,
                "records": [...],
                "count": int
            }
        """
        try:
            entity_set = self.get_entity_set_name(entity_name)
            if not entity_set:
                return {"success": False, "error": f"Entity '{entity_name}' not found"}
            
            url = f"{self.org_url}/api/data/v9.2/{entity_set}({record_id})/{nav_property}"
            headers = self._get_headers()
            
            params = {
                "$top": max_records,
                "$count": True
            }
            
            if attributes:
                params["$select"] = ",".join(attributes)
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "records": data.get("value", []),
                    "count": data.get("@odata.count", len(data.get("value", [])))
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error fetching related records: {str(e)}"}
    
    def fetch_lookup_record_details(self, entity_name: str, record_id: str,
                                   primary_name_attr: str) -> Dict:
        """
        Fetch details of a lookup reference
        Args:
            entity_name: Logical name of the related entity
            record_id: GUID of the related record
            primary_name_attr: Primary name attribute of the entity
        Returns:
            {
                "success": bool,
                "name": str,
                "id": str,
                "entity": str,
                "record": {...}
            }
        """
        try:
            result = self.fetch_record_with_attributes(
                entity_name,
                record_id,
                [primary_name_attr, "statecode", "statuscode"]
            )
            
            if result.get("success"):
                record = result.get("record", {})
                return {
                    "success": True,
                    "name": record.get(primary_name_attr, "Unknown"),
                    "id": record_id,
                    "entity": entity_name,
                    "record": record
                }
            else:
                return result
        
        except Exception as e:
            return {"success": False, "error": f"Error fetching lookup details: {str(e)}"}
    
    def get_attribute_metadata_map(self, entity_name: str, use_cache: bool = True) -> Dict[str, Dict]:
        """
        Get a map of attribute logical names to their metadata
        Returns: Dict mapping LogicalName -> attribute metadata dict
        """
        result = self.fetch_entity_attributes(entity_name, use_cache)
        
        if result.get("success"):
            attributes = result.get("attributes", [])
            return {
                attr.get("LogicalName"): attr
                for attr in attributes
                if attr.get("LogicalName")
            }
        
        return {}
    
    def get_relationship_display_name(self, relationship_metadata: Dict) -> str:
        """
        Extract display name from relationship metadata
        """
        schema_name = relationship_metadata.get("SchemaName", "")
        
        # Try to get display name from referenced/referencing entities
        if "ReferencedEntity" in relationship_metadata:
            return f"{relationship_metadata.get('ReferencedEntity')} (Lookup)"
        elif "Entity1LogicalName" in relationship_metadata:
            return f"{relationship_metadata.get('Entity1LogicalName')} ↔ {relationship_metadata.get('Entity2LogicalName')} (Many-to-Many)"
        elif "ReferencingEntity" in relationship_metadata:
            return f"{relationship_metadata.get('ReferencingEntity')} (Related)"
        
        return schema_name or "Unknown Relationship"
    
    def extract_lookup_info_from_value(self, value: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract entity name and record ID from lookup value string
        Format: "/accounts(guid)" or similar
        Returns: (entity_name, record_id) or (None, None) if not a valid lookup
        """
        if not isinstance(value, str) or not value.startswith("/"):
            return None, None
        
        try:
            # Format: /entityset(guid)
            entity_part = value.split("(")[0].lstrip("/")
            id_part = value.split("(")[1].rstrip(")")
            return entity_part, id_part
        except (IndexError, AttributeError):
            return None, None
    
    def get_choice_display_value(self, options: List[Dict], value: int) -> str:
        """
        Get display label for a choice value
        Args:
            options: List of choice options from fetch_choice_options
            value: Integer value of the choice
        Returns:
            Display label or the value as string if not found
        """
        for opt in options:
            if opt.get("value") == value:
                return opt.get("label", str(value))
        
        return str(value)
    
    def format_attribute_value(self, attr_metadata: Dict, value: Any, 
                              lookup_entity: Optional[str] = None) -> Tuple[str, str]:
        """
        Format attribute value for display with type information
        Args:
            attr_metadata: Attribute metadata dict
            value: Raw attribute value
            lookup_entity: For lookup types, the referenced entity name
        Returns:
            (display_value, value_type_description)
        """
        if value is None or value == "":
            return "N/A", "Empty"
        
        attr_type = attr_metadata.get("AttributeType", "String")
        
        if attr_type == "Lookup":
            # Lookup values come as /entityset(guid)
            entity, guid = self.extract_lookup_info_from_value(str(value))
            if entity and guid:
                return f"{guid}", f"Lookup: {entity}"
            return str(value), "Lookup"
        
        elif attr_type == "Picklist":
            try:
                int_val = int(float(value))
                return str(int_val), f"Choice (ID: {int_val})"
            except:
                return str(value), "Choice"
        
        elif attr_type == "Boolean":
            bool_val = value in [True, "true", 1, "1"]
            return "Yes" if bool_val else "No", "Boolean"
        
        elif attr_type == "DateTime":
            return str(value), "DateTime"
        
        elif attr_type == "Decimal":
            try:
                return f"{float(value):.2f}", "Decimal"
            except:
                return str(value), "Decimal"
        
        elif attr_type == "Integer":
            try:
                return f"{int(value)}", "Integer"
            except:
                return str(value), "Integer"
        
        else:
            return str(value), attr_type
    
    def compare_entities(self, entity_name: str, record_ids: List[str]) -> Dict:
        """
        Compare multiple records of the same entity
        Returns a comparison matrix of attribute values
        """
        try:
            records = []
            for record_id in record_ids:
                result = self.fetch_record_with_attributes(entity_name, record_id)
                if result.get("success"):
                    records.append(result.get("record"))
                else:
                    records.append(None)
            
            return {
                "success": True,
                "records": records,
                "entity_name": entity_name,
                "count": len([r for r in records if r])
            }
        
        except Exception as e:
            return {"success": False, "error": f"Error comparing records: {str(e)}"}
