"""
Entity Metadata Exporter - Simple utility to export complete entity metadata
Fetches entity definition with all attributes, relationships, and saves to file
Usage: python entity_metadata_exporter.py <entity_name> [output_file]
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.metadata_client import MetadataClient
from utils.config import Config


def fetch_entity_metadata(client: MetadataClient, entity_name: str) -> dict:
    """
    Fetch complete entity metadata using the exact endpoint from requirements
    GET [OrgUrl]/api/data/v9.2/EntityDefinitions(LogicalName='{entity}')?
        $expand=Attributes,OneToManyRelationships,ManyToOneRelationships,ManyToManyRelationships
    """
    try:
        print(f"📋 Fetching metadata for entity: {entity_name}")
        
        url = f"{client.org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')"
        headers = client._get_headers()
        
        params = {
            "$expand": (
                "Attributes,"
                "OneToManyRelationships,"
                "ManyToOneRelationships,"
                "ManyToManyRelationships"
            )
        }
        
        print(f"🔗 URL: {url}")
        print(f"📡 Expanding: Attributes, Relationships (1-to-Many, Many-to-One, Many-to-Many)")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully fetched metadata!")
            return {"success": True, "data": data}
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_json = response.json()
                error_dict = error_json.get('error') if error_json else None
                if error_dict and isinstance(error_dict, dict):
                    error_msg = f"{error_msg}: {error_dict.get('message', response.text)}"
                else:
                    error_msg = f"{error_msg}: {response.text}"
            except:
                error_msg = f"{error_msg}: {response.text}"
            print(f"❌ Error: {error_msg}")
            return {"success": False, "error": error_msg}
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"success": False, "error": str(e)}


def fetch_record_data(client: MetadataClient, entity_set_name: str, record_id: str = None) -> dict:
    """
    Optionally fetch sample record data if provided
    """
    if not record_id:
        return None
    
    try:
        print(f"\n📦 Fetching sample record: {record_id}")
        
        url = f"{client.org_url}/api/data/v9.2/{entity_set_name}({record_id})"
        headers = client._get_headers()
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully fetched record data!")
            return {"success": True, "data": data}
        else:
            print(f"⚠️  Could not fetch record (HTTP {response.status_code})")
            return None
    
    except Exception as e:
        print(f"⚠️  Exception fetching record: {str(e)}")
        return None


def format_metadata_report(entity_name: str, metadata: dict, record_data: dict = None) -> str:
    """Generate a formatted report of entity metadata"""
    
    lines = []
    lines.append("=" * 100)
    lines.append("ENTITY METADATA REPORT")
    lines.append("=" * 100)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Entity: {entity_name}")
    lines.append("")
    
    # Entity Information
    lines.append("ENTITY INFORMATION:")
    lines.append("-" * 100)
    entity_info = metadata.get("data", {})
    
    info_fields = [
        ("LogicalName", "Logical Name"),
        ("SchemaName", "Schema Name"),
        ("EntitySetName", "Entity Set Name"),
        ("PrimaryIdAttribute", "Primary Key Attribute"),
        ("PrimaryNameAttribute", "Primary Display Attribute"),
    ]
    
    for field, label in info_fields:
        value = entity_info.get(field, "N/A")
        lines.append(f"  {label:.<40} {value}")
    
    if "DisplayName" in entity_info:
        display = entity_info["DisplayName"]
        if isinstance(display, dict):
            user_label = display.get("UserLocalizedLabel") if display else None
            display = user_label.get("Label", "N/A") if user_label else "N/A"
        elif display is None:
            display = "N/A"
        lines.append(f"  {'Display Name':.<40} {display}")
    
    lines.append("")
    
    # Attributes
    lines.append("ATTRIBUTES:")
    lines.append("-" * 100)
    attributes = entity_info.get("Attributes", [])
    
    if attributes:
        for attr in attributes:
            lines.append(f"\n  [{attr.get('LogicalName', 'UNKNOWN')}]")
            
            attr_info = [
                ("LogicalName", "Logical Name"),
                ("SchemaName", "Schema Name"),
                ("DisplayName", "Display Name"),
                ("AttributeType", "Type"),
                ("RequiredLevel", "Required Level"),
                ("IsValidForCreate", "Valid for Create"),
                ("IsValidForUpdate", "Valid for Update"),
                ("Description", "Description"),
                ("Format", "Format"),
                ("MaxLength", "Max Length"),
                ("MaxValue", "Max Value"),
                ("MinValue", "Min Value"),
                ("Precision", "Precision"),
                ("PrecisionSource", "Precision Source"),
            ]
            
            for field, label in attr_info:
                value = attr.get(field)
                if value is not None:
                    if isinstance(value, dict):
                        user_label = value.get("UserLocalizedLabel") if value else None
                        if user_label and isinstance(user_label, dict):
                            value = user_label.get("Label", str(value))
                        else:
                            value = str(value) if value else "N/A"
                    lines.append(f"    {label:.<35} {value}")
    
    lines.append("")
    
    # Relationships
    lines.append("RELATIONSHIPS:")
    lines.append("-" * 100)
    
    rels = entity_info.get("OneToManyRelationships", [])
    if rels:
        lines.append("\n  ONE-TO-MANY RELATIONSHIPS:")
        for rel in rels:
            lines.append(f"\n    [{rel.get('SchemaName', 'UNKNOWN')}]")
            lines.append(f"      Referencing Entity ... {rel.get('ReferencingEntity', 'N/A')}")
            lines.append(f"      Referenced Entity ... {rel.get('ReferencedEntity', 'N/A')}")
            lines.append(f"      Referencing Attribute . {rel.get('ReferencingAttribute', 'N/A')}")
            lines.append(f"      Referenced Attribute .. {rel.get('ReferencedAttribute', 'N/A')}")
            lines.append(f"      Navigation Property ... {rel.get('ReferencingEntityNavigationPropertyName', 'N/A')}")
            lines.append(f"      Custom Relationship ... {rel.get('IsCustomRelationship', False)}")
    
    rels = entity_info.get("ManyToOneRelationships", [])
    if rels:
        lines.append("\n  MANY-TO-ONE RELATIONSHIPS (Lookups):")
        for rel in rels:
            lines.append(f"\n    [{rel.get('SchemaName', 'UNKNOWN')}]")
            lines.append(f"      References Entity ... {rel.get('ReferencedEntity', 'N/A')}")
            lines.append(f"      This Entity ......... {rel.get('ReferencingEntity', 'N/A')}")
            lines.append(f"      Lookup Attribute ... {rel.get('ReferencingAttribute', 'N/A')}")
            lines.append(f"      Target Attribute ... {rel.get('ReferencedAttribute', 'N/A')}")
            lines.append(f"      Navigation Property  {rel.get('ReferencingEntityNavigationPropertyName', 'N/A')}")
            lines.append(f"      Custom Relationship  {rel.get('IsCustomRelationship', False)}")
    
    rels = entity_info.get("ManyToManyRelationships", [])
    if rels:
        lines.append("\n  MANY-TO-MANY RELATIONSHIPS:")
        for rel in rels:
            lines.append(f"\n    [{rel.get('SchemaName', 'UNKNOWN')}]")
            lines.append(f"      Entity 1 ............. {rel.get('Entity1LogicalName', 'N/A')}")
            lines.append(f"      Entity 2 ............. {rel.get('Entity2LogicalName', 'N/A')}")
            lines.append(f"      Intersection Entity .. {rel.get('IntersectEntityName', 'N/A')}")
            lines.append(f"      Entity 1 Nav Property  {rel.get('Entity1NavigationPropertyName', 'N/A')}")
            lines.append(f"      Entity 2 Nav Property  {rel.get('Entity2NavigationPropertyName', 'N/A')}")
            lines.append(f"      Custom Relationship .. {rel.get('IsCustomRelationship', False)}")
    
    lines.append("")
    
    # Sample Record Data
    if record_data and record_data.get("success"):
        lines.append("SAMPLE RECORD DATA:")
        lines.append("-" * 100)
        record = record_data.get("data", {})
        for key, value in sorted(record.items()):
            if key.startswith("_"):
                continue
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            lines.append(f"  {key:.<40} {str(value)[:60]}")
        lines.append("")
    
    lines.append("=" * 100)
    lines.append("END OF REPORT")
    lines.append("=" * 100)
    
    return "\n".join(lines)


def format_metadata_json(metadata: dict, record_data: dict = None) -> str:
    """Export metadata as JSON"""
    export = {
        "timestamp": datetime.now().isoformat(),
        "entity_metadata": metadata.get("data", {}),
    }
    
    if record_data and record_data.get("success"):
        export["sample_record"] = record_data.get("data", {})
    
    return json.dumps(export, indent=2, default=str)


def main():
    """Main function"""
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python entity_metadata_exporter.py <entity_name> [output_file] [--record-id GUID]")
        print()
        print("Examples:")
        print("  python entity_metadata_exporter.py lmdm_location")
        print("  python entity_metadata_exporter.py lmdm_location output.txt")
        print("  python entity_metadata_exporter.py lmdm_location output.json --record-id a1b2c3d4-...")
        sys.exit(1)
    
    entity_name = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"{entity_name}_metadata.txt"
    record_id = None
    
    # Parse optional parameters
    for i, arg in enumerate(sys.argv):
        if arg == "--record-id" and i + 1 < len(sys.argv):
            record_id = sys.argv[i + 1]
    
    try:
        # Initialize client
        print("🔐 Initializing Dataverse client...")
        config = Config()
        
        # Get environment configuration
        environments = config.get_available_environments()
        if not environments:
            print("❌ No environments found in .env file!")
            print("Please configure ORG_URL_* variables in .env")
            sys.exit(1)
        
        # Use first available environment or specific one from .env
        env_name = list(environments.keys())[0]
        org_url = environments[env_name]
        
        print(f"📡 Using environment: {env_name}")
        print(f"🔗 Organization URL: {org_url}")
        
        # Authenticate
        print("🔓 Authenticating...")
        client = MetadataClient(
            config.get_tenant_id(),
            config.get_client_id(),
            config.get_client_secret(),
            org_url,
            cache_dir=config.get_cache_directory()
        )
        
        if not client.authenticate():
            print("❌ Authentication failed!")
            sys.exit(1)
        
        print(f"✅ Authenticated to {client.org_url}\n")
        
        # Fetch metadata
        metadata_result = fetch_entity_metadata(client, entity_name)
        
        if not metadata_result.get("success"):
            print("❌ Failed to fetch metadata!")
            sys.exit(1)
        
        # Optionally fetch record data
        record_data = None
        if record_id:
            entity_set = metadata_result.get("data", {}).get("EntitySetName")
            if entity_set:
                record_data = fetch_record_data(client, entity_set, record_id)
        
        # Generate report
        print("\n📝 Generating report...")
        
        # Determine output format
        if output_file.endswith(".json"):
            content = format_metadata_json(metadata_result, record_data)
        else:
            content = format_metadata_report(entity_name, metadata_result, record_data)
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
        
        print(f"✅ Metadata saved to: {output_path.absolute()}")
        print(f"📊 File size: {output_path.stat().st_size} bytes")
        
        # Also save JSON version
        json_file = output_path.with_suffix(".json")
        json_content = format_metadata_json(metadata_result, record_data)
        json_file.write_text(json_content, encoding='utf-8')
        print(f"✅ JSON version saved to: {json_file.absolute()}")
        
        print("\n✨ Done!")
        
    except KeyError as e:
        print(f"❌ Configuration error: Missing environment variable")
        print("Make sure .env file is properly configured with:")
        print("  TENANT_ID, CLIENT_ID, CLIENT_SECRET")
        print("  ORG_URL_DEV (or ORG_URL_PROD, ORG_URL_UAT, etc.)")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
