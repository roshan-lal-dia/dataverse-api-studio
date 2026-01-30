#!/usr/bin/env python3
"""
Publish customizations to make Custom API discoverable in Web API metadata.
Run this AFTER creating/modifying a custom API.
"""
import requests
import json
from client.metadata_client import MetadataClient
from utils.config import Config

def publish_all_customizations():
    """Publish all customizations to Dataverse"""
    
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
    
    print("\n" + "=" * 80)
    print("PUBLISHING CUSTOMIZATIONS")
    print("=" * 80)
    print(f"📍 Organization: {org_url}")
    print(f"⏳ This will take 1-2 minutes to propagate...")
    print("-" * 80)
    
    # Call PublishAllXml action
    api_url = f"{org_url}/api/data/v9.1/PublishAllXml"
    headers = {
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {client.access_token}"
    }
    
    payload = {}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        
        if response.status_code in [200, 204]:
            print("✅ PublishAllXml ACTION EXECUTED SUCCESSFULLY")
            print("\n⏳ Customizations are being published...")
            print("   Wait 1-2 minutes before calling your custom API again")
            print("\n📋 After publishing:")
            print("   1. Run: python test_custom_api.py")
            print("   2. Your custom API should now be discoverable")
            return True
        else:
            print(f"❌ Status Code: {response.status_code}")
            print(f"📄 Response: {response.json()}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    publish_all_customizations()
    print("=" * 80)
