# Dataverse API Studio - AI Coding Agent Instructions

## Project Overview
Single-file Python GUI application (tkinter) providing a desktop interface for Dataverse Web API operations. Acts as an all-in-one tool for CRUD operations, batch processing (up to 1000 ops/call), OData queries, and data export—supporting all Dataverse datatypes without manual type conversion.

## Architecture

### Two-Class Design
1. **DataverseClient** (lines 25-192): Pure API client handling authentication (MSAL/OAuth2), HTTP requests (requests library), and batch multipart operations. No UI dependencies.
2. **DataverseAPIGUI** (lines 198-969): Tkinter-based UI with tabbed interface for CRUD, Batch, Query, and Results operations. Manages form inputs, threading for async operations, and output display.

### Key Data Flows
- **Auth**: `.env` → `_load_env_defaults()` → MSAL token → `DataverseClient.authenticate()` → Bearer headers
- **CRUD**: User input → JSON validation → `create_record()`/`read_record()`/`update_record()`/`delete_record()` → response parsing
- **Batch**: CSV/JSON file → `_build_batch_body()` (multipart/mixed boundary format) → batch API endpoint
- **Query**: OData filter/select parameters → `read_multiple()` → table display

## Critical Patterns

### Environment Management
- `.env` file defines `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`, and multiple `ORG_URL_*` variables (auto-detected)
- App extracts environment names from suffix: `ORG_URL_DEV` → "DEV" dropdown option
- Environment change triggers auto-population of org URL in read-only field (see `_on_environment_change()`)

### Batch Operations
- Multipart body format (lines 169-192): boundary delimiter, Content-Type headers, method+path+JSON per operation
- Max 1000 operations per batch (API constraint)
- Line 176: `method = op.get("method", "POST")` assumes POST by default—verify client code passes explicit method for PATCH/DELETE

### Data Type Handling
- `DATA_TYPES` dict (lines 202-212) maps datatype names to UI hints; no conversion logic—user responsible for format
- Lookups: expects GUID with `@odata.bind` binding (documented in example helper text)
- No file upload implementation despite "File" type listed (aspirational only)

### Threading
- Long operations (auth, API calls) run in background threads to prevent UI freeze
- Pattern: `threading.Thread(target=..., daemon=True).start()`

## Setup & Execution
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/macOS
pip install -r requirements.txt
python dataverse_api_gui.py
```

**First-time setup**: User must provide Azure app registration (CLIENT_ID, CLIENT_SECRET) and org URL in `.env`—no defaults provided.

## Common Extension Points

### Adding New CRUD Operations
- `DataverseClient`: Add method following pattern of `create_record(table_name, data)` → returns `{"success": bool, "data"/"error": str}`
- GUI: Add tab in `_create_gui()`, call `client.method_name()` with form inputs

### Modifying Batch Processing
- Edit `_build_batch_body()` to adjust multipart format or `batch_operation()` endpoint version (currently v9.2)

### Query Builder Enhancements
- OData filter/select building happens in `_create_query_tab()` (input fields only)—no dynamic builder logic yet

## Testing Notes
- No unit tests in repo; test manually via GUI
- Connection test available via "Test Connection" button in auth panel
- Check operation history in left sidebar for debugging

## External Dependencies
- **msal**: OAuth2 token acquisition for Entra ID
- **requests**: HTTP client for API calls
- **python-dotenv**: Environment variable loading
- **tkinter**: Built-in Python GUI framework

## File Structure Reference
- `dataverse_api_gui.py`: Main application (969 lines, monolithic)
- `requirements.txt`: Dependencies (3 packages)
- `.env`: Secrets file (user-created, git-ignored)
- `docs/`: Setup guides and examples
- `README.md`: Features and quick start


## Notes:
- Whenver implementing code changes update relevant readme and other guides as well, including the agent instructions file.