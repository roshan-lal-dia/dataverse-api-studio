"""
Article Sequential Create POC
=============================
Creates two mdm_article records and relates them via mdm_articlerelationship
using 3 sequential POST operations with GUID binding.

Approach:
1. POST Article 1 → get GUID from OData-EntityId header
2. POST Article 2 → get GUID from OData-EntityId header
3. POST Relationship with @odata.bind using the captured GUIDs

Usage:
    python scripts/article_sequential_create.py --env=DEV --auto-confirm
"""

import sys
import os
import json
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class ArticleSequentialCreate:
    """POC: 3 sequential creates with GUID binding"""
    
    # Table names
    ARTICLE_TABLE = "mdm_article"
    ARTICLE_ENDPOINT = "mdm_articles"
    RELATIONSHIP_TABLE = "mdm_articlerelationship"
    RELATIONSHIP_ENDPOINT = "mdm_articlerelationships"
    
    # Navigation property names (from metadata discovery)
    # These are the ACTUAL nav prop names on mdm_articlerelationship
    PARENT_NAV_PROP = "mdm_ParentArticle"  # Note: PascalCase!
    CHILD_NAV_PROP = "mdm_ChildArticle"    # Note: PascalCase!
    
    def __init__(self, auto_confirm: bool = False, environment: str = None):
        self.config = Config()
        self.client = None
        self.auto_confirm = auto_confirm
        self.environment = environment
        self.selected_environment = None
        self.selected_org_url = None
        
        # Store created GUIDs
        self.article1_guid = None
        self.article2_guid = None
        self.relationship_guid = None
    
    def authenticate(self) -> bool:
        """Authenticate with Dataverse"""
        print("\n🔐 Authenticating with Dataverse...")
        try:
            tenant_id = self.config.get_tenant_id()
            client_id = self.config.get_client_id()
            client_secret = self.config.get_client_secret()
            
            environments = self.config.get_available_environments()
            if not environments:
                print("❌ No ORG_URL environments found in .env file")
                return False
            
            # Use specified environment or default to DEV
            if self.environment:
                env_upper = self.environment.upper()
                env_name = next((e for e in environments.keys() if e.upper() == env_upper), None)
                if not env_name:
                    print(f"❌ Environment '{self.environment}' not found. Available: {list(environments.keys())}")
                    return False
                org_url = environments[env_name]
            else:
                # Safe default: DEV > SANDBOX > others
                for priority in ["DEV", "SANDBOX", "STAGING", "UAT"]:
                    env_name = next((e for e in environments.keys() if priority in e.upper()), None)
                    if env_name:
                        break
                if not env_name:
                    env_name = list(environments.keys())[0]
                org_url = environments[env_name]
            
            self.client = MetadataClient(tenant_id, client_id, client_secret, org_url)
            self.selected_environment = env_name
            self.selected_org_url = org_url
            
            if self.client.authenticate():
                print(f"✅ Authenticated to {env_name}")
                print(f"   {org_url}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def _confirm_environment(self) -> bool:
        """Confirm environment before creating records"""
        print(f"\n⚠️  Target: {self.selected_environment} ({self.selected_org_url})")
        
        if "PROD" in self.selected_environment.upper():
            print("🚨 WARNING: PRODUCTION environment!")
        
        if self.auto_confirm:
            print("   ✓ Auto-confirmed")
            return True
        
        response = input("\nProceed? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
    
    def _create_record(self, endpoint: str, data: dict, description: str) -> Optional[str]:
        """Create a record and return its GUID from OData-EntityId header"""
        print(f"\n📝 Creating {description}...")
        print(f"   Payload: {json.dumps(data, indent=2)[:200]}...")
        
        url = f"{self.client.org_url}/api/data/v9.2/{endpoint}"
        headers = self.client._get_headers()
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"  # Get created record back
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201, 204]:
                # Extract GUID from OData-EntityId header or response body
                entity_id = response.headers.get("OData-EntityId", "")
                
                if entity_id:
                    # Format: https://org.crm.dynamics.com/api/data/v9.2/table(guid)
                    guid = entity_id.split("(")[-1].rstrip(")")
                    print(f"   ✅ Created! GUID: {guid}")
                    return guid
                
                # Fallback: try response body
                if response.text:
                    try:
                        body = response.json()
                        # Try common primary key patterns
                        for key in [f"{self.ARTICLE_TABLE}id", f"{self.RELATIONSHIP_TABLE}id", "id"]:
                            if key in body:
                                guid = body[key]
                                print(f"   ✅ Created! GUID: {guid}")
                                return guid
                    except:
                        pass
                
                print(f"   ✅ Created (204 No Content)")
                return "created-but-no-guid"
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def create_article(self, article_num: int) -> Optional[str]:
        """Create an article with minimal required fields"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Minimal payload - adjust based on your required fields
        data = {
            "mdm_article_id": f"SEQ_ART_{article_num:03d}_{timestamp[:8]}",
            "mdm_description": f"Sequential Create Test Article {article_num}",
        }
        
        return self._create_record(
            self.ARTICLE_ENDPOINT,
            data,
            f"Article {article_num}"
        )
    
    def create_relationship(self, parent_guid: str, child_guid: str) -> Optional[str]:
        """Create relationship linking parent and child articles"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Use @odata.bind with the navigation property names
        data = {
            "mdm_relationshipname": f"SeqCreate Rel {timestamp}",
            "mdm_baseunit": "Test Unit",
            "mdm_unit": "Test Unit",
            # Key: Use the actual nav prop names with @odata.bind
            f"{self.PARENT_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({parent_guid})",
            f"{self.CHILD_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({child_guid})",
        }
        
        return self._create_record(
            self.RELATIONSHIP_ENDPOINT,
            data,
            "Relationship (with parent/child binding)"
        )
    
    def run(self) -> bool:
        """Execute 3 sequential creates"""
        print("\n" + "=" * 60)
        print("🚀 ARTICLE SEQUENTIAL CREATE POC")
        print("   3 POST operations with GUID binding")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        if not self._confirm_environment():
            print("\n❌ Cancelled.")
            return False
        
        # Step 2: Create Article 1
        print("\n" + "-" * 40)
        print("STEP 1/3: Create Parent Article")
        print("-" * 40)
        self.article1_guid = self.create_article(1)
        if not self.article1_guid:
            print("❌ Failed to create Article 1")
            return False
        
        # Step 3: Create Article 2
        print("\n" + "-" * 40)
        print("STEP 2/3: Create Child Article")
        print("-" * 40)
        self.article2_guid = self.create_article(2)
        if not self.article2_guid:
            print("❌ Failed to create Article 2")
            return False
        
        # Step 4: Create Relationship with GUIDs
        print("\n" + "-" * 40)
        print("STEP 3/3: Create Relationship with @odata.bind")
        print("-" * 40)
        print(f"   Parent GUID: {self.article1_guid}")
        print(f"   Child GUID:  {self.article2_guid}")
        
        self.relationship_guid = self.create_relationship(
            self.article1_guid,
            self.article2_guid
        )
        
        if not self.relationship_guid:
            print("❌ Failed to create Relationship")
            return False
        
        # Success!
        print("\n" + "=" * 60)
        print("✅ SUCCESS! All 3 records created and linked!")
        print("=" * 60)
        print(f"\n   Parent Article:  {self.article1_guid}")
        print(f"   Child Article:   {self.article2_guid}")
        print(f"   Relationship:    {self.relationship_guid}")
        print("\n🎯 Key Achievement:")
        print("   ✓ 3 sequential POST calls")
        print("   ✓ GUID binding via @odata.bind")
        print("   ✓ Parent/Child properly linked!")
        print("   ✓ No read operations needed")
        print("=" * 60)
        
        return True


def main():
    auto_confirm = "--auto-confirm" in sys.argv or "--yes" in sys.argv
    
    environment = None
    for arg in sys.argv[1:]:
        if arg.startswith("--env="):
            environment = arg.split("=")[1]
            break
    
    poc = ArticleSequentialCreate(auto_confirm=auto_confirm, environment=environment)
    success = poc.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
