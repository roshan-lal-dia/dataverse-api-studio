# Entity Metadata Exporter - Implementation Summary

## What Was Built

A comprehensive solution for exploring and exporting Dataverse entity metadata, designed for ETL teams and data analysts.

## Components

### 1. Command-Line Script (Recommended for ETL)
**File**: `scripts/entity_metadata_exporter.py`

Simple standalone Python script that:
- Takes entity name as input
- Fetches metadata using the endpoint: `EntityDefinitions(LogicalName='{entity}')?$expand=Attributes,OneToManyRelationships,ManyToOneRelationships,ManyToManyRelationships`
- Saves to both readable `.txt` and raw `.json` formats
- Optionally includes sample record data

**Usage**:
```bash
python scripts/entity_metadata_exporter.py lmdm_location
python scripts/entity_metadata_exporter.py lmdm_location output.json --record-id [GUID]
```

**Best for**: 
- ✅ ETL teams (no UI needed, just pure data export)
- ✅ Automation scripts
- ✅ Batch processing
- ✅ Integration with other tools

### 2. UI Entity Explorer Tab (For Interactive Use)
**Files**:
- `client/entity_explorer.py` - Core API client extending MetadataClient
- `utils/entity_details_formatter.py` - Formatting utilities
- `ui/tabs/entity_explorer_tab.py` - PyQt6 UI tab

Features:
- Interactive GUI for browsing entities
- Multiple views: Attributes table, Relationships, JSON, HTML
- Clickable relationships to navigate between records
- Multi-format export: JSON, HTML, CSV, TXT, XML
- Progress indicators and status updates

**Best for**:
- ✅ Manual data exploration
- ✅ Finding specific records
- ✅ Understanding relationships visually
- ✅ Learning entity structure

## What You Get About Each Entity

### Basic Entity Information
- Logical name (e.g., `lmdm_location`)
- Schema name
- Entity set name (collection name)
- Primary key attribute
- Primary display attribute

### All Attributes with:
- Type (String, Integer, DateTime, Lookup, Choice, etc.)
- Max length, precision, min/max values
- Required level
- Valid for Create/Update flags
- Description
- Display name

### Complete Relationship Map
1. **One-to-Many Relationships**
   - Child entities that reference this entity
   - Example: `lmdm_location → lmdm_keypersonale`
   - Navigation properties for queries

2. **Many-to-One Relationships (Lookups)**
   - Parent entities this entity references
   - Lookup attributes
   - Target attributes

3. **Many-to-Many Relationships**
   - Related entities through junction table
   - Intersection entity names
   - Navigation properties both ways

### Optional Sample Record
- Actual values from a record
- Resolved lookup display names
- Real data structure

## For lmdm_location Entity

The exporter will provide:

```
Entity Information:
  - Logical Name: lmdm_location
  - Primary Key: lmdm_locationid
  - Display Field: lmdm_locationname

Attributes:
  - lmdm_locationid (Uniqueidentifier) - Primary Key
  - lmdm_locationname (String, 100 chars) - Display Name
  - lmdm_address (String, 1000 chars)
  - lmdm_city (String, 50 chars)
  - lmdm_parent_location (Lookup → lmdm_location)
  - lmdm_status (Choice: Active, Inactive, Suspended)
  - lmdm_operatinghours (String)
  - [... all other attributes ...]

Relationships:
  ✓ One-to-Many:
    - lmdm_location → lmdm_keypersonale (Location has key personnel)
    - lmdm_location → lmdm_storelocation_businesshours (Location has business hours)
  
  ✓ Many-to-One (Lookups):
    - lmdm_location.parent_location → lmdm_location (Parent location reference)
    - [... other lookups ...]
  
  ✓ Many-to-Many:
    - [... if any exist ...]

Sample Record (optional):
  - Record ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  - Location Name: "New York Store"
  - Address: "123 Main St, New York, NY 10001"
  - Status: "Active"
  - Parent Location: "Northeast Region" (resolved from lookup)
  - [... actual values for all fields ...]
```

## File Outputs

### Text Report (.txt)
```
====================================================================================================
ENTITY METADATA REPORT
====================================================================================================

ENTITY INFORMATION:
  Logical Name........................... lmdm_location
  Schema Name............................ lmdm_location
  Entity Set Name........................ lmdm_locations
  Primary Key Attribute.................. lmdm_locationid
  Primary Display Attribute.............. lmdm_locationname

ATTRIBUTES:
  [lmdm_locationid]
    Type....................... Uniqueidentifier
    Required Level............. SystemRequired
    ...

  [lmdm_locationname]
    Type....................... String
    Max Length................. 100
    Required Level............. Required
    Valid for Create........... True
    ...

RELATIONSHIPS:
  ONE-TO-MANY RELATIONSHIPS:
    [lmdm_location_lmdm_keypersonale]
      Referencing Entity....... lmdm_keypersonale
      Navigation Property...... lmdm_location_lmdm_keypersonale
      ...
```

### JSON Export (.json)
```json
{
  "timestamp": "2026-01-28T15:30:45.123456",
  "entity_metadata": {
    "LogicalName": "lmdm_location",
    "Attributes": [
      {
        "LogicalName": "lmdm_locationid",
        "SchemaName": "lmdm_locationid",
        "AttributeType": "Uniqueidentifier",
        "RequiredLevel": { ... },
        ...
      }
    ],
    "OneToManyRelationships": [...],
    "ManyToOneRelationships": [...],
    "ManyToManyRelationships": [...]
  }
}
```

## Usage Examples

### For ETL Teams

**Step 1**: Export entity metadata
```bash
python scripts/entity_metadata_exporter.py lmdm_location
```

**Step 2**: Open `lmdm_location_metadata.txt`
- Review all fields and their types
- Check lookups and their target entities
- Note required fields and constraints
- Understand relationships for data mapping

**Step 3**: Use JSON for automation
- Open `lmdm_location_metadata.json`
- Parse in your ETL tool
- Implement field mapping
- Set up validation rules

### For Data Analysts

**Step 1**: Export with sample record
```bash
python scripts/entity_metadata_exporter.py lmdm_location report.txt --record-id [GUID]
```

**Step 2**: Review complete picture
- See metadata + actual values
- Understand data structure
- Verify relationships

### For Developers

**Step 1**: Export as JSON
```bash
python scripts/entity_metadata_exporter.py lmdm_location lmdm_location.json
```

**Step 2**: Use in development
- Reference for API calls
- Type checking
- Integration testing
- Documentation

## API Endpoint Reference

The script uses this exact endpoint:

```
GET [OrgUrl]/api/data/v9.2/EntityDefinitions(LogicalName='lmdm_location')?
    $expand=Attributes,OneToManyRelationships,ManyToOneRelationships,ManyToManyRelationships
```

Returns:
- **Attributes**: All fields with their metadata
- **OneToManyRelationships**: Child entities
- **ManyToOneRelationships**: Lookups to parent entities
- **ManyToManyRelationships**: Junction relationships

## Key Features

✅ **No UI Required** - Works as pure script  
✅ **Multiple Formats** - TXT (readable) + JSON (structured)  
✅ **ETL Ready** - All information needed for integration  
✅ **Complete Information** - Attributes, types, constraints, relationships  
✅ **Sample Data** - Optional real record inclusion  
✅ **Automatic** - No manual field selection needed  
✅ **Reliable** - Uses MetadataClient foundation  

## Getting Started

### 1. Setup
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows

# Ensure .env is configured
# TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL
```

### 2. Run Exporter
```bash
# Basic usage - most common
python scripts/entity_metadata_exporter.py lmdm_location

# This creates:
# - lmdm_location_metadata.txt (readable report)
# - lmdm_location_metadata.json (raw data)
```

### 3. Use Output
- **For ETL**: Open `.txt` file, use field list for mapping
- **For Integration**: Use `.json` file in your tools
- **For Documentation**: Share `.txt` file with team

## File Locations

```
scripts/
  ├── entity_metadata_exporter.py    ← Main script
  └── README.md                      ← Script documentation

docs/
  ├── ENTITY_METADATA_EXPORTER_GUIDE.md  ← Detailed guide
  └── ...

Output files created in current directory:
  ├── lmdm_location_metadata.txt     ← Human-readable report
  └── lmdm_location_metadata.json    ← Raw JSON response
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Authentication failed" | Check `.env` credentials |
| "Entity not found" | Verify entity logical name |
| "HTTP 400" | Script handles invalid fields automatically |
| Missing fields | Some fields may be filtered by API permissions |

## Next Steps

1. **Run the script**: `python scripts/entity_metadata_exporter.py lmdm_location`
2. **Review output**: Open the generated `.txt` file
3. **Use in ETL**: Reference the `.json` file for automation
4. **Share results**: Send `.txt` to team for documentation

## Support

Run with no arguments for help:
```bash
python scripts/entity_metadata_exporter.py
```

See documentation:
- [ENTITY_METADATA_EXPORTER_GUIDE.md](ENTITY_METADATA_EXPORTER_GUIDE.md)
- [Scripts README](scripts/README.md)
