"""
Dataverse Utilities - Smart formatting and conversion helpers
Provides utilities for common Dataverse field operations
"""

import re
from typing import Optional, Dict, List
from urllib.parse import quote, unquote


class DataverseUtilities:
    """Collection of utilities for Dataverse field handling"""
    
    # Common entity plural mappings
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
        'systemuser': 'systemusers',
        'role': 'roles',
        'businessunit': 'businessunits',
        'organization': 'organizations',
    }
    
    @staticmethod
    def format_lookup(guid: str, entity_name: str, field_name: Optional[str] = None) -> Dict[str, str]:
        """
        Format a lookup field with @odata.bind syntax
        Args:
            guid: GUID of target record
            entity_name: Singular name of target entity (e.g., 'account')
            field_name: Optional field name for validation
        Returns:
            Dict with formatted @odata.bind property
        """
        # Normalize GUID
        clean_guid = DataverseUtilities.normalize_guid(guid)
        plural = DataverseUtilities.get_plural_name(entity_name)
        
        return {
            f"{field_name or entity_name}id@odata.bind": f"/{plural}({clean_guid})"
        }
    
    @staticmethod
    def format_odata_bind(entity_name: str, guid: str) -> str:
        """
        Format OData bind string
        Args:
            entity_name: Singular entity name
            guid: GUID
        Returns:
            Formatted string: /entityname(guid)
        """
        plural = DataverseUtilities.get_plural_name(entity_name)
        clean_guid = DataverseUtilities.normalize_guid(guid)
        return f"/{plural}({clean_guid})"
    
    @staticmethod
    def get_plural_name(entity_singular: str) -> str:
        """
        Get plural name for an entity
        Args:
            entity_singular: Singular entity name
        Returns:
            Plural entity name
        """
        entity_lower = entity_singular.lower().strip()
        
        if entity_lower in DataverseUtilities.PLURAL_MAPPINGS:
            return DataverseUtilities.PLURAL_MAPPINGS[entity_lower]
        
        # Default: add 's'
        return f"{entity_lower}s"
    
    @staticmethod
    def normalize_guid(guid: str) -> str:
        """
        Normalize a GUID to standard format (8-4-4-4-12)
        Args:
            guid: GUID string (with or without hyphens)
        Returns:
            Normalized GUID
        """
        # Remove all non-hex characters
        clean = re.sub(r'[^0-9a-fA-F]', '', guid.strip())
        
        if len(clean) != 32:
            raise ValueError(f"Invalid GUID length: {guid}")
        
        # Reformat: 8-4-4-4-12
        return f"{clean[0:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:32]}".lower()
    
    @staticmethod
    def is_valid_guid(guid: str) -> bool:
        """Check if string is a valid GUID"""
        try:
            DataverseUtilities.normalize_guid(guid)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def format_table_name(table_name: str) -> str:
        """
        Get proper table name (plural form) from singular
        Args:
            table_name: Entity name
        Returns:
            Proper plural table name for API calls
        """
        return DataverseUtilities.get_plural_name(table_name)
    
    @staticmethod
    def extract_guid_from_odata_bind(odata_bind_value: str) -> Optional[str]:
        """
        Extract GUID from an @odata.bind value
        Args:
            odata_bind_value: String like '/accounts(guid)' or '/contacts(guid)'
        Returns:
            Extracted GUID or None
        """
        match = re.search(r'\(([a-f0-9\-]+)\)', odata_bind_value, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def extract_entity_from_odata_bind(odata_bind_value: str) -> Optional[str]:
        """
        Extract entity name from an @odata.bind value
        Args:
            odata_bind_value: String like '/accounts(guid)'
        Returns:
            Extracted entity name (plural) or None
        """
        match = re.match(r'^/([a-z]+)\(', odata_bind_value, re.IGNORECASE)
        if match:
            entity_plural = match.group(1)
            # Try to get singular form (reverse mapping)
            for singular, plural in DataverseUtilities.PLURAL_MAPPINGS.items():
                if plural.lower() == entity_plural.lower():
                    return singular
            return entity_plural.rstrip('s')  # Simple fallback
        return None
    
    @staticmethod
    def url_encode_special_chars(value: str) -> str:
        """
        URL encode special characters (for OData queries)
        Args:
            value: String value
        Returns:
            URL encoded string
        """
        return quote(value, safe='')
    
    @staticmethod
    def url_decode(value: str) -> str:
        """
        URL decode a string
        Args:
            value: URL encoded string
        Returns:
            Decoded string
        """
        return unquote(value)
    
    @staticmethod
    def sanitize_json_field_name(field_name: str) -> str:
        """
        Sanitize field name for JSON (remove special chars)
        Args:
            field_name: Field name
        Returns:
            Sanitized field name
        """
        # Convert to lowercase, remove special chars except underscore
        return re.sub(r'[^a-z0-9_]', '', field_name.lower())
    
    @staticmethod
    def is_lookup_field_syntax(field_value: str) -> bool:
        """
        Check if a value looks like @odata.bind syntax
        Args:
            field_value: Field value
        Returns:
            True if looks like /entity(guid) pattern
        """
        return bool(re.match(r'^/[a-z]+\([a-f0-9\-]+\)$', field_value, re.IGNORECASE))
    
    @staticmethod
    def infer_target_entity_from_field(field_name: str) -> Optional[str]:
        """
        Infer target entity from lookup field name
        Args:
            field_name: Field name (e.g., 'ownerid', 'parentaccountid')
        Returns:
            Inferred entity name or None
        """
        field_lower = field_name.lower()
        
        # Remove 'id' suffix
        if field_lower.endswith("id"):
            base = field_lower[:-2]
        else:
            base = field_lower
        
        # Remove underscores
        base = base.replace("_", "")
        
        # Common mappings
        mappings = {
            "owner": "user",
            "parentaccount": "account",
            "parent": "account",
            "company": "account",
            "account": "account",
            "contact": "contact",
            "transactioncurrency": "transactioncurrency",
            "businessunit": "businessunit",
            "team": "team",
            "user": "user",
            "systemuser": "user",
        }
        
        return mappings.get(base)
    
    @staticmethod
    def build_odata_filter(field_name: str, operator: str, value: str) -> str:
        """
        Build an OData filter expression
        Args:
            field_name: Field name
            operator: Operator (eq, contains, startswith, etc.)
            value: Filter value
        Returns:
            OData filter string
        """
        if operator == "eq":
            return f"{field_name} eq '{DataverseUtilities.url_encode_special_chars(value)}'"
        elif operator == "contains":
            return f"contains({field_name},'{DataverseUtilities.url_encode_special_chars(value)}')"
        elif operator == "startswith":
            return f"startswith({field_name},'{DataverseUtilities.url_encode_special_chars(value)}')"
        elif operator == "gt":
            return f"{field_name} gt {value}"
        elif operator == "lt":
            return f"{field_name} lt {value}"
        elif operator == "gte":
            return f"{field_name} ge {value}"
        elif operator == "lte":
            return f"{field_name} le {value}"
        elif operator == "neq":
            return f"{field_name} ne '{DataverseUtilities.url_encode_special_chars(value)}'"
        else:
            return f"{field_name} eq '{DataverseUtilities.url_encode_special_chars(value)}'"
    
    @staticmethod
    def get_entity_set_path(entity_name: str, record_id: Optional[str] = None) -> str:
        """
        Build entity set path for API calls
        Args:
            entity_name: Entity singular name
            record_id: Optional GUID
        Returns:
            Entity set path
        """
        plural = DataverseUtilities.get_plural_name(entity_name)
        if record_id:
            normalized_guid = DataverseUtilities.normalize_guid(record_id)
            return f"{plural}({normalized_guid})"
        return plural
