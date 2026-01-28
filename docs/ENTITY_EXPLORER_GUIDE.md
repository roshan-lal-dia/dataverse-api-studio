# Entity Explorer - Comprehensive Record Details Viewer

## Overview
The Entity Explorer tab provides a complete view of any Dataverse record, including all attributes (with actual and display values), metadata, relationships, and the ability to navigate through related records. Designed specifically for ETL teams and data analysts.

## Features

### 1. Complete Metadata Display
- **Entity Information**: Display name, logical name, primary key, collection name
- **All Attributes**: Every field with its type, value, display value, description, and validation rules
- **Relationships**: One-to-Many, Many-to-One, and Many-to-Many relationships
- **Type Icons**: Visual indicators for different data types (📝 String, 🔢 Number, 📅 Date, etc.)

### 2. Advanced Data Exploration
- **Record Lookup**: Find any record by GUID or unique identifier
- **Multiple Views**:
  - **Attributes Table**: Tabular view with all field details
  - **Relationships**: Clickable list to navigate related records
  - **JSON View**: Raw JSON response from API
  - **HTML Summary**: Formatted HTML report

### 3. Comprehensive Export Options
The **"💾 Save Response"** button offers multiple export formats:

#### JSON Format
- Complete record details in structured JSON
- Includes metadata, attributes, values, and relationships
- Perfect for API integration and data processing

#### HTML Format
- Formatted report with styling
- Easy to view in browsers
- Includes all metadata and relationships
- Great for documentation and reporting

#### CSV Format
- Spreadsheet-friendly format
- Columns: Attribute Name, Type, Value, Display Value, Description, Required, Valid for Create, Valid for Update
- Ideal for Excel analysis and bulk operations

#### Plain Text Format
- Human-readable summary
- Organized sections for attributes and relationships
- Easy to share via email or documentation

#### XML Format
- Structured XML output for ETL systems
- Includes attribute metadata and validation flags
- Compatible with enterprise integration tools

### 4. API Endpoint Used
```
GET [OrgUrl]/api/data/v9.2/EntityDefinitions(LogicalName='{entity}')?$expand=Attributes,OneToManyRelationships,ManyToOneRelationships,ManyToManyRelationships
```

This endpoint provides complete entity metadata including all properties needed for ETL operations.

## Usage Workflow

### Step 1: Authentication
1. Navigate to the **Entity Explorer** tab
2. Ensure you're authenticated (Auth Panel shows ✅ Connected)
3. Entity dropdown will auto-populate with available entities

### Step 2: Select Entity and Record
1. Choose an entity from the dropdown (e.g., `lmdm_location`)
2. Enter the record GUID in the "Record GUID" field
3. Click **"🔎 Load Record"**

### Step 3: Explore Data
- **Attributes Tab**: Review all field values, types, and metadata
- **Relationships Tab**: Click any relationship to navigate to related records
- **JSON View**: See the raw API response
- **HTML Summary**: View formatted report

### Step 4: Export/Save
- Click **"💾 Save Response"** for multiple format options
- Click **"📤 Export JSON"** for quick JSON export with clipboard copy

## Use Cases

### For ETL Teams
1. **Field Discovery**: Identify all available fields and their types
2. **Lookup Resolution**: See actual GUID values and their display names
3. **Relationship Mapping**: Understand entity relationships for data integration
4. **Validation Rules**: Know which fields are required and valid for create/update operations
5. **Data Export**: Export complete record details in XML/CSV for ETL tools

### For Data Analysts
1. **Data Exploration**: Browse records with all metadata visible
2. **Report Generation**: Export HTML reports for stakeholders
3. **CSV Analysis**: Export to CSV for Excel-based analysis
4. **Relationship Navigation**: Follow relationships to explore data lineage

### For Developers
1. **API Testing**: Verify API responses and field values
2. **Metadata Discovery**: Understand entity structure and capabilities
3. **JSON Templates**: Use exported JSON as templates for API calls
4. **Integration Reference**: XML export for integration documentation

## Target Entity: lmdm_location

### Key Attributes to Display
- **Basic Info**: Location name, code, address fields
- **Lookups**: Associated entities (resolved with display names)
- **Status Fields**: Active status, operational hours
- **Audit Fields**: Created/modified dates and users

### Key Relationships
1. **lmdm_keypersonnel** (One-to-Many)
   - Navigate to all key personnel for this location
   - See roles, contact info, etc.

2. **lmdm_storelocation_businesshours** (One-to-Many)
   - View all business hours configurations
   - Understand operating schedules

3. **Many-to-One Lookups**
   - Parent location (if hierarchy exists)
   - Region, market, or organizational references

## File Structure

```
client/
  └── entity_explorer.py          # Core API client for metadata and record fetching
utils/
  └── entity_details_formatter.py # Formatting utilities for display and export
ui/
  └── tabs/
      └── entity_explorer_tab.py  # UI implementation with all views and exports
```

## Technical Details

### Caching Strategy
- **Metadata Cache**: Entity definitions cached for 24 hours (SchemaCache)
- **Manual Refresh**: "🔄 Refresh" button to reload current record
- **Cache Location**: `.cache/` directory

### Threading Model
- All API calls run in background threads (QThread)
- Progress indicators show fetch status
- UI remains responsive during operations

### Data Type Handling
Supports all Dataverse types:
- String, Memo (📝)
- Integer, Decimal, Money, Double (🔢)
- Boolean (☑️)
- DateTime, Date (📅)
- Lookup (🔗)
- Choice/Picklist (📋)
- Owner (👤)
- UniqueIdentifier (🆔)
- Image, File (🖼️)

### Lookup Resolution
- Automatically fetches display names for lookup fields
- Shows both GUID and resolved entity name
- Click to navigate to referenced record

### Relationship Navigation
- Click any relationship in the Relationships tab
- For Many-to-One: Navigate to the referenced record
- For One-to-Many/Many-to-Many: Open dialog with related records list

## Export File Naming
Files are automatically named with:
```
{entity_name}_{record_id_prefix}_{timestamp}.{extension}
```
Example: `lmdm_location_a1b2c3d4_20260128_143022.json`

## Environment Confirmation
The Entity Explorer respects the selected environment from the Auth Panel. All operations are performed against the authenticated Dataverse environment.

## Limitations and Notes
1. **Fetch Limits**: Related records limited to 100 per relationship (configurable)
2. **Large Fields**: Memo/text fields truncated in table view (full in JSON/exports)
3. **Performance**: First metadata fetch may take time; subsequent loads use cache
4. **Permissions**: Requires read permissions on target entities
5. **Formatted Values**: Not all lookups may have display names if related records are inaccessible

## Future Enhancements (Planned)
- [ ] Alternate key lookup (in addition to GUID)
- [ ] Bulk export (multiple records)
- [ ] Custom field selection for exports
- [ ] Comparison view (compare two records)
- [ ] Change tracking visualization
- [ ] Excel export with multiple sheets

## Troubleshooting

### "No data to save"
- Ensure you've loaded a record first (🔎 Load Record)
- Verify authentication is active

### "Failed to fetch metadata"
- Check network connectivity
- Verify entity name is correct
- Ensure proper permissions

### Empty display values for lookups
- Related record may not exist or be inaccessible
- Check security roles and permissions

### Slow loading
- First load fetches and caches metadata (24hr cache)
- Subsequent loads will be faster
- Use "🔄 Refresh" to reload without re-fetching metadata

## Support
For issues or feature requests, check:
1. `.cache/` directory for cached metadata
2. Application logs for detailed error messages
3. API responses in JSON View tab
