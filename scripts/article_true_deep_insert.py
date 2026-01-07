"""
TRUE Deep Insert - Create ALL 3 Records in ONE API Call!
=========================================================

Manager's Insight:
  "You can create Article 1, the Relationship record, and Article 2 
   all in a single atomic POST request."

This script demonstrates:
1. Option A: Deep Insert with Alternate Key (child already exists)
2. Option B: TRUE Deep Insert (all 3 records in ONE call!)
3. Option C: Batch with Upserts (idempotent pattern)

Usage:
    python scripts/article_true_deep_insert.py --env=DEV --option=A --auto-confirm
    python scripts/article_true_deep_insert.py --env=DEV --option=B --auto-confirm
    python scripts/article_true_deep_insert.py --env=DEV --option=C --auto-confirm
"""

import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class TrueDeepInsert:
    """Demonstrate all deep insert approaches including TRUE single-call creation."""
    
    ARTICLE_ENDPOINT = "mdm_articles"
    RELATIONSHIP_ENDPOINT = "mdm_articlerelationships"
    
    # Navigation property names (discovered from metadata)
    # Collection nav prop on article (for deep insert)
    PARENT_COLLECTION_NAV_PROP = "mdm_articlerelationship_ParentArticle_mdm_article"
    
    # Single-valued nav props on relationship
    PARENT_NAV_PROP = "mdm_ParentArticle"  # Points to parent article
    CHILD_NAV_PROP = "mdm_ChildArticle"    # Points to child article
    
    # Alternate key field
    ALT_KEY = "mdm_itemcode"
    
    def __init__(self, auto_confirm: bool = False, environment: str = None):
        self.config = Config()
        self.client = None
        self.auto_confirm = auto_confirm
        self.environment = environment or "DEV"
        self.org_url = None
        
        # Generate unique keys
        self.ts = datetime.now().strftime("%Y%m%d%H%M%S")
        self.parent_key = f"PARENT_{self.ts}"
        self.child_key = f"CHILD_{self.ts}"
    
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
                print(f"   {self.org_url}")
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
    
    def _post(self, endpoint: str, data: dict, description: str) -> dict:
        """POST request to Dataverse."""
        url = f"{self.org_url}/api/data/v9.2/{endpoint}"
        headers = self.client._get_headers()
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201, 204]:
                return {"success": True, "data": response.json() if response.text else {}}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text[:500]}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _batch(self, operations: list) -> dict:
        """Execute batch request."""
        url = f"{self.org_url}/api/data/v9.2/$batch"
        headers = self.client._get_headers()
        
        batch_id = f"batch_{self.ts}"
        changeset_id = f"changeset_{self.ts}"
        
        headers["Content-Type"] = f"multipart/mixed; boundary={batch_id}"
        
        # Build batch body
        body_parts = []
        body_parts.append(f"--{batch_id}")
        body_parts.append(f"Content-Type: multipart/mixed; boundary={changeset_id}")
        body_parts.append("")
        
        for i, op in enumerate(operations, 1):
            body_parts.append(f"--{changeset_id}")
            body_parts.append("Content-Type: application/http")
            body_parts.append("Content-Transfer-Encoding: binary")
            body_parts.append(f"Content-ID: {i}")
            body_parts.append("")
            body_parts.append(f"{op['method']} {self.org_url}/api/data/v9.2/{op['endpoint']} HTTP/1.1")
            body_parts.append("Content-Type: application/json")
            body_parts.append("")
            body_parts.append(json.dumps(op['data']))
            body_parts.append("")
        
        body_parts.append(f"--{changeset_id}--")
        body_parts.append(f"--{batch_id}--")
        
        body = "\r\n".join(body_parts)
        
        try:
            response = requests.post(url, headers=headers, data=body.encode('utf-8'))
            
            if response.status_code in [200, 204]:
                return {"success": True, "data": response.text}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text[:1000]}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # OPTION A: Deep Insert with Child Existing (2 API calls)
    # =========================================================================
    def option_a_deep_insert_child_exists(self) -> bool:
        """
        Deep Insert where child article already exists.
        
        Call 1: Create Child Article
        Call 2: Deep Insert Parent + Relationship (references child via alternate key)
        
        Result: 2 API calls, child referenced by alternate key
        """
        print("\n" + "=" * 70)
        print("OPTION A: Deep Insert (Child Already Exists)")
        print("=" * 70)
        print("\n📋 Strategy:")
        print("   1. Create Child Article first")
        print("   2. Deep Insert Parent + nested Relationship")
        print("   3. Relationship references Child via ALTERNATE KEY")
        print("\n   Result: 2 API calls, 0 GUIDs needed!")
        
        if not self._confirm("Execute Option A?"):
            return False
        
        # Step 1: Create Child
        print("\n" + "-" * 50)
        print("STEP 1: Create Child Article")
        print("-" * 50)
        
        child_data = {
            self.ALT_KEY: self.child_key,
            "mdm_article_id": f"Child_{self.ts}",
            "mdm_articledescription": "Child Article (Option A)",
            "mdm_description": "Created first for deep insert",
            "mdm_casesperpallet": 1,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "Child",
            "mdm_sellablestatus": True
        }
        
        print(f"\nPOST /mdm_articles")
        print(f"   {self.ALT_KEY}: {self.child_key}")
        
        result = self._post(self.ARTICLE_ENDPOINT, child_data, "Child Article")
        if not result["success"]:
            print(f"\n❌ Failed: {result['error']}")
            return False
        
        print(f"   ✅ Child created!")
        
        # Step 2: Deep Insert Parent + Relationship
        print("\n" + "-" * 50)
        print("STEP 2: Deep Insert Parent + Relationship")
        print("-" * 50)
        
        parent_data = {
            self.ALT_KEY: self.parent_key,
            "mdm_article_id": f"Parent_{self.ts}",
            "mdm_articledescription": "Parent Article (Option A)",
            "mdm_description": "Deep inserted with nested relationship",
            "mdm_casesperpallet": 1,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "Parent",
            "mdm_sellablestatus": True,
            
            # DEEP INSERT: Nested relationship
            self.PARENT_COLLECTION_NAV_PROP: [
                {
                    "mdm_relationshipname": f"Rel_OptionA_{self.ts}",
                    "mdm_baseunit": "EA",
                    "mdm_unit": "EA",
                    # Reference child via ALTERNATE KEY
                    f"{self.CHILD_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{self.child_key}')"
                }
            ]
        }
        
        print(f"\nPOST /mdm_articles (with nested relationship)")
        print(f"   Parent: {self.ALT_KEY}='{self.parent_key}'")
        print(f"   Nested: {self.PARENT_COLLECTION_NAV_PROP}[]")
        print(f"      └─ {self.CHILD_NAV_PROP}@odata.bind: ...({self.ALT_KEY}='{self.child_key}')")
        
        result = self._post(self.ARTICLE_ENDPOINT, parent_data, "Parent + Relationship")
        if not result["success"]:
            print(f"\n❌ Failed: {result['error']}")
            return False
        
        print(f"   ✅ Parent + Relationship created!")
        
        self._print_success("Option A", 2)
        return True
    
    # =========================================================================
    # OPTION B: TRUE Deep Insert - ALL 3 Records in ONE Call!
    # =========================================================================
    def option_b_true_deep_insert(self) -> bool:
        """
        TRUE Deep Insert: Create Parent, Relationship, AND Child in ONE call!
        
        The child article is NESTED inside the relationship payload.
        
        Result: 1 API call creates all 3 records!
        """
        print("\n" + "=" * 70)
        print("OPTION B: TRUE Deep Insert (1 API Call = 3 Records!)")
        print("=" * 70)
        print("\n📋 Strategy:")
        print("   Single POST creates:")
        print("   └─ Parent Article")
        print("      └─ Relationship")
        print("         └─ Child Article (nested!)")
        print("\n   Result: 1 API call, 3 records, 0 GUIDs!")
        
        if not self._confirm("Execute Option B?"):
            return False
        
        # Single call with fully nested structure
        print("\n" + "-" * 50)
        print("SINGLE POST: Parent + Relationship + Child")
        print("-" * 50)
        
        # Use fresh keys for this test
        parent_key = f"PARENT_B_{self.ts}"
        child_key = f"CHILD_B_{self.ts}"
        
        payload = {
            self.ALT_KEY: parent_key,
            "mdm_article_id": f"Parent_TrueDeep_{self.ts}",
            "mdm_articledescription": "Parent Article (TRUE Deep Insert)",
            "mdm_description": "Created with fully nested child",
            "mdm_casesperpallet": 1,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "Parent",
            "mdm_sellablestatus": True,
            
            # DEEP INSERT: Nested relationship with NESTED CHILD!
            self.PARENT_COLLECTION_NAV_PROP: [
                {
                    "mdm_relationshipname": f"Rel_TrueDeep_{self.ts}",
                    "mdm_baseunit": "EA",
                    "mdm_unit": "EA",
                    
                    # TRUE DEEP INSERT: Child article nested INSIDE relationship!
                    self.CHILD_NAV_PROP: {
                        self.ALT_KEY: child_key,
                        "mdm_article_id": f"Child_TrueDeep_{self.ts}",
                        "mdm_articledescription": "Child Article (Nested in Deep Insert)",
                        "mdm_description": "Created inside relationship",
                        "mdm_casesperpallet": 1,
                        "mdm_expenseitem": False,
                        "mdm_fooditem": True,
                        "mdm_hazard": False,
                        "mdm_logisticalvariantdescription": "Child",
                        "mdm_sellablestatus": True
                    }
                }
            ]
        }
        
        print(f"\nPOST /mdm_articles")
        print(f"\n📦 Payload Structure:")
        print(f"   {{")
        print(f"     \"{self.ALT_KEY}\": \"{parent_key}\",")
        print(f"     \"mdm_article_id\": \"Parent_TrueDeep_{self.ts}\",")
        print(f"     \"{self.PARENT_COLLECTION_NAV_PROP}\": [")
        print(f"       {{")
        print(f"         \"mdm_relationshipname\": \"Rel_TrueDeep_{self.ts}\",")
        print(f"         \"{self.CHILD_NAV_PROP}\": {{                   ← NESTED CHILD!")
        print(f"           \"{self.ALT_KEY}\": \"{child_key}\",")
        print(f"           \"mdm_article_id\": \"Child_TrueDeep_{self.ts}\"")
        print(f"         }}")
        print(f"       }}")
        print(f"     ]")
        print(f"   }}")
        
        result = self._post(self.ARTICLE_ENDPOINT, payload, "TRUE Deep Insert")
        
        if not result["success"]:
            print(f"\n❌ Failed: {result['error']}")
            print("\n💡 Note: If this fails, Dataverse may not support this level of nesting")
            print("   for your specific table configuration. Try Option A or C instead.")
            return False
        
        print(f"\n   ✅ SUCCESS! All 3 records created in ONE call!")
        
        self._print_success("Option B", 1)
        return True
    
    # =========================================================================
    # OPTION C: Batch with Upserts (Idempotent Pattern)
    # =========================================================================
    def option_c_batch_upsert(self) -> bool:
        """
        Batch with PATCH (Upsert) - Idempotent pattern.
        
        Uses PATCH with alternate keys for articles (upsert behavior)
        and POST for relationship. All in one atomic batch.
        
        Benefits:
        - Idempotent: Re-running won't fail on duplicates
        - Transactional: All succeed or all fail
        - Zero latency: No GET calls needed
        """
        print("\n" + "=" * 70)
        print("OPTION C: Batch with Upserts (Idempotent Pattern)")
        print("=" * 70)
        print("\n📋 Strategy:")
        print("   Single $batch request with changeset:")
        print("   - PATCH Article 1 (upsert via alternate key)")
        print("   - PATCH Article 2 (upsert via alternate key)")
        print("   - POST Relationship (using alternate key bindings)")
        print("\n   Benefits:")
        print("   - Idempotent: Re-run safe, no duplicate errors")
        print("   - Transactional: All or nothing")
        print("   - 1 HTTP request (contains 3 operations)")
        
        if not self._confirm("Execute Option C?"):
            return False
        
        # Use fresh keys
        parent_key = f"PARENT_C_{self.ts}"
        child_key = f"CHILD_C_{self.ts}"
        
        print("\n" + "-" * 50)
        print("BATCH REQUEST: 3 Operations in Changeset")
        print("-" * 50)
        
        operations = [
            {
                "method": "PATCH",
                "endpoint": f"{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{parent_key}')",
                "data": {
                    "mdm_article_id": f"Parent_Batch_{self.ts}",
                    "mdm_articledescription": "Parent Article (Batch Upsert)",
                    "mdm_description": "Created via batch upsert",
                    "mdm_casesperpallet": 1,
                    "mdm_expenseitem": False,
                    "mdm_fooditem": True,
                    "mdm_hazard": False,
                    "mdm_logisticalvariantdescription": "Parent",
                    "mdm_sellablestatus": True
                }
            },
            {
                "method": "PATCH",
                "endpoint": f"{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{child_key}')",
                "data": {
                    "mdm_article_id": f"Child_Batch_{self.ts}",
                    "mdm_articledescription": "Child Article (Batch Upsert)",
                    "mdm_description": "Created via batch upsert",
                    "mdm_casesperpallet": 1,
                    "mdm_expenseitem": False,
                    "mdm_fooditem": True,
                    "mdm_hazard": False,
                    "mdm_logisticalvariantdescription": "Child",
                    "mdm_sellablestatus": True
                }
            },
            {
                "method": "POST",
                "endpoint": self.RELATIONSHIP_ENDPOINT,
                "data": {
                    "mdm_relationshipname": f"Rel_Batch_{self.ts}",
                    "mdm_baseunit": "EA",
                    "mdm_unit": "EA",
                    f"{self.PARENT_NAV_PROP}@odata.bind": f"{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{parent_key}')",
                    f"{self.CHILD_NAV_PROP}@odata.bind": f"{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{child_key}')"
                }
            }
        ]
        
        print(f"\nPOST /$batch")
        print(f"\n📦 Changeset Operations:")
        for i, op in enumerate(operations, 1):
            print(f"   {i}. {op['method']} /{op['endpoint'][:50]}...")
        
        result = self._batch(operations)
        
        if not result["success"]:
            print(f"\n❌ Batch failed: {result['error']}")
            return False
        
        # Check for errors in response
        response_text = result.get("data", "")
        if "HTTP/1.1 4" in response_text or "HTTP/1.1 5" in response_text:
            print(f"\n⚠️  Batch completed but contains errors:")
            print(response_text[:1000])
            return False
        
        print(f"\n   ✅ Batch completed successfully!")
        
        self._print_success("Option C", 1, note="(1 batch = 3 operations)")
        return True
    
    def _print_success(self, option: str, calls: int, note: str = ""):
        """Print success summary."""
        print("\n" + "=" * 70)
        print(f"✅ {option} SUCCESS!")
        print("=" * 70)
        print(f"""
   Records Created:
   ├─ Article (Parent)
   ├─ Article (Child)
   └─ Relationship (linking them)

   API Calls: {calls} {note}
   GUIDs Needed: 0
   READ Calls: 0
""")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TRUE Deep Insert Demo")
    parser.add_argument("--env", default="DEV", help="Environment (DEV, PROD)")
    parser.add_argument("--option", default="B", choices=["A", "B", "C", "ALL"],
                        help="Which option to run (A, B, C, or ALL)")
    parser.add_argument("--auto-confirm", action="store_true", help="Skip confirmations")
    args = parser.parse_args()
    
    print("=" * 70)
    print("TRUE DEEP INSERT DEMO")
    print("=" * 70)
    print("""
    Manager's Insight:
    "You can create Article 1, the Relationship record, and Article 2 
     all in a single atomic POST request."

    Options:
    A: Deep Insert (child exists) - 2 calls
    B: TRUE Deep Insert - 1 call creates ALL 3 records!
    C: Batch Upsert - 1 batch with 3 idempotent operations
""")
    
    poc = TrueDeepInsert(auto_confirm=args.auto_confirm, environment=args.env)
    
    if not poc.authenticate():
        print("❌ Authentication failed!")
        sys.exit(1)
    
    option = args.option.upper()
    
    if option == "A" or option == "ALL":
        poc.option_a_deep_insert_child_exists()
        poc.ts = datetime.now().strftime("%Y%m%d%H%M%S")  # New timestamp
    
    if option == "B" or option == "ALL":
        poc.option_b_true_deep_insert()
        poc.ts = datetime.now().strftime("%Y%m%d%H%M%S")  # New timestamp
    
    if option == "C" or option == "ALL":
        poc.option_c_batch_upsert()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
