# Entity Metadata Exporter - Usage Guide

## Overview
Simple Python script to fetch and export complete entity metadata from Dataverse. No UI needed - just runs from command line and saves everything to a file.

## What It Does
1. Authenticates to your Dataverse environment
2. Fetches the entity metadata endpoint:
   ```
   GET [OrgUrl]/api/data/v9.2/EntityDefinitions(LogicalName='{entity}')?
       $expand=Attributes,OneToManyRelationships,ManyToOneRelationships,ManyToManyRelationships
   ```
3. Saves everything to both `.txt` (readable report) and `.json` (raw data) formats
4. Optionally fetches and includes sample record data

## Quick Start

### Basic Usage
```bash
# Fetch lmdm_location metadata and save to default file
python scripts/entity_metadata_exporter.py lmdm_location

# Fetch and save to custom filename
python scripts/entity_metadata_exporter.py lmdm_location my_entity_report.txt

# Fetch as JSON
python scripts/entity_metadata_exporter.py lmdm_location output.json
```

### With Sample Record Data
```bash
# Include a sample record in the export
python scripts/entity_metadata_exporter.py lmdm_location output.txt --record-id a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## Output Files

### Text Report (.txt)
Human-readable report including:
- Entity information (logical name, display name, primary keys)
- All attributes with their properties:
  - Type (String, Integer, DateTime, Lookup, Choice, etc.)
  - Required level
  - Valid for Create/Update
  - Min/Max values, formats, precision
  - Descriptions
- All relationships:
  - One-to-Many (child records)
  - Many-to-One (lookups)
  - Many-to-Many (junction relationships)
- Sample record data (if provided)

### JSON Export (.json)
Raw API response in JSON format - useful for:
- Integration with other tools
- Programmatic processing
- Direct API reference
- Comparing with API documentation

## Examples

### Example 1: Export lmdm_location Metadata
```bash
python scripts/entity_metadata_exporter.py lmdm_location
```

**Output:**
- `lmdm_location_metadata.txt` (readable report)
- `lmdm_location_metadata.json` (raw JSON)

Contents will include:
- All columns in the entity
- Type of each column (string, number, lookup, choice, datetime)
- Relationships to keypersonale (One-to-Many)
- Relationships to storelocation_businesshours (One-to-Many)
- All lookup references and their target entities

### Example 2: Export with Sample Record
```bash
python scripts/entity_metadata_exporter.py lmdm_location loc_report.txt --record-id 12345678-1234-1234-1234-123456789012
```

**Output includes:**
- Full metadata (as above)
- Actual values from the sample record
- Resolved lookup display names
- All relationship data

### Example 3: JSON Export for ETL Teams
```bash
python scripts/entity_metadata_exporter.py lmdm_location lmdm_location.json
```

Perfect for:
- ETL tool configuration
- Data mapping documents
- Integration specifications
- API testing

## Sample Output Format

### Text Report
```
====================================================================================================
ENTITY METADATA REPORT
====================================================================================================
Generated: 2026-01-28 15:30:45
Entity: lmdm_location

ENTITY INFORMATION:
---------
  Logical Name........................... lmdm_location
  Schema Name............................ lmdm_location
  Entity Set Name........................ lmdm_locations
  Primary Key Attribute.................. lmdm_locationid
  Primary Display Attribute.............. lmdm_locationname

ATTRIBUTES:
---------

  [lmdm_locationid]
    Logical Name............... lmdm_locationid
    Type....................... Uniqueidentifier
    Required Level............. SystemRequired
    Valid for Create........... False
    Valid for Update........... False

  [lmdm_locationname]
    Logical Name............... lmdm_locationname
    Type....................... String
    Max Length................. 100
    Required Level............. Required
    Valid for Create........... True
    Valid for Update........... True

  [lmdm_parent_location]
    Logical Name............... lmdm_parent_location
    Type....................... Lookup
    Required Level............. None
    Valid for Create........... True
    Valid for Update........... True
    Description................ Reference to parent location

RELATIONSHIPS:
---------

  ONE-TO-MANY RELATIONSHIPS:

    [lmdm_location_lmdm_keypersonale]
      Referencing Entity....... lmdm_keypersonale
      Referenced Entity........ lmdm_location
      Navigation Property...... lmdm_location_lmdm_keypersonale
      Custom Relationship...... False

    [lmdm_location_lmdm_storelocation_businesshours]
      Referencing Entity....... lmdm_storelocation_businesshours
      Referenced Entity........ lmdm_location
      Navigation Property...... lmdm_location_lmdm_storelocation_businesshours
      Custom Relationship...... False

  MANY-TO-ONE RELATIONSHIPS (Lookups):

    [lmdm_location_lmdm_location]
      References Entity........ lmdm_location
      This Entity.............. lmdm_location
      Lookup Attribute......... lmdm_parent_location
      Target Attribute......... lmdm_locationid

====================================================================================================
```

### JSON Export
```json
{
  "timestamp": "2026-01-28T15:30:45.123456",
  "entity_metadata": {
    "LogicalName": "lmdm_location",
    "SchemaName": "lmdm_location",
    "EntitySetName": "lmdm_locations",
    "PrimaryIdAttribute": "lmdm_locationid",
    "PrimaryNameAttribute": "lmdm_locationname",
    "Attributes": [
      {
        "LogicalName": "lmdm_locationid",
        "SchemaName": "lmdm_locationid",
        "AttributeType": "Uniqueidentifier",
        "RequiredLevel": "SystemRequired",
        "IsValidForCreate": false,
        "IsValidForUpdate": false
      },
      ...
    ],
    "OneToManyRelationships": [...],
    "ManyToOneRelationships": [...],
    "ManyToManyRelationships": [...]
  },
  "sample_record": { ... }
}
```

## Requirements
- `.env` file properly configured with:
  ```
  TENANT_ID=your-tenant-id
  CLIENT_ID=your-client-id
  CLIENT_SECRET=your-client-secret
  ORG_URL=https://yourorg.crm.dynamics.com
  ```
- Python 3.7+
- All dependencies from `requirements.txt` installed

## For ETL Teams

This script provides everything you need to know about an entity:

1. **Field Mapping**: All columns with their types and constraints
2. **Lookup Resolution**: See which lookups point to which entities
3. **Relationship Navigation**: Understand parent-child relationships
4. **Validation Rules**: Know required fields, min/max values
5. **Create/Update Rules**: See which fields are valid for which operations
6. **Sample Data**: Optional real record to see data structure

Perfect for:
- ✅ ETL configuration (field mapping, type conversion)
- ✅ Data validation (required fields, constraints)
- ✅ Integration planning (relationship mapping)
- ✅ Documentation (complete reference)
- ✅ Data quality checks (min/max, format constraints)

## Troubleshooting

### "Authentication failed"
- Check `.env` file is in the root directory
- Verify TENANT_ID, CLIENT_ID, CLIENT_SECRET
- Ensure CLIENT_SECRET is not expired

### "HTTP 400: Could not find property..."
- Script automatically uses only valid fields
- No manual fixes needed

### Empty or missing relationships
- Entity may have no relationships
- Or relationships may not be expanded by API
- Check JSON file for raw response

### Sample record not found
- Record ID must be valid GUID
- User must have read permissions on the record
- Try without `--record-id` first

## Examples for lmdm_location Entity

```bash
# Get everything about lmdm_location
python scripts/entity_metadata_exporter.py lmdm_location

# Save with custom name
python scripts/entity_metadata_exporter.py lmdm_location location_metadata.txt

# Export as JSON for tools
python scripts/entity_metadata_exporter.py lmdm_location location_data.json

# Include sample record data
python scripts/entity_metadata_exporter.py lmdm_location location_full.txt --record-id [GUID]
```

## Support
Run with no arguments for help:
```bash
python scripts/entity_metadata_exporter.py
```

Check output files for complete entity reference documentation.
