"""
User-friendly error message formatter
Converts technical Dataverse errors to plain English explanations
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import quote


class ErrorFormatter:
    """Format Dataverse API errors into user-friendly messages"""
    
    # Common error patterns and their user-friendly explanations
    ERROR_PATTERNS = {
        r"Required attribute missing": {
            "title": "Missing Required Field",
            "message": "This field must be filled in before you can save.",
            "action": "Please fill in all required fields marked with (Required)"
        },
        r"PrimitiveValue.*null": {
            "title": "Field Cannot Be Empty",
            "message": "This field does not accept empty values.",
            "action": "Please enter a valid value for this field"
        },
        r"Invalid GUID": {
            "title": "Invalid ID Format",
            "message": "The ID format is incorrect. It should be a valid GUID.",
            "action": "Use format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        },
        r"(0x80048307|Not Found)": {
            "title": "Record Not Found",
            "message": "The record you're trying to update or delete does not exist.",
            "action": "Check the record ID and try again"
        },
        r"(0x80048404|Entity does not exist)": {
            "title": "Entity Not Found",
            "message": "This table/entity does not exist in Dataverse.",
            "action": "Check the table name (logical name) and try again"
        },
        r"(0x80048846|Invalid Lookup)": {
            "title": "Invalid Lookup Reference",
            "message": "The lookup value is incorrect or the referenced record doesn't exist.",
            "action": "Check the lookup format and ensure the reference ID exists"
        },
        r"(0x80048890|Invalid Choice)": {
            "title": "Invalid Choice/Option",
            "message": "The value selected is not a valid option for this field.",
            "action": "Select from the available choices for this field"
        },
        r"(decimal|Invalid value).*expected": {
            "title": "Invalid Value Type",
            "message": "The value doesn't match the expected data type.",
            "action": "Check the field type and enter a valid value"
        },
        r"(ReadableProperties|Does not have read permission)": {
            "title": "Permission Denied",
            "message": "You don't have permission to read this field.",
            "action": "Contact your administrator for access"
        },
        r"(WritableProperties|Does not have write permission)": {
            "title": "Read-Only Field",
            "message": "You cannot modify this field (it's read-only).",
            "action": "Remove this field from your data or contact your administrator"
        },
        r"Duplicate Record": {
            "title": "Duplicate Prevention",
            "message": "A record with this data already exists.",
            "action": "Check if the record exists or disable duplicate detection"
        }
    }
    
    @staticmethod
    def extract_field_name(error: str) -> str:
        """Extract field name from error message"""
        # Pattern: (FieldLogicalName)
        match = re.search(r'\(([a-z_][a-z0-9_]*)\)', error, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""
    
    @staticmethod
    def format_dataverse_error(error_msg: str, field_name: str = None) -> Dict:
        """
        Convert Dataverse error to user-friendly format
        
        Returns:
        {
            "title": str,
            "message": str,
            "field": str,
            "action": str,
            "detailed_info": str
        }
        """
        
        # Extract field if present
        if not field_name:
            field_name = ErrorFormatter.extract_field_name(error_msg)
        
        # Try to match against known patterns
        for pattern, response in ErrorFormatter.ERROR_PATTERNS.items():
            if re.search(pattern, error_msg, re.IGNORECASE):
                result = response.copy()
                if field_name:
                    result["field"] = field_name
                    result["message"] = f"{response['message']} (Field: {field_name})"
                result["detailed_info"] = error_msg
                return result
        
        # Fallback for unknown errors
        return {
            "title": "Validation Error",
            "message": "There was an issue with your data.",
            "action": "Check the detailed information below",
            "field": field_name,
            "detailed_info": error_msg
        }
    
    @staticmethod
    def format_validation_errors(errors: List[str]) -> List[Dict]:
        """Format multiple validation errors"""
        return [ErrorFormatter.format_dataverse_error(err) for err in errors]
    
    @staticmethod
    def create_user_friendly_message(errors: List[str], auto_corrections: List[str] = None) -> str:
        """
        Create a user-friendly error message combining multiple errors
        
        Args:
            errors: List of error messages
            auto_corrections: List of available autocorrections
            
        Returns:
            Formatted message suitable for display in UI
        """
        
        if not errors:
            return ""
        
        # Group errors by type
        formatted_errors = []
        for error in errors:
            if error.startswith("Warning:"):
                formatted_errors.append(("⚠️ " + error[8:].strip(), "warning"))
            else:
                result = ErrorFormatter.format_dataverse_error(error)
                formatted_errors.append((result["message"], "error"))
        
        # Build message
        lines = []
        
        error_section = [msg for msg, typ in formatted_errors if typ == "error"]
        warning_section = [msg for msg, typ in formatted_errors if typ == "warning"]
        
        if error_section:
            lines.append("❌ Issues Found:")
            for msg in error_section:
                lines.append(f"  • {msg}")
        
        if warning_section:
            lines.append("\n⚠️ Warnings:")
            for msg in warning_section:
                lines.append(f"  • {msg}")
        
        if auto_corrections:
            lines.append("\n✅ Auto-corrections available:")
            for correction in auto_corrections:
                lines.append(f"  ✓ {correction}")
        
        return "\n".join(lines)
    
    @staticmethod
    def url_encode_lookup(value: str, field_name: str = None) -> str:
        """
        URL-encode special characters for lookup/alternate key syntax
        
        Dataverse alternate key syntax requires URL encoding for special characters
        like @ in emails and . in field names.
        
        Args:
            value: The value to encode (e.g., email address)
            field_name: Optional field name for context
            
        Returns:
            URL-encoded value safe for Dataverse queries
            
        Examples:
            url_encode_lookup("john@example.com") -> "john%40example.com"
            url_encode_lookup("test.value") -> "test%2Evalue"
        """
        # URL encode special characters that are problematic in Dataverse
        encoded = quote(value, safe='')
        return encoded
    
    @staticmethod
    def suggest_lookup_format(field_value: str, field_name: str = None) -> Tuple[str, str]:
        """
        Suggest proper lookup formatting with @odata.bind
        
        Args:
            field_value: The GUID or alternate key value
            field_name: The logical name of the lookup field
            
        Returns:
            (suggestion: str, explanation: str)
        """
        
        # Check if it looks like a GUID
        guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(guid_pattern, field_value.lower()):
            entity_name = field_name.replace("id", "") if field_name else "entity"
            suggestion = f"/{entity_name}s({field_value})"
            explanation = f"Standard GUID lookup format for {field_name}"
            return suggestion, explanation
        
        # Check if it looks like an email (alternate key)
        if "@" in field_value:
            encoded = ErrorFormatter.url_encode_lookup(field_value)
            suggestion = f"/accounts(emailaddress1='{encoded}')"
            explanation = f"Alternate key format with URL-encoded email (@ → %40)"
            return suggestion, explanation
        
        # Check if it has special characters
        if any(c in field_value for c in "@ . , ; : / \\ ' \" "):
            encoded = ErrorFormatter.url_encode_lookup(field_value)
            suggestion = f"/entities({field_name}='{encoded}')"
            explanation = f"URL-encoded format for special characters"
            return suggestion, explanation
        
        return field_value, "Direct value (no encoding needed)"
    
    @staticmethod
    def validate_lookup_syntax(field_name: str, value: str, with_odata_bind: bool = True) -> Dict:
        """
        Validate and suggest corrections for lookup field values
        
        Returns:
        {
            "valid": bool,
            "value": str (corrected if needed),
            "suggestion": str,
            "explanation": str
        }
        """
        
        suggestion, explanation = ErrorFormatter.suggest_lookup_format(value, field_name)
        
        # Add @odata.bind if needed
        if with_odata_bind and "@odata.bind" not in value:
            final_value = suggestion
        else:
            final_value = suggestion
        
        return {
            "valid": True,
            "value": final_value,
            "suggestion": suggestion,
            "explanation": explanation
        }
