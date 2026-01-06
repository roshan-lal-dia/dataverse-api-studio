"""
Payload Validator - Preflight validation layer
Validates payloads against metadata before sending to API
Includes smart formatters for lookups, choices, and multi-value fields
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import re
from datetime import datetime


class RequiredLevel(str, Enum):
    """Required level enum for field validation"""
    NONE = "None"
    APPLICATION_REQUIRED = "ApplicationRequired"
    SYSTEM_REQUIRED = "SystemRequired"
    RECOMMENDED = "Recommended"


class PayloadValidator:
    """Validate payloads against Dataverse metadata"""
    
    # Common plural mappings for entity names
    PLURAL_MAPPINGS = {
        'account': 'accounts',
        'contact': 'contacts',
        'lead': 'leads',
        'opportunity': 'opportunities',
        'case': 'cases',
        'task': 'tasks',
        'appointment': 'appointments',
        'note': 'notes',
        'phonecall': 'phonecalls',
        'email': 'emails',
        'quote': 'quotes',
        'order': 'orders',
        'invoice': 'invoices',
        'product': 'products',
        'campaign': 'campaigns',
        'team': 'teams',
        'user': 'users',
        'role': 'roles',
        'businessunit': 'businessunits',
    }
    
    def __init__(self, metadata: Dict, entity_plural_name: Optional[str] = None):
        """
        Initialize validator with entity metadata
        Args:
            metadata: Entity attributes metadata from MetadataClient
            entity_plural_name: Optional plural name for the entity (e.g., 'accounts')
        """
        self.metadata = metadata
        self.entity_plural_name = entity_plural_name
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
    
    def autocorrect_payload(self, payload: Dict) -> Tuple[Dict, List[str]]:
        """
        Attempt to auto-correct common payload errors
        Returns corrected payload and list of corrections made
        """
        corrected = {}
        corrections = []
        
        for field_name, value in payload.items():
            if field_name not in self.attributes and "@odata.bind" not in field_name:
                # Keep unknown fields as-is
                corrected[field_name] = value
                continue
            
            # Handle @odata.bind fields (skip formatting)
            if "@odata.bind" in field_name:
                corrected[field_name] = value
                continue
            
            attr_meta = self.attributes.get(field_name, {})
            attr_type = attr_meta.get("AttributeType", "")
            
            # LOOKUP FIELD CORRECTION
            if attr_type == "Lookup":
                if isinstance(value, str) and (value.startswith("/") or "(" in value):
                    # Check if it's an alternate key lookup (has = in it)
                    if "=" in value and "(" in value:
                        # Alternate key syntax - this is actually valid for Dataverse!
                        # Just need to ensure it has @odata.bind
                        corrected_field = f"{field_name}@odata.bind"
                        corrected[corrected_field] = value
                        
                        corrections.append(
                            f"✅ Alternate key lookup fixed: '{field_name}' → '{corrected_field}'\n"
                            f"   Value: {value}\n"
                            f"   Note: URL encoding used for special characters (e.g., %40 for @, %27 for ')"
                        )
                    else:
                        # Regular GUID-based lookup
                        target_entity = self._infer_target_entity(field_name)
                        plural_name = self._get_plural_name(target_entity or "owner")
                        
                        # Extract GUID
                        guid = value.strip("/").replace("(", "").replace(")", "")
                        if "(" in guid or "/" in guid:
                            guid = guid.split("(")[-1].replace(")", "")
                        
                        # Clean GUID
                        guid = guid.strip()
                        
                        corrected_field = f"{field_name}@odata.bind"
                        corrected_value = f"/{plural_name}({guid})"
                        corrected[corrected_field] = corrected_value
                        
                        corrections.append(
                            f"✅ Lookup fixed: '{field_name}' → '{corrected_field}'\n"
                            f"   Value: {value} → {corrected_value}"
                        )
                    continue
                else:
                    corrected[field_name] = value
                    continue
            
            # Try to format based on type
            formatted_value, correction = self._autoformat_value(
                field_name, value, attr_type, attr_meta
            )
            
            if formatted_value is not None:
                corrected[field_name] = formatted_value
                if correction:
                    corrections.append(f"✅ {correction}")
            else:
                corrected[field_name] = value
        
        return corrected, corrections
    
    def format_lookup_field(self, field_name: str, guid: str, target_entity: str) -> Dict[str, str]:
        """
        Format a lookup field with @odata.bind syntax
        Args:
            field_name: The logical name of the lookup field
            guid: The GUID of the target record
            target_entity: The logical name of the target entity (singular)
        Returns:
            Dict with formatted @odata.bind property
        """
        # Get plural name from metadata or mapping
        plural_name = self._get_plural_name(target_entity)
        
        return {
            f"{field_name}@odata.bind": f"/{plural_name}({guid})"
        }
    
    def get_plural_name(self, entity_singular: str) -> str:
        """
        Get plural name for an entity
        Args:
            entity_singular: Singular entity name (e.g., 'account')
        Returns:
            Plural entity name (e.g., 'accounts')
        """
        return self._get_plural_name(entity_singular)
    
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
                        errors.append(f"Invalid lookup format for {field_name}: must start with / (e.g., /accounts(guid))")
                continue
            
            # Get attribute metadata
            if field_name not in self.attributes:
                continue
            
            attr_meta = self.attributes[field_name]
            attr_type = attr_meta.get("AttributeType", "")
            
            # Special handling for Lookup fields without @odata.bind
            if attr_type == "Lookup":
                # Check if value looks like it should be a lookup
                if isinstance(value, str) and (value.startswith("/") or "(" in value):
                    # User provided a lookup value but didn't use @odata.bind syntax
                    is_alternate_key = "=" in value and "(" in value  # e.g., /systemusers(systemuserid=...)
                    
                    if is_alternate_key:
                        errors.append(
                            f"LOOKUP SYNTAX ERROR: Field '{field_name}' uses alternate key syntax.\n"
                            f"  ⚠️  Current: \"{field_name}\": \"{value}\"\n"
                            f"  ℹ️  Note: Alternate key syntax requires URL encoding (@, . → %40, %2E)\n"
                            f"  ✅ Standard format: \"{field_name}@odata.bind\": \"/systemusers(guid)\""
                        )
                    else:
                        target_entity = self._infer_target_entity(field_name)
                        plural_name = self._get_plural_name(target_entity or "owner")
                        
                        # Extract GUID if present
                        guid = value.strip("/").replace("(", "").replace(")", "").split("(")[-1]
                        
                        errors.append(
                            f"LOOKUP SYNTAX ERROR: Field '{field_name}' is a lookup.\n"
                            f"  ❌ Current: \"{field_name}\": \"{value}\"\n"
                            f"  ✅ Correct: \"{field_name}@odata.bind\": \"/{plural_name}({guid})\""
                        )
                    continue
            
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
    
    def _autoformat_value(self, field_name: str, value: Any, attr_type: str, attr_meta: Dict) -> Tuple[Optional[Any], Optional[str]]:
        """
        Attempt to auto-format a value based on field type
        Returns (formatted_value, correction_message)
        """
        if value is None or value == "":
            return None, None
        
        # Boolean formatting
        if attr_type == "Boolean":
            if isinstance(value, bool):
                return value, None
            if isinstance(value, str):
                if value.lower() in ["true", "yes", "1", "on"]:
                    return True, f"{field_name}: converted '{value}' to True"
                elif value.lower() in ["false", "no", "0", "off"]:
                    return False, f"{field_name}: converted '{value}' to False"
            return None, None
        
        # Integer/Money formatting
        if attr_type in ["Integer", "BigInt", "Money", "Decimal", "Double"]:
            if isinstance(value, (int, float)):
                return value, None
            if isinstance(value, str):
                try:
                    if "." in value and attr_type in ["Money", "Decimal", "Double"]:
                        formatted = float(value)
                        return formatted, f"{field_name}: converted '{value}' to {formatted}"
                    else:
                        formatted = int(float(value))
                        return formatted, f"{field_name}: converted '{value}' to {formatted}"
                except (ValueError, TypeError):
                    return None, None
        
        # String trimming
        if attr_type in ["String", "Memo"]:
            if isinstance(value, str):
                trimmed = value.strip()
                if trimmed != value:
                    return trimmed, f"{field_name}: trimmed whitespace"
                return value, None
        
        # DateTime formatting
        if attr_type == "DateTime":
            if isinstance(value, str):
                # Try to parse and reformat
                try:
                    parsed = self._parse_datetime(value)
                    if parsed:
                        iso_str = parsed.isoformat() + "Z"
                        if iso_str != value:
                            return iso_str, f"{field_name}: formatted to ISO 8601"
                        return value, None
                except:
                    return None, None
        
        return None, None
    
    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """Parse various datetime formats"""
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_plural_name(self, entity_singular: str) -> str:
        """
        Get plural name for an entity
        Uses metadata if available, then falls back to mapping
        """
        if self.entity_plural_name:
            return self.entity_plural_name
        
        entity_lower = entity_singular.lower().strip()
        
        # Check mapping table first
        if entity_lower in self.PLURAL_MAPPINGS:
            return self.PLURAL_MAPPINGS[entity_lower]
        
        # Simple fallback: add 's'
        return f"{entity_lower}s"
    
    def suggest_lookup_format(self, field_name: str, raw_guid: str) -> str:
        """
        Suggest proper lookup format for a GUID
        Returns the formatted string with @odata.bind
        """
        # Clean up GUID (remove hyphens if present, standardize)
        clean_guid = raw_guid.strip().lower()
        clean_guid = clean_guid.replace("-", "")
        
        # Reformat with hyphens in proper positions: 8-4-4-4-12
        if len(clean_guid) == 32:
            guid_formatted = f"{clean_guid[0:8]}-{clean_guid[8:12]}-{clean_guid[12:16]}-{clean_guid[16:20]}-{clean_guid[20:32]}"
        else:
            guid_formatted = clean_guid
        
        # Try to infer target entity from field name
        # Common pattern: field_name = "ownerid" -> target = "owner"
        target_entity = self._infer_target_entity(field_name)
        if not target_entity:
            target_entity = "owner"  # Default fallback
        
        plural_name = self._get_plural_name(target_entity)
        return f"{field_name}@odata.bind:/{plural_name}({guid_formatted})"
    
    def _infer_target_entity(self, field_name: str) -> Optional[str]:
        """
        Infer target entity from lookup field name
        e.g., 'ownerid' -> 'owner', 'parentaccountid' -> 'account'
        """
        field_lower = field_name.lower()
        
        # Remove 'id' suffix
        if field_lower.endswith("id"):
            base = field_lower[:-2]
        else:
            base = field_lower
        
        # Remove common prefixes
        base = base.replace("_", "")
        
        # Check if matches known entity
        common_targets = {
            "owner": "user",
            "parentaccount": "account",
            "createdon": None,
            "modifiedon": None,
        }
        
        return common_targets.get(base)
