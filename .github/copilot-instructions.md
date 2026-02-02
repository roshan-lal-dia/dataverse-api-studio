# Dataverse API Studio - AI Coding Agent Instructions

## Project Overview
Modern PyQt6 desktop application (modular architecture) providing comprehensive interface for Dataverse Web API operations. Features include CRUD, batch processing (up to 1000 ops/call), OData queries, Excel/CSV mapper with field mapping, metadata discovery with caching, template library, and **Custom API development with .NET plugins**—supporting all Dataverse datatypes.

### Latest Capabilities (2026)
- **Custom API Development**: Complete .NET plugin development using .NET CLI (no Visual Studio required)
- **Many-to-Many Relationships**: ✅ Resolved complex intersection table queries (KeyPersonnel case study)
- **Plugin Deployment**: Automated build and deployment with Plugin Registration Tool
- **Metadata Analysis**: Deep relationship discovery and troubleshooting tools
- **Performance Optimization**: Sub-second API responses with complex data retrieval

## Architecture

### Modular Design (Version 2.0)
The application has been refactored from monolithic tkinter (v1.0, deprecated) to modular PyQt6 architecture:

1. **Client Layer** (`client/`):
   - `dataverse_client.py`: Pure API client (CRUD, batch, OData queries)
   - `metadata_client.py`: Extends DataverseClient with metadata discovery + 24hr caching

2. **UI Layer** (`ui/`):
   - `main_window.py`: Main orchestrator (tabs, menus, signals)
   - `panels/`: auth_panel.py, history_panel.py
   - `tabs/`: crud_tab.py, excel_mapper_tab.py, batch_tab.py, query_tab.py, results_tab.py

3. **Utilities Layer** (`utils/`):
   - `config.py`: Environment loading (.env parser)
   - `schema_cache.py`: Local JSON cache with TTL
   - `validators.py`: Datatype validation (String, Integer, GUID, etc.)
   - `formatters.py`: Format conversions (dates, lookups, @odata.bind)
   - `excel_processor.py`: Excel/CSV reader with auto-header detection
   - `json_builder.py`: Excel→Dataverse JSON conversion with datatype mapping
   - `template_manager.py`: Save/load templates with ${placeholder} syntax

4. **Custom API Development Layer** (`AlshayaLocationAPI/`, `scripts/`):
   - **Plugin Development**: .NET Framework 4.6.2 plugins with .NET CLI workflow
   - **Custom API Integration**: Unbound functions for complex data retrieval
   - **Relationship Handling**: Many-to-many and one-to-many relationship queries
   - **Deployment Tools**: Plugin Registration Tool automation
   - **Testing Scripts**: Python validation and comparison tools

### Key Data Flows
- **Auth**: `.env` → `Config` → `AuthPanel` → `MetadataClient.authenticate()` → MSAL token
- **CRUD**: User input → validation → `CRUDOperationThread` (QThread) → `DataverseClient` → API
- **Batch**: JSON array → `batch_operation()` → multipart/mixed format → $batch endpoint
- **Query**: OData params → `read_multiple()` → results displayed in table + JSON views
- **Excel Mapper**: File upload → `ExcelProcessor` → header detection → metadata fetch → field mapping UI → `JSONBuilder` → CRUD/Batch tabs
- **Metadata**: Entity request → `SchemaCache.get()` → cache miss? → API fetch → cache store (24hr TTL)
- **Templates**: User saves config → `TemplateManager` → `templates/*.template.json` → load with placeholder prompts
- **Custom API Development**: Requirements → .NET plugin → `dotnet build` → Plugin Registration Tool → Custom API activation → Testing
- **Plugin Deployment**: C# code → .NET CLI build → DLL → PRT registration → Custom API association → HTTP testing

## Critical Patterns

### Custom API Development (.NET Plugins)
- **Development Environment**: .NET SDK 6.0+ with .NET Framework 4.6.2 targeting (no Visual Studio required)
- **Build Process**: `dotnet restore` → `dotnet build --configuration Release` → Plugin Registration Tool
- **Plugin Pattern**: Inherit from `PluginBase`, implement `ExecuteDataversePlugin()`, use `ILocalPluginContext`
- **Many-to-Many Queries**: ✅ **RESOLVED** - Use correct intersection table names from metadata analysis
- **Performance**: QueryExpression with LinkEntity for complex relationships, efficient field selection
- **Error Handling**: Graceful degradation, trace logging, return empty collections on relationship failures
- **Testing**: Python scripts for API validation, HTTP GET requests with MSAL authentication

#### Key Success Pattern (KeyPersonnel Resolution):
```csharp
// Many-to-many relationship query pattern
var query = new QueryExpression("lmdm_keypersonale");
LinkEntity linkToIntersection = query.AddLink(
    linkToEntityName: "lmdm_location_lmdm_keypersonale",  // Correct intersection table
    linkFromAttributeName: "lmdm_keypersonaleid",
    linkToAttributeName: "lmdm_keypersonaleid",
    joinOperator: JoinOperator.Inner);
linkToIntersection.LinkCriteria.AddCondition("lmdm_locationid", ConditionOperator.Equal, locationId);
```

### Environment Management
- `.env` defines `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`, `ORG_URL_*` (multiple environments)
- `Config.get_available_environments()` extracts env names from `ORG_URL_*` suffix
- AuthPanel dropdown auto-populates with environments

### Metadata Caching
- `SchemaCache` stores fetched metadata in `.cache/` as JSON with timestamp
- TTL: 24 hours (configurable)
- Cache keys: `{org_url}/{endpoint}` (e.g., `https___org.crm.dynamics.com_EntityDefinitions`)
- Manual invalidation: "Refresh Schema" button → `cache.clear_all()`

### Excel/CSV Processing
- **Auto-header detection**: Scores first 5 rows (text content, uniqueness)
- **Manual override**: Header row spinner in UI
- **Merged cells**: Reads first cell value
- **Datatype conversion**: `JSONBuilder` uses `validators` + `formatters`
- **Choice mapping**: Fetches choice metadata, maps labels to values (case-insensitive)
- **Lookup formatting**: Auto-adds `@odata.bind` suffix with entity name

### Template System
- Templates stored in `templates/*.template.json`
- Placeholder syntax: `${variable_name}`
- `TemplateManager.extract_placeholders()` finds all placeholders
- On load, prompts user to fill placeholders
- Template types: CRUD, Batch, Query (future)

### Threading Strategy
All long operations use `QThread` to prevent UI freeze:
- `AuthThread`: Authentication
- `CRUDOperationThread`: CRUD ops
- `BatchOperationThread`: Batch ops
- `QueryThread`: Query ops
- `MetadataFetchThread`: Metadata fetching

Pattern:
```python
thread = OperationThread(...)
thread.success.connect(handler)
thread.error.connect(error_handler)
thread.start()
```

### PyQt6 Signals
- `authenticated(client)`: Auth panel → Main window → Tabs
- `operation_executed(data)`: Tabs → Main window → Results tab + History panel
- `load_to_crud_requested(json)`: Excel Mapper → CRUD tab
- `load_to_batch_requested(ops)`: Excel Mapper → Batch tab
- `cache_refresh_requested()`: Auth panel → Main window → Client

## Setup & Execution
```bash
# Python Application Setup
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
python main.py  # New PyQt6 version

# Custom API Plugin Development Setup (Optional)
# Install .NET SDK 6.0+ (includes .NET Framework 4.6.2 targeting)
# No Visual Studio required - .NET CLI handles all operations
dotnet --version  # Verify installation
cd AlshayaLocationAPI
dotnet restore    # Restore NuGet packages
dotnet build --configuration Release  # Build plugin DLL
```

**First-time setup**: 
1. Create `.env` with Azure app registration credentials
2. For Custom API development: Install Plugin Registration Tool
3. Verify .NET SDK installation for plugin development

## Common Extension Points

### Adding New CRUD Operations
1. Add method to `DataverseClient` (return `{"success": bool, "data"/"error": str}`)
2. Create/extend tab in `ui/tabs/`
3. Wire signal to `MainWindow`

### Adding New Datatypes
1. Add validator to `utils/validators.py` (`validate_<type>()`)
2. Add formatter to `utils/formatters.py` (`format_<type>()`)
3. Update `JSONBuilder._convert_value()` with new case

### Extending Excel Mapper
- Add choice option fetching: `MetadataClient.fetch_choice_options(entity, attribute)`
- Implement in Excel Mapper tab's metadata fetch flow
- Store in `self.choice_mappings` dict for `JSONBuilder`

### Custom Themes
- Modify `MainWindow._apply_theme()` stylesheet
- PyQt6 supports CSS-like styling

### Custom API Plugin Development
1. **Create new plugin project**:
   ```powershell
   dotnet new classlib -n YourEntityAPI -f net462
   dotnet add package Microsoft.CrmSdk.CoreAssemblies
   dotnet add package Microsoft.Xrm.Sdk
   ```
2. **Implement plugin class**: Inherit from `PluginBase`, override `ExecuteDataversePlugin()`
3. **Define field arrays**: Main entity fields, related entity fields for relationships
4. **Build and deploy**: `dotnet build --configuration Release` → Plugin Registration Tool
5. **Create Custom API**: Power Platform admin center, associate with plugin
6. **Test with Python**: Use `test_custom_api.py` pattern for validation

### Many-to-Many Relationship Troubleshooting
- **Metadata Analysis**: Use `entity_metadata_exporter.py` to discover intersection table names
- **QueryExpression Pattern**: Start with target entity, link through intersection table
- **Field Validation**: Ensure correct `Entity1IntersectAttribute` and `Entity2IntersectAttribute`
- **Testing Strategy**: Compare with working Python implementation using same intersection table

## Testing Notes
- No automated tests yet (manual testing only)
- Connection test: "🔗 Connect" button in Auth panel
- Test with sample Excel files in various formats (see `docs/` for examples)
- Verify metadata caching: check `.cache/` directory timestamps
- Test templates: save/load with and without placeholders

## External Dependencies
- **PyQt6**: Modern cross-platform UI framework
- **msal**: OAuth2 token acquisition (Entra ID)
- **requests**: HTTP client for API calls
- **python-dotenv**: Environment variable loading
- **openpyxl**: Excel file reading (.xlsx)
- **pandas**: CSV/Excel processing (alternative)

## File Structure Reference
```
client/
  ├── dataverse_client.py       # Core API client
  ├── metadata_client.py        # Metadata + caching
  └── entity_explorer.py        # Entity relationship discovery
ui/
  ├── main_window.py            # Main orchestrator
  ├── panels/
  │   ├── auth_panel.py         # Auth + connection
  │   └── history_panel.py      # Operation history
  └── tabs/
      ├── crud_tab.py           # CRUD operations
      ├── excel_mapper_tab.py   # Excel/CSV mapping (Tier 1)
      ├── batch_tab.py          # Batch operations
      ├── query_tab.py          # OData queries
      └── results_tab.py        # Result display
utils/
  ├── config.py                 # Environment config
  ├── schema_cache.py           # Metadata cache (24hr TTL)
  ├── validators.py             # Datatype validation
  ├── formatters.py             # Format conversions
  ├── excel_processor.py        # Excel/CSV reader
  ├── json_builder.py           # JSON payload generator
  └── template_manager.py       # Template save/load
AlshayaLocationAPI/              # Custom API Plugin Project
  ├── AlshayaLocationAPI.csproj  # .NET Framework 4.6.2 project
  ├── GetLocationDetailsPlugin.cs # Main plugin implementation
  ├── PluginBase.cs             # Plugin infrastructure
  └── bin/Release/net462/       # Build output (.dll files)
scripts/
  ├── custom-api-location.py    # Python reference implementation
  ├── test_custom_api.py        # API testing and validation
  └── entity_metadata_exporter.py # Metadata analysis tools
docs/
  ├── ARCHITECTURE.md           # Module architecture
  ├── CUSTOM_API_COMPLETE_GUIDE.md # ✅ Custom API development guide
  ├── TIER1_FEATURES.md         # Feature user guide
  ├── setup_guide.md            # Installation guide
  └── QUICK_REFERENCE.md        # Quick commands
main.py                         # PyQt6 entry point
requirements.txt                # Python dependencies
.env                            # Credentials (git-ignored)
.cache/                         # Metadata cache (git-ignored)
templates/                      # User templates (git-ignored)
```

## Data Type Handling (Excel Mapper)
- **String**: Direct passthrough, trim whitespace
- **Integer**: `int()` conversion, reject non-numeric
- **Decimal**: `float()` conversion
- **Boolean**: Accepts true/false, yes/no, 1/0 (case-insensitive)
- **Date**: Parses YYYY-MM-DD, MM/DD/YYYY, etc. → outputs YYYY-MM-DD
- **DateTime**: Multiple formats → ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **Lookup**: GUID → `/entityname(guid)` with `@odata.bind` suffix
- **Choice**: Label (string) → maps to integer value via metadata, or accepts integer directly
- **Empty values**: Skipped (not included in JSON payload)

## Excel Mapper Details
- **Header detection**: Analyzes first 5 rows, scores by text content + uniqueness
- **Preview**: Shows first 3 rows in table widget
- **Field mapping**: Dropdown assignment (Excel column → Dataverse field)
- **Metadata fetch**: Background thread fetches entity attributes with types
- **JSON preview**: Real-time preview of first row as user maps fields
- **Actions**:
  - "Generate JSON": Validates all rows, shows summary
  - "Load to CRUD": Populates CRUD tab with first row
  - "Load to Batch": Generates batch operations for all rows (POST method)

## Template Details
- **Placeholder extraction**: Regex `\$\{([^}]+)\}` finds all placeholders
- **Fill on load**: Prompts user for each placeholder value
- **Storage**: JSON files in `templates/` with `.template.json` extension
- **Metadata**: `_metadata` field includes created timestamp, version
- **Security**: Never store secrets in templates (use placeholders instead)

## Notes
- Old tkinter version (`dataverse_api_gui.py`) kept as reference with deprecation notice
- PyQt6 Fusion theme provides modern, native look across platforms
- All async operations use QThread to prevent UI freezing
- Cache directory (`.cache/`) and templates directory (`templates/`) auto-created on first run
- Choice metadata includes display labels, not just values (user-friendly)
- When implementing code changes, update relevant docs and this instructions file
- Activate venv before running the application
- Any implementation we will be making just add a option to confirm environment before executing operations

## Custom API Development Achievements (2026)
- ✅ **Complete Custom API Implementation**: `mdm_alshaya_GetLocationDetails` with complex relationships
- ✅ **KeyPersonnel Many-to-Many Resolution**: Solved intersection table query issues through metadata analysis
- ✅ **No Visual Studio Dependency**: Full development workflow using .NET CLI only
- ✅ **Performance Optimization**: Sub-second responses with 60+ fields and multiple relationships
- ✅ **Comprehensive Documentation**: Complete guide for replicating Custom API development
- ✅ **Plugin Versioning**: Implemented version tracking (v2.1.0+) for debugging and updates
- ✅ **Error Handling Strategy**: Graceful degradation with detailed trace logging

## Development Patterns Established
- **Metadata-First Approach**: Always analyze entity relationships before coding
- **.NET CLI Workflow**: `dotnet restore` → `dotnet build` → Plugin Registration Tool → Test
- **Python Validation**: Create reference implementations for complex queries before plugin development
- **Intersection Table Discovery**: Use metadata exports to find correct many-to-many table names
- **Field Configuration**: Define field arrays in code for maintainability and documentation