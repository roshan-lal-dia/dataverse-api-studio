"""Discover navigation property names for deep insert"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config
import requests

def main():
    config = Config()
    client = MetadataClient(
        config.get_tenant_id(),
        config.get_client_id(), 
        config.get_client_secret(),
        config.get_available_environments().get('DEV')
    )
    client.authenticate()
    print("✅ Authenticated\n")
    
    # Query ManyToOne relationships from mdm_articlerelationship
    # This will show us the navigation property names on both sides
    url = (
        f"{client.org_url}/api/data/v9.2/"
        f"EntityDefinitions(LogicalName='mdm_articlerelationship')?"
        f"$select=LogicalName"
        f"&$expand=ManyToOneRelationships("
        f"$select=SchemaName,ReferencedEntity,ReferencingAttribute,"
        f"ReferencingEntityNavigationPropertyName,ReferencedEntityNavigationPropertyName)"
    )
    
    headers = client._get_headers()
    response = requests.get(url, headers=headers)
    data = response.json()
    
    print("=" * 80)
    print("MANY-TO-ONE RELATIONSHIPS FROM mdm_articlerelationship")
    print("(Looking for relationships TO mdm_article)")
    print("=" * 80)
    
    relationships = data.get('ManyToOneRelationships', [])
    article_rels = []
    
    for rel in relationships:
        ref_entity = rel.get('ReferencedEntity', '')
        if 'mdm_article' in ref_entity.lower() and 'relationship' not in ref_entity.lower():
            article_rels.append(rel)
            print(f"\n📌 Schema Name: {rel.get('SchemaName')}")
            print(f"   Referenced Entity (parent): {ref_entity}")
            print(f"   Referencing Attribute (FK): {rel.get('ReferencingAttribute')}")
            print(f"   Nav Prop on Relationship: {rel.get('ReferencingEntityNavigationPropertyName')}")
            print(f"   Nav Prop on Article (COLLECTION): {rel.get('ReferencedEntityNavigationPropertyName')}")
    
    if not article_rels:
        print("\n⚠️  No direct relationships to mdm_article found.")
        print("\nAll ManyToOne relationships:")
        for rel in relationships:
            print(f"  - {rel.get('SchemaName')} -> {rel.get('ReferencedEntity')}")
    
    # Also check entity keys (alternate keys)
    print("\n" + "=" * 80)
    print("ALTERNATE KEYS ON mdm_article")
    print("=" * 80)
    
    url = (
        f"{client.org_url}/api/data/v9.2/"
        f"EntityDefinitions(LogicalName='mdm_article')?"
        f"$select=LogicalName"
        f"&$expand=Keys($select=LogicalName,SchemaName,KeyAttributes)"
    )
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    keys = data.get('Keys', [])
    if keys:
        for key in keys:
            print(f"\n🔑 Key: {key.get('SchemaName')}")
            print(f"   Logical Name: {key.get('LogicalName')}")
            print(f"   Attributes: {key.get('KeyAttributes')}")
    else:
        print("\n⚠️  No alternate keys defined on mdm_article")
        print("   You need to create an alternate key in Power Apps / Dataverse settings")
    
    # Also query OneToMany from article side
    print("\n" + "=" * 80)
    print("ONE-TO-MANY RELATIONSHIPS FROM mdm_article")
    print("(Collection navigation properties)")
    print("=" * 80)
    
    url = (
        f"{client.org_url}/api/data/v9.2/"
        f"EntityDefinitions(LogicalName='mdm_article')?"
        f"$select=LogicalName"
        f"&$expand=OneToManyRelationships("
        f"$select=SchemaName,ReferencingEntity,ReferencingAttribute,"
        f"ReferencingEntityNavigationPropertyName,ReferencedEntityNavigationPropertyName)"
    )
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    relationships = data.get('OneToManyRelationships', [])
    
    for rel in relationships:
        ref_entity = rel.get('ReferencingEntity', '')
        if 'articlerelationship' in ref_entity.lower():
            print(f"\n📌 Schema Name: {rel.get('SchemaName')}")
            print(f"   Referencing Entity (child): {ref_entity}")
            print(f"   Referencing Attribute: {rel.get('ReferencingAttribute')}")
            print(f"   Collection Nav Prop on Article: {rel.get('ReferencedEntityNavigationPropertyName')}")
            print(f"   Single Nav Prop on Relationship: {rel.get('ReferencingEntityNavigationPropertyName')}")

if __name__ == "__main__":
    main()
