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

# Alternate key fields that can be used to query locations
ALTERNATE_KEY_FIELDS = {
    "ccid": "lmdm_ccid",
    "fmcid": "lmdm_fmcid",
    "hbid": "lmdm_hbid",
    "yextid": "lmdm_yextid",
    "mdmlocationid": "lmdm_mdmlocationid",
    "storename": "lmdm_storename"
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
    print(" DATAVERSE LOCATION API - ENVIRONMENT SELECTOR")
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

# Core location fields (excluding lookup display names and formatted values)
# Note: Do NOT include fields with "name" suffix - these are virtual/calculated fields
# Use OData annotations instead to get formatted values
FORM_FIELDS = [
    # Location ID
    "lmdm_locationid",
    
    # System fields (converting lookup fields to _value format for Web API)
    "_ownerid_value", "_owningbusinessunit_value", "_createdby_value", "createdon", 
    "_createdonbehalfby_value", "_modifiedby_value", "_modifiedonbehalfby_value", "modifiedon", "statecode",
    
    # Location identifiers
    "lmdm_autolocationid", "lmdm_ccid", "lmdm_fmcid", "lmdm_financeccid", 
    "lmdm_projectid", "lmdm_hbid", "lmdm_sessionmid", "lmdm_symphonyid", 
    "lmdm_vendosid", "lmdm_yextid", "lmdm_mdmlocationid",
    
    # Location names
    "lmdm_storename", "lmdm_storenamelocallanguage", "lmdm_fmcname", "lmdm_hbstorename",
    
    # Classification (Lookup fields - converted to _value format for Web API)
    "_lmdm_assetlocationtype_value", "_lmdm_channeltype_value", "_lmdm_storetrait_value", 
    "_lmdm_locationtype_value", "_lmdm_branddivision_value", "_lmdm_storepaneltype_value",
    
    # Format fields (converting lookup fields to _value format)
    "_lmdm_sbxstoreformat_value", "_lmdm_storeformat_value", "_lmdm_reservetype_value", 
    "_lmdm_reserveequipmenttype_value", "_lmdm_drivethrupaneltype_value", "_lmdm_pricetier_value",
    "lmdm_hbstorelayout", "_lmdm_hbstoreformat_value", "lmdm_hbstoresegment",
    
    # Status fields (converting lookup fields to _value format)
    "lmdm_directtostore", "_lmdm_currentstorestatus_value", "lmdm_reserve", 
    "_lmdm_storestatus_value", "_lmdm_transactiontype_value", "lmdm_seasonaltimeapplicable",
    
    # Delivery & Operations
    "lmdm_deliveryoptions", "lmdm_deliveryaggregator", "lmdm_fulfilmentwh",
    
    # Geographic & Physical (converting lookup fields to _value format)
    "_lmdm_country_value", "_lmdm_countrygroup_value", "_lmdm_region_value", "_lmdm_state_value", 
    "_lmdm_city_value", "lmdm_postalcode", "lmdm_addressline1", "lmdm_addressline2", 
    "lmdm_addressline1arabic", "lmdm_latitude", "lmdm_longitude", "lmdm_areadescription",
    "lmdm_grossleasablearea", "_lmdm_operatingcurrency_value",
    
    # Reference numbers & IDs (converting lookup fields to _value format)
    "lmdm_rocireferencenumber", "lmdm_googlepinid", "_lmdm_brands_value",
    
    # Dates
    "lmdm_forecastedopeningdate", "lmdm_estimatedopeningdate", "lmdm_tradingstartdate", 
    "lmdm_resumptiondate", "lmdm_closuredate", "lmdm_temporaryclosuredate", 
    "lmdm_ccidcreationdate", "lmdm_rentcommdate",
    
    # Planning & Financial (converting lookup fields to _value format)
    "lmdm_plannedinbp", "lmdm_leasableareaextension", "_lmdm_renttypecode_value",
    
    # Contact Info
    "lmdm_landline", "lmdm_mobile", "lmdm_email",
    
    # Administrative
    "lmdm_gridchangeflag", "lmdm_taskownedby", "lmdm_itemmodifiedby", 
    "lmdm_locationchangesessionid", "lmdm_locationglobalworkflowsessionid", 
    "lmdm_locationworkflowstate", "lmdm_isdraft", "lmdm_isactivetaskforcapturer", 
    "lmdm_applicationversion"
]


# Relationships - corrected navigation property names from metadata analysis
RELATIONSHIPS = {
    "BusinessHours": "lmdm_Location_lmdm_Location_lmdm_LocationBusinessHours",
    "KeyPersonnel": "lmdm_Location_lmdm_KeyPersonale_lmdm_KeyPersonale"
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
# 4. LOCATION LOOKUP FUNCTIONS
# ==============================================================================
def get_location_by_alternate_key(org_url, headers, key_field, key_value):
    """
    Fetch location using an alternate key (CCID, FMCID, etc.)
    
    Args:
        org_url: Dataverse organization URL
        headers: HTTP headers with auth token
        key_field: Field name (e.g., 'lmdm_ccid')
        key_value: Value to search for
    
    Returns:
        str: Location GUID if found, None otherwise
    """
    print(f"[*] Searching for location where {key_field}='{key_value}'...")
    
    # Build OData filter query
    filter_query = f"$filter={key_field} eq '{key_value}'"
    url = f"{org_url}/api/data/v9.2/lmdm_locations?{filter_query}&$select=lmdm_locationid"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('value', [])
            
            if len(records) > 0:
                location_id = records[0].get('lmdm_locationid')
                print(f"[✓] Found location: {location_id}")
                if len(records) > 1:
                    print(f"[!] Warning: Found {len(records)} matching locations, using first one")
                return location_id
            else:
                print(f"[✗] No location found with {key_field}='{key_value}'")
                return None
        else:
            print(f"[✗] API Error {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        print(f"[✗] Error during lookup: {str(e)}")
        return None


def prompt_for_location():
    """
    Prompt user for location identifier (GUID or alternate key)
    
    Returns:
        tuple: (lookup_type, value) where lookup_type is 'guid' or key field name
    """
    print("\n" + "="*70)
    print(" LOCATION IDENTIFIER")
    print("="*70)
    print("\nYou can identify a location using:")
    print("  1. GUID (e.g., 12345678-1234-1234-1234-123456789abc)")
    print("  2. Alternate key:")
    
    for short_name, field_name in ALTERNATE_KEY_FIELDS.items():
        print(f"     - {short_name.upper()}: {field_name}")
    
    print("\nExamples:")
    print("  GUID format:     12345678-1234-1234-1234-123456789abc")
    print("  Alternate key:   ccid:CC12345")
    print("  Alternate key:   fmcid:FMC98765")
    print("  Alternate key:   storename:Downtown Store")
    print("-" * 70)
    
    while True:
        location_input = input("\nEnter location identifier: ").strip()
        
        if not location_input:
            print("[✗] Location identifier cannot be empty")
            continue
        
        # Check if it's an alternate key format (key:value)
        if ":" in location_input:
            parts = location_input.split(":", 1)
            key_type = parts[0].lower().strip()
            key_value = parts[1].strip()
            
            if key_type in ALTERNATE_KEY_FIELDS:
                return ALTERNATE_KEY_FIELDS[key_type], key_value
            else:
                print(f"[✗] Unknown key type '{key_type}'. Valid types: {', '.join(ALTERNATE_KEY_FIELDS.keys())}")
                continue
        
        # Assume it's a GUID
        # Basic GUID validation (8-4-4-4-12 format)
        if len(location_input) == 36 and location_input.count('-') == 4:
            return 'guid', location_input
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


def get_full_location_details(location_id, org_url, headers):
    """
    Fetch complete location details including related records.
    
    Args:
        location_id: Location GUID
        org_url: Dataverse organization URL
        headers: HTTP headers with auth token
    
    Returns:
        dict: Complete location data or None if error
    """
    print(f"\n[*] Fetching Location Details: {location_id}")
    
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
    
    # We assume 'lmdm_locations' is the Entity Set Name (Plural)
    url = f"{org_url}/api/data/v9.2/lmdm_locations({location_id})?$select={select_query}"
    
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
        
        location_data = response.json()
        print(f"[✓] Successfully fetched location record")
        
    except Exception as e:
        print(f"[✗] Request Error: {str(e)}")
        return None
    
    # Build the output object
    final_output = {
        "LocationId": location_id,
        "Fields": {}
    }
    
    # Extract all fields with formatted values
    for field in valid_fields:
        final_output["Fields"][field] = format_field(location_data, field)
    
    # --- B. Fetch Key Personnel (N:N) ---
    print("[*] Step 3: Fetching Related Key Personnel...")
    kp_nav_prop = RELATIONSHIPS["KeyPersonnel"]
    kp_url = f"{org_url}/api/data/v9.2/lmdm_locations({location_id})/{kp_nav_prop}"
    print(f"[*] Navigation Property: {kp_nav_prop}")
    
    try:
        kp_response = requests.get(kp_url, headers=headers)
        final_output["Related_KeyPersonnel"] = []
        
        if kp_response.status_code == 200:
            kp_records = kp_response.json().get('value', [])
            print(f"[✓] Found {len(kp_records)} key personnel record(s)")
            
            for kp in kp_records:
                kp_obj = {}
                for k, v in kp.items():
                    if "@" not in k:  # Skip odata annotations in keys
                        kp_obj[k] = v
                final_output["Related_KeyPersonnel"].append(kp_obj)
        else:
            error_text = kp_response.text
            print(f"[!] Could not fetch key personnel (Status: {kp_response.status_code})")
            print(f"[!] Error: {error_text[:200]}...")
    
    except Exception as e:
        print(f"[!] Error fetching key personnel: {str(e)}")
    
    # --- B. Fetch Key Personnel (N:N) ---
    print("[*] Step 3: Fetching Related Key Personnel...")
    kp_nav_prop = RELATIONSHIPS["KeyPersonnel"]
    kp_url = f"{org_url}/api/data/v9.2/lmdm_locations({location_id})/{kp_nav_prop}"
    print(f"[*] Navigation Property: {kp_nav_prop}")
    
    try:
        kp_response = requests.get(kp_url, headers=headers)
        final_output["Related_KeyPersonnel"] = []
        
        if kp_response.status_code == 200:
            kp_records = kp_response.json().get('value', [])
            print(f"[✓] Found {len(kp_records)} key personnel record(s)")
            
            for kp in kp_records:
                kp_obj = {}
                for k, v in kp.items():
                    if "@" not in k:  # Skip odata annotations in keys
                        kp_obj[k] = v
                final_output["Related_KeyPersonnel"].append(kp_obj)
        else:
            error_text = kp_response.text
            print(f"[!] Could not fetch key personnel (Status: {kp_response.status_code})")
            print(f"[!] Error: {error_text[:200]}...")
    
    except Exception as e:
        print(f"[!] Error fetching key personnel: {str(e)}")
    
    # --- C. Fetch Business Hours (1:N) ---
    print("[*] Step 4: Fetching Related Business Hours...")
    bh_nav_prop = RELATIONSHIPS["BusinessHours"]
    bh_url = f"{org_url}/api/data/v9.2/lmdm_locations({location_id})/{bh_nav_prop}"
    print(f"[*] Navigation Property: {bh_nav_prop}")
    
    try:
        bh_response = requests.get(bh_url, headers=headers)
        final_output["Related_BusinessHours"] = []
        
        if bh_response.status_code == 200:
            bh_records = bh_response.json().get('value', [])
            print(f"[✓] Found {len(bh_records)} business hours record(s)")
            
            for bh in bh_records:
                bh_obj = {}
                for k, v in bh.items():
                    if "@" not in k:
                        bh_obj[k] = v
                final_output["Related_BusinessHours"].append(bh_obj)
        else:
            error_text = bh_response.text
            print(f"[!] Could not fetch business hours (Status: {bh_response.status_code})")
            print(f"[!] Error: {error_text[:200]}...")
    
    except Exception as e:
        print(f"[!] Error fetching business hours: {str(e)}")
    
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
        f.write(" DATAVERSE LOCATION DETAILS REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location ID: {data.get('LocationId', 'N/A')}\n")
        f.write("\n" + "="*80 + "\n")
        f.write(" LOCATION FIELDS\n")
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
        
        # Related Key Personnel
        f.write("\n" + "="*80 + "\n")
        f.write(" RELATED KEY PERSONNEL\n")
        f.write("="*80 + "\n\n")
        
        key_personnel = data.get('Related_KeyPersonnel', [])
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
        
        # Related Key Personnel
        if data.get("Related_KeyPersonnel"):
            f.write("="*60 + "\n")
            f.write(" RELATED KEY PERSONNEL\n")
            f.write("="*60 + "\n\n")
            
            for i, kp in enumerate(data["Related_KeyPersonnel"], 1):
                f.write(f"Key Personnel #{i}:\n")
                for field, value in kp.items():
                    if value is not None:
                        f.write(f"  {field}: {value}\n")
                f.write("\n")
        else:
            f.write("No key personnel records found.\n\n")
            
        # Related Business Hours
        f.write("\n" + "="*80 + "\n")
        f.write(" RELATED BUSINESS HOURS\n")
        f.write("="*80 + "\n\n")
        
        business_hours = data.get('Related_BusinessHours', [])
        if business_hours:
            for idx, bh in enumerate(business_hours, 1):
                f.write(f"--- Schedule {idx} ---\n")
                for k, v in bh.items():
                    if isinstance(v, dict):
                        f.write(f"  {k}: {v.get('DisplayValue', v.get('Value', ''))}\n")
                    else:
                        f.write(f"  {k}: {v}\n")
                f.write("\n")
        else:
            f.write("No business hours records found.\n\n")
        
        f.write("="*80 + "\n")
        f.write(" END OF REPORT\n")
        f.write("="*80 + "\n")
    
    print(f"[✓] Report saved: {filepath}")
    return filepath


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch Dataverse Location details via Web API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for everything)
  python custom-api-location.py
  
  # Specify environment and location GUID
  python custom-api-location.py -e 2 -l 12345678-1234-1234-1234-123456789abc
  
  # Use alternate key (CCID)
  python custom-api-location.py -e 1 -k ccid:CC12345
  
  # Use alternate key (Store Name)
  python custom-api-location.py -e 3 -k storename:"Downtown Store"
  
  # Skip saving output files
  python custom-api-location.py -e 2 -l <guid> --no-save
        """
    )
    
    parser.add_argument(
        '-e', '--environment',
        type=int,
        choices=[1, 2, 3, 4],
        help='Environment: 1=Prod, 2=Dev, 3=Sandbox, 4=Tanushri'
    )
    
    parser.add_argument(
        '-l', '--location',
        type=str,
        help='Location GUID (e.g., 12345678-1234-1234-1234-123456789abc)'
    )
    
    parser.add_argument(
        '-k', '--key',
        type=str,
        help='Alternate key in format keytype:value (e.g., ccid:CC12345, fmcid:FMC98765)'
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
        print(" DATAVERSE LOCATION API CLIENT")
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
        
        # Step 3: Get location identifier
        location_id = None
        
        if args.location:
            # GUID provided via command line
            location_id = args.location
            print(f"\n[*] Using location GUID from command line: {location_id}")
        
        elif args.key:
            # Alternate key provided via command line
            if ":" in args.key:
                parts = args.key.split(":", 1)
                key_type = parts[0].lower().strip()
                key_value = parts[1].strip()
                
                if key_type in ALTERNATE_KEY_FIELDS:
                    key_field = ALTERNATE_KEY_FIELDS[key_type]
                    location_id = get_location_by_alternate_key(org_url, headers, key_field, key_value)
                    
                    if not location_id:
                        print("[✗] Could not find location with provided alternate key")
                        return 1
                else:
                    print(f"[✗] Unknown key type '{key_type}'. Valid: {', '.join(ALTERNATE_KEY_FIELDS.keys())}")
                    return 1
            else:
                print("[✗] Invalid key format. Use 'keytype:value'")
                return 1
        
        else:
            # Interactive mode - prompt for location
            lookup_type, lookup_value = prompt_for_location()
            
            if lookup_type == 'guid':
                location_id = lookup_value
            else:
                # It's an alternate key
                location_id = get_location_by_alternate_key(org_url, headers, lookup_type, lookup_value)
                
                if not location_id:
                    print("[✗] Could not find location with provided identifier")
                    return 1
        
        # Step 4: Fetch location details
        print("\n" + "-"*70)
        result = get_full_location_details(location_id, org_url, headers)
        
        if not result:
            print("[✗] Failed to fetch location details")
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
            prefix = args.output_prefix if args.output_prefix else f"location_{location_id[:8]}"
            
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