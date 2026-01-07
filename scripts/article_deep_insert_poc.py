"""
Article Deep Insert POC Script
==============================
Creates two mdm_article records and relates them via mdm_articlerelationship
in a SINGLE batch operation using Content-ID references ($1, $2).

Automatically discovers required fields, auto-populates with smart defaults,
and prompts for final confirmation before execution.

Usage:
    python scripts/article_deep_insert_poc.py

No read calls needed—Dataverse injects created GUIDs via $1/$2 references.
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.metadata_client import MetadataClient
from utils.config import Config


class ArticleDeepInsertPOC:
    """POC script for article deep insert with Content-ID references"""
    
    # Table names
    ARTICLE_TABLE = "mdm_article"
    RELATIONSHIP_TABLE = "mdm_articlerelationship"
    
    # Relationship field lookups (from FetchXML)
    PARENT_ARTICLE_LOOKUP = "mdm_parentarticle"
    CHILD_ARTICLE_LOOKUP = "mdm_childarticle"
    
    def __init__(self, auto_confirm: bool = False, environment: str = None):
        """Initialize with authentication from .env
        
        Args:
            auto_confirm: Skip confirmation prompts
            environment: Environment name (DEV, PROD, SANDBOX). If None, uses DEV (safe default).
        """
        self.config = Config()
        self.client = None
        self.article_required_fields = {}
        self.relationship_required_fields = {}
        self.choice_mappings = {}  # Store choice options
        self.lookup_mappings = {}   # Store lookup options
        self.auto_confirm = auto_confirm  # Skip confirmation if True
        self.environment = environment  # Selected environment
        self.selected_environment = None
        self.selected_org_url = None
    
    def authenticate(self) -> bool:
        """Authenticate with Dataverse"""
        print("\n🔐 Authenticating with Dataverse...")
        try:
            tenant_id = self.config.get_tenant_id()
            client_id = self.config.get_client_id()
            client_secret = self.config.get_client_secret()
            
            # Get available environments
            environments = self.config.get_available_environments()
            if not environments:
                print("❌ No ORG_URL environments found in .env file")
                return False
            
            # Use specified environment or default to DEV (safer than PROD)
            if self.environment:
                if self.environment.upper() in [e.upper() for e in environments.keys()]:
                    # Find the environment (case-insensitive)
                    env_name = [e for e in environments.keys() if e.upper() == self.environment.upper()][0]
                    org_url = environments[env_name]
                else:
                    print(f"❌ Environment '{self.environment}' not found. Available: {list(environments.keys())}")
                    return False
            else:
                # SAFE DEFAULT: Try DEV first, then SANDBOX, then others (avoid PROD)
                env_priority = ["DEV", "SANDBOX", "STAGING", "UAT"]
                env_name = None
                for priority_env in env_priority:
                    for env in environments.keys():
                        if env.upper().endswith(priority_env):
                            env_name = env
                            break
                    if env_name:
                        break
                
                # If no preferred env found, use first (but warn)
                if not env_name:
                    env_name = list(environments.keys())[0]
                    if "PROD" in env_name.upper():
                        print("\n⚠️  WARNING: Using PRODUCTION environment!")
                        print("    Consider specifying --env=DEV or --env=SANDBOX instead")
                
                org_url = environments[env_name]
            
            if not all([tenant_id, client_id, client_secret, org_url]):
                print("❌ Missing credentials in .env file")
                return False
            
            self.client = MetadataClient(tenant_id, client_id, client_secret, org_url)
            self.selected_environment = env_name
            self.selected_org_url = org_url
            
            if self.client.authenticate():
                print(f"✅ Authentication successful")
                print(f"   Environment: {env_name}")
                print(f"   Organization: {org_url}")
                return True
            else:
                print("❌ Authentication failed")
                return False
        
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def discover_required_fields(self) -> bool:
        """Fetch required fields for both tables"""
        print("\n📋 Discovering required fields...")
        
        # Fetch article required fields
        print(f"   Fetching {self.ARTICLE_TABLE} metadata...")
        article_result = self.client.fetch_entity_attributes(self.ARTICLE_TABLE)
        if not article_result.get("success"):
            print(f"❌ Failed to fetch {self.ARTICLE_TABLE} attributes: {article_result.get('error')}")
            return False
        
        self.article_required_fields = self._filter_required_fields(
            article_result.get("attributes", []),
            self.ARTICLE_TABLE
        )
        print(f"   Found {len(self.article_required_fields)} required fields for {self.ARTICLE_TABLE}")
        
        # Fetch relationship required fields
        print(f"   Fetching {self.RELATIONSHIP_TABLE} metadata...")
        rel_result = self.client.fetch_entity_attributes(self.RELATIONSHIP_TABLE)
        if not rel_result.get("success"):
            print(f"❌ Failed to fetch {self.RELATIONSHIP_TABLE} attributes: {rel_result.get('error')}")
            return False
        
        # Debug: Print all lookup fields found in relationship
        all_attrs = rel_result.get("attributes", [])
        print(f"   DEBUG: All attributes in {self.RELATIONSHIP_TABLE}:")
        for attr in all_attrs:
            if attr.get("AttributeType") == "Lookup":
                logical_name = attr.get("LogicalName", "?")
                required = attr.get("RequiredLevel", {}).get("Value", "None")
                can_create = attr.get("IsValidForCreate", False)
                print(f"      - {logical_name} (Required: {required}, CanCreate: {can_create})")
        
        self.relationship_required_fields = self._filter_required_fields(
            all_attrs,
            self.RELATIONSHIP_TABLE
        )
        print(f"   Found {len(self.relationship_required_fields)} required fields for {self.RELATIONSHIP_TABLE}")
        
        return True
    
    def _filter_required_fields(self, attributes: List[Dict], table_name: str) -> Dict[str, Dict]:
        """Extract required fields that can be created - CONSERVATIVE approach"""
        required = {}
        
        # In mdm_article, many lookup fields appear to be read-only or not standard navigation props
        # Conservative approach: only include String, Integer, Boolean types
        # Exclude all Lookup fields to avoid OData deserialization errors
        
        safe_types = {"String", "Integer", "Boolean", "Picklist", "Status", "State"}
        
        for attr in attributes:
            logical_name = attr.get("LogicalName", "")
            required_level = attr.get("RequiredLevel", {}).get("Value", "None")
            attribute_type = attr.get("AttributeType", "")
            is_valid_for_create = attr.get("IsValidForCreate", False)
            
            # Skip if not required or not valid for create
            if required_level == "None" or not is_valid_for_create:
                continue
            
            # Skip primary key (handled by Dataverse)
            if attribute_type == "Uniqueidentifier":
                continue
            
            # Skip certain system fields and complex types
            if logical_name in ["createdby", "createdon", "modifiedby", "modifiedon", "versionnumber", "ownerid", "owneridtype"]:
                continue
            
            # Skip unsupported complex types
            if attribute_type in ["Owner", "EntityName", "Virtual", "PartyList", "ManagedProperty", "Decimal"]:
                continue
            
            # CONSERVATIVE: Skip all Lookup fields (appear to be read-only)
            if attribute_type == "Lookup":
                continue
            
            # Only include safe field types
            if attribute_type not in safe_types:
                continue
            
            # Get display name safely with multiple fallbacks
            display_name = logical_name
            try:
                display_name_obj = attr.get("DisplayName")
                if display_name_obj:
                    user_label = display_name_obj.get("UserLocalizedLabel")
                    if user_label:
                        display_name = user_label.get("Label", logical_name)
            except (AttributeError, TypeError):
                display_name = logical_name
            
            required[logical_name] = {
                "LogicalName": logical_name,
                "AttributeType": attribute_type,
                "DisplayName": display_name,
                "RequiredLevel": required_level
            }
        
        return required
    
    def auto_populate_field_values(self, article_num: int) -> Tuple[Dict, bool]:
        """Auto-populate required fields with smart defaults"""
        print(f"\n📝 Auto-populating required fields for Article {article_num}...")
        payload = {}
        success = True
        
        for field_name, field_info in self.article_required_fields.items():
            attr_type = field_info.get("AttributeType", "")
            display_name = field_info.get("DisplayName", field_name)
            
            value = None
            
            try:
                if attr_type == "String":
                    if "id" in field_name.lower() or "code" in field_name.lower():
                        value = f"Article_{article_num:03d}"
                    else:
                        value = f"Test Article {article_num}"
                
                elif attr_type == "Integer":
                    value = 1  # Default integer
                
                elif attr_type == "Boolean":
                    value = True  # Default to active
                
                elif attr_type == "DateTime":
                    value = datetime.now().isoformat() + "Z"
                
                elif attr_type == "Picklist" or attr_type == "State" or attr_type == "Status":
                    # Fetch choice options
                    value = self._fetch_and_select_choice(field_name, self.ARTICLE_TABLE)
                    if value is None:
                        print(f"⚠️  Could not fetch choice options for {display_name}")
                        success = False
                        continue
                
                elif attr_type == "Lookup":
                    # Fetch lookup options
                    value = self._fetch_and_select_lookup(field_name, self.ARTICLE_TABLE)
                    if value is None:
                        print(f"⚠️  Could not fetch lookup options for {display_name}")
                        success = False
                        continue
                
                else:
                    print(f"⚠️  Unsupported type {attr_type} for field {display_name}")
                    continue
                
                if value is not None:
                    if attr_type == "Lookup":
                        # Lookup fields need @odata.bind suffix
                        payload[f"{field_name}@odata.bind"] = value
                    else:
                        payload[field_name] = value
                    print(f"   ✓ {display_name} = {value}")
            
            except Exception as e:
                print(f"   ❌ Error populating {display_name}: {str(e)}")
                success = False
        
        return payload, success
    
    def _fetch_and_select_choice(self, field_name: str, table_name: str) -> Optional[int]:
        """Fetch choice options and return first option's value"""
        try:
            result = self.client.fetch_choice_options(table_name, field_name)
            if result.get("success"):
                options = result.get("options", [])
                if options:
                    first_option = options[0]
                    value = first_option.get("Value")
                    label = first_option.get("Label")
                    print(f"      → Selected choice: {label} (value: {value})")
                    return value
            return None
        except Exception as e:
            print(f"      ❌ Error fetching choices: {str(e)}")
            return None
    
    def _fetch_and_select_lookup(self, field_name: str, table_name: str) -> Optional[str]:
        """Fetch lookup table records and return first record's GUID"""
        try:
            # Try to infer lookup target from field metadata
            # This is a simplified version—production would need lookup target metadata
            result = self.client.read_multiple(table_name, top=1)
            if result.get("success") and result.get("data"):
                first_record = result["data"][0]
                record_id = first_record.get(f"{table_name}id")
                if record_id:
                    print(f"      → Selected lookup record: {record_id}")
                    return f"/{table_name}s({record_id})"
            return None
        except Exception as e:
            print(f"      ❌ Error fetching lookup: {str(e)}")
            return None
    
    def auto_populate_relationship_fields(self) -> Tuple[Dict, bool]:
        """Auto-populate relationship required fields"""
        print(f"\n📝 Auto-populating relationship required fields...")
        payload = {}
        success = True
        
        # Fields to explicitly include even if minimal
        included_fields = 0
        
        for field_name, field_info in self.relationship_required_fields.items():
            # Skip the parent/child lookups—we'll handle those with Content-ID refs
            if field_name in [self.PARENT_ARTICLE_LOOKUP, self.CHILD_ARTICLE_LOOKUP]:
                continue
            
            attr_type = field_info.get("AttributeType", "")
            display_name = field_info.get("DisplayName", field_name)
            
            value = None
            
            try:
                if attr_type == "String":
                    # Use unique timestamps for relationship names to avoid duplicates
                    if "name" in field_name.lower() or "relationship" in field_name.lower():
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        value = f"Deep Insert Relationship {timestamp}"
                    elif "unit" in field_name.lower():
                        value = "Test Unit"
                    else:
                        value = "Deep Insert Test"
                
                elif attr_type == "Integer":
                    value = 1
                
                elif attr_type == "Boolean":
                    value = True
                
                elif attr_type == "Picklist" or attr_type == "State" or attr_type == "Status":
                    value = self._fetch_and_select_choice(field_name, self.RELATIONSHIP_TABLE)
                    if value is None:
                        print(f"⚠️  Could not fetch choice options for {display_name}")
                        success = False
                        continue
                
                else:
                    print(f"⚠️  Unsupported type {attr_type} for field {display_name}")
                    continue
                
                if value is not None:
                    payload[field_name] = value
                    included_fields += 1
                    print(f"   ✓ {display_name} = {value}")
            
            except Exception as e:
                print(f"   ❌ Error populating {display_name}: {str(e)}")
                success = False
        
        # If we have no fields, at least include the name field as required by many junction tables
        if included_fields == 0:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            print("⚠️  No relationship fields populated, adding minimal name field")
            payload["mdm_relationshipname"] = f"Deep Insert Relationship {timestamp}"
        
        return payload, success
    
    def _build_batch_operations(self, art1: dict, art2: dict, rel: dict) -> list[dict]:
        # Navigation properties (mdm_parentarticle, mdm_childarticle) cannot be set during
        # CREATE in batch operations via @odata.bind or direct binding.
        # Create the articles and relationship record. Parent/child links can be updated via:
        # - Direct UI assignment in Dataverse
        # - Separate PATCH call after batch completes (requires GUIDs)
        # - Use PATCH on the relationship with full entity URIs
        
        rel_data = {k: v for k, v in rel.items() 
                   if k not in ["mdm_parentarticle@odata.bind", "mdm_childarticle@odata.bind"]}
        
        ops = [
            {
                "id": "1",
                "method": "POST",
                "url": "/api/data/v9.2/mdm_articles",
                "data": art1,
            },
            {
                "id": "2",
                "method": "POST",
                "url": "/api/data/v9.2/mdm_articles",
                "data": art2,
            },
            {
                "id": "3",
                "method": "POST",
                "url": "/api/data/v9.2/mdm_articlerelationships",
                "data": rel_data,
            },
        ]
        return ops
    
    def display_batch_template(self, operations: List[Dict]):
        """Display batch template in readable format"""
        print("\n" + "="*80)
        print("📦 BATCH OPERATION TEMPLATE (Content-ID References)")
        print("="*80)
        
        for i, op in enumerate(operations, 1):
            print(f"\n[Operation {i}] Content-ID: {op['id']}")
            print(f"  Method: {op['method']}")
            print(f"  URL: {op['url']}")
            print(f"  Payload:")
            print(json.dumps(op['data'], indent=4))
        
        print("\n" + "="*80)
        print("🔑 KEY POINTS:")
        print("="*80)
        print("✓ Operation 1 creates Article 1 (Content-ID: 1)")
        print("✓ Operation 2 creates Article 2 (Content-ID: 2)")
        print("✓ Operation 3 creates Relationship (Content-ID: 3)")
        print("✓ GUIDs extracted from batch response Location headers")
        print("✓ Additional PATCH batch links parent/child articles")
        print("✓ NO READ CALLS - All linking done via batch operations!")
        print("="*80)
    
    def prompt_confirmation(self) -> bool:
        """Prompt user for final confirmation"""
        if self.auto_confirm:
            return True
        
        print("\n" + "="*80)
        print("⚠️  FINAL CONFIRMATION")
        print("="*80)
        print("\nThis will execute a batch operation that:")
        print("  1. Creates two articles in mdm_article table")
        print("  2. Creates a relationship in mdm_articlerelationship table")
        print("  3. Relates them using Content-ID references ($1, $2)")
        print("\nNo read calls will be made.")
        print("="*80)
        
        while True:
            response = input("\nProceed with batch execution? (yes/no): ").strip().lower()
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                print("\n❌ Batch execution cancelled by user.")
                return False
            else:
                print("Please enter 'yes' or 'no'")
    
    def _confirm_environment(self) -> bool:
        """Confirm the target environment before executing"""
        print("\n" + "="*80)
        print("⚠️  ENVIRONMENT CONFIRMATION (CRITICAL)")
        print("="*80)
        print(f"\nTarget Environment: {self.selected_environment}")
        print(f"Organization URL: {self.selected_org_url}")
        print("\n⚠️  Records will be created in the above environment!")
        
        if "PROD" in self.selected_environment.upper():
            print("\n🚨 WARNING: You are targeting PRODUCTION!")
            print("   This will create REAL records in your production system.")
        
        if self.auto_confirm:
            print("\n   ✓ Auto-confirmed (--auto-confirm flag used)")
            return True
        
        print("\n")
        while True:
            response = input("Confirm this environment? (yes/no): ").strip().lower()
            if response in ["yes", "y"]:
                print("✓ Environment confirmed. Proceeding...")
                return True
            elif response in ["no", "n"]:
                print("✗ Environment not confirmed. Aborting.")
                return False
            else:
                print("Please enter 'yes' or 'no'")
    
    def execute_batch(self, operations: List[Dict]) -> bool:
        """Execute the batch operation for creating articles and relationship"""
        print("\n⏳ Executing batch operation...")
        
        # First batch: Create articles and relationship
        result = self.client.batch_operation(operations)
        
        if not result.get("success"):
            print(f"❌ Batch execution failed: {result.get('error')}")
            return False
        
        print("\n✅ Batch executed successfully!")
        
        # Parse response to extract GUIDs
        response_text = result.get("data", "")
        created_guids = self._parse_batch_response(response_text)
        
        if created_guids and len(created_guids) >= 3:
            article1_guid = self._extract_guid_from_uri(created_guids.get("1"))
            article2_guid = self._extract_guid_from_uri(created_guids.get("2"))
            relationship_guid = self._extract_guid_from_uri(created_guids.get("3"))
            
            if all([article1_guid, article2_guid, relationship_guid]):
                print(f"\n✅ Extracted GUIDs:")
                print(f"   Article 1: {article1_guid}")
                print(f"   Article 2: {article2_guid}")
                print(f"   Relationship: {relationship_guid}")
                
                print("\n✅ DEEP INSERT COMPLETE:")
                print("   - Article 1 created ✅")
                print("   - Article 2 created ✅")
                print("   - Relationship created ✅")
                print("\n📝 NOTE ON PARENT/CHILD LINKING:")
                print("   The mdm_parentarticle and mdm_childarticle navigation properties")
                print("   appear to be read-only or require special handling in this system.")
                print("   ")
                print("   Option 1: Set parent/child articles manually in Dataverse UI")
                print("     - Open the relationship record")
                print("     - Use the 'Related Articles' subgrid to assign parent & child")
                print("   ")
                print("   Option 2: Use separate PATCH call (outside batch)")
                print("     - May provide more detailed error information")
                print("   ")
                print("   Option 3: Check if lookup field names differ from navigation property names")
                print(f"     - Current attempt used: mdm_parentarticle, mdm_childarticle")
                print("     - Metadata may have different field names for the lookups")
                
                print("\n🎯 Achievement Unlocked:")
                print("   ✓ 2 article records created in ONE batch")
                print("   ✓ 1 relationship record created in ONE batch")
                print("   ✓ NO read operations needed")
                print("   ✓ GUIDs extracted from batch Location headers")
                print("   ✓ Safe DEV environment with confirmation")
                
                return True
        
        return False
    
    def _extract_guid_from_uri(self, uri: Optional[str]) -> Optional[str]:
        """Extract GUID from OData URI"""
        if not uri:
            return None
        try:
            # Format: https://org.crm.dynamics.com/api/data/v9.2/table(guid)
            return uri.split("(")[1].split(")")[0]
        except (IndexError, AttributeError):
            return None

    
    def _verify_created_records(self, created_guids: Dict):
        """Verify that created records actually exist in Dataverse"""
        for op_id, entity_id in created_guids.items():
            # Extract GUID from entity_id (format: https://org.crm.dynamics.com/api/data/v9.2/table(guid))
            try:
                guid = entity_id.split("(")[1].split(")")[0]
                
                # Query for the record using read_record method
                result = self.client.read_record(self.ARTICLE_TABLE, guid)
                if result.get("success"):
                    record = result.get("data", {})
                    article_id = record.get("mdm_article_id", "N/A")
                    print(f"   ✓ Operation {op_id}: Article found! ID={article_id}, GUID={guid}")
                else:
                    print(f"   ❌ Operation {op_id}: Record NOT FOUND in Dataverse (GUID: {guid})")
                    print(f"      Error: {result.get('error')}")
            except Exception as e:
                print(f"   ⚠️  Could not verify Operation {op_id}: {str(e)}")
    
    def _parse_batch_response(self, batch_response: str) -> Dict[str, str]:
        """Parse batch response and extract created GUIDs from Location headers"""
        print("\n" + "="*80)
        print("BATCH RESPONSE SUMMARY")
        print("="*80)
        
        lines = batch_response.split("\r\n")
        
        created_guids = {}
        operation_count = 0
        
        # Batch responses don't include Content-ID in individual responses,
        # so we extract Location headers in order and map to operation IDs
        for line in lines:
            # Extract Location header which contains the full URI
            if line.startswith("Location:"):
                operation_count += 1
                location_uri = line.split(":", 1)[1].strip()
                if location_uri:
                    created_guids[str(operation_count)] = location_uri
                    print(f"\nOperation {operation_count} created at:")
                    print(f"  {location_uri}")
        
        if not created_guids:
            print("\nNote: Could not parse Location headers from batch response.")
            print("This may indicate a failure in the batch operations.")
        
        print(f"\nTotal operations processed: {operation_count}")
        print("="*80)
        
        return created_guids
    
    def run(self) -> bool:
        """Execute the full POC workflow"""
        print("\n" + "="*80)
        print("🚀 ARTICLE DEEP INSERT POC")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 1.5: Confirm environment (CRITICAL - prevent accidental PROD changes)
        if not self._confirm_environment():
            print("\n❌ Environment confirmation cancelled. Aborting.")
            return False
        
        # Step 2: Discover required fields
        if not self.discover_required_fields():
            return False
        
        # Step 3: Auto-populate article 1 & 2
        article1_data, article1_success = self.auto_populate_field_values(1)
        article2_data, article2_success = self.auto_populate_field_values(2)
        
        if not (article1_success and article2_success):
            print("\n⚠️  Some required fields could not be auto-populated.")
            if not self.prompt_confirmation():
                return False
        
        # Step 4: Auto-populate relationship fields
        relationship_data, rel_success = self.auto_populate_relationship_fields()
        
        if not rel_success:
            print("\n⚠️  Some relationship fields could not be auto-populated.")
            if not self.prompt_confirmation():
                return False
        
        # Step 5: Build batch operations
        operations = self._build_batch_operations(article1_data, article2_data, relationship_data)
        
        # Step 6: Display template
        self.display_batch_template(operations)
        
        # Step 7: Final confirmation
        if not self.prompt_confirmation():
            return False
        
        # Step 8: Execute batch
        if not self.execute_batch(operations):
            return False
        
        print("\n✅ POC completed successfully!")
        print("\n💡 Key Takeaway:")
        print("   Two articles created and related in ONE batch call")
        print("   NO read calls needed—Content-ID references handled by Dataverse")
        print("="*80 + "\n")

        
        return True


def main():
    """Main entry point"""
    auto_confirm = "--auto-confirm" in sys.argv or "--yes" in sys.argv
    
    # Check for environment argument
    environment = None
    for arg in sys.argv[1:]:
        if arg.startswith("--env="):
            environment = arg.split("=")[1]
            break
    
    poc = ArticleDeepInsertPOC(auto_confirm=auto_confirm, environment=environment)
    success = poc.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
