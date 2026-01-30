#!/usr/bin/env python3
"""
Test Custom API via Web API directly.
This script calls your alshaya_GetLocationDetails custom API without worrying about Status.
"""
import requests
import json
from client.metadata_client import MetadataClient
from utils.config import Config

def test_custom_api():
    """Call custom API directly via Web API."""
    
    # Load config
    config = Config()
    tenant_id = config.get_tenant_id()
    client_id = config.get_client_id()
    client_secret = config.get_client_secret()
    org_url = config.get_org_url("DEV")
    
    if not all([tenant_id, client_id, client_secret, org_url]):
        print("❌ Missing credentials in .env (TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL_DEV)")
        return
    
    # Authenticate
    client = MetadataClient(tenant_id, client_id, client_secret, org_url)
    if not client.authenticate():
        print("❌ Authentication failed")
        return
    
    # The custom API endpoint
    # For UNBOUND function: GET /api/data/v9.1/{custom_api_name}(ParameterName=value)
    # NOTE: Unique name is mdm_alshaya_GetLocationDetails (with mdm_ prefix)
    api_name = "mdm_alshaya_GetLocationDetails"
    location_id = "f7339688-8a76-f011-b4cc-7c1e5250ed32"
    
    # For GET functions, parameters go inside parentheses in URL
    api_url = f"{org_url}/api/data/v9.1/{api_name}(LocationId='{location_id}')"
    
    headers = {
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {client.access_token}"
    }
    
    print(f"\n🔗 Testing Custom API (FUNCTION - GET): {api_name}")
    print(f"📍 URL: {api_url}")
    print(f"🔐 Token: {client.access_token[:50]}...")
    print("-" * 80)
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📋 Response Body:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201, 204]:
            print("\n✅ SUCCESS! Your custom API is working!")
            print("   The 'Off' status has NO impact on functionality.")
        elif response.status_code == 400:
            print("\n⚠️  Bad Request (400)")
            print("   Check your request parameters match the custom API definition")
        elif response.status_code == 404:
            print("\n❌ NOT FOUND (404)")
            print("   The custom API may not exist or the name is incorrect")
            print("   Verify the unique name in PRT matches 'alshaya_GetLocationDetails'")
        elif response.status_code == 401:
            print("\n❌ UNAUTHORIZED (401)")
            print("   Token may be expired or invalid")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
        
        return response
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CUSTOM API DIRECT TEST")
    print("=" * 80)
    test_custom_api()
    print("=" * 80)
