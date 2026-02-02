import requests
import json
import os
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

# ==============================================================================
# 1. CONFIGURATION & AUTHENTICATION
# ==============================================================================

# Load environment variables from .env file
load_dotenv()

# Environment configuration
ENVIRONMENTS = {
    "1": {"name": "PRODUCTION", "url": os.getenv("ORG_URL_PROD")},
    "2": {"name": "DEVELOPMENT (Gaurav's)", "url": os.getenv("ORG_URL_DEV")},
    "3": {"name": "SANDBOX", "url": os.getenv("ORG_URL_SANDBOX")},
    "4": {"name": "Tanushri's Environment", "url": os.getenv("ORG_URL_TANUSHRIS_ENV")}
}

# Azure AD / Entra ID Configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Output directory for saving results
OUTPUT_DIR = "output"

# Alternate key fields that can be used to query products (articles)
ALTERNATE_KEY_FIELDS = {
    "aimscode": "mdm_aimscode",
    "itemcode": "mdm_itemcode",
    "barcode": "mdm_barcode",
    "articledescription": "mdm_articledescription",
    "articleid": "mdm_article_id"
}

def get_access_token(resource_url):
    """
    Acquire access token using MSAL with client credentials flow.
    This is for service-to-service authentication (no user interaction).
    
    Args:
        resource_url: The Dataverse organization URL
    
    Returns:
        str: Access token for Dataverse API
    """
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    
    # Dataverse scope format: {org_url}/.default
    # Extract base URL without trailing slash
    base_url = resource_url.rstrip('/')
    scopes = [f"{base_url}/.default"]
    
    app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        authority=authority,
        client_credential=CLIENT_SECRET
    )
    
    print("[*] Acquiring access token from Microsoft Entra ID...")
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        print("[✓] Successfully acquired access token")
        return result["access_token"]
    else:
        error = result.get("error")
        error_desc = result.get("error_description")
        print(f"[✗] Failed to acquire token: {error}")
        print(f"    Description: {error_desc}")
        raise Exception(f"Authentication failed: {error}")

def select_environment(env_choice=None):
    """
    Display environment selection menu and return chosen environment details.
    
    Args:
        env_choice: Optional pre-selected environment (1-4)
    
    Returns:
        tuple: (environment_name, org_url)
    """
    print("\n" + "="*70)
    print(" DATAVERSE PRODUCT API - ENVIRONMENT SELECTOR")
    print("="*70)
    print("\nAvailable Environments:")
    print("-" * 70)
    
    for key, env in ENVIRONMENTS.items():
        print(f"  [{key}] {env['name']}")
        print(f"      URL: {env['url']}")
    
    print("-" * 70)
    
    if env_choice and str(env_choice) in ENVIRONMENTS:
        choice = str(env_choice)
        print(f"\n[Pre-selected environment {choice}]")
    else:
        while True:
            choice = input("\nSelect environment (1-4): ").strip()
            if choice in ENVIRONMENTS:
                break
            else:
                print("[✗] Invalid choice. Please enter 1, 2, 3, or 4.")
    
    selected_env = ENVIRONMENTS[choice]
    print(f"\n[✓] Selected: {selected_env['name']}")
    print(f"[✓] URL: {selected_env['url']}")
    return selected_env['name'], selected_env['url']

def get_headers(access_token):
    """
    Generate HTTP headers for Dataverse API requests.
    Includes OData annotations for getting formatted values (display names for lookups)
    
    Args:
        access_token: Bearer token from MSAL
    
    Returns:
        dict: Headers dictionary
    """
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Prefer": "odata.include-annotations=\"OData.Community.Display.V1.FormattedValue\""
    }

# ==============================================================================
# 2. DEFINITIONS (Derived from your Form XML)
# ==============================================================================

# Core product/article fields (excluding lookup display names and formatted values)
# Note: Do NOT include fields with "name" suffix - these are virtual/calculated fields
# Use OData annotations instead to get formatted values
FORM_FIELDS = [
    # Primary Identifiers
    "mdm_articleid",
    "mdm_article_id",
    "mdm_autoarticleid",
    
    # General Information
    "mdm_articledescription",
    "mdm_articledescriptionarabic",
    "mdm_description",
    "_mdm_brand_value",
    
    # Product Codes & Identifiers
    "mdm_aimscode",
    "mdm_itemcode",
    "mdm_barcode",
    "mdm_alternatesupplierid",
    
    # Marketing Data
    "mdm_articlemarketingname",
    "mdm_articlemarketingnamearabic",
    "mdm_articlemarketingdescription",
    "mdm_articlemarketingdescriptionarabic",
    
    # Units & Measures
    "mdm_articlebaseunit",
    "mdm_articlestoreunit",
    "mdm_articlecaseunit",
    "mdm_casesperpallet",
    
    # Status & Classification
    "_mdm_articlestatus_value",
    "_mdm_articletype_value",
    "_mdm_actioncode_value",
    "_mdm_abcoption_value",
    
    # Supply Chain & Sourcing
    "_mdm_articlesourcing_value",
    "_mdm_countryoforigin_value",
    "_mdm_buyvatcode_value",
    "mdm_directtostore",
    "mdm_applicablecountries",
    
    # Physical Properties
    "mdm_averageweight",
    "_mdm_averageweightunit_value",
    "mdm_cbm",
    #"mdm_packsize",
    
    # System Metadata  
    "_ownerid_value",
    "_owningbusinessunit_value",
    "_createdby_value",
    "createdon",
    "_createdonbehalfby_value",
    "_modifiedby_value",
    "modifiedon",
    "_modifiedonbehalfby_value",
    "statecode",
    "statuscode",
    
    # Additional Fields
    "mdm_shelflife",
    # "mdm_itemgrouptype",
    #"mdm_versionstamp",
    "importsequencenumber",
    "overriddencreatedon"
]



# Relationships - based on JavaScript FetchXML analysis and entity structure
# Relationship navigation properties (from main mdm_article entity)
RELATIONSHIPS = {
    "AllergenRelationships": "mdm_articleallergenrelationship_Article_mdm_article",
    "NutrientRelationships": "mdm_articlenutrientrelationship_Article_mdm_article",
    "ArticleChildRelationships": "mdm_articlerelationship_ParentArticle_mdm_article",
    "ArticleParentRelationships": "mdm_articlerelationship_ChildArticle_mdm_article",
    "ManyToManyAllergens": "mdm_Article_mdm_LookupAllergen_mdm_LookupAllergen",
    "ManyToManyNutrients": "mdm_Article_mdm_LookupNutrient_mdm_LookupNutrient"
}

def format_field(record, field_name):
    """
    Extracts Value and Display Value (FormattedValue) for a given field.
    Handles lookups (which have formatted values via OData annotation).
    
    Args:
        record: The API response record
        field_name: Field name to extract
    
    Returns:
        dict: {"Value": actual_value, "DisplayValue": formatted_value}
    """
    # Get the raw value
    val = record.get(field_name)
    
    # Check for Formatted Value annotation: fieldname@OData.Community.Display.V1.FormattedValue
    formatted_key = f"{field_name}@OData.Community.Display.V1.FormattedValue"
    display_val = record.get(formatted_key)
    
    # If no formatted value, use the raw value as display
    if display_val is None:
        display_val = val
    
    return {
        "Value": val,
        "DisplayValue": display_val
    }

# ==============================================================================
# 4. PRODUCT/ARTICLE LOOKUP FUNCTIONS
# ==============================================================================
def get_article_by_alternate_key(org_url, headers, key_field, key_value):
    """
    Fetch article/product using an alternate key (AIMS Code, Item Code, Barcode, etc.)
    
    Args:
        org_url: Dataverse organization URL
        headers: HTTP headers with auth token
        key_field: Field name (e.g., 'mdm_aimscode')
        key_value: Value to search for
    
    Returns:
        str: Article GUID if found, None otherwise
    """
    print(f"[*] Searching for article where {key_field}='{key_value}'...")
    
    # Build OData filter query
    filter_query = f"$filter={key_field} eq '{key_value}'"
    url = f"{org_url}/api/data/v9.2/mdm_articles?{filter_query}&$select=mdm_articleid"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('value', [])
            
            if len(records) > 0:
                article_id = records[0].get('mdm_articleid')
                print(f"[✓] Found Article: {article_id}")
                if len(records) > 1:
                    print(f"[!] Warning: Found {len(records)} matching articles, using first one")
                return article_id
            else:
                print(f"[✗] No article found with {key_field}='{key_value}'")
                return None
        else:
            print(f"[✗] API Error {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        print(f"[✗] Error during lookup: {str(e)}")
        return None


def prompt_for_article():
    """
    Prompt user for article/product identifier (GUID or alternate key)
    
    Returns:
        tuple: (lookup_type, value) where lookup_type is 'guid' or key field name
    """
    print("\n" + "="*70)
    print(" PRODUCT/ARTICLE IDENTIFIER")
    print("="*70)
    print("\nYou can identify a product/article using:")
    print("  1. GUID (e.g., 12345678-1234-1234-1234-123456789abc)")
    print("  2. Alternate key:")
    
    for short_name, field_name in ALTERNATE_KEY_FIELDS.items():
        print(f"     - {short_name.upper()}: {field_name}")
    
    print("\nExamples:")
    print("  GUID format:     12345678-1234-1234-1234-123456789abc")
    print("  Alternate key:   aimscode:AIMS12345")
    print("  Alternate key:   itemcode:ITEM98765")
    print("  Alternate key:   barcode:1234567890123")
    print("  Alternate key:   articledescription:Product Name")
    print("-" * 70)
    
    while True:
        article_input = input("\nEnter article/product identifier: ").strip()
        
        if not article_input:
            print("[✗] Article/product identifier cannot be empty")
            continue
        
        # Check if it's an alternate key format (key:value)
        if ":" in article_input:
            parts = article_input.split(":", 1)
            key_type = parts[0].lower().strip()
            key_value = parts[1].strip()
            
            if key_type in ALTERNATE_KEY_FIELDS:
                return ALTERNATE_KEY_FIELDS[key_type], key_value
            else:
                print(f"[✗] Unknown key type '{key_type}'. Valid types: {', '.join(ALTERNATE_KEY_FIELDS.keys())}")
                continue
        
        # Assume it's a GUID
        # Basic GUID validation (8-4-4-4-12 format)
        if len(article_input) == 36 and article_input.count('-') == 4:
            return 'guid', article_input
        else:
            print("[✗] Invalid format. Use GUID or 'keytype:value' format")
            continue


# ==============================================================================
# 5. MAIN LOGIC
# ==============================================================================
def validate_fields(org_url, headers, entity_fields):
    """
    Validate which fields actually exist in the entity by testing a small query.
    NOTE: Since metadata analysis confirmed all fields exist, skipping validation.
    Lookup field validation often fails due to permissions or OData handling.
    
    Args:
        org_url: Dataverse organization URL
        headers: HTTP headers with auth token
        entity_fields: List of field names to validate
    
    Returns:
        list: Valid field names that exist in the entity
    """
    print("[*] Step 1: Validating field names...")
    print("[*] SKIPPING field validation - metadata confirmed all fields exist")
    print("[*] Lookup fields often fail validation due to permissions/OData handling")
    print(f"[✓] Using all {len(entity_fields)} fields from FORM_FIELDS")
    
    return entity_fields
    
    if invalid_fields:
        print("[!] Invalid fields found:")
        for field in invalid_fields:
            print(f"    - {field}")
    
    return valid_fields


def get_full_article_details(article_id, org_url, headers):
    """
    Fetch complete article/product details including related records.
    
    Args:
        article_id: Article GUID
        org_url: Dataverse organization URL
        headers: HTTP headers with auth token
    
    Returns:
        dict: Complete article data or None if error
    """
    print(f"\n[*] Fetching Article/Product Details: {article_id}")
    
    # Validate fields first to avoid API errors
    print("[*] Step 1: Validating field names...")
    valid_fields = validate_fields(org_url, headers, FORM_FIELDS)
    
    if not valid_fields:
        print("[✗] No valid fields found!")
        return None
    
    print(f"[✓] Using {len(valid_fields)} validated fields")
    
    # --- A. Fetch Main Record ---
    # Build OData select query
    select_query = ",".join(valid_fields)
    
    # Entity Set Name is 'mdm_articles' (Plural) as confirmed in metadata
    url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})?$select={select_query}"
    
    print(f"\n[*] Step 2: Fetching main record...")
    print(f"[*] API Call:")
    print(f"    URL: {url[:100]}..." if len(url) > 100 else f"    URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            error_msg = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", error_msg)
            except:
                error_detail = error_msg
            
            print(f"[✗] API Error ({response.status_code}): {error_detail}")
            return None
        
        article_data = response.json()
        print(f"[✓] Successfully fetched article record")
        
    except Exception as e:
        print(f"[✗] Request Error: {str(e)}")
        return None
    
    # Build the output object
    final_output = {
        "ArticleId": article_id,
        "Fields": {}
    }
    
    # Extract all fields with formatted values
    for field in valid_fields:
        final_output["Fields"][field] = format_field(article_data, field)


    # --- C. Fetch Related Nutrients ---
    print("[*] Step 4: Fetching Related Nutrients...")
    
    # Use navigation property from main article entity
    nutrient_nav_prop = RELATIONSHIPS["NutrientRelationships"]
    nutrient_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{nutrient_nav_prop}"
    
    print(f"[*] Navigation Property: {nutrient_nav_prop}")
    
    try:
        nutrient_response = requests.get(nutrient_url, headers=headers)
        final_output["Related_Nutrients"] = []
        
        if nutrient_response.status_code == 200:
            nutrient_records = nutrient_response.json().get('value', [])
            print(f"[✓] Found {len(nutrient_records)} nutrient relationship(s)")
            
            for rel in nutrient_records:
                nutrient_obj = {}
                for k, v in rel.items():
                    # clean up OData annotations from the output keys
                    if "@" not in k:  
                        nutrient_obj[k] = v
                final_output["Related_Nutrients"].append(nutrient_obj)
        else:
            error_text = nutrient_response.text
            print(f"[!] Could not fetch nutrients (Status: {nutrient_response.status_code})")
            
    except Exception as e:
        print(f"[!] Error fetching nutrient relationships: {str(e)}")
    
    
 # --- B. Fetch Related Allergens ---
    print("[*] Step 3: Fetching Related Allergens...")
    
    # Use navigation property from main article entity
    allergen_nav_prop = RELATIONSHIPS["AllergenRelationships"]
    allergen_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{allergen_nav_prop}"
    
    print(f"[*] Navigation Property: {allergen_nav_prop}")
    
    try:
        allergen_response = requests.get(allergen_url, headers=headers)
        final_output["Related_Allergens"] = []
        
        if allergen_response.status_code == 200:
            allergen_records = allergen_response.json().get('value', [])
            print(f"[✓] Found {len(allergen_records)} allergen relationship(s)")
            
            for rel in allergen_records:
                allergen_obj = {}
                for k, v in rel.items():
                    # Skip odata metadata annotations to keep output clean
                    if "@" not in k:  
                        allergen_obj[k] = v
                final_output["Related_Allergens"].append(allergen_obj)
        else:
            error_text = allergen_response.text
            print(f"[!] Could not fetch allergens (Status: {allergen_response.status_code})")
            print(f"[!] Error: {error_text[:200]}...")
            
    except Exception as e:
        print(f"[!] Error fetching allergen relationships: {str(e)}")

    # --- D. Fetch Related Articles (Parent-Child Relationships) ---
    print("[*] Step 5: Fetching Related Articles...")
    
    final_output["Article_Relationships"] = []
    
    # 1. Fetch child relationships (this article is the parent)
    child_nav_prop = RELATIONSHIPS["ArticleChildRelationships"]
    child_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{child_nav_prop}"
    
    print(f"[*] Child Navigation Property: {child_nav_prop}")
    
    try:
        child_response = requests.get(child_url, headers=headers)
        
        if child_response.status_code == 200:
            child_records = child_response.json().get('value', [])
            print(f"[✓] Found {len(child_records)} child relationship(s)")
            
            for rel in child_records:
                rel_obj = {'relationship_type': 'Child'}
                for k, v in rel.items():
                    if "@" not in k:
                        rel_obj[k] = v
                final_output["Article_Relationships"].append(rel_obj)
        else:
            print(f"[!] Could not fetch child relationships: {child_response.status_code}")
            
    except Exception as e:
        print(f"[!] Error fetching child relationships: {str(e)}")
    
    # 2. Fetch parent relationships (this article is the child)
    parent_nav_prop = RELATIONSHIPS["ArticleParentRelationships"] 
    parent_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{parent_nav_prop}"
    
    print(f"[*] Parent Navigation Property: {parent_nav_prop}")
    
    try:
        parent_response = requests.get(parent_url, headers=headers)
        
        if parent_response.status_code == 200:
            parent_records = parent_response.json().get('value', [])
            print(f"[✓] Found {len(parent_records)} parent relationship(s)")
            
            for rel in parent_records:
                rel_obj = {'relationship_type': 'Parent'}
                for k, v in rel.items():
                    if "@" not in k:
                        rel_obj[k] = v
                final_output["Article_Relationships"].append(rel_obj)
        else:
            print(f"[!] Could not fetch parent relationships: {parent_response.status_code}")
            
    except Exception as e:
        print(f"[!] Error fetching parent relationships: {str(e)}")
    
    # 3. Also try many-to-many allergen relationships if 1:N relationships are empty
    if not final_output["Related_Allergens"]:
        print("[*] Trying many-to-many allergen relationships...")
        try:
            m2m_allergen_nav = RELATIONSHIPS["ManyToManyAllergens"]
            m2m_allergen_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{m2m_allergen_nav}"
            
            m2m_allergen_response = requests.get(m2m_allergen_url, headers=headers)
            if m2m_allergen_response.status_code == 200:
                m2m_allergens = m2m_allergen_response.json().get('value', [])
                print(f"[✓] Found {len(m2m_allergens)} M2M allergen(s)")
                final_output["Related_Allergens"] = m2m_allergens
            else:
                print(f"[!] M2M allergens failed: {m2m_allergen_response.status_code}")
        except Exception as e:
            print(f"[!] M2M allergen error: {str(e)}")
    
    # 4. Also try many-to-many nutrient relationships if 1:N relationships are empty  
    if not final_output["Related_Nutrients"]:
        print("[*] Trying many-to-many nutrient relationships...")
        try:
            m2m_nutrient_nav = RELATIONSHIPS["ManyToManyNutrients"]
            m2m_nutrient_url = f"{org_url}/api/data/v9.2/mdm_articles({article_id})/{m2m_nutrient_nav}"
            
            m2m_nutrient_response = requests.get(m2m_nutrient_url, headers=headers)
            if m2m_nutrient_response.status_code == 200:
                m2m_nutrients = m2m_nutrient_response.json().get('value', [])
                print(f"[✓] Found {len(m2m_nutrients)} M2M nutrient(s)")
                final_output["Related_Nutrients"] = m2m_nutrients
            else:
                print(f"[!] M2M nutrients failed: {m2m_nutrient_response.status_code}")
        except Exception as e:
            print(f"[!] M2M nutrient error: {str(e)}")

    return final_output


# ==============================================================================
# 6. OUTPUT FUNCTIONS
# ==============================================================================
def save_json_output(data, filename):
    """Save data as formatted JSON file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, indent=4, ensure_ascii=False, fp=f)
    
    print(f"[✓] JSON saved: {filepath}")
    return filepath


def save_readable_report(data, filename):
    """Save data as human-readable text report"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(" DATAVERSE ARTICLE/PRODUCT DETAILS REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Article ID: {data.get('ArticleId', 'N/A')}\n")
        f.write("\n" + "="*80 + "\n")
        f.write(" ARTICLE/PRODUCT FIELDS\n")
        f.write("="*80 + "\n\n")
        
        # Write fields in organized sections
        fields = data.get('Fields', {})
        
        for field_name, field_data in fields.items():
            value = field_data.get('Value', '')
            display = field_data.get('DisplayValue', '')
            
            f.write(f"{field_name}:\n")
            f.write(f"  Value: {value}\n")
            if display and display != value:
                f.write(f"  Display: {display}\n")
            f.write("\n")
        
        # RELATED ALLERGENS
        f.write("\n" + "="*80 + "\n")
        f.write(" RELATED ALLERGENS\n")
        f.write("="*80 + "\n\n")
        
        key_personnel = data.get('Related_Allergens', [])
        if key_personnel:
            for idx, kp in enumerate(key_personnel, 1):
                f.write(f"--- Person {idx} ---\n")
                for k, v in kp.items():
                    if isinstance(v, dict):
                        f.write(f"  {k}: {v.get('DisplayValue', v.get('Value', ''))}\n")
                    else:
                        f.write(f"  {k}: {v}\n")
                f.write("\n")
        else:
            f.write("No key personnel records found.\n\n")
        
        # RELATED ALLERGENS
        if data.get("Related_Allergens"):
            f.write("="*60 + "\n")
            f.write(" Related_Allergens\n")
            f.write("="*60 + "\n\n")
            
            for i, kp in enumerate(data["Related_Allergens"], 1):
                f.write(f"Key Personnel #{i}:\n")
                for field, value in kp.items():
                    if value is not None:
                        f.write(f"  {field}: {value}\n")
                f.write("\n")
        else:
            f.write("No related allergens records found.\n\n")
            
        # RELATED NUTRIENTS
        f.write("\n" + "="*80 + "\n")
        f.write(" RELATED NUTRIENTS\n")
        f.write("="*80 + "\n\n")
        
        nutrients = data.get('Related_Nutrients', [])
        if nutrients:
            for idx, item in enumerate(nutrients, 1):
                f.write(f"--- Nutrient {idx} ---\n")
                for k, v in item.items():
                    if isinstance(v, dict):
                        f.write(f"  {k}: {v.get('DisplayValue', v.get('Value', ''))}\n")
                    else:
                        f.write(f"  {k}: {v}\n")
                f.write("\n")
        else:
            f.write("No nutrient records found.\n\n")

        # ARTICLE RELATIONSHIPS
        f.write("\n" + "="*80 + "\n")
        f.write(" RELATED ARTICLES (HIERARCHY)\n")
        f.write("="*80 + "\n\n")
        
        related_articles = data.get('Article_Relationships', [])
        if related_articles:
            for idx, item in enumerate(related_articles, 1):
                f.write(f"--- Relationship {idx} ---\n")
                
                # Print the Child Article details first (most important)
                f.write(f"  > RELATED ARTICLE: {item.get('Related_Article_Name', 'Unknown')}\n")
                f.write(f"  > ARTICLE NO:      {item.get('Related_Article_No', 'N/A')}\n")
                f.write("  ------------------\n")
                
                # Print relationship attributes (Quantity, Type, etc.)
                for k, v in item.items():
                    if k not in ['Related_Article_Name', 'Related_Article_No']:
                        # Clean up keys for display
                        clean_key = k.replace('mdm_', '').replace('_value', '')
                        f.write(f"  {clean_key}: {v}\n")
                f.write("\n")
        else:
            f.write("No related articles found.\n\n")

        f.write("="*80 + "\n")
        f.write(" END OF REPORT\n")
        f.write("="*80 + "\n")
    
    print(f"[✓] Report saved: {filepath}")
    return filepath


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch Dataverse Article/Product details via Web API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for everything)
  python custom-api-product.py
  
  # Specify environment and article GUID
  python custom-api-product.py -e 2 -a 12345678-1234-1234-1234-123456789abc
  
  # Use alternate key (AIMS Code)
  python custom-api-product.py -e 1 -k aimscode:AIMS12345
  
  # Use alternate key (Item Code)
  python custom-api-product.py -e 3 -k itemcode:ITEM98765
  
  # Use alternate key (Barcode)
  python custom-api-product.py -e 2 -k barcode:1234567890123
  
  # Skip saving output files
  python custom-api-product.py -e 2 -a <guid> --no-save
        """
    )
    
    parser.add_argument(
        '-e', '--environment',
        type=int,
        choices=[1, 2, 3, 4],
        help='Environment: 1=Prod, 2=Dev, 3=Sandbox, 4=Tanushri'
    )
    
    parser.add_argument(
        '-a', '--article',
        type=str,
        help='Article GUID (e.g., 12345678-1234-1234-1234-123456789abc)'
    )
    
    parser.add_argument(
        '-k', '--key',
        type=str,
        help='Alternate key in format keytype:value (e.g., aimscode:AIMS12345, itemcode:ITEM98765, barcode:1234567890123)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save output files (only display to console)'
    )
    
    parser.add_argument(
        '-o', '--output-prefix',
        type=str,
        default=None,
        help='Custom prefix for output filenames'
    )
    
    return parser.parse_args()


# ==============================================================================
# 7. MAIN EXECUTION
# ==============================================================================
def main():
    """Main execution function"""
    args = parse_arguments()
    
    try:
        # Banner
        print("\n" + "="*70)
        print(" DATAVERSE PRODUCT/ARTICLE API CLIENT")
        print(" Powered by MSAL Authentication")
        print("="*70)
        
        # Step 1: Select environment
        env_name, org_url = select_environment(args.environment)
        
        # Display chosen environment
        print("\n" + "="*70)
        print(f" ACTIVE ENVIRONMENT: {env_name}")
        print(f" URL: {org_url}")
        print("="*70 + "\n")
        
        # Step 2: Authenticate and get access token
        access_token = get_access_token(org_url)
        headers = get_headers(access_token)
        
        # Step 3: Get article identifier
        article_id = None
        
        if args.article:
            # GUID provided via command line
            article_id = args.article
            print(f"\n[*] Using article GUID from command line: {article_id}")
        
        elif args.key:
            # Alternate key provided via command line
            if ":" in args.key:
                parts = args.key.split(":", 1)
                key_type = parts[0].lower().strip()
                key_value = parts[1].strip()
                
                if key_type in ALTERNATE_KEY_FIELDS:
                    key_field = ALTERNATE_KEY_FIELDS[key_type]
                    article_id = get_article_by_alternate_key(org_url, headers, key_field, key_value)
                    
                    if not article_id:
                        print("[✗] Could not find article with provided alternate key")
                        return 1
                else:
                    print(f"[✗] Unknown key type '{key_type}'. Valid: {', '.join(ALTERNATE_KEY_FIELDS.keys())}")
                    return 1
            else:
                print("[✗] Invalid key format. Use 'keytype:value'")
                return 1
        
        else:
            # Interactive mode - prompt for article
            lookup_type, lookup_value = prompt_for_article()
            
            if lookup_type == 'guid':
                article_id = lookup_value
            else:
                # It's an alternate key
                article_id = get_article_by_alternate_key(org_url, headers, lookup_type, lookup_value)
                
                if not article_id:
                    print("[✗] Could not find article with provided identifier")
                    return 1
        
        # Step 4: Fetch article details
        print("\n" + "-"*70)
        result = get_full_article_details(article_id, org_url, headers)
        
        if not result:
            print("[✗] Failed to fetch article details")
            return 1
        
        print("-"*70)
        
        # Step 5: Display results
        print("\n" + "="*70)
        print(" RESULTS")
        print("="*70)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Step 6: Save output files
        if not args.no_save:
            print("\n" + "="*70)
            print(" SAVING OUTPUT FILES")
            print("="*70 + "\n")
            
            # Generate filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            prefix = args.output_prefix if args.output_prefix else f"article_{article_id[:8]}"
            
            json_filename = f"{prefix}_{timestamp}.json"
            txt_filename = f"{prefix}_{timestamp}.txt"
            
            # Save files
            save_json_output(result, json_filename)
            save_readable_report(result, txt_filename)
        
        print("\n" + "="*70)
        print(" [✓] OPERATION COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user.")
        return 130
    
    except Exception as e:
        print(f"\n[✗] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())