"""
Batch Upsert: 1 REG + N LVs + N Relationships using $batch
============================================================

Requirement:
  - If parent record exists → USE IT (don't delete)
  - If parent doesn't exist → CREATE IT
  - Same for children
  - Create relationships linking them

Solution: $batch with PATCH (upsert) + POST (relationships)
  - PATCH parent article (upsert via alternate key)
  - PATCH each child article (upsert via alternate key)
  - POST each relationship with @odata.bind using alternate keys

Key Insight:
  ✅ @odata.bind can use ALTERNATE KEYS - no GUIDs needed!
  Example: "mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='REG_001')"

Benefits:
  ✅ Atomic: All succeed or all fail
  ✅ Idempotent: Safe to re-run (upsert pattern)
  ✅ No GUIDs: Uses alternate keys throughout
  ✅ No READ calls: Zero GET requests needed
  ✅ Preserves existing data: Updates, doesn't delete

Usage:
    python scripts/article_batch_upsert.py --env=DEV --auto-confirm
    python scripts/article_batch_upsert.py --env=DEV --children=10
"""

import os
import sys
import argparse
import requests
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class BatchUpsertMultipleChildren:
    """
    Batch Upsert: PATCH parent + PATCH children + POST relationships.
    All in one atomic $batch request using alternate keys.
    """
    
    ARTICLE_ENDPOINT = "mdm_articles"
    RELATIONSHIP_ENDPOINT = "mdm_articlerelationships"
    
    # Navigation properties for @odata.bind
    PARENT_NAV_PROP = "mdm_ParentArticle"
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
    
    def _build_batch_request(self, reg_itemcode: str, num_children: int) -> tuple:
        """
        Build the $batch request body.
        
        Structure:
        1. PATCH parent (upsert)
        2. PATCH each child (upsert)
        3. POST each relationship (with @odata.bind using alternate keys)
        
        Returns: (batch_body, changeset_id, batch_id)
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        changeset_id = f"changeset_{uuid.uuid4().hex[:8]}"
        
        parts = []
        
        # Start changeset (for atomicity)
        parts.append(f"--{batch_id}")
        parts.append(f"Content-Type: multipart/mixed; boundary={changeset_id}")
        parts.append("")
        
        content_id = 0
        
        # === 1. PATCH Parent Article (Upsert) ===
        content_id += 1
        parent_payload = {
            self.ALT_KEY: reg_itemcode,
            "mdm_article_id": f"REG Article {self.ts}",
            "mdm_articledescription": "Regular Article - Upserted via Batch",
            "mdm_description": f"REG with {num_children} LVs - Batch Upsert",
            "mdm_casesperpallet": 100,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_logisticalvariantdescription": "REG",
            "mdm_sellablestatus": True
        }
        
        parts.append(f"--{changeset_id}")
        parts.append("Content-Type: application/http")
        parts.append("Content-Transfer-Encoding: binary")
        parts.append(f"Content-ID: {content_id}")
        parts.append("")
        # PATCH with alternate key URL = Upsert
        parts.append(f"PATCH {self.org_url}/api/data/v9.2/{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{reg_itemcode}') HTTP/1.1")
        parts.append("Content-Type: application/json")
        parts.append("")
        parts.append(self._json_dumps(parent_payload))
        
        # === 2. PATCH Each Child Article (Upsert) ===
        child_itemcodes = []
        for i in range(1, num_children + 1):
            content_id += 1
            lv_itemcode = f"LV{i}_{self.ts}"
            child_itemcodes.append(lv_itemcode)
            
            child_payload = {
                self.ALT_KEY: lv_itemcode,
                "mdm_article_id": f"LV{i} Article {self.ts}",
                "mdm_articledescription": f"Logistical Variant {i} - Upserted via Batch",
                "mdm_description": f"LV{i} for {reg_itemcode}",
                "mdm_casesperpallet": 10 + i,
                "mdm_expenseitem": False,
                "mdm_fooditem": True,
                "mdm_hazard": False,
                "mdm_logisticalvariantdescription": f"LV{i} Variant",
                "mdm_sellablestatus": True
            }
            
            parts.append(f"--{changeset_id}")
            parts.append("Content-Type: application/http")
            parts.append("Content-Transfer-Encoding: binary")
            parts.append(f"Content-ID: {content_id}")
            parts.append("")
            parts.append(f"PATCH {self.org_url}/api/data/v9.2/{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{lv_itemcode}') HTTP/1.1")
            parts.append("Content-Type: application/json")
            parts.append("")
            parts.append(self._json_dumps(child_payload))
        
        # === 3. POST Each Relationship (with @odata.bind using alternate keys) ===
        for i, lv_itemcode in enumerate(child_itemcodes, 1):
            content_id += 1
            
            # Use alternate keys in @odata.bind - NO GUIDs needed!
            relationship_payload = {
                "mdm_relationshipname": f"{reg_itemcode}-to-{lv_itemcode}",
                "mdm_baseunit": "EA",
                "mdm_unit": "EA",
                # Bind to parent using alternate key
                f"{self.PARENT_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{reg_itemcode}')",
                # Bind to child using alternate key
                f"{self.CHILD_NAV_PROP}@odata.bind": f"/{self.ARTICLE_ENDPOINT}({self.ALT_KEY}='{lv_itemcode}')"
            }
            
            parts.append(f"--{changeset_id}")
            parts.append("Content-Type: application/http")
            parts.append("Content-Transfer-Encoding: binary")
            parts.append(f"Content-ID: {content_id}")
            parts.append("")
            parts.append(f"POST {self.org_url}/api/data/v9.2/{self.RELATIONSHIP_ENDPOINT} HTTP/1.1")
            parts.append("Content-Type: application/json")
            parts.append("")
            parts.append(self._json_dumps(relationship_payload))
        
        # End changeset
        parts.append(f"--{changeset_id}--")
        
        # End batch
        parts.append(f"--{batch_id}--")
        
        batch_body = "\r\n".join(parts)
        
        return batch_body, changeset_id, batch_id, child_itemcodes
    
    def _json_dumps(self, obj: dict) -> str:
        """Convert dict to JSON string without extra spaces."""
        import json
        return json.dumps(obj, separators=(',', ':'))
    
    def batch_upsert_with_relationships(self, num_children: int = 5) -> dict:
        """
        Execute batch upsert: PATCH parent + PATCH children + POST relationships.
        
        All operations are atomic - all succeed or all fail.
        Uses alternate keys throughout - no GUIDs needed!
        """
        
        print("\n" + "=" * 70)
        print(f"BATCH UPSERT: 1 REG + {num_children} LVs + {num_children} Relationships")
        print("=" * 70)
        
        reg_itemcode = f"REG_BATCH_{self.ts}"
        
        print(f"\n📦 Operations in this batch:")
        print(f"   1. PATCH (upsert) parent: {reg_itemcode}")
        for i in range(1, num_children + 1):
            print(f"   {1+i}. PATCH (upsert) child: LV{i}_{self.ts}")
        for i in range(1, num_children + 1):
            print(f"   {1+num_children+i}. POST relationship: {reg_itemcode} → LV{i}_{self.ts}")
        
        total_ops = 1 + num_children + num_children  # parent + children + relationships
        print(f"\n   📊 Total operations: {total_ops} (in 1 atomic batch)")
        print(f"   ✅ Idempotent: Parent and children use UPSERT")
        print(f"   ⚠️  Relationships: Will fail if already exist (use unique names)")
        
        if not self._confirm("Execute batch?"):
            return {"success": False, "error": "Cancelled"}
        
        # Build batch request
        batch_body, changeset_id, batch_id, child_itemcodes = self._build_batch_request(
            reg_itemcode, num_children
        )
        
        # Execute batch
        url = f"{self.org_url}/api/data/v9.2/$batch"
        headers = self.client._get_headers()
        headers["Content-Type"] = f"multipart/mixed; boundary={batch_id}"
        headers["Accept"] = "application/json"
        headers["OData-MaxVersion"] = "4.0"
        headers["OData-Version"] = "4.0"
        
        print(f"\n🚀 Executing batch request...")
        print(f"   URL: {url}")
        print(f"   Batch ID: {batch_id}")
        print(f"   Changeset ID: {changeset_id}")
        print(f"   Total operations: {total_ops}")
        
        try:
            response = requests.post(url, headers=headers, data=batch_body)
            
            print(f"\n📡 Response: HTTP {response.status_code}")
            
            if response.status_code in [200, 202]:
                # Parse batch response to check for individual failures
                response_text = response.text
                
                # Check if any operation failed
                if "HTTP/1.1 4" in response_text or "HTTP/1.1 5" in response_text:
                    print(f"\n⚠️  BATCH COMPLETED WITH ERRORS!")
                    print(f"\nResponse excerpt:")
                    # Find and print error sections
                    lines = response_text.split('\n')
                    in_error = False
                    for line in lines:
                        if "HTTP/1.1 4" in line or "HTTP/1.1 5" in line:
                            in_error = True
                        if in_error:
                            print(f"   {line.strip()}")
                            if line.strip().startswith('"message"'):
                                in_error = False
                    
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": "Some operations failed",
                        "response": response_text[:2000]
                    }
                
                print(f"\n✅ BATCH COMPLETED SUCCESSFULLY!")
                print(f"\n{'=' * 70}")
                print("BATCH UPSERT RESULTS")
                print('=' * 70)
                print(f"""
   Upserted:
   ├─ REG (Parent): {reg_itemcode}
   │""")
                for i, lv in enumerate(child_itemcodes, 1):
                    connector = "└" if i == num_children else "├"
                    print(f"   {connector}── LV{i}: {lv}")
                    print(f"   {'   ' if i == num_children else '│'}     + Relationship created")
                
                print(f"""
   Summary:
   ├─ Parent Upserts: 1
   ├─ Child Upserts: {num_children}
   ├─ Relationships Created: {num_children}
   ├─ Total Operations: {total_ops}
   ├─ API Calls: 1 ($batch)
   ├─ GUIDs Used: 0 (alternate keys only!)
   └─ READ Calls: 0
""")
                
                return {
                    "success": True,
                    "reg_itemcode": reg_itemcode,
                    "child_itemcodes": child_itemcodes,
                    "total_operations": total_ops,
                    "api_calls": 1
                }
            else:
                print(f"\n❌ BATCH FAILED!")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text[:1000]}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
            return {"success": False, "error": str(e)}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Upsert: Parent + Children + Relationships")
    parser.add_argument("--env", default="DEV", help="Environment (DEV, PROD)")
    parser.add_argument("--children", type=int, default=5, help="Number of child LVs (default: 5)")
    parser.add_argument("--auto-confirm", action="store_true", help="Skip confirmations")
    args = parser.parse_args()
    
    print("=" * 70)
    print("BATCH UPSERT: PARENT + CHILDREN + RELATIONSHIPS")
    print("=" * 70)
    print(f"""
Approach: $batch with PATCH (upsert) + POST (relationships)

Pattern:
  1. PATCH parent article    → Upsert (creates or updates)
  2. PATCH each child article → Upsert (creates or updates)
  3. POST each relationship   → Create with @odata.bind

Key Features:
  ✅ Atomic: All operations succeed or all fail
  ✅ Idempotent: PATCH = upsert (safe to re-run for articles)
  ✅ No GUIDs: Uses alternate keys in @odata.bind
  ✅ No READs: Zero GET requests needed
  ✅ Preserves Data: Updates existing, creates new

⚠️  Note: Relationships use POST (not upsert) - will fail if
    relationship with same name already exists.

Operations:
  - 1 REG (parent) upsert
  - {args.children} LV (child) upserts
  - {args.children} Relationship creates
""")
    
    poc = BatchUpsertMultipleChildren(auto_confirm=args.auto_confirm, environment=args.env)
    
    if not poc.authenticate():
        sys.exit(1)
    
    result = poc.batch_upsert_with_relationships(num_children=args.children)
    
    if result.get("success"):
        print(f"\n✅ Batch upsert completed successfully!")
        print(f"\n💡 Run again to test upsert behavior - parent and children will UPDATE, ")
        print(f"   but relationships will FAIL (duplicate) unless you change the timestamp.")
    else:
        print(f"\n❌ Batch upsert failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
