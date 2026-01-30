#!/usr/bin/env python3
"""
Check Custom API metadata to see the exact message name and configuration.
"""
import requests
import json
from client.metadata_client import MetadataClient
from utils.config import Config

def check_custom_api_metadata():
    """Check the actual Custom API metadata from Dataverse."""
    
    # Load config
    config = Config()
    tenant_id = config.get_tenant_id()
    client_id = config.get_client_id()
    client_secret = config.get_client_secret()
    org_url = config.get_org_url("DEV")
    
    # Authenticate
    client = MetadataClient(tenant_id, client_id, client_secret, org_url)
    if not client.authenticate():
        print("❌ Authentication failed")
        return
    
    print("🔍 CUSTOM API METADATA CHECK")
    print("=" * 80)
    
    # Query for our Custom API
    api_query = f"{org_url}/api/data/v9.1/customapis?$filter=uniquename eq 'mdm_alshaya_GetLocationDetails'"
    
    headers = {
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {client.access_token}"
    }
    
    try:
        response = requests.get(api_query, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('value'):
                custom_api = data['value'][0]
                print("✅ Custom API Found:")
                print(f"   Unique Name: {custom_api.get('uniquename')}")
                print(f"   Name: {custom_api.get('name')}")
                print(f"   Display Name: {custom_api.get('displayname')}")
                print(f"   Binding Type: {custom_api.get('bindingtype')}")
                print(f"   Bound Entity Logical Name: {custom_api.get('boundentitylogicalname')}")
                print(f"   Is Function: {custom_api.get('isfunction')}")
                print(f"   Plugin Type ID: {custom_api.get('_plugintypeid_value')}")
                print(f"   Enabled: {custom_api.get('isworkflowactivity')}")
                
                # The message name for plugins is typically the unique name
                print(f"\n🔑 Expected Plugin Message Name: '{custom_api.get('uniquename')}'")
                
            else:
                print("❌ Custom API not found in metadata")
        else:
            print(f"❌ Failed to query Custom API: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Also check for plugin steps
    print("\n" + "-" * 80)
    print("Checking Plugin Steps...")
    
    plugin_query = f"{org_url}/api/data/v9.1/sdkmessageprocessingsteps?$filter=contains(name,'GetLocationDetails')&$expand=sdkmessageid"
    
    try:
        response = requests.get(plugin_query, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('value'):
                for step in data['value']:
                    print(f"✅ Plugin Step Found:")
                    print(f"   Name: {step.get('name')}")
                    print(f"   Message: {step.get('sdkmessageid', {}).get('name')}")
                    print(f"   Stage: {step.get('stage')}")
                    print(f"   Mode: {step.get('mode')}")
                    print(f"   Status: {step.get('statecode')}")
                    print()
            else:
                print("❌ No plugin steps found")
        else:
            print(f"❌ Failed to query plugin steps: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception checking plugin steps: {e}")

if __name__ == "__main__":
    check_custom_api_metadata()