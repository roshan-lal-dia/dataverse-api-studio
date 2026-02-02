import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

# Load environment variables from .env file
load_dotenv()

# Environment configuration
ENVIRONMENTS = {
    "1": {"name": "PRODUCTION", "url": os.getenv("ORG_URL_PROD")},
    "2": {"name": "DEVELOPMENT (Gaurav's)", "url": os.getenv("ORG_URL_DEV")},
    "3": {"name": "SANDBOX", "url": os.getenv("ORG_URL_SANDBOX")},
    "4": {"name": "Tanushri's Environment", "url": os.getenv("ORG_URL_TANUSHRIS_ENV")}
}

# Azure AD / Entra ID Configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token():
    """Get access token using MSAL"""
    try:
        app = ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )
        
        scope = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            print("Authentication failed:", result.get("error_description"))
            return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def get_dataverse_token(org_url):
    """Get Dataverse access token"""
    try:
        app = ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )
        
        scope = [f"{org_url}/.default"]
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            print("Dataverse authentication failed:", result.get("error_description"))
            return None
    except Exception as e:
        print(f"Dataverse authentication error: {e}")
        return None

def get_entity_metadata(org_url, token, entity_name):
    """Get metadata for a specific entity"""
    headers = {
        'Authorization': f'Bearer {token}',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Accept': 'application/json'
    }
    
    url = f"{org_url}/api/data/v9.2/EntityDefinitions(LogicalName='{entity_name}')?$expand=Attributes"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching {entity_name} metadata: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error fetching {entity_name} metadata: {e}")
        return None

def extract_lookup_fields(metadata):
    """Extract lookup field information from entity metadata"""
    if not metadata or 'Attributes' not in metadata:
        return []
    
    lookup_fields = []
    for attr in metadata['Attributes']:
        if attr.get('AttributeTypeName', {}).get('Value') == 'LookupType':
            lookup_info = {
                'LogicalName': attr.get('LogicalName'),
                'SchemaName': attr.get('SchemaName'),
                'DisplayName': attr.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label'),
                'Targets': attr.get('Targets', [])
            }
            lookup_fields.append(lookup_info)
    
    return lookup_fields

def main():
    print("🔍 Fetching Relationship Entity Metadata\n")
    
    # Choose environment
    print("Available environments:")
    for key, env in ENVIRONMENTS.items():
        if env["url"]:
            print(f"{key}. {env['name']} - {env['url']}")
    
    choice = input("\nSelect environment (1-4): ")
    if choice not in ENVIRONMENTS or not ENVIRONMENTS[choice]["url"]:
        print("❌ Invalid environment selection")
        return
    
    org_url = ENVIRONMENTS[choice]["url"]
    print(f"✅ Selected: {ENVIRONMENTS[choice]['name']}")
    
    # Get access token
    print("🔐 Getting access token...")
    token = get_dataverse_token(org_url)
    if not token:
        print("❌ Failed to get access token")
        return
    print("✅ Token obtained")
    
    # Entities to check
    entities = [
        "mdm_articleallergenrelationship",
        "mdm_articlenutrientrelationship", 
        "mdm_articlerelationship"
    ]
    
    results = {}
    
    for entity in entities:
        print(f"\n📥 Fetching metadata for {entity}...")
        metadata = get_entity_metadata(org_url, token, entity)
        
        if metadata:
            lookup_fields = extract_lookup_fields(metadata)
            results[entity] = lookup_fields
            
            print(f"✅ Found {len(lookup_fields)} lookup fields in {entity}:")
            for field in lookup_fields:
                print(f"   • {field['LogicalName']} ({field['SchemaName']}) -> targets: {field['Targets']}")
        else:
            print(f"❌ Failed to fetch metadata for {entity}")
            results[entity] = []
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"relationship_entities_lookup_fields_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    
    # Summary
    print("\n📋 SUMMARY - Lookup Fields for $expand:")
    for entity, fields in results.items():
        if fields:
            print(f"\n{entity}:")
            for field in fields:
                # Create expand syntax
                targets = field['Targets']
                if targets:
                    target_entity = targets[0]  # Usually single target
                    expand_syntax = f"$expand={field['LogicalName']}($select=...)"
                    print(f"   {field['LogicalName']} -> {expand_syntax}")
        else:
            print(f"\n{entity}: No lookup fields found (entity may not exist)")

if __name__ == "__main__":
    main()