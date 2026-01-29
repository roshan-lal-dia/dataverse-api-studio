#!/usr/bin/env python3
"""
Script to analyze lmdm_location_metadata.json and extract:
1. All lookup field logical names
2. Personnel/staff related relationships 
3. Navigation property names for relationships
"""

import json
import re
from typing import List, Dict, Any

def analyze_location_metadata():
    """Main analysis function"""
    
    # Read the metadata file
    with open('lmdm_location_metadata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entity_metadata = data['entity_metadata']
    
    # Extract lookup fields
    lookup_fields = []
    if 'Attributes' in entity_metadata:
        for attr in entity_metadata['Attributes']:
            if attr.get('AttributeType') == 'Lookup':
                logical_name = attr.get('LogicalName')
                if logical_name:
                    lookup_fields.append(logical_name)
    
    # Search for personnel/staff related relationships
    personnel_keywords = ['personnel', 'staff', 'employee', 'user', 'owner', 'manager', 'contact', 'person', 'people']
    
    # Check OneToManyRelationships
    personnel_onetomany = []
    if 'OneToManyRelationships' in entity_metadata:
        for rel in entity_metadata['OneToManyRelationships']:
            schema_name = rel.get('SchemaName', '').lower()
            nav_prop = rel.get('ReferencedEntityNavigationPropertyName', '').lower()
            ref_entity = rel.get('ReferencedEntity', '').lower()
            
            # Check if any field contains personnel-related keywords
            if any(keyword in schema_name or keyword in nav_prop or keyword in ref_entity 
                   for keyword in personnel_keywords):
                personnel_onetomany.append({
                    'SchemaName': rel.get('SchemaName'),
                    'NavigationPropertyName': rel.get('ReferencedEntityNavigationPropertyName'),
                    'ReferencedEntity': rel.get('ReferencedEntity'),
                    'Type': 'OneToMany'
                })
    
    # Check ManyToOneRelationships
    personnel_manytoone = []
    if 'ManyToOneRelationships' in entity_metadata:
        for rel in entity_metadata['ManyToOneRelationships']:
            schema_name = rel.get('SchemaName', '').lower()
            nav_prop = rel.get('ReferencingEntityNavigationPropertyName', '').lower()
            ref_entity = rel.get('ReferencedEntity', '').lower()
            
            if any(keyword in schema_name or keyword in nav_prop or keyword in ref_entity 
                   for keyword in personnel_keywords):
                personnel_manytoone.append({
                    'SchemaName': rel.get('SchemaName'),
                    'NavigationPropertyName': rel.get('ReferencingEntityNavigationPropertyName'),
                    'ReferencedEntity': rel.get('ReferencedEntity'),
                    'Type': 'ManyToOne'
                })
    
    # Check ManyToManyRelationships
    personnel_manytomany = []
    if 'ManyToManyRelationships' in entity_metadata:
        for rel in entity_metadata['ManyToManyRelationships']:
            schema_name = rel.get('SchemaName', '').lower()
            nav_prop1 = rel.get('Entity1NavigationPropertyName', '').lower()
            nav_prop2 = rel.get('Entity2NavigationPropertyName', '').lower()
            entity1 = rel.get('Entity1LogicalName', '').lower()
            entity2 = rel.get('Entity2LogicalName', '').lower()
            
            if any(keyword in schema_name or keyword in nav_prop1 or keyword in nav_prop2 
                   or keyword in entity1 or keyword in entity2 
                   for keyword in personnel_keywords):
                personnel_manytomany.append({
                    'SchemaName': rel.get('SchemaName'),
                    'Entity1NavigationProperty': rel.get('Entity1NavigationPropertyName'),
                    'Entity2NavigationProperty': rel.get('Entity2NavigationPropertyName'),
                    'Entity1': rel.get('Entity1LogicalName'),
                    'Entity2': rel.get('Entity2LogicalName'),
                    'Type': 'ManyToMany'
                })
    
    # Also search for business hours or schedule related relationships
    schedule_keywords = ['businesshours', 'schedule', 'calendar', 'hours', 'time']
    schedule_relationships = []
    
    # Check all relationship types for schedule/business hours
    for rel_type, relationships in [
        ('OneToMany', entity_metadata.get('OneToManyRelationships', [])),
        ('ManyToOne', entity_metadata.get('ManyToOneRelationships', [])),
        ('ManyToMany', entity_metadata.get('ManyToManyRelationships', []))
    ]:
        for rel in relationships:
            schema_name = rel.get('SchemaName', '').lower()
            
            # Check different nav property names based on relationship type
            nav_props = []
            if rel_type == 'OneToMany':
                nav_props.append(rel.get('ReferencedEntityNavigationPropertyName', '').lower())
            elif rel_type == 'ManyToOne':
                nav_props.append(rel.get('ReferencingEntityNavigationPropertyName', '').lower())
            elif rel_type == 'ManyToMany':
                nav_props.append(rel.get('Entity1NavigationPropertyName', '').lower())
                nav_props.append(rel.get('Entity2NavigationPropertyName', '').lower())
            
            if any(keyword in schema_name or any(keyword in nav for nav in nav_props) 
                   for keyword in schedule_keywords):
                schedule_relationships.append({
                    'SchemaName': rel.get('SchemaName'),
                    'NavigationProperties': [prop for prop in nav_props if prop],
                    'Type': rel_type,
                    'FullRelationship': rel
                })
    
    # Print results
    print("="*80)
    print("DATAVERSE LOCATION ENTITY ANALYSIS")
    print("="*80)
    
    print("\n🔍 LOOKUP FIELDS (need _value suffix for Web API):")
    print("-" * 50)
    for field in sorted(lookup_fields):
        print(f"  • {field}  →  {field}_value")
    
    print(f"\n   Total lookup fields found: {len(lookup_fields)}")
    
    print("\n👥 PERSONNEL/STAFF RELATED RELATIONSHIPS:")
    print("-" * 50)
    
    if personnel_onetomany:
        print("  OneToMany Relationships:")
        for rel in personnel_onetomany:
            print(f"    • {rel['SchemaName']} → Nav: {rel['NavigationPropertyName']} → Entity: {rel['ReferencedEntity']}")
    
    if personnel_manytoone:
        print("  ManyToOne Relationships:")
        for rel in personnel_manytoone:
            print(f"    • {rel['SchemaName']} → Nav: {rel['NavigationPropertyName']} → Entity: {rel['ReferencedEntity']}")
    
    if personnel_manytomany:
        print("  ManyToMany Relationships:")
        for rel in personnel_manytomany:
            print(f"    • {rel['SchemaName']} → Nav1: {rel['Entity1NavigationProperty']} → Nav2: {rel['Entity2NavigationProperty']}")
    
    if not (personnel_onetomany or personnel_manytoone or personnel_manytomany):
        print("    No personnel/staff relationships found with keywords: " + ", ".join(personnel_keywords))
    
    print("\n📅 BUSINESS HOURS/SCHEDULE RELATED RELATIONSHIPS:")
    print("-" * 50)
    
    if schedule_relationships:
        for rel in schedule_relationships:
            print(f"    • {rel['SchemaName']} ({rel['Type']}) → Nav: {', '.join(rel['NavigationProperties'])}")
    else:
        print("    No business hours/schedule relationships found")
    
    print("\n📋 SUMMARY FOR CUSTOM API FIX:")
    print("-" * 50)
    print("For your custom-api-location.py script:")
    print("\n1. FORM_FIELDS that are lookup types (use _value suffix):")
    
    # Common form fields that might be lookups
    common_form_fields = ['createdby', 'modifiedby', 'ownerid', 'owninguser', 'owningteam']
    form_lookup_fields = [field for field in lookup_fields if any(common in field for common in common_form_fields)]
    
    for field in form_lookup_fields:
        print(f"   '{field}': location_data.get('{field}_value')")
    
    print("\n2. Business Hours Navigation Property:")
    business_hours_nav = None
    for rel in schedule_relationships:
        if 'businesshours' in rel['SchemaName'].lower():
            business_hours_nav = rel['NavigationProperties'][0] if rel['NavigationProperties'] else None
            break
    
    if business_hours_nav:
        print(f"   Use: '{business_hours_nav}'")
    else:
        print("   No specific business hours navigation property found")
    
    print("\n3. Personnel Navigation Properties:")
    all_personnel_navs = []
    for rel in personnel_onetomany + personnel_manytoone:
        if rel['NavigationPropertyName']:
            all_personnel_navs.append(rel['NavigationPropertyName'])
    
    for rel in personnel_manytomany:
        if rel['Entity1NavigationProperty']:
            all_personnel_navs.append(rel['Entity1NavigationProperty'])
        if rel['Entity2NavigationProperty']:
            all_personnel_navs.append(rel['Entity2NavigationProperty'])
    
    if all_personnel_navs:
        for nav in set(all_personnel_navs):
            print(f"   Available: '{nav}'")
    else:
        print("   No personnel navigation properties found")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        analyze_location_metadata()
    except FileNotFoundError:
        print("ERROR: lmdm_location_metadata.json file not found!")
    except Exception as e:
        print(f"ERROR: {str(e)}")