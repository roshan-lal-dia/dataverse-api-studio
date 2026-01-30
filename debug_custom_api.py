#!/usr/bin/env python3
"""
Debug Custom API - More detailed testing to understand plugin execution.
"""
import requests
import json
from client.metadata_client import MetadataClient
from utils.config import Config

def debug_custom_api():
    """Debug custom API with detailed tracing."""
    
    # Load config
    config = Config()
    tenant_id = config.get_tenant_id()
    client_id = config.get_client_id()
    client_secret = config.get_client_secret()
    org_url = config.get_org_url("DEV")
    
    if not all([tenant_id, client_id, client_secret, org_url]):
        print("❌ Missing credentials in .env")
        return
    
    # Authenticate
    client = MetadataClient(tenant_id, client_id, client_secret, org_url)
    if not client.authenticate():
        print("❌ Authentication failed")
        return
    
    print("🔍 CUSTOM API DEBUG TEST")
    print("=" * 80)
    
    # Step 1: Check if location exists first
    location_id = "f7339688-8a76-f011-b4cc-7c1e5250ed32"
    print(f"Step 1: Checking if location {location_id} exists...")
    
    location_url = f"{org_url}/api/data/v9.1/lmdm_locations({location_id})"
    headers = {
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {client.access_token}"
    }
    
    try:
        location_response = requests.get(location_url, headers=headers)
        if location_response.status_code == 200:
            location_data = location_response.json()
            print(f"✅ Location found: {location_data.get('lmdm_storename', 'No name')}")
            print(f"   CCID: {location_data.get('lmdm_ccid', 'No CCID')}")
        else:
            print(f"❌ Location not found: {location_response.status_code}")
            print(f"   Response: {location_response.text}")
    except Exception as e:
        print(f"❌ Error checking location: {e}")
    
    print("\n" + "-" * 80)
    
    # Step 2: Test Custom API
    print("Step 2: Testing Custom API...")
    api_name = "mdm_alshaya_GetLocationDetails"
    api_url = f"{org_url}/api/data/v9.1/{api_name}(LocationId='{location_id}')"
    
    print(f"🔗 URL: {api_url}")
    
    try:
        api_response = requests.get(api_url, headers=headers)
        print(f"📊 Status Code: {api_response.status_code}")
        
        if api_response.status_code == 200:
            response_data = api_response.json()
            print(f"📄 Full Response:")
            print(json.dumps(response_data, indent=2))
            
            # Check if we got actual data
            location_details = response_data.get('LocationDetails')
            execution_time = response_data.get('ExecutionTime')
            
            if location_details is None and execution_time is None:
                print("\n❌ ISSUE: Both LocationDetails and ExecutionTime are NULL")
                print("   This suggests the plugin is not executing or not setting output parameters")
            elif location_details is None:
                print(f"\n⚠️ PARTIAL: ExecutionTime = {execution_time}, but LocationDetails is NULL")
                print("   Plugin is executing but failing to retrieve/set location data")
            else:
                print(f"\n✅ SUCCESS: Got data! Execution time: {execution_time}ms")
                
        else:
            print(f"❌ API call failed: {api_response.status_code}")
            print(f"   Error: {api_response.text}")
            
    except Exception as e:
        print(f"❌ Exception during API call: {e}")
    
    print("\n" + "=" * 80)
    print("🛠️ TROUBLESHOOTING STEPS:")
    print("1. Check Plugin Registration Tool for plugin execution logs")
    print("2. Verify plugin message name matches Custom API unique name")
    print("3. Ensure plugin assembly is properly updated and published")
    print("4. Check if plugin user has proper permissions to read location data")

if __name__ == "__main__":
    debug_custom_api()