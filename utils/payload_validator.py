"""
Payload Validator - Preflight validation layer
Validates payloads against metadata before sending to API
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class RequiredLevel(str, Enum):
    """Required level enum for field validation"""
    NONE = "None"
    APPLICATION_REQUIRED = "ApplicationRequired"
    SYSTEM_REQUIRED = "SystemRequired"
    RECOMMENDED = "Recommended"


class PayloadValidator:
    """Validate payloads against Dataverse metadata"""
    
    def __init__(self, metadata: Dict):
        """
        Initialize validator with entity metadata
        Args:
            metadata: Entity attributes metadata from MetadataClient
        """
        self.metadata = metadata
        self.attributes = {
            attr.get("LogicalName"): attr 
            for attr in metadata.get("attributes", [])
        }
    
    def validate_payload(self, payload: Dict, operation: str = "CREATE") -> Tuple[bool, List[str]]:
        """
        Validate a payload against metadata
        Args:
            payload: Data to validate
            operation: Operation type (CREATE, UPDATE)
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required fields (for CREATE only)
        if operation == "CREATE":
            required_errors = self._check_required_fields(payload)
            errors.extend(required_errors)
        
        # Validate field types
        type_errors = self._validate_field_types(payload)
        errors.extend(type_errors)
        
        # Check for invalid fields
        invalid_errors = self._check_invalid_fields(payload, operation)
        errors.extend(invalid_errors)
        
        return len(errors) == 0, errors
    
    def _check_required_fields(self, payload: Dict) -> List[str]:
        """Check if required fields are present"""
        errors = []
        
        for attr_name, attr_meta in self.attributes.items():
            required_level = attr_meta.get("RequiredLevel", {})
            
            # Check if field is required
            if isinstance(required_level, dict):
                value = required_level.get("Value", RequiredLevel.NONE.value)
                if value in [RequiredLevel.APPLICATION_REQUIRED.value, RequiredLevel.SYSTEM_REQUIRED.value]:
                    # Check if field is in payload
                    if attr_name not in payload and f"{attr_name}@odata.bind" not in payload:
                        display_name = self._get_display_name(attr_meta)
                        errors.append(f"Required field missing: {attr_name} ({display_name})")
        
        return errors
    
    def _validate_field_types(self, payload: Dict) -> List[str]:
        """Validate that field values match expected types"""
        errors = []
        
        for field_name, value in payload.items():
            # Skip @odata.bind fields
            if "@odata.bind" in field_name:
                base_field = field_name.replace("@odata.bind", "")
                if base_field in self.attributes:
                    # Validate lookup format
                    if not isinstance(value, str) or not value.startswith("/"):
                        errors.append(f"Invalid lookup format for {field_name}: must start with /")
                continue
            
            # Get attribute metadata
            if field_name not in self.attributes:
                continue
            
            attr_meta = self.attributes[field_name]
            attr_type = attr_meta.get("AttributeType", "")
            
            # Validate based on type
            type_error = self._validate_type(field_name, value, attr_type, attr_meta)
            if type_error:
                errors.append(type_error)
        
        return errors
    
    def _validate_type(self, field_name: str, value: Any, attr_type: str, attr_meta: Dict) -> Optional[str]:
        """Validate a single field's type"""
        if value is None:
            return None
        
        # String types
        if attr_type in ["String", "Memo"]:
            if not isinstance(value, str):
                return f"Field {field_name} expects String, got {type(value).__name__}"
            
            # Check max length if available
            max_length = attr_meta.get("MaxLength")
            if max_length and len(value) > max_length:
                return f"Field {field_name} exceeds max length {max_length}"
        
        # Integer types
        elif attr_type in ["Integer", "BigInt"]:
            if not isinstance(value, int):
                return f"Field {field_name} expects Integer, got {type(value).__name__}"
        
        # Decimal/Money types
        elif attr_type in ["Decimal", "Double", "Money"]:
            if not isinstance(value, (int, float)):
                return f"Field {field_name} expects Decimal, got {type(value).__name__}"
        
        # Boolean type
        elif attr_type == "Boolean":
            if not isinstance(value, bool):
                return f"Field {field_name} expects Boolean, got {type(value).__name__}"
        
        # DateTime types
        elif attr_type == "DateTime":
            if not isinstance(value, str):
                return f"Field {field_name} expects DateTime string, got {type(value).__name__}"
            # Could add format validation here
        
        # Picklist/Choice types
        elif attr_type in ["Picklist", "State", "Status"]:
            if not isinstance(value, int):
                return f"Field {field_name} expects Integer (choice value), got {type(value).__name__}"
        
        # Lookup types
        elif attr_type == "Lookup":
            # Should be handled via @odata.bind
            return f"Field {field_name} is a lookup and should use @odata.bind suffix"
        
        return None
    
    def _check_invalid_fields(self, payload: Dict, operation: str) -> List[str]:
        """Check for fields that cannot be created/updated"""
        errors = []
        
        for field_name in payload.keys():
            # Skip @odata.bind fields
            if "@odata.bind" in field_name:
                base_field = field_name.replace("@odata.bind", "")
                if base_field not in self.attributes:
                    errors.append(f"Unknown lookup field: {base_field}")
                continue
            
            # Check if field exists
            if field_name not in self.attributes:
                errors.append(f"Unknown field: {field_name}")
                continue
            
            attr_meta = self.attributes[field_name]
            
            # Check if valid for operation
            if operation == "CREATE":
                if not attr_meta.get("IsValidForCreate", False):
                    display_name = self._get_display_name(attr_meta)
                    errors.append(f"Field {field_name} ({display_name}) cannot be set on create")
            elif operation == "UPDATE":
                if not attr_meta.get("IsValidForUpdate", False):
                    display_name = self._get_display_name(attr_meta)
                    errors.append(f"Field {field_name} ({display_name}) cannot be updated")
        
        return errors
    
    def _get_display_name(self, attr_meta: Dict) -> str:
        """Extract display name from attribute metadata"""
        display_name_data = attr_meta.get("DisplayName", {})
        
        if isinstance(display_name_data, dict):
            user_label = display_name_data.get("UserLocalizedLabel", {})
            if isinstance(user_label, dict):
                label = user_label.get("Label", "")
                if label:
                    return label
        
        return attr_meta.get("LogicalName", "")
    
    def get_required_fields(self) -> List[Dict]:
        """Get list of required fields"""
        required = []
        
        for attr_name, attr_meta in self.attributes.items():
            required_level = attr_meta.get("RequiredLevel", {})
            
            if isinstance(required_level, dict):
                value = required_level.get("Value", RequiredLevel.NONE.value)
                if value in [RequiredLevel.APPLICATION_REQUIRED.value, RequiredLevel.SYSTEM_REQUIRED.value]:
                    required.append({
                        "logical_name": attr_name,
                        "display_name": self._get_display_name(attr_meta),
                        "type": attr_meta.get("AttributeType", ""),
                        "required_level": value
                    })
        
        return required
    
    def get_createable_fields(self) -> List[Dict]:
        """Get list of fields that can be set on create"""
        createable = []
        
        for attr_name, attr_meta in self.attributes.items():
            if attr_meta.get("IsValidForCreate", False):
                createable.append({
                    "logical_name": attr_name,
                    "display_name": self._get_display_name(attr_meta),
                    "type": attr_meta.get("AttributeType", "")
                })
        
        return createable
    
    def get_updateable_fields(self) -> List[Dict]:
        """Get list of fields that can be updated"""
        updateable = []
        
        for attr_name, attr_meta in self.attributes.items():
            if attr_meta.get("IsValidForUpdate", False):
                updateable.append({
                    "logical_name": attr_name,
                    "display_name": self._get_display_name(attr_meta),
                    "type": attr_meta.get("AttributeType", "")
                })
        
        return updateable
