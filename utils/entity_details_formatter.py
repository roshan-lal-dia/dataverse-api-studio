"""
Entity Details Formatter - Format entity metadata and record data for display
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
import json


class EntityDetailsFormatter:
    """Format entity metadata and attribute values for display"""
    
    ATTRIBUTE_TYPE_ICONS = {
        "String": "📝",
        "Integer": "🔢",
        "Decimal": "💯",
        "Boolean": "✓",
        "DateTime": "📅",
        "Lookup": "🔗",
        "Picklist": "📋",
        "MultiSelectPicklist": "📊",
        "Owner": "👤",
        "Money": "💰",
        "BigInt": "📈",
        "ManagedProperty": "🛡️",
    }
    
    @staticmethod
    def format_attribute_row(attr_name: str, attr_metadata: Dict, attr_value: Any, 
                            choice_options: Dict = None) -> Dict[str, Any]:
        """
        Format a single attribute for display
        Returns a dict with formatted information
        """
        attr_type = attr_metadata.get("AttributeType", "String")
        display_name = attr_metadata.get("DisplayName", {})
        
        if isinstance(display_name, dict):
            display_name = display_name.get("UserLocalizedLabel", {}).get("Label", attr_name)
        
        required_level = attr_metadata.get("RequiredLevel", {})
        if isinstance(required_level, dict):
            required_level = required_level.get("Value", "None")
        
        icon = EntityDetailsFormatter.ATTRIBUTE_TYPE_ICONS.get(attr_type, "📌")
        
        # Format value based on type
        formatted_value, value_note = EntityDetailsFormatter._format_value(
            attr_type, attr_value, choice_options
        )
        
        return {
            "attribute_name": attr_name,
            "display_name": display_name,
            "type": attr_type,
            "type_icon": icon,
            "value": formatted_value,
            "value_note": value_note,
            "required": required_level != "None",
            "required_level": required_level,
            "is_valid_create": attr_metadata.get("IsValidForCreate", False),
            "is_valid_update": attr_metadata.get("IsValidForUpdate", False),
            "description": attr_metadata.get("Description", ""),
            "raw_value": attr_value,
        }
    
    @staticmethod
    def _format_value(attr_type: str, value: Any, choice_options: Dict = None) -> Tuple[str, str]:
        """Format attribute value based on type"""
        if value is None or value == "":
            return "∅", "Empty/Null"
        
        if attr_type == "Lookup":
            return EntityDetailsFormatter._format_lookup(value)
        
        elif attr_type in ["Picklist", "MultiSelectPicklist"]:
            return EntityDetailsFormatter._format_choice(value, choice_options)
        
        elif attr_type == "Boolean":
            bool_val = value in [True, "true", 1, "1", "T"]
            return ("✓ Yes" if bool_val else "✗ No"), "Boolean"
        
        elif attr_type == "DateTime":
            return str(value), "ISO 8601"
        
        elif attr_type == "Money":
            try:
                return f"${float(value):,.2f}", "Currency"
            except:
                return str(value), "Currency"
        
        elif attr_type == "Decimal":
            try:
                return f"{float(value):.4f}", "Decimal"
            except:
                return str(value), "Decimal"
        
        elif attr_type == "Integer" or attr_type == "BigInt":
            try:
                return f"{int(float(value)):,}", attr_type
            except:
                return str(value), attr_type
        
        else:
            return str(value)[:100], attr_type
    
    @staticmethod
    def _format_lookup(value: str) -> Tuple[str, str]:
        """Parse and format lookup value"""
        if not isinstance(value, str):
            return str(value), "Lookup"
        
        # Extract GUID and entity from format: /entityname(guid)
        try:
            if "/" in value and "(" in value:
                entity_part = value.split("(")[0].lstrip("/")
                id_part = value.split("(")[1].rstrip(")")
                return f"{id_part[:8]}... ({entity_part})", "Lookup Reference"
            else:
                return value, "Lookup"
        except:
            return value, "Lookup"
    
    @staticmethod
    def _format_choice(value: Any, choice_options: Dict = None) -> Tuple[str, str]:
        """Format choice/picklist value"""
        if choice_options:
            for opt in choice_options.get("options", []):
                if opt.get("value") == value or opt.get("value") == int(value) if isinstance(value, str) and value.isdigit() else False:
                    return opt.get("label", str(value)), "Choice"
        
        return str(value), "Choice (ID)"
    
    @staticmethod
    def format_relationship(rel_metadata: Dict, rel_type: str) -> Dict[str, Any]:
        """
        Format relationship metadata for display
        rel_type: 'many_to_one', 'one_to_many', or 'many_to_many'
        """
        schema_name = rel_metadata.get("SchemaName", "Unknown")
        is_custom = rel_metadata.get("IsCustomRelationship", False)
        
        if rel_type == "many_to_one":
            return {
                "type": "Many-to-One (Lookup)",
                "type_icon": "🔗",
                "schema_name": schema_name,
                "target_entity": rel_metadata.get("ReferencedEntity", "Unknown"),
                "target_attribute": rel_metadata.get("ReferencedAttribute", ""),
                "source_attribute": rel_metadata.get("ReferencingAttribute", ""),
                "nav_property": rel_metadata.get("ReferencingEntityNavigationPropertyName", ""),
                "description": f"Lookup to {rel_metadata.get('ReferencedEntity')}",
                "is_custom": is_custom,
            }
        
        elif rel_type == "one_to_many":
            return {
                "type": "One-to-Many (Related)",
                "type_icon": "1️⃣➡️🔢",
                "schema_name": schema_name,
                "source_entity": rel_metadata.get("ReferencingEntity", "Unknown"),
                "target_entity": rel_metadata.get("ReferencedEntity", "Unknown"),
                "target_attribute": rel_metadata.get("ReferencedAttribute", ""),
                "source_attribute": rel_metadata.get("ReferencingAttribute", ""),
                "nav_property": rel_metadata.get("ReferencingEntityNavigationPropertyName", ""),
                "description": f"{rel_metadata.get('ReferencingEntity')} records linked to this",
                "is_custom": is_custom,
            }
        
        elif rel_type == "many_to_many":
            return {
                "type": "Many-to-Many",
                "type_icon": "🔀",
                "schema_name": schema_name,
                "entity1": rel_metadata.get("Entity1LogicalName", "Unknown"),
                "entity2": rel_metadata.get("Entity2LogicalName", "Unknown"),
                "intersect_entity": rel_metadata.get("IntersectEntityName", ""),
                "entity1_nav_property": rel_metadata.get("Entity1NavigationPropertyName", ""),
                "entity2_nav_property": rel_metadata.get("Entity2NavigationPropertyName", ""),
                "description": f"Many-to-many link with {rel_metadata.get('Entity2LogicalName')}",
                "is_custom": is_custom,
            }
        
        return {}
    
    @staticmethod
    def generate_html_summary(entity_info: Dict, attributes_with_values: List[Dict], 
                             relationships: Dict) -> str:
        """
        Generate HTML summary for entity details
        """
        html = []
        html.append("<html><body style='font-family: Arial, sans-serif;'>")
        
        # Entity header
        entity = entity_info.get("entity", {})
        html.append(f"<h2>{entity.get('DisplayName', entity.get('LogicalName'))}</h2>")
        html.append(f"<p><strong>Entity:</strong> {entity.get('LogicalName')} | "
                   f"<strong>Set:</strong> {entity.get('EntitySetName')} | "
                   f"<strong>Primary ID:</strong> {entity.get('PrimaryIdAttribute')}</p>")
        
        # Attributes section
        html.append("<h3>📋 Attributes</h3>")
        html.append("<table border='1' style='border-collapse: collapse; width: 100%;'>")
        html.append("<tr style='background-color: #f2f2f2;'><th>Name</th><th>Type</th><th>Value</th><th>Notes</th></tr>")
        
        for attr in attributes_with_values:
            html.append(f"<tr>")
            html.append(f"<td><strong>{attr.get('attribute_name')}</strong><br/><small>{attr.get('display_name')}</small></td>")
            html.append(f"<td>{attr.get('type_icon')} {attr.get('type')}</td>")
            html.append(f"<td><code>{attr.get('value')}</code></td>")
            html.append(f"<td>{attr.get('value_note')}</td>")
            html.append(f"</tr>")
        
        html.append("</table>")
        
        # Relationships section
        if relationships.get("many_to_one") or relationships.get("one_to_many") or relationships.get("many_to_many"):
            html.append("<h3>🔗 Relationships</h3>")
            
            for rel_type, rels in relationships.items():
                if rels:
                    html.append(f"<h4>{rel_type.replace('_', ' ').title()}</h4>")
                    for rel in rels:
                        formatted_rel = EntityDetailsFormatter.format_relationship(rel, rel_type)
                        html.append(f"<p><strong>{formatted_rel.get('type_icon')} {formatted_rel.get('schema_name')}</strong>")
                        html.append(f" → {formatted_rel.get('description')}</p>")
        
        html.append("</body></html>")
        return "\n".join(html)
    
    @staticmethod
    def export_as_json(entity_info: Dict, record_data: Dict, attributes_with_values: List[Dict], 
                       relationships: Dict) -> str:
        """Export entity details as formatted JSON"""
        export = {
            "entity_metadata": entity_info.get("entity", {}),
            "record_id": record_data.get("id", ""),
            "attributes": {}
        }
        
        for attr in attributes_with_values:
            export["attributes"][attr["attribute_name"]] = {
                "display_name": attr["display_name"],
                "type": attr["type"],
                "value": attr["value"],
                "raw_value": attr["raw_value"],
                "value_note": attr["value_note"],
            }
        
        export["relationships"] = {
            "many_to_one": [
                EntityDetailsFormatter.format_relationship(r, "many_to_one")
                for r in relationships.get("many_to_one", [])
            ],
            "one_to_many": [
                EntityDetailsFormatter.format_relationship(r, "one_to_many")
                for r in relationships.get("one_to_many", [])
            ],
            "many_to_many": [
                EntityDetailsFormatter.format_relationship(r, "many_to_many")
                for r in relationships.get("many_to_many", [])
            ],
        }
        
        return json.dumps(export, indent=2, default=str)
