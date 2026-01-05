# 🚀 Dataverse Web API Studio - Ultimate Edition

**The #1 Desktop GUI Application for Dataverse Web API Operations**

A modern, user-friendly Python GUI application that enables you to perform ALL Dataverse Web API operations (CRUD, Batch, Query) regardless of datatype in a single unified interface.

![Architecture](https://github.com/roshan-lal-dia/dataverse-api-studio/blob/6167e32a913b8697ea939aff4db110abf83bd47d/docs/dataverse_api_flowchart.png)

---

## ✨ Features

### 🎯 Complete CRUD Operations
- **Create** new records with validation
- **Read** single records or query multiple with filters
- **Update** existing records with lookups
- **Delete** records safely with confirmation

### ⚡ Batch Operations (Game Changer!)
- Execute **up to 1,000 operations in ONE API call**
- Create bulk records **100x faster** than individual calls
- Support for POST (Create), PATCH (Update), DELETE
- Load from JSON or CSV files
- Real-time batch status tracking

### 🔍 Advanced Querying
- **OData query builder** with visual interface
- Complex filters: `revenue gt 1000000 and status eq 0`
- Select specific columns to reduce payload
- Order results by any field
- Set record limits (1-5000)

### 📊 All Datatype Support
- **Primitives**: String, Integer, Decimal, Boolean
- **Date/Time**: Date, DateTime
- **Complex**: Lookup (with @odata.bind), Choice, Memo, File
- Smart validation for each datatype
- Helpful examples and tooltips

### 💾 Export & Import
- **Export** results as JSON or CSV
- **Save** query templates for reuse
- **Load** CSV files for bulk import
- **Copy** results to clipboard
- **Operation history** tracking

### 🔒 Security & Best Practices
- Environment variables (.env) for secrets
- MSAL authentication with Entra ID
- No hardcoded credentials
- Secure token handling
- Thread-safe operations

### 💡 User Guidance & Intelligence
- Smart defaults based on operation type
- Input validation with helpful error messages
- Operation history sidebar
- Tooltip hints for every field
- Example JSON snippets
- Copy-paste ready code blocks

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
.\.venv\Scripts\activate.bat         # Windows CMD
# Install dependencies
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

[Detailed credential setup guide](QUICK_REFERENCE.md#how-to-get-credentials)

### 3. Run the Application

```bash
python dataverse_api_gui.py
```

That's it! 🎉 Your Dataverse GUI app is running.

---

## 📖 Usage Examples

### Example 1: Create an Account (2 seconds)

1. Select **CRUD Operations** tab
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
5. Click **✅ Execute**
6. View result in **Results** tab

**You just created your first record!** ✅

### Example 2: Batch Create 500 Accounts (3 seconds)

Instead of 500 API calls, do it in ONE:

1. Select **⚡ Batch Operations** tab
2. Paste JSON:
```json
[
  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Company 1"}},
  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Company 2"}},
  ... (repeat 498 more)
]
```
3. Click **⚡ Execute Batch**
4. Done! All 500 records created in seconds

**Performance Comparison:**
- Individual API calls: ~500 seconds (8+ minutes) ⏱️
- Batch operation: ~5 seconds ⚡⚡⚡

### Example 3: Query Rich Accounts (1 second)

1. Select **🔍 Query** tab
2. Table Name: `account`
3. Filter: `revenue gt 1000000 and statecode eq 0`
4. Select: `name,revenue,websiteurl`
5. Order By: `revenue desc`
6. Top: 100
7. Click **🔍 Execute Query**

**Results:** Get your top 100 richest accounts, ordered by revenue!

### Example 4: Update Owner (1 second)

1. Select **CRUD Operations** tab
2. Choose **UPDATE** operation
3. Table Name: `contact`
4. Record ID: `00000000-0000-0000-0000-000000000001`
5. Data JSON:
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "ownerid@odata.bind": "/systemusers(00000000-0000-0000-0000-000000000099)"
}
```
6. Click **✅ Execute**

**The contact is now assigned to the new owner!** ✅

---

## 🎓 Learning Path

| Level | Task | Time |
|-------|------|------|
| 🟢 Beginner | Setup credentials & test connection | 5 min |
| 🟢 Beginner | Create your first record | 2 min |
| 🟡 Intermediate | Query with filters | 5 min |
| 🟡 Intermediate | Batch create 10 records | 5 min |
| 🔴 Advanced | Batch create 1,000 records from CSV | 10 min |
| 🔴 Advanced | Complex queries with multiple filters | 10 min |

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
