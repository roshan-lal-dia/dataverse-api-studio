"""
Data type validators for Dataverse fields
"""

import re
from datetime import datetime
from typing import Any, Tuple


class DataTypeValidator:
    """Validate data against Dataverse field types"""
    
    GUID_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    
    @staticmethod
    def validate_string(value: Any) -> Tuple[bool, str]:
        """Validate string type"""
        if value is None or value == "":
            return True, ""
        
        if not isinstance(value, str):
            return False, "Value must be a string"
        
        return True, ""
    
    @staticmethod
    def validate_integer(value: Any) -> Tuple[bool, str]:
        """Validate integer type"""
        if value is None or value == "":
            return True, ""
        
        try:
            int(value)
            return True, ""
        except (ValueError, TypeError):
            return False, "Value must be a valid integer"
    
    @staticmethod
    def validate_decimal(value: Any) -> Tuple[bool, str]:
        """Validate decimal/float type"""
        if value is None or value == "":
            return True, ""
        
        try:
            float(value)
            return True, ""
        except (ValueError, TypeError):
            return False, "Value must be a valid decimal number"
    
    @staticmethod
    def validate_boolean(value: Any) -> Tuple[bool, str]:
        """Validate boolean type"""
        if value is None or value == "":
            return True, ""
        
        if isinstance(value, bool):
            return True, ""
        
        if isinstance(value, str):
            if value.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
                return True, ""
        
        return False, "Value must be true/false or yes/no"
    
    @staticmethod
    def validate_date(value: Any) -> Tuple[bool, str]:
        """Validate date format (YYYY-MM-DD)"""
        if value is None or value == "":
            return True, ""
        
        try:
            datetime.strptime(str(value), "%Y-%m-%d")
            return True, ""
        except ValueError:
            return False, "Date must be in YYYY-MM-DD format"
    
    @staticmethod
    def validate_datetime(value: Any) -> Tuple[bool, str]:
        """Validate datetime format (ISO 8601)"""
        if value is None or value == "":
            return True, ""
        
        # Try multiple datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(str(value), fmt)
                return True, ""
            except ValueError:
                continue
        
        return False, "DateTime must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"
    
    @staticmethod
    def validate_guid(value: Any) -> Tuple[bool, str]:
        """Validate GUID format"""
        if value is None or value == "":
            return True, ""
        
        value_str = str(value).strip()
        
        # Remove braces if present
        value_str = value_str.strip('{}')
        
        if DataTypeValidator.GUID_PATTERN.match(value_str):
            return True, ""
        
        return False, "GUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    
    @staticmethod
    def validate_lookup(value: Any) -> Tuple[bool, str]:
        """Validate lookup field (GUID or @odata.bind format)"""
        if value is None or value == "":
            return True, ""
        
        value_str = str(value).strip()
        
        # Check if it's @odata.bind format
        if value_str.startswith('/') and '(' in value_str and ')' in value_str:
            # Extract GUID from format like "/accounts(guid)"
            # Use more specific regex to validate GUID format within parentheses
            guid_pattern = r'\(([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\)'
            guid_match = re.search(guid_pattern, value_str)
            if guid_match:
                guid = guid_match.group(1)
                return DataTypeValidator.validate_guid(guid)
            else:
                return False, "Invalid @odata.bind format: GUID not found or malformed"
        
        # Otherwise validate as plain GUID
        return DataTypeValidator.validate_guid(value_str)
    
    @staticmethod
    def validate_choice(value: Any, valid_values: list = None) -> Tuple[bool, str]:
        """Validate choice/picklist field"""
        if value is None or value == "":
            return True, ""
        
        # Choice values are integers
        try:
            int(value)
            
            # If valid_values provided, check membership
            if valid_values is not None and int(value) not in valid_values:
                return False, f"Value must be one of: {valid_values}"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Choice value must be an integer"
