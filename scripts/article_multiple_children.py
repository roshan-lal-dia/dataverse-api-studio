"""
Multiple Children Deep Insert - 1 REG + 5 LVs in ONE API Call!
==============================================================

Use Case (from Manager):
  "If we have 5 LV that we need to associate with REG"

Solution:
  Single POST creates:
  - 1 REG (Parent Article)
  - 5 LV (Child Articles)
  - 5 Relationships (linking REG to each LV)

Total: 11 records in 1 API call!

Usage:
    python scripts/article_multiple_children.py --env=DEV --auto-confirm
"""

import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class MultipleChildrenDeepInsert:
    """Create 1 Parent + N Children + N Relationships in ONE API call."""
    
    ARTICLE_ENDPOINT = "mdm_articles"
    
    # Collection nav prop on article (for deep insert)
    PARENT_COLLECTION_NAV_PROP = "mdm_articlerelationship_ParentArticle_mdm_article"
    
    # Single-valued nav prop on relationship
    CHILD_NAV_PROP = "mdm_ChildArticle"
    
    # Alternate key field
    ALT_KEY = "mdm_itemcode"
    
    def __init__(self, auto_confirm: bool = False, environment: str = None):
        self.config = Config()
        self.client = None
        self.auto_confirm = auto_confirm
        self.environment = environment or "DEV"
        self.org_url = None
        self.ts = datetime.now().strftime("%Y%m%d%H%M%S")
    
    def authenticate(self) -> bool:
        """Authenticate with Dataverse."""
        print("\n🔐 Authenticating...")
        try:
            tenant_id = self.config.get_tenant_id()
            client_id = self.config.get_client_id()
            client_secret = self.config.get_client_secret()
            
            environments = self.config.get_available_environments()
            env_upper = self.environment.upper()
            env_name = next((e for e in environments.keys() if e.upper() == env_upper), None)
            
            if not env_name:
                print(f"❌ Environment '{self.environment}' not found")
                return False
            
            self.org_url = environments[env_name]
            self.client = MetadataClient(tenant_id, client_id, client_secret, self.org_url)
            
            if self.client.authenticate():
                print(f"✅ Authenticated to {env_name}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def _confirm(self, message: str = "Proceed?") -> bool:
        if self.auto_confirm:
            print("   ✓ Auto-confirmed")
            return True
        response = input(f"\n{message} (yes/no): ").strip().lower()
        return response in ["yes", "y"]
    
    def create_reg_with_multiple_lvs(self, num_children: int = 5) -> dict:
        """
        Create 1 REG (parent) + N LVs (children) + N relationships in ONE call!
        
        Structure:
        POST /mdm_articles
        {
          "REG article data...",
          "mdm_articlerelationship_ParentArticle_mdm_article": [
            { "relationship 1", "mdm_ChildArticle": { "LV1 data" } },
            { "relationship 2", "mdm_ChildArticle": { "LV2 data" } },
            { "relationship 3", "mdm_ChildArticle": { "LV3 data" } },
            { "relationship 4", "mdm_ChildArticle": { "LV4 data" } },
            { "relationship 5", "mdm_ChildArticle": { "LV5 data" } }
          ]
        }
        """
        
        print("\n" + "=" * 70)
        print(f"MULTIPLE CHILDREN DEEP INSERT: 1 REG + {num_children} LVs")
        print("=" * 70)
        
        reg_itemcode = f"REG_{self.ts}"
        
        print(f"\n📦 What will be created in 1 API call:")
        print(f"   - 1 REG (Parent): {reg_itemcode}")
        for i in range(1, num_children + 1):
            print(f"   - LV{i} (Child): LV{i}_{self.ts}")
        print(f"   - {num_children} Relationships linking them")
        print(f"\n   Total: {1 + num_children + num_children} records = 1 API call!")
        
        if not self._confirm("Execute?"):
            return {"success": False, "error": "Cancelled"}
        
        # Build the nested relationships array
        relationships = []
        for i in range(1, num_children + 1):
            lv_itemcode = f"LV{i}_{self.ts}"
            
            relationship = {
                "mdm_relationshipname": f"REG-to-LV{i}_{self.ts}",
                "mdm_baseunit": "EA",
                "mdm_unit": "EA",
                
                # NESTED CHILD CREATION
                self.CHILD_NAV_PROP: {
                    self.ALT_KEY: lv_itemcode,
                    "mdm_article_id": f"Logistical Variant {i}",
                    "mdm_articledescription": f"LV{i} for REG_{self.ts}",
                    "mdm_description": f"Logistical Variant {i} - Created via deep insert",
                    "mdm_casesperpallet": i * 10,  # Different values
                    "mdm_expenseitem": False,
                    "mdm_fooditem": True,
                    "mdm_hazard": False,
                    "mdm_logisticalvariantdescription": f"LV{i} Description",
                    "mdm_sellablestatus": True
                }
            }
            relationships.append(relationship)
        
        # Full payload: REG + nested relationships with nested children
        payload = {
            self.ALT_KEY: reg_itemcode,
            "mdm_article_id": f"Regular Article {self.ts}",
            "mdm_articledescription": f"REG with {num_children} LVs",
            "mdm_description": f"Parent article with {num_children} logistical variants",
            "mdm_casesperpallet": 100,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "REG",
            "mdm_sellablestatus": True,
            
            # ARRAY OF NESTED RELATIONSHIPS WITH NESTED CHILDREN
            self.PARENT_COLLECTION_NAV_PROP: relationships
        }
        
        print("\n" + "-" * 70)
        print("SINGLE POST REQUEST")
        print("-" * 70)
        print(f"\nPOST /api/data/v9.2/mdm_articles")
        print(f"\n📦 Payload Structure:")
        print(f"{{")
        print(f'  "{self.ALT_KEY}": "{reg_itemcode}",')
        print(f'  "mdm_article_id": "Regular Article...",')
        print(f'  "{self.PARENT_COLLECTION_NAV_PROP}": [')
        for i in range(1, min(3, num_children + 1)):  # Show first 2-3
            print(f'    {{')
            print(f'      "mdm_relationshipname": "REG-to-LV{i}...",')
            print(f'      "{self.CHILD_NAV_PROP}": {{')
            print(f'        "{self.ALT_KEY}": "LV{i}_{self.ts}",')
            print(f'        "mdm_article_id": "Logistical Variant {i}"')
            print(f'      }}')
            print(f'    }},')
        if num_children > 3:
            print(f'    ... ({num_children - 3} more relationships)')
        print(f'  ]')
        print(f'}}')
        
        # Execute the API call
        url = f"{self.org_url}/api/data/v9.2/{self.ARTICLE_ENDPOINT}"
        headers = self.client._get_headers()
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
        
        print(f"\n🚀 Executing single POST...")
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"\n✅ SUCCESS! HTTP {response.status_code}")
                
                result_data = response.json()
                reg_guid = result_data.get("mdm_articleid", "N/A")
                
                print("\n" + "=" * 70)
                print("✅ ALL RECORDS CREATED IN 1 API CALL!")
                print("=" * 70)
                print(f"""
   Created:
   ├─ REG (Parent): {reg_itemcode}
   │     GUID: {reg_guid}
   │""")
                for i in range(1, num_children + 1):
                    connector = "└" if i == num_children else "├"
                    print(f"   {connector}── LV{i}: LV{i}_{self.ts}")
                    print(f"   {'   ' if i == num_children else '│'}     + Relationship: REG-to-LV{i}")
                
                print(f"""
   Summary:
   ├─ Total Records: {1 + num_children + num_children}
   ├─ API Calls: 1
   ├─ GUIDs Needed: 0
   └─ READ Calls: 0
""")
                
                return {
                    "success": True,
                    "reg_itemcode": reg_itemcode,
                    "reg_guid": reg_guid,
                    "children_count": num_children,
                    "total_records": 1 + num_children + num_children
                }
            else:
                print(f"\n❌ FAILED: HTTP {response.status_code}")
                print(f"   {response.text[:500]}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"success": False, "error": str(e)}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multiple Children Deep Insert")
    parser.add_argument("--env", default="DEV", help="Environment (DEV, PROD)")
    parser.add_argument("--children", type=int, default=5, help="Number of child LVs (default: 5)")
    parser.add_argument("--auto-confirm", action="store_true", help="Skip confirmations")
    args = parser.parse_args()
    
    print("=" * 70)
    print("MULTIPLE CHILDREN DEEP INSERT")
    print("=" * 70)
    print(f"""
    Use Case: "If we have 5 LV that we need to associate with REG"
    
    This demonstrates creating:
    - 1 REG (Regular Article) as parent
    - {args.children} LV (Logistical Variants) as children
    - {args.children} Relationships linking them
    
    All in ONE API call!
""")
    
    poc = MultipleChildrenDeepInsert(auto_confirm=args.auto_confirm, environment=args.env)
    
    if not poc.authenticate():
        print("❌ Authentication failed!")
        sys.exit(1)
    
    result = poc.create_reg_with_multiple_lvs(num_children=args.children)
    
    if result.get("success"):
        print("\n🎉 Demo complete! Check Dataverse to verify all records.")
    else:
        print(f"\n❌ Failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
