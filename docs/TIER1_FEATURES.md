# Tier 1 Features Guide

## Overview

This guide covers the three major Tier 1 features introduced in Dataverse API Studio 2.0:
1. **Metadata Discovery** - Automatic entity and field discovery with caching
2. **Excel/CSV Mapper** - Visual mapping tool for bulk data import
3. **Template Library** - Save and reuse operation configurations

---

## Feature 1: Metadata Discovery

### What is Metadata Discovery?

Metadata discovery automatically fetches entity definitions, field metadata, and choice option labels from your Dataverse environment. This eliminates manual lookup of field names and datatypes.

### Key Benefits

- ✅ **Auto-complete** for entity and field names
- ✅ **Datatype hints** (String, Integer, Lookup, Choice, etc.)
- ✅ **Choice labels** (e.g., "Active" → 1, "Inactive" → 0)
- ✅ **24-hour caching** for performance
- ✅ **Manual refresh** via "Refresh Schema" button

### How to Use

#### 1. Automatic Loading
Once connected, metadata is fetched automatically when you:
- Select an entity in Excel Mapper
- Use autocomplete in CRUD/Query tabs (future enhancement)

#### 2. Manual Cache Refresh
If your schema changes (new fields, updated choices):
1. Click **"🔄 Refresh Schema"** button in Auth panel
2. Cache is cleared
3. Next metadata request will fetch fresh data

#### 3. Cache Status
Check status bar for cache information:
- "✅ Connected to DEV" - Normal operation
- Cache expires after 24 hours automatically

### Behind the Scenes

```python
# Metadata fetch with caching
client = MetadataClient(...)
result = client.fetch_entity_attributes("account", use_cache=True)

# Result includes:
{
  "success": True,
  "attributes": [
    {
      "LogicalName": "name",
      "DisplayName": {"UserLocalizedLabel": {"Label": "Account Name"}},
      "AttributeType": "String",
      "IsValidForCreate": True,
      "IsValidForUpdate": True
    },
    ...
  ],
  "from_cache": True  # Indicates cache hit
}
```

### Cache Location

Metadata is stored in `.cache/` folder (git-ignored):
```
.cache/
  ├── https___org.crm.dynamics.com_EntityDefinitions.json
  ├── https___org.crm.dynamics.com_EntityDefinitions_account_Attributes.json
  └── https___org.crm.dynamics.com_Choice_account_statecode.json
```

Each file contains:
```json
{
  "timestamp": 1704537600.0,
  "data": { ... }
}
```

---

## Feature 2: Excel/CSV Mapper

### What is Excel/CSV Mapper?

A visual tool for mapping Excel columns to Dataverse fields with automatic datatype conversion. Perfect for bulk data imports from spreadsheets.

### Key Benefits

- ✅ **Visual mapping** - Drag-free dropdown assignment
- ✅ **Auto-detect headers** - Scans first 5 rows
- ✅ **Datatype validation** - Validates before import
- ✅ **Preview** - See first 3 rows before import
- ✅ **Batch generation** - Create 1000s of records at once
- ✅ **Choice label mapping** - Use friendly names (e.g., "Active" instead of 1)

### Step-by-Step Workflow

#### Step 1: Select File
1. Go to **📊 Excel Mapper** tab
2. Click **"📂 Select File"**
3. Choose `.xlsx`, `.xls`, or `.csv` file
4. Adjust **Header Row** number if needed (default: 1)

**Example:**
```
Excel file: customers.xlsx
Row 1: Company Name, Website, Phone, Status
Row 2: Contoso Corp, https://contoso.com, 555-0100, Active
Row 3: Fabrikam Inc, https://fabrikam.com, 555-0200, Active
```

#### Step 2: Select Target Entity
1. Enter or select entity name (e.g., `account`)
2. Click **"🔍 Fetch Fields"**
3. Wait for metadata to load (uses cache if available)

**Result:** Right panel populates with Dataverse fields:
```
name (String)
websiteurl (String)
telephone1 (String)
statecode (State)
accountid (Uniqueidentifier)
...
```

#### Step 3: Map Fields
1. Select Excel column from left dropdown
2. Select Dataverse field from right dropdown
3. Click **"✅ Assign"**
4. Repeat for all columns

**Example Mapping:**
```
Company Name  →  name (String)
Website       →  websiteurl (String)
Phone         →  telephone1 (String)
Status        →  statecode (State)
```

#### Step 4: Preview & Generate
1. **JSON Preview** updates automatically showing first row
2. Click **"🔨 Generate JSON"** to validate all rows
3. Review summary:
   - Total Rows: 500
   - Valid Rows: 498
   - Errors: Row 15 (Invalid phone format), Row 42 (Missing required field)

#### Step 5: Load to CRUD or Batch
**Option A: Single Record (CRUD)**
1. Click **"📝 Load to CRUD"**
2. First row loaded to CRUD tab
3. Review and click **"✅ Execute"**

**Option B: Bulk Import (Batch)**
1. Click **"⚡ Load to Batch"**
2. All rows converted to batch operations
3. Review JSON array in Batch tab
4. Click **"⚡ Execute Batch"**
5. 498 records created in ~5 seconds! ⚡

### Supported File Formats

#### Excel (.xlsx, .xls)
- ✅ Multiple sheets (active sheet used)
- ✅ Merged cells (reads first cell value)
- ✅ Formulas (reads calculated values)
- ✅ Date cells (auto-converted)

#### CSV (.csv)
- ✅ Quoted fields ("Company, Inc.")
- ✅ Escaped characters (\n, \t)
- ✅ Various encodings (UTF-8, Latin-1)

### Datatype Conversion Rules

| Excel Value | Dataverse Type | Result |
|-------------|----------------|--------|
| "John Doe" | String | "John Doe" |
| 12345 | Integer | 12345 |
| 123.45 | Decimal | 123.45 |
| "TRUE" or "Yes" | Boolean | true |
| "2024-01-15" | Date | "2024-01-15" |
| "2024-01-15 14:30:00" | DateTime | "2024-01-15T14:30:00Z" |
| "550e8400-e29b-41d4-a716-446655440000" | Lookup | "/accounts(550e8400-e29b-41d4-a716-446655440000)" |
| "Active" | Choice | 1 (mapped from metadata) |

### Choice Field Mapping

When mapping to choice/picklist fields, you can use **friendly labels** instead of numeric values:

**Metadata provides:**
```json
{
  "label": "Active",
  "value": 0
},
{
  "label": "Inactive",
  "value": 1
}
```

**Excel can contain:**
```
Status
Active
Inactive
Active
```

**JSON Builder converts:**
```json
{"statecode": 0}
{"statecode": 1}
{"statecode": 0}
```

### Lookup Field Mapping

For lookup fields, provide either:

1. **Plain GUID:**
   ```
   550e8400-e29b-41d4-a716-446655440000
   ```
   → Formatted to: `"/accounts(550e8400-e29b-41d4-a716-446655440000)"`

2. **@odata.bind format:**
   ```
   /accounts(550e8400-e29b-41d4-a716-446655440000)
   ```
   → Used as-is

### Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid date format" | Excel date not recognized | Use YYYY-MM-DD format |
| "GUID must be in format..." | Invalid GUID | Check GUID structure (8-4-4-4-12) |
| "Choice label not found" | Label doesn't match metadata | Use exact label from metadata or numeric value |
| "Value must be an integer" | Text in Integer field | Ensure column contains only numbers |

### Advanced: Header Row Detection

Excel Mapper auto-detects the header row by scoring each of the first 5 rows:

**Scoring Algorithm:**
- +2 points: Text (non-numeric) cell
- +1 point: Non-numeric cell
- +10 points: High unique value ratio

**Example:**
```
Row 1: [empty]              → Score: 0
Row 2: "Data Import 2024"   → Score: 2
Row 3: Name, Email, Phone   → Score: 26 ✅ (selected)
Row 4: John, john@ex.com    → Score: 6
Row 5: Jane, jane@ex.com    → Score: 6
```

Override if incorrect: Set **Header Row** to correct row number.

---

## Feature 3: Template Library

### What are Templates?

Templates are saved operation configurations with optional placeholders (`${variable_name}`). Reuse common operations without re-typing JSON.

### Key Benefits

- ✅ **Save time** - Reuse frequent operations
- ✅ **Consistency** - Same structure every time
- ✅ **Placeholders** - Customize on load
- ✅ **Shareable** - Export templates as JSON files
- ✅ **Version control** - Track changes in git (optional)

### Template Types

1. **CRUD Templates** - CREATE, READ, UPDATE, DELETE configurations
2. **Batch Templates** - Bulk operation arrays
3. **Query Templates** - OData filter configurations (future)

### Creating a CRUD Template

#### Step 1: Configure Operation
In CRUD tab:
1. Select operation: **CREATE**
2. Table name: `account`
3. Data JSON:
   ```json
   {
     "name": "${company_name}",
     "websiteurl": "${website}",
     "telephone1": "${phone}",
     "industry": "Technology"
   }
   ```

#### Step 2: Save Template
1. Click **"Save Template"**
2. Enter name: `new_tech_account`
3. Click OK

**Saved to:** `templates/new_tech_account.template.json`

```json
{
  "type": "crud",
  "operation": "CREATE",
  "table_name": "account",
  "data": {
    "name": "${company_name}",
    "websiteurl": "${website}",
    "telephone1": "${phone}",
    "industry": "Technology"
  },
  "_metadata": {
    "created": "2024-01-15T10:30:00",
    "version": "1.0"
  }
}
```

#### Step 3: Load Template
1. Select template from **Template:** dropdown
2. Click **"Load Template"**
3. If placeholders exist, prompted to fill:
   - `company_name`: **Contoso Corp**
   - `website`: **https://contoso.com**
   - `phone`: **555-0100**
4. JSON updated with filled values

### Placeholder Syntax

#### Standard Placeholder
```json
{"field": "${placeholder_name}"}
```

#### Multiple Placeholders
```json
{
  "firstname": "${first_name}",
  "lastname": "${last_name}",
  "fullname": "${first_name} ${last_name}"
}
```

#### Nested Placeholders
```json
{
  "ownerid@odata.bind": "/systemusers(${owner_id})"
}
```

### Creating a Batch Template

#### Example: Bulk Contact Creation
```json
{
  "type": "batch",
  "operations": [
    {
      "method": "POST",
      "url": "/api/data/v9.2/contacts",
      "data": {
        "firstname": "${contact1_first}",
        "lastname": "${contact1_last}",
        "parentcustomerid@odata.bind": "/accounts(${account_id})"
      }
    },
    {
      "method": "POST",
      "url": "/api/data/v9.2/contacts",
      "data": {
        "firstname": "${contact2_first}",
        "lastname": "${contact2_last}",
        "parentcustomerid@odata.bind": "/accounts(${account_id})"
      }
    }
  ]
}
```

**Use Case:** Add multiple contacts to same account

### Template Management

#### List Templates
- View all templates in dropdown in CRUD/Batch tabs
- Alphabetically sorted

#### Delete Template
1. Load template
2. (Manual: Delete file from `templates/` folder)

#### Export/Import Templates
Templates are JSON files in `templates/` folder:
- **Export:** Copy `.template.json` files
- **Import:** Paste into `templates/` folder
- **Share:** Commit to git (ensure no secrets!)

### Best Practices

#### 1. Naming Conventions
```
create_account_with_contacts.template.json
update_opportunity_stage.template.json
query_active_leads.template.json
```

#### 2. Placeholder Names
- Use descriptive names: `${account_name}` not `${x}`
- Snake_case: `${customer_phone}` not `${CustomerPhone}`
- No spaces: `${first_name}` not `${first name}`

#### 3. Documentation
Add comments in template (metadata section):
```json
{
  "type": "crud",
  "_metadata": {
    "created": "2024-01-15",
    "author": "John Doe",
    "description": "Create new technology account with default settings",
    "placeholders": {
      "company_name": "Full company name",
      "website": "Company website URL",
      "phone": "Main phone number (format: 555-0100)"
    }
  }
}
```

#### 4. Security
⚠️ **Never store secrets in templates:**
- ❌ Client secrets
- ❌ Passwords
- ❌ API keys
- ❌ Personal data

Use placeholders instead:
```json
{
  "password": "${user_password}"  // ✅ Prompted on load
}
```

### Advanced: Template Validation

Templates are validated on load:

**Validation Rules:**
1. Must have `type` field ("crud", "batch", or "query")
2. CRUD templates must have `operation` field
3. Batch templates must have `operations` array
4. Valid JSON structure

**Example Error:**
```
Template validation failed:
- Missing 'operation' field in CRUD template
- Expected 'operations' array in batch template
```

---

## Tier 1 Feature Comparison

| Feature | Metadata Discovery | Excel Mapper | Templates |
|---------|-------------------|--------------|-----------|
| **Primary Use** | Schema exploration | Bulk import | Reusable configs |
| **Performance** | 95% cache hit rate | Process 1000s rows | Instant load |
| **User Benefit** | No manual lookup | Visual mapping | Time savings |
| **Storage** | `.cache/` folder | In-memory | `templates/` folder |
| **TTL** | 24 hours | Session only | Permanent |
| **Shareable** | No | No | Yes |

---

## Troubleshooting

### Metadata Issues

**Problem:** Fields not appearing in Excel Mapper
- **Solution:** Click "🔄 Refresh Schema" and retry

**Problem:** Choice labels wrong
- **Solution:** Cache expired, refresh schema

### Excel Mapper Issues

**Problem:** Wrong header row detected
- **Solution:** Manually set Header Row number

**Problem:** Datatype conversion errors
- **Solution:** Check preview table, ensure correct format

**Problem:** Choice label not found
- **Solution:** Use numeric value or fetch metadata again

### Template Issues

**Problem:** Template not loading
- **Solution:** Check JSON syntax, validate structure

**Problem:** Placeholders not prompted
- **Solution:** Ensure `${...}` syntax is correct

**Problem:** Template contains old entity names
- **Solution:** Update template file manually or recreate

---

## Next Steps

Now that you've mastered Tier 1 features:

1. **Practice:** Import sample Excel file with various datatypes
2. **Create Templates:** Save your most common operations
3. **Optimize:** Use metadata caching for faster workflows
4. **Explore:** Check ARCHITECTURE.md for technical details

**Need help?** Check:
- `docs/setup_guide.md` - Installation and setup
- `docs/ARCHITECTURE.md` - Technical architecture
- `README.md` - Quick reference and examples
