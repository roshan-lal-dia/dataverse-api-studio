"""
JSON Builder - Converts Excel data to Dataverse API JSON payloads
Handles datatype conversion, validation, and formatting
"""

import json
from typing import Dict, List, Any, Optional
from utils.validators import DataTypeValidator
from utils.formatters import DataFormatter


class JSONBuilder:
    """Build Dataverse API JSON payloads from Excel data"""
    
    # Datatype mappings
    DATAVERSE_TYPES = {
        "String": "string",
        "Integer": "integer",
        "Decimal": "decimal",
        "Boolean": "boolean",
        "Date": "date",
        "DateTime": "datetime",
        "Lookup": "lookup",
        "Choice": "choice",
        "Memo": "string"
    }
    
    def __init__(
        self,
        field_mappings: Dict[str, Dict],
        choice_mappings: Optional[Dict] = None,
        blank_handling: str = "skip_field",
        default_blank_value: Optional[str] = None,
        key_attribute: Optional[str] = None,
    ):
        """
        Initialize JSON builder
        Args:
            field_mappings: Dict mapping Excel column -> Dataverse field info
                           {"ExcelCol": {"field": "dvField", "type": "String"}, ...}
            choice_mappings: Optional dict for choice label->value mappings
                           {"dvField": {"Active": 1, "Inactive": 0}, ...}
            blank_handling: Policy for blank cells (skip_field | set_null | default_value | drop_row)
            default_blank_value: Value to use when blank_handling is "default_value"
            key_attribute: Dataverse field that must be present (used for upsert/key checks)
        """
        self.field_mappings = field_mappings
        self.choice_mappings = choice_mappings or {}
        self.blank_handling = blank_handling
        self.default_blank_value = default_blank_value
        self.key_attribute = key_attribute
        self.validator = DataTypeValidator()
        self.formatter = DataFormatter()
    
    def build_json_for_row(self, row_data: Dict) -> Dict:
        """
        Convert a single Excel row to Dataverse JSON payload
        Args:
            row_data: Dict with Excel column names as keys
        Returns:
            {"success": bool, "payload": Dict, "errors": List}
        """
        payload = {}
        errors = []
        
        for excel_col, field_info in self.field_mappings.items():
            # Skip if column not in row data
            if excel_col not in row_data:
                continue
            
            value = row_data[excel_col]
            is_blank = value is None or (isinstance(value, str) and value.strip() == "")
            
            if is_blank:
                if self.blank_handling == "drop_row":
                    errors.append(f"Blank value found for '{excel_col}' - row dropped")
                    return {"success": False, "payload": {}, "errors": errors}
                if self.blank_handling == "set_null":
                    dv_field = field_info.get("field")
                    if dv_field:
                        payload[dv_field] = None
                    continue
                if self.blank_handling == "default_value" and self.default_blank_value is not None:
                    value = self.default_blank_value
                else:
                    # skip_field behavior (default)
                    continue
            
            dv_field = field_info.get("field")
            dv_type = field_info.get("type", "String")
            
            # Convert based on type
            converted_value, error = self._convert_value(value, dv_type, dv_field)
            
            if error:
                errors.append(f"Column '{excel_col}': {error}")
            elif converted_value is not None:
                # Handle lookup fields (need @odata.bind suffix)
                if dv_type == "Lookup":
                    payload[f"{dv_field}@odata.bind"] = converted_value
                else:
                    payload[dv_field] = converted_value
        
        # Enforce key attribute presence when configured
        if self.key_attribute:
            key_field = self.key_attribute
            key_present = (
                key_field in payload or
                f"{key_field}@odata.bind" in payload
            )
            if not key_present:
                errors.append(f"Key attribute '{key_field}' is missing or blank")
        
        return {
            "success": len(errors) == 0,
            "payload": payload,
            "errors": errors
        }
    
    def build_json_for_all_rows(self, rows: List[Dict]) -> Dict:
        """
        Convert all Excel rows to Dataverse JSON payloads
        Returns:
            {"success": bool, "payloads": List[Dict], "errors": Dict}
        """
        payloads = []
        all_errors = {}
        
        for idx, row in enumerate(rows):
            result = self.build_json_for_row(row)
            
            if result["success"]:
                payloads.append(result["payload"])
            else:
                all_errors[f"Row {idx + 1}"] = result["errors"]
                # Still include payload with partial data
                payloads.append(result["payload"])
        
        return {
            "success": len(all_errors) == 0,
            "payloads": payloads,
            "errors": all_errors,
            "total_rows": len(rows),
            "valid_rows": len([p for p in payloads if p])
        }
    
    def _convert_value(self, value: Any, dv_type: str, field_name: str) -> tuple:
        """
        Convert value to appropriate Dataverse type
        Returns: (converted_value, error_message)
        """
        # Validate first
        is_valid, error_msg = self._validate_value(value, dv_type)
        
        if not is_valid:
            return None, error_msg
        
        # Convert based on type
        try:
            if dv_type == "String" or dv_type == "Memo":
                return self.formatter.format_string(value), None
            
            elif dv_type == "Integer":
                return self.formatter.format_integer(value), None
            
            elif dv_type == "Decimal":
                return self.formatter.format_decimal(value), None
            
            elif dv_type == "Boolean":
                return self.formatter.format_boolean(value), None
            
            elif dv_type == "Date":
                formatted = self.formatter.format_date(value)
                if formatted is None:
                    return None, "Invalid date format"
                return formatted, None
            
            elif dv_type == "DateTime":
                formatted = self.formatter.format_datetime(value)
                if formatted is None:
                    return None, "Invalid datetime format"
                return formatted, None
            
            elif dv_type == "Lookup":
                # Need entity name for lookup formatting
                # Extract from field_name (assuming pattern like "accountid" -> "account")
                entity_name = self._extract_entity_from_lookup(field_name)
                formatted = self.formatter.format_lookup(value, entity_name)
                if formatted is None:
                    return None, "Invalid GUID format"
                return formatted, None
            
            elif dv_type == "Choice":
                # Check if value is a label (string) that needs mapping
                if isinstance(value, str) and field_name in self.choice_mappings:
                    label_map = self.choice_mappings[field_name]
                    # Case-insensitive lookup
                    for label, choice_value in label_map.items():
                        if label.lower() == value.lower():
                            return choice_value, None
                    
                    return None, f"Choice label '{value}' not found in metadata"
                
                # Otherwise treat as integer value
                return self.formatter.format_choice(value), None
            
            else:
                return str(value), None
        
        except Exception as e:
            return None, str(e)
    
    def _validate_value(self, value: Any, dv_type: str) -> tuple:
        """
        Validate value against datatype
        Returns: (is_valid, error_message)
        """
        if dv_type == "String" or dv_type == "Memo":
            return self.validator.validate_string(value)
        elif dv_type == "Integer":
            return self.validator.validate_integer(value)
        elif dv_type == "Decimal":
            return self.validator.validate_decimal(value)
        elif dv_type == "Boolean":
            return self.validator.validate_boolean(value)
        elif dv_type == "Date":
            return self.validator.validate_date(value)
        elif dv_type == "DateTime":
            return self.validator.validate_datetime(value)
        elif dv_type == "Lookup":
            return self.validator.validate_lookup(value)
        elif dv_type == "Choice":
            return self.validator.validate_choice(value)
        else:
            return True, ""
    
    def _extract_entity_from_lookup(self, field_name: str) -> str:
        """
        Extract entity name from lookup field name
        Examples: accountid -> account, ownerid -> systemuser
        
        Note: This is a simplistic heuristic. For production use, fetch the target
        entity from metadata (NavigationProperty.ReferencedEntity) for accuracy.
        """
        # Simple heuristic: remove "id" suffix
        if field_name.endswith("id"):
            base = field_name[:-2]
            
            # Handle common special cases
            # TODO: Replace with metadata lookup for accuracy
            special_cases = {
                "owner": "systemuser",
                "parentcustomer": "account",
                "createdby": "systemuser",
                "modifiedby": "systemuser"
            }
            
            return special_cases.get(base, base)
        
        return field_name
    
    def get_json_preview(self, row_data: Dict) -> str:
        """
        Get formatted JSON preview for a single row
        """
        result = self.build_json_for_row(row_data)
        
        if result["success"]:
            return json.dumps(result["payload"], indent=2)
        else:
            return json.dumps({
                "payload": result["payload"],
                "errors": result["errors"]
            }, indent=2)
