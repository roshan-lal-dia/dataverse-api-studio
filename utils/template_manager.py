"""
Template Manager - Save and load CRUD/Batch operation templates
Supports placeholder syntax: ${variable_name}
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class TemplateManager:
    """Manage operation templates with placeholder support"""
    
    PLACEHOLDER_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self, templates_dir: Path):
        """Initialize template manager"""
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(exist_ok=True)
    
    def save_template(self, name: str, template_data: Dict) -> bool:
        """
        Save a template to disk
        Args:
            name: Template name (without .template.json extension)
            template_data: Dict containing template configuration
        Returns:
            True on success
        """
        try:
            # Ensure .template.json extension
            if not name.endswith('.template.json'):
                name = f"{name}.template.json"
            
            template_path = self.templates_dir / name
            
            # Add metadata
            template_data["_metadata"] = {
                "created": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)
            
            return True
        
        except Exception as e:
            return False
    
    def load_template(self, name: str) -> Optional[Dict]:
        """
        Load a template from disk
        Args:
            name: Template name (with or without extension)
        Returns:
            Template data dict or None
        """
        try:
            # Ensure .template.json extension
            if not name.endswith('.template.json'):
                name = f"{name}.template.json"
            
            template_path = self.templates_dir / name
            
            if not template_path.exists():
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception:
            return None
    
    def list_templates(self) -> List[str]:
        """
        List all available templates
        Returns:
            List of template names (without extension)
        """
        try:
            templates = []
            for file_path in self.templates_dir.glob("*.template.json"):
                # Remove .template.json extension
                name = file_path.stem.replace('.template', '')
                templates.append(name)
            
            return sorted(templates)
        
        except Exception:
            return []
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template
        Args:
            name: Template name
        Returns:
            True if deleted
        """
        try:
            if not name.endswith('.template.json'):
                name = f"{name}.template.json"
            
            template_path = self.templates_dir / name
            
            if template_path.exists():
                template_path.unlink()
                return True
            
            return False
        
        except Exception:
            return False
    
    def extract_placeholders(self, template_data: Dict) -> List[str]:
        """
        Extract all placeholders from template data
        Args:
            template_data: Template dict
        Returns:
            List of unique placeholder names
        """
        placeholders = set()
        
        # Convert dict to JSON string to search
        json_str = json.dumps(template_data)
        
        # Find all ${...} patterns
        matches = self.PLACEHOLDER_PATTERN.findall(json_str)
        placeholders.update(matches)
        
        return sorted(list(placeholders))
    
    def fill_placeholders(self, template_data: Dict, values: Dict[str, str]) -> Dict:
        """
        Replace placeholders with actual values
        Args:
            template_data: Template dict with placeholders
            values: Dict mapping placeholder names to values
        Returns:
            Template with filled values
        """
        # Convert to JSON string
        json_str = json.dumps(template_data)
        
        # Replace each placeholder
        for placeholder, value in values.items():
            pattern = f"${{{placeholder}}}"
            json_str = json_str.replace(pattern, str(value))
        
        # Convert back to dict
        return json.loads(json_str)
    
    def validate_template(self, template_data: Dict) -> tuple:
        """
        Validate template structure
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check required fields
            if "type" not in template_data:
                return False, "Template missing 'type' field"
            
            template_type = template_data.get("type")
            
            if template_type not in ["crud", "batch", "query"]:
                return False, f"Invalid template type: {template_type}"
            
            # Type-specific validation
            if template_type == "crud":
                if "operation" not in template_data:
                    return False, "CRUD template missing 'operation' field"
            
            elif template_type == "batch":
                if "operations" not in template_data:
                    return False, "Batch template missing 'operations' field"
            
            return True, ""
        
        except Exception as e:
            return False, str(e)
    
    def create_crud_template(self, operation: str, table_name: str, 
                            data: Dict, record_id: str = None) -> Dict:
        """
        Create a CRUD operation template
        Args:
            operation: CREATE, READ, UPDATE, DELETE
            table_name: Entity logical name
            data: JSON data (can include placeholders)
            record_id: Optional record ID for READ/UPDATE/DELETE
        """
        template = {
            "type": "crud",
            "operation": operation,
            "table_name": table_name,
            "data": data
        }
        
        if record_id:
            template["record_id"] = record_id
        
        return template
    
    def create_batch_template(self, operations: List[Dict]) -> Dict:
        """
        Create a batch operations template
        Args:
            operations: List of operation dicts
        """
        return {
            "type": "batch",
            "operations": operations
        }
    
    def create_query_template(self, table_name: str, filter_query: str = None,
                             select: List[str] = None, order_by: str = None,
                             top: int = 100) -> Dict:
        """
        Create a query template
        """
        template = {
            "type": "query",
            "table_name": table_name,
            "top": top
        }
        
        if filter_query:
            template["filter"] = filter_query
        if select:
            template["select"] = select
        if order_by:
            template["order_by"] = order_by
        
        return template
