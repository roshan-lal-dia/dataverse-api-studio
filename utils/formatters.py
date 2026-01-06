"""
Data formatters for converting values to Dataverse-compatible formats
"""

import re
from datetime import datetime
from typing import Any, Optional


class DataFormatter:
    """Format data for Dataverse API consumption"""
    
    @staticmethod
    def format_string(value: Any) -> str:
        """Format as string"""
        if value is None or value == "":
            return ""
        return str(value).strip()
    
    @staticmethod
    def format_integer(value: Any) -> Optional[int]:
        """Format as integer"""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_decimal(value: Any) -> Optional[float]:
        """Format as decimal/float"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_boolean(value: Any) -> Optional[bool]:
        """Format as boolean"""
        if value is None or value == "":
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ('true', '1', 'yes', 'y'):
                return True
            elif value_lower in ('false', '0', 'no', 'n'):
                return False
        
        return None
    
    @staticmethod
    def format_date(value: Any) -> Optional[str]:
        """Format as date (YYYY-MM-DD)"""
        if value is None or value == "":
            return None
        
        try:
            # Try parsing various date formats
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            
            # Try common date formats
            formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(value), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def format_datetime(value: Any) -> Optional[str]:
        """Format as ISO 8601 datetime"""
        if value is None or value == "":
            return None
        
        try:
            # Try parsing various datetime formats
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(value), fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def format_guid(value: Any) -> Optional[str]:
        """Format GUID (remove braces, lowercase)"""
        if value is None or value == "":
            return None
        
        value_str = str(value).strip().strip('{}').lower()
        
        # Validate GUID pattern
        guid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
        
        if guid_pattern.match(value_str):
            return value_str
        
        return None
    
    @staticmethod
    def format_lookup(value: Any, entity_name: str) -> Optional[str]:
        """
        Format lookup field with @odata.bind
        Args:
            value: GUID or @odata.bind string
            entity_name: Target entity logical name (e.g., 'account')
        """
        if value is None or value == "":
            return None
        
        value_str = str(value).strip()
        
        # If already in @odata.bind format, return as-is
        if value_str.startswith('/') and '(' in value_str:
            return value_str
        
        # Extract GUID if present
        guid = DataFormatter.format_guid(value_str)
        
        if guid:
            return f"/{entity_name}s({guid})"
        
        return None
    
    @staticmethod
    def format_choice(value: Any) -> Optional[int]:
        """Format choice/picklist value as integer"""
        if value is None or value == "":
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def normalize_whitespace(value: str) -> str:
        """Normalize whitespace in string values"""
        if not value:
            return ""
        return " ".join(str(value).split())
