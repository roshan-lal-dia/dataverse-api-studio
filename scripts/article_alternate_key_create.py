"""
Article Creation with Alternate Keys - NO GUID NEEDED!
=======================================================
Creates two articles and relates them using ALTERNATE KEYS.
No need to store or read GUIDs from any response.

Manager's Concern Addressed:
- ❌ Don't want to read GUIDs
- ❌ Don't want to store response
- ✅ Use alternate keys instead!

Approach:
1. Create Article 1 with known business key (e.g., itemcode='PARENT001')
2. Create Article 2 with known business key (e.g., itemcode='CHILD001')
3. Create Relationship referencing by alternate keys (NOT GUIDs!)

Available Alternate Keys on mdm_article:
- mdm_itemcode (single key)
- mdm_productcode (single key)
- mdm_supplierarticlecode + mdm_supplierid (composite key)

Usage:
    python scripts/article_alternate_key_create.py --env=DEV --auto-confirm
"""

import sys
import os
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class ArticleAlternateKeyCreate:
    """Create articles and relationship using ALTERNATE KEYS - no GUID needed!"""
    
    ARTICLE_ENDPOINT = "mdm_articles"
    RELATIONSHIP_ENDPOINT = "mdm_articlerelationships"
    
    # Navigation property names (PascalCase!)
    PARENT_NAV_PROP = "mdm_ParentArticle"
    CHILD_NAV_PROP = "mdm_ChildArticle"
    
    # Alternate key field (using itemcode - discovered from metadata)
    ALTERNATE_KEY_FIELD = "mdm_itemcode"
    
    def __init__(self, auto_confirm: bool = False, environment: str = None):
        self.config = Config()
        self.client = None
        self.auto_confirm = auto_confirm
        self.environment = environment
        self.selected_environment = None
        self.selected_org_url = None
        
        # Generate unique business keys upfront - NO GUID NEEDED!
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.parent_key = f"PARENT_{timestamp}"
        self.child_key = f"CHILD_{timestamp}"
    
    def authenticate(self) -> bool:
        """Authenticate with Dataverse"""
        print("\n🔐 Authenticating...")
        try:
            tenant_id = self.config.get_tenant_id()
            client_id = self.config.get_client_id()
            client_secret = self.config.get_client_secret()
            
            environments = self.config.get_available_environments()
            if not environments:
                print("❌ No environments found")
                return False
            
            if self.environment:
                env_upper = self.environment.upper()
                env_name = next((e for e in environments.keys() if e.upper() == env_upper), None)
                if not env_name:
                    print(f"❌ Environment '{self.environment}' not found")
                    return False
                org_url = environments[env_name]
            else:
                env_name = next((e for e in environments.keys() if "DEV" in e.upper()), None)
                if not env_name:
                    env_name = list(environments.keys())[0]
                org_url = environments[env_name]
            
            self.client = MetadataClient(tenant_id, client_id, client_secret, org_url)
            self.selected_environment = env_name
            self.selected_org_url = org_url
            
            if self.client.authenticate():
                print(f"✅ Authenticated to {env_name}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def _confirm(self) -> bool:
        if self.auto_confirm:
            print("   ✓ Auto-confirmed")
            return True
        response = input("\nProceed? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
    
    def _post(self, endpoint: str, data: dict, description: str) -> bool:
        """POST a record - we DON'T need to capture GUID!"""
        print(f"\n📝 Creating {description}...")
        
        url = f"{self.client.org_url}/api/data/v9.2/{endpoint}"
        headers = self.client._get_headers()
        headers["Content-Type"] = "application/json"
        # Note: We DON'T need "Prefer: return=representation" because
        # we're using alternate keys - no GUID needed!
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201, 204]:
                print(f"   ✅ Created successfully!")
                # We intentionally DON'T extract GUID - we don't need it!
                return True
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run(self) -> bool:
        """Execute the alternate key approach"""
        print("\n" + "=" * 70)
        print("🚀 ALTERNATE KEY APPROACH - NO GUID NEEDED!")
        print("=" * 70)
        print("\n📌 Manager's Concern Addressed:")
        print("   ✓ No need to READ GUIDs")
        print("   ✓ No need to STORE response")
        print("   ✓ Reference by BUSINESS KEY instead!")
        
        # Show the keys we'll use
        print(f"\n🔑 Business Keys (known upfront):")
        print(f"   Parent Article: {self.ALTERNATE_KEY_FIELD}='{self.parent_key}'")
        print(f"   Child Article:  {self.ALTERNATE_KEY_FIELD}='{self.child_key}'")
        
        # Authenticate
        if not self.authenticate():
            return False
        
        print(f"\n⚠️  Target: {self.selected_environment}")
        if not self._confirm():
            print("❌ Cancelled")
            return False
        
        # =====================================================
        # STEP 1: Create Parent Article (with known business key)
        # =====================================================
        print("\n" + "-" * 50)
        print("STEP 1/3: Create Parent Article")
        print(f"   Using alternate key: {self.ALTERNATE_KEY_FIELD}='{self.parent_key}'")
        print("-" * 50)
        
        parent_data = {
            "mdm_article_id": f"ART_PARENT_{self.parent_key}",
            self.ALTERNATE_KEY_FIELD: self.parent_key,  # This is our alternate key!
            "mdm_description": "Parent Article (Alternate Key Demo)",
            "mdm_articledescription": "Parent",
            "mdm_casesperpallet": 1,
            "mdm_expenseitem": True,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "Parent",
            "mdm_sellablestatus": True
        }
        
        if not self._post(self.ARTICLE_ENDPOINT, parent_data, "Parent Article"):
            return False
        
        # =====================================================
        # STEP 2: Create Child Article (with known business key)
        # =====================================================
        print("\n" + "-" * 50)
        print("STEP 2/3: Create Child Article")
        print(f"   Using alternate key: {self.ALTERNATE_KEY_FIELD}='{self.child_key}'")
        print("-" * 50)
        
        child_data = {
            "mdm_article_id": f"ART_CHILD_{self.child_key}",
            self.ALTERNATE_KEY_FIELD: self.child_key,  # This is our alternate key!
            "mdm_description": "Child Article (Alternate Key Demo)",
            "mdm_articledescription": "Child",
            "mdm_casesperpallet": 1,
            "mdm_expenseitem": True,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "Child",
            "mdm_sellablestatus": True
        }
        
        if not self._post(self.ARTICLE_ENDPOINT, child_data, "Child Article"):
            return False
        
        # =====================================================
        # STEP 3: Create Relationship using ALTERNATE KEYS!
        # =====================================================
        print("\n" + "-" * 50)
        print("STEP 3/3: Create Relationship using ALTERNATE KEYS")
        print("-" * 50)
        print(f"\n   🔑 Referencing by business key (NOT GUID!):")
        print(f"      Parent: /{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}='{self.parent_key}')")
        print(f"      Child:  /{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}='{self.child_key}')")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        relationship_data = {
            "mdm_relationshipname": f"AltKey Rel {timestamp}",
            "mdm_baseunit": "EA",
            "mdm_unit": "EA",
            # THE KEY PART: Reference by ALTERNATE KEY, not GUID!
            f"{self.PARENT_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}='{self.parent_key}')",
            f"{self.CHILD_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}='{self.child_key}')",
        }
        
        print(f"\n   Payload:")
        print(f"   {{")
        print(f'     "{self.PARENT_NAV_PROP}@odata.bind": "/{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}=\'{self.parent_key}\')"')
        print(f'     "{self.CHILD_NAV_PROP}@odata.bind": "/{self.ARTICLE_ENDPOINT}({self.ALTERNATE_KEY_FIELD}=\'{self.child_key}\')"')
        print(f"   }}")
        
        if not self._post(self.RELATIONSHIP_ENDPOINT, relationship_data, "Relationship"):
            return False
        
        # =====================================================
        # SUCCESS!
        # =====================================================
        print("\n" + "=" * 70)
        print("✅ SUCCESS! All 3 records created and linked!")
        print("=" * 70)
        
        print("\n🎯 MANAGER'S CONCERN ADDRESSED:")
        print("   ✓ Created 2 articles + 1 relationship")
        print("   ✓ NO GUIDs read or stored")
        print("   ✓ Referenced by ALTERNATE KEY instead!")
        print("   ✓ 3 POST calls, 0 GET calls, 0 GUIDs handled")
        
        print(f"\n🔑 Business Keys Used:")
        print(f"   Parent: {self.ALTERNATE_KEY_FIELD}='{self.parent_key}'")
        print(f"   Child:  {self.ALTERNATE_KEY_FIELD}='{self.child_key}'")
        
        print("\n📌 Key Insight:")
        print("   Instead of: /mdm_articles(00000000-0000-0000-0000-000000000000)")
        print(f"   We used:    /mdm_articles({self.ALTERNATE_KEY_FIELD}='PARENT_...')")
        print("\n   The business key is known BEFORE creation, so no need to")
        print("   read or store the GUID from the response!")
        
        print("=" * 70)
        
        return True


def main():
    auto_confirm = "--auto-confirm" in sys.argv or "--yes" in sys.argv
    
    environment = None
    for arg in sys.argv[1:]:
        if arg.startswith("--env="):
            environment = arg.split("=")[1]
            break
    
    poc = ArticleAlternateKeyCreate(auto_confirm=auto_confirm, environment=environment)
    success = poc.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
