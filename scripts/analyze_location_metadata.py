#!/usr/bin/env python3
"""
Analyze lmdm_location_metadata.json to extract lookup fields and relationship navigation properties.
This script helps identify the correct field names and relationships for the custom-api-location.py script.
"""

import json
import re
from typing import Dict, List, Set

def analyze_metadata(json_file_path: str):
    """Analyze the metadata JSON file and extract lookup fields and relationships."""
    
    print("=" * 80)
    print("LMDM LOCATION METADATA ANALYSIS")
    print("=" * 80)
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entity_metadata = data.get('entity_metadata', {})
    
    # Extract lookup fields
    print("\n1. LOOKUP FIELDS (AttributeType: 'Lookup')")
    print("-" * 50)
    
    lookup_fields = []
    attributes = entity_metadata.get('Attributes', [])
    
    for attr in attributes:
        if attr.get('AttributeType') == 'Lookup':
            logical_name = attr.get('LogicalName', '')
            schema_name = attr.get('SchemaName', '')
            targets = attr.get('Targets', [])
            display_name = ''
            
            # Extract display name
            display_info = attr.get('DisplayName', {})
            if display_info and 'UserLocalizedLabel' in display_info:
                if display_info['UserLocalizedLabel']:
                    display_name = display_info['UserLocalizedLabel'].get('Label', '')
            
            lookup_fields.append({
                'logical_name': logical_name,
                'schema_name': schema_name,
                'display_name': display_name,
                'targets': targets
            })
    
    # Filter for LMDM custom fields (those starting with 'lmdm_')
    lmdm_lookup_fields = [f for f in lookup_fields if f['logical_name'].startswith('lmdm_')]
    
    print(f"Total lookup fields: {len(lookup_fields)}")
    print(f"LMDM custom lookup fields: {len(lmdm_lookup_fields)}")
    print("\nLMDM Custom Lookup Fields:")
    
    for field in sorted(lmdm_lookup_fields, key=lambda x: x['logical_name']):
        target_str = ', '.join(field['targets']) if field['targets'] else 'N/A'
        print(f"  • {field['logical_name']:<25} -> {target_str:<35} ({field['display_name']})")
    
    # Identify mentioned problematic fields
    problematic_fields = [
        'lmdm_assetlocationtype',
        'lmdm_channeltype', 
        'lmdm_storetrait',
        'lmdm_locationtype',
        'lmdm_brands',
        'lmdm_region',
        'lmdm_country',
        'lmdm_city'
    ]
    
    print(f"\n2. VALIDATION: Fields mentioned in custom-api-location.py")
    print("-" * 50)
    
    found_fields = []
    missing_fields = []
    
    for field_name in problematic_fields:
        found = any(f['logical_name'] == field_name for f in lmdm_lookup_fields)
        if found:
            found_fields.append(field_name)
            field_info = next(f for f in lmdm_lookup_fields if f['logical_name'] == field_name)
            print(f"  ✓ {field_name:<25} -> {', '.join(field_info['targets'])}")
        else:
            missing_fields.append(field_name)
            print(f"  ✗ {field_name:<25} -> NOT FOUND")
    
    # Extract relationship navigation properties
    print(f"\n3. RELATIONSHIP NAVIGATION PROPERTIES")
    print("-" * 50)
    
    one_to_many = entity_metadata.get('OneToManyRelationships', [])
    many_to_one = entity_metadata.get('ManyToOneRelationships', [])
    
    print(f"OneToManyRelationships: {len(one_to_many)}")
    print(f"ManyToOneRelationships: {len(many_to_one)}")
    
    # Business Hours and Key Personnel related relationships
    print(f"\n4. BUSINESS HOURS & PERSONNEL RELATED RELATIONSHIPS")
    print("-" * 50)
    
    business_hours_relationships = []
    personnel_relationships = []
    
    for rel in one_to_many:
        nav_prop = rel.get('ReferencedEntityNavigationPropertyName', '')
        referencing_entity = rel.get('ReferencingEntity', '')
        
        if any(keyword in nav_prop.lower() or keyword in referencing_entity.lower() 
               for keyword in ['businesshours', 'business_hours', 'hours']):
            business_hours_relationships.append({
                'nav_property': nav_prop,
                'referencing_entity': referencing_entity,
                'schema_name': rel.get('SchemaName', ''),
                'referencing_attribute': rel.get('ReferencingAttribute', '')
            })
        
        if any(keyword in nav_prop.lower() or keyword in referencing_entity.lower() 
               for keyword in ['personnel', 'staff', 'employee', 'manager']):
            personnel_relationships.append({
                'nav_property': nav_prop,
                'referencing_entity': referencing_entity,
                'schema_name': rel.get('SchemaName', ''),
                'referencing_attribute': rel.get('ReferencingAttribute', '')
            })
    
    print("Business Hours Relationships:")
    for rel in business_hours_relationships:
        print(f"  • Navigation Property: {rel['nav_property']}")
        print(f"    Referencing Entity: {rel['referencing_entity']}")
        print(f"    Schema Name: {rel['schema_name']}")
        print(f"    Referencing Attribute: {rel['referencing_attribute']}")
        print()
    
    print("Personnel Relationships:")
    if personnel_relationships:
        for rel in personnel_relationships:
            print(f"  • Navigation Property: {rel['nav_property']}")
            print(f"    Referencing Entity: {rel['referencing_entity']}")
            print(f"    Schema Name: {rel['schema_name']}")
            print(f"    Referencing Attribute: {rel['referencing_attribute']}")
            print()
    else:
        print("  No personnel-related relationships found.")
    
    # All important OneToMany relationships
    print(f"\n5. ALL ONE-TO-MANY NAVIGATION PROPERTIES")
    print("-" * 50)
    
    important_relationships = []
    for rel in one_to_many:
        nav_prop = rel.get('ReferencedEntityNavigationPropertyName', '')
        referencing_entity = rel.get('ReferencingEntity', '')
        
        # Filter for LMDM-related relationships
        if 'lmdm' in nav_prop.lower() or 'lmdm' in referencing_entity.lower():
            important_relationships.append({
                'nav_property': nav_prop,
                'referencing_entity': referencing_entity,
                'schema_name': rel.get('SchemaName', '')
            })
    
    print("LMDM-related OneToMany Navigation Properties:")
    for rel in sorted(important_relationships, key=lambda x: x['nav_property']):
        print(f"  • {rel['nav_property']:<50} <- {rel['referencing_entity']}")
    
    # Summary with recommendations
    print(f"\n6. SUMMARY & RECOMMENDATIONS")
    print("-" * 50)
    
    print("✓ CONFIRMED LOOKUP FIELDS (use these exact names):")
    for field in sorted(found_fields):
        field_info = next(f for f in lmdm_lookup_fields if f['logical_name'] == field)
        print(f"  - {field}")
    
    if missing_fields:
        print(f"\n✗ FIELDS NOT FOUND (check spelling or existence):")
        for field in missing_fields:
            print(f"  - {field}")
    
    print(f"\n📋 BUSINESS HOURS NAVIGATION PROPERTY:")
    if business_hours_relationships:
        for rel in business_hours_relationships:
            print(f"  - Use: {rel['nav_property']}")
            print(f"    Entity: {rel['referencing_entity']}")
    else:
        print("  - No business hours relationships found")
    
    print(f"\n📝 NAMING CONVENTION OBSERVED:")
    print("  - Lookup fields: lmdm_{fieldname}")
    print("  - Navigation properties: lmdm_Location_{relationship_name}")
    print("  - Target entities: lmdm_lookup{entitytype}")

if __name__ == "__main__":
    analyze_metadata('lmdm_location_metadata.json')