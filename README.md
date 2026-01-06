# 🚀 Dataverse Web API Studio - Professional Edition v2.0

**Modern PyQt6 Desktop Application for Dataverse Web API Operations**

A professional-grade desktop application with **Excel/CSV mapper**, **metadata discovery**, and **template library**. Perform CRUD operations, batch processing (up to 1000 ops/call), OData queries, and bulk imports with visual field mapping—all in a modern, user-friendly interface.

![Architecture](https://github.com/roshan-lal-dia/dataverse-api-studio/blob/6167e32a913b8697ea939aff4db110abf83bd47d/docs/dataverse_api_flowchart.png)

---

## ✨ What's New in v2.0

### 🆕 Tier 1 Features

#### 📊 **Excel/CSV Mapper** (Core Feature)
- **Visual field mapping** - Map Excel columns to Dataverse fields with dropdowns
- **Auto-detect headers** - Scans first 5 rows automatically
- **Datatype conversion** - Automatic conversion (String, Integer, Date, Lookup, Choice, etc.)
- **Choice label mapping** - Use friendly names like "Active" instead of 1
- **Preview data** - See first 3 rows before import
- **Bulk generation** - Create 1000s of records at once
- **Load to CRUD/Batch** - Seamless integration with other tabs

#### 🔍 **Metadata Discovery**
- **Automatic schema fetching** - Get all entities and fields
- **24-hour caching** - Lightning-fast repeated access
- **Choice option labels** - Display names for picklist values
- **Manual refresh** - "Refresh Schema" button in auth panel
- **Field type hints** - See datatypes for each field

#### 📁 **Template Library**
- **Save configurations** - Reuse common operations
- **Placeholder support** - `${variable_name}` syntax
- **CRUD & Batch templates** - For all operation types
- **Quick load** - Select from dropdown and fill placeholders

### 🎨 Modern PyQt6 UI
- **Fusion theme** - Professional, native-looking interface
- **Responsive panels** - Resizable splitters
- **Background threading** - Non-blocking operations
- **Status indicators** - Real-time connection and cache status
- **Tabbed interface** - Clean organization

---

## ✨ Core Features

### 🎯 Complete CRUD Operations
- **Create** new records with validation
- **Read** single records or query multiple with filters
- **Update** existing records with lookups
- **Delete** records safely with confirmation
- **Template support** - Save and reuse configurations

### ⚡ Batch Operations (Game Changer!)
- Execute **up to 1,000 operations in ONE API call**
- Create bulk records **100x faster** than individual calls
- Support for POST (Create), PATCH (Update), DELETE
- Load from JSON files or Excel Mapper
- Real-time batch status tracking

### 🔍 Advanced Querying
- **OData query builder** with visual interface
- Complex filters: `revenue gt 1000000 and status eq 0`
- Select specific columns to reduce payload
- Order results by any field
- Set record limits (1-5000)
- Export results as JSON or CSV

### 📊 All Datatype Support
- **Primitives**: String, Integer, Decimal, Boolean
- **Date/Time**: Date, DateTime (multiple format support)
- **Complex**: Lookup (with @odata.bind), Choice, Memo
- **Auto-conversion** in Excel Mapper
- Smart validation for each datatype
- Helpful examples and tooltips

### 💾 Export & Import
- **Export** results as JSON or CSV
- **Import** from Excel/CSV with visual mapper
- **Save** operation templates
- **Copy** results to clipboard
- **Operation history** tracking (last 20 operations)

### 🔒 Security & Best Practices
- Environment variables (.env) for secrets
- MSAL authentication with Entra ID
- No hardcoded credentials
- Secure token handling
- Thread-safe operations (PyQt6 QThread)

---

## 🚀 Quick Start

### 1. Installation (2 minutes)

```bash
# Clone or download this project
cd dataverse-api-studio

# Create virtual environment
python -m venv .venv

# Activate venv (choose your OS)
source .venv/bin/activate          # Linux/macOS
# OR
.\.venv\Scripts\Activate.ps1       # Windows PowerShell
# OR
.\.venv\Scripts\activate.bat       # Windows CMD

# Install dependencies (includes PyQt6, openpyxl, pandas)
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Setup Credentials (5 minutes)

**Create `.env` file:**
```
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-app-registration-client-secret

# Add your environments (DEV, PROD, SANDBOX, UAT, etc.)
ORG_URL_DEV=https://your-org-dev.crm.dynamics.com
ORG_URL_PROD=https://your-org.crm.dynamics.com
# ORG_URL_SANDBOX=https://your-org-sandbox.crm.dynamics.com
```

[Detailed credential setup guide](docs/setup_guide.md)

### 3. Run the Application

```bash
python main.py
```

**That's it!** 🎉 The modern PyQt6 application launches.

> **Note:** The old tkinter version (`dataverse_api_gui.py`) is deprecated but kept for reference.

---

## 📖 Usage Examples

### Example 1: Bulk Import from Excel (New in v2.0!) ⭐

**Scenario:** Import 500 accounts from Excel spreadsheet

1. Prepare Excel file:
   ```
   | Company Name  | Website              | Phone      | Industry   |
   |---------------|----------------------|------------|------------|
   | Contoso Corp  | https://contoso.com  | 555-0100   | Technology |
   | Fabrikam Inc  | https://fabrikam.com | 555-0200   | Technology |
   ... (498 more rows)
   ```

2. Open **📊 Excel Mapper** tab
3. Click **📂 Select File** → Choose `accounts.xlsx`
4. Select entity: `account`
5. Click **🔍 Fetch Fields** (loads metadata)
6. Map columns:
   - Company Name → `name` (String)
   - Website → `websiteurl` (String)
   - Phone → `telephone1` (String)
   - Industry → `industrycode` (Choice) - Maps "Technology" to value 1
7. Click **🔨 Generate JSON** → Validates all 500 rows
8. Click **⚡ Load to Batch**
9. Review batch operations in Batch tab
10. Click **⚡ Execute Batch**

**Result:** 500 accounts created in ~5 seconds! ⚡⚡⚡

### Example 2: Create an Account (CRUD Operation)

1. Select **📝 CRUD Operations** tab
2. Choose **CREATE** operation
3. Table Name: `account`
4. Data JSON:
```json
{
  "name": "Contoso Corp",
  "websiteurl": "https://contoso.com",
  "telephone1": "555-0100"
}
```
5. Click **✅ Execute Operation**
6. View result in **📋 Results** tab

**You just created your first record!** ✅

### Example 3: Query with Metadata (New in v2.0!)

1. Connect to environment (metadata cached automatically)
2. Select **🔍 Query** tab
3. Start typing table name: `acc...` (autocomplete from metadata - future)
4. Table Name: `account`
5. Filter: `revenue gt 1000000 and statecode eq 0`
6. Select: `name,revenue,websiteurl`
7. Order By: `revenue desc`
8. Top: 100
9. Click **🔍 Execute Query**

**Results:** Top 100 richest accounts displayed in table view!

### Example 4: Save & Reuse Template (New in v2.0!)

1. Configure a CRUD operation (e.g., CREATE account)
2. Use placeholders in JSON:
```json
{
  "name": "${company_name}",
  "websiteurl": "${website}",
  "industry": "Technology"
}
```
3. Click **Save Template** → Name: `new_tech_account`
4. Later: Select template from dropdown
5. Click **Load Template**
6. Fill placeholders when prompted:
   - `company_name`: Fabrikam
   - `website`: https://fabrikam.com
7. Click **✅ Execute Operation**

**Reused in seconds!** 🚀

---

## 📚 Documentation

- **[TIER1_FEATURES.md](docs/TIER1_FEATURES.md)** - Complete guide to Excel Mapper, Metadata Discovery, Templates
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Module architecture, data flows, extension points
- **[setup_guide.md](docs/setup_guide.md)** - Detailed installation, Azure AD setup, troubleshooting
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Keyboard shortcuts, common filters, error fixes

---

## 🛠️ Tech Stack

### New in v2.0
- **PyQt6** - Modern cross-platform UI framework
- **openpyxl** - Excel file reading (.xlsx)
- **pandas** - CSV/DataFrame processing

### Core Technologies
- **Python 3.8+** - Cross-platform compatibility
- **msal** - Microsoft Authentication Library (OAuth2)
- **requests** - HTTP client for Dataverse API
- **python-dotenv** - Environment variable management

---

## 🆕 What's Different in v2.0?

| Feature | v1.0 (Tkinter) | v2.0 (PyQt6) |
|---------|----------------|--------------|
| **UI Framework** | tkinter (basic) | PyQt6 (modern) |
| **Architecture** | Monolithic (1 file) | Modular (multiple modules) |
| **Excel Mapper** | ❌ | ✅ Visual field mapping |
| **Metadata Discovery** | ❌ | ✅ With 24hr caching |
| **Template Library** | ❌ | ✅ With placeholders |
| **Threading** | Basic Python threads | PyQt6 QThread (robust) |
| **Theme** | Basic tkinter | Fusion (professional) |
| **Responsive UI** | Fixed panels | Resizable splitters |
| **Status Bar** | ❌ | ✅ Real-time status |
| **Operation History** | Simple list | Rich display with icons |

**Migration:** Old tkinter version kept as `dataverse_api_gui.py` (deprecated)

---

## 📦 Directory Structure

```
dataverse-api-studio/
├── main.py                      # PyQt6 entry point (NEW)
├── dataverse_api_gui.py         # Old tkinter version (deprecated)
├── requirements.txt             # Updated with PyQt6, openpyxl, pandas
├── .env                         # Credentials (create this)
├── .env.example                 # Template
├── .gitignore                   # Updated for .cache/, templates/
├── client/                      # API client modules (NEW)
│   ├── dataverse_client.py      # Core CRUD/Batch operations
│   └── metadata_client.py       # Metadata fetching + caching
├── ui/                          # PyQt6 UI components (NEW)
│   ├── main_window.py           # Main orchestrator
│   ├── panels/
│   │   ├── auth_panel.py        # Authentication panel
│   │   └── history_panel.py     # Operation history
│   └── tabs/
│       ├── crud_tab.py          # CRUD operations
│       ├── excel_mapper_tab.py  # Excel/CSV mapper ⭐
│       ├── batch_tab.py         # Batch operations
│       ├── query_tab.py         # OData queries
│       └── results_tab.py       # Result display
├── utils/                       # Utility modules (NEW)
│   ├── config.py                # Environment config
│   ├── schema_cache.py          # Metadata cache (24hr TTL)
│   ├── validators.py            # Datatype validation
│   ├── formatters.py            # Format conversions
│   ├── excel_processor.py       # Excel/CSV reader
│   ├── json_builder.py          # JSON payload generator
│   └── template_manager.py      # Template save/load
├── docs/
│   ├── ARCHITECTURE.md          # Architecture documentation (NEW)
│   ├── TIER1_FEATURES.md       # Feature guide (NEW)
│   ├── setup_guide.md           # Installation guide
│   ├── QUICK_REFERENCE.md       # Quick reference
│   └── dataverse_api_flowchart.png
├── .cache/                      # Metadata cache (auto-created, git-ignored)
└── templates/                   # User templates (auto-created, git-ignored)
```

---

## 🎓 Learning Path

| Level | Task | Time | New in v2.0? |
|-------|------|------|--------------|
| 🟢 Beginner | Setup credentials & test connection | 5 min | |
| 🟢 Beginner | Create your first record (CRUD) | 2 min | |
| 🟢 Beginner | **Import 10 rows from Excel** | 5 min | ✅ |
| 🟡 Intermediate | Query with filters | 5 min | |
| 🟡 Intermediate | Batch create 10 records | 5 min | |
| 🟡 Intermediate | **Save and reuse template** | 3 min | ✅ |
| 🔴 Advanced | **Bulk import 1,000 rows with Excel Mapper** | 10 min | ✅ |
| 🔴 Advanced | Complex queries with metadata | 10 min | ✅ |

---

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Keyboard shortcuts, common filters, error fixes
- **[setup_guide.md](setup_guide.md)** - Detailed setup instructions, Azure AD setup
- **[.env.example](.env.example)** - Environment variable template

---

## 🛠️ Supported Operations

| Operation | Method | Use Case |
|-----------|--------|----------|
| **Create** | POST | Insert new records |
| **Read** | GET | Retrieve single or multiple records |
| **Update** | PATCH | Modify existing records |
| **Delete** | DELETE | Remove records |
| **Batch** | POST to $batch | 100-1000 operations in one call |
| **Query** | GET with $filter | Complex filtering with OData |

---

## 🔐 Security

✅ **What's Protected:**
- Environment variables (.env) not in version control
- MSAL authentication with Entra ID
- No hardcoded credentials
- Secure token handling
- Thread-safe operations

✅ **Best Practices Included:**
- Rotate secrets every 3-6 months
- Use separate app registrations per environment
- Grant minimal required permissions
- Audit API calls in Dataverse logs
- Never commit .env file

---

## 💾 Data Export

### Export Options
- **JSON**: Full structured format with metadata
- **CSV**: Spreadsheet-ready format
- **Templates**: Save query configurations
- **Clipboard**: Quick copy for other tools

### Example Export Flow
1. Run query or operation
2. Results appear in **Results** tab
3. Click **💾 Export JSON** or **💾 Export CSV**
4. Choose location and filename
5. File saved! ✅

---

## ⚡ Performance

### Why Batch Operations Matter

**Scenario: Create 1,000 contacts**

| Method | API Calls | Time | Status |
|--------|-----------|------|--------|
| Individual | 1,000 | ~500 sec | ❌ Slow |
| Batch (500 per) | 2 | ~5 sec | ✅ **100x faster!** |
| CSV Batch | 2 | ~5 sec | ✅ **100x faster!** |

### Optimization Tips
1. Use batch operations for bulk inserts
2. Select only needed columns
3. Use filters to reduce transfers
4. Set appropriate $top value
5. Leverage operation history

---

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Not Connected" | Click 🔗 Connect after filling credentials |
| "Table not found" | Use logical name (account, not Account) |
| "Invalid GUID" | Verify format: 00000000-0000-0000-0000-000000000000 |
| "Auth failed" | Check TENANT_ID, CLIENT_ID, CLIENT_SECRET in .env |
| "JSON error" | Use [JSON validator](https://jsonlint.com/) |
| "Permission denied" | Grant API permissions in Azure AD |

[Full troubleshooting guide →](setup_guide.md#-troubleshooting)

---

## 📋 Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, Linux
- **Dataverse**: Power Apps environment with Web API enabled
- **Azure AD**: App registration with API permissions

### Dependencies
```
requests==2.32.3        # HTTP client
msal==1.30.0           # Microsoft Authentication
python-dotenv==1.0.1   # Environment variables
```

---

## 🎯 Datatype Reference

### Supported Datatypes

| Type | Example | Format |
|------|---------|--------|
| String | "Contoso" | Text |
| Integer | 12345 | Whole number |
| Decimal | 123.45 | Number |
| Boolean | true | true/false |
| Date | "2024-01-15" | YYYY-MM-DD |
| DateTime | "2024-01-15 14:30:00" | YYYY-MM-DD HH:MM:SS |
| Lookup | `/accounts(guid)` | @odata.bind format |
| Choice | 1 | Integer value |
| Memo | "Long text..." | Multi-line text |
| File | base64 | File content |

### Lookup Field Format

```json
{
  "ownerid@odata.bind": "/systemusers(guid)",
  "parentcustomerid@odata.bind": "/accounts(guid)"
}
```

---

## 🚀 Advanced Features

### Saved Templates
- Save frequently-used CRUD operations
- Reuse query configurations
- Build library of common operations
- Share templates with team

### Operation History
- 20 most recent operations tracked
- Quick reference sidebar
- Learn from successful queries
- Audit trail for debugging

### CSV Import
- Bulk load operations from files
- Standard CSV format
- Automatic format validation
- Progress tracking

---

## 📊 Use Cases

- **Data Migration**: Bulk transfer data between environments
- **Testing**: Quickly create test records
- **Reporting**: Query and export data for analysis
- **Maintenance**: Update multiple records in seconds
- **Integration**: Automate data synchronization
- **Troubleshooting**: Test API connectivity and permissions

---

## 🤝 Contributing

Want to improve this tool? Ideas welcome!
- Report bugs
- Suggest features
- Share use cases
- Contribute code

---

## 📄 License

MIT License - Free to use and modify for any purpose

---

## 🎓 Learning Resources

- **[Dataverse Web API Docs](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/)**
- **[OData Query Reference](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/query-data-web-api)**
- **[Batch Operations Guide](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api)**
- **[Lookup Relationships](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/create-update-entity-relationships-using-web-api)**

---

## ✅ What's Included

```
dataverse-api-studio/
├── dataverse_api_gui.py          # Main application (2000+ lines)
├── requirements.txt               # Python dependencies
├── .env.example                   # Credentials template
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
├── QUICK_REFERENCE.md            # Quick commands & tips
└── setup_guide.md                # Detailed setup instructions
```

---

## 🎉 Getting Started

### First Time? Do This:

1. **Install** (2 min):
   ```bash
   git clone <repo>
   cd dataverse-api-studio
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure** (5 min):
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run** (1 sec):
   ```bash
   python dataverse_api_gui.py
   ```

4. **Connect** (1 click):
   - Fill credentials
   - Click 🔗 Connect
   - See ✅ Connected

5. **Create Record** (10 sec):
   - Go to CRUD tab
   - Add JSON data
   - Click ✅ Execute
   - See result!

**You're ready to manage Dataverse like a pro!** 🚀

---

## 📞 Support

- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) first
- See [setup_guide.md](setup_guide.md) for detailed help
- Review troubleshooting section above
- Check Microsoft documentation links

---

## 🌟 Star This Project!

If this tool helps you, please give it a star ⭐

---

**Made with ❤️ for Dataverse developers**

*Last Updated: January 2025*
*Version: 1.0.0*
