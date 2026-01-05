# Dataverse API GUI Application - Setup & Usage Guide

## 📋 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate venv
# Windows (CMD):
.\.venv\Scripts\activate.bat
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
# Install required packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-app-registration-client-secret

# Add your environments - the app will detect them automatically
# Environment names are extracted from the suffix (e.g., ORG_URL_DEV → DEV)
ORG_URL_DEV=https://your-org-dev.crm.dynamics.com
ORG_URL_PROD=https://your-org.crm.dynamics.com

# Optional: Add more environments as needed
# ORG_URL_SANDBOX=https://your-org-sandbox.crm.dynamics.com
# ORG_URL_UAT=https://your-org-uat.crm.dynamics.com
# ORG_URL_TEST=https://your-org-test.crm.dynamics.com
```

**Note:** The application will automatically detect all `ORG_URL_*` variables and create a dropdown selector for easy environment switching.

### 3. Run the Application

```bash
python dataverse_api_gui.py
```

---

## 🔑 Getting Credentials

### Step 1: Register Application in Entra ID

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory → App registrations → New registration**
3. Enter name: "Dataverse API Studio"
4. Select "Accounts in any organizational directory"
5. Click **Register**

### Step 2: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Set expiration (12 months recommended)
4. Copy the **Value** (not ID) → Paste as `CLIENT_SECRET` in `.env`

### Step 3: Grant API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Select **APIs my organization uses** → Search for "Dynamics CRM"
4. Select **Dynamics CRM**
5. Choose **Delegated permissions** or **Application permissions**
6. Select `user_impersonation` or `Organization` scope
7. Click **Add permissions**
8. Click **Grant admin consent**

### Step 4: Find Your Org URL

1. Log in to Power Apps: https://make.powerapps.com
2. Your org URL appears in the address bar: `https://your-org.crm.dynamics.com`

---

## 🚀 Feature Overview

### 📝 CRUD Operations
- **CREATE**: Insert new records
- **READ**: Retrieve single or multiple records
- **UPDATE**: Modify existing records
- **DELETE**: Remove records

### ⚡ Batch Operations
- Execute up to 1000 operations in one API call
- Supports POST (Create), PATCH (Update), DELETE
- Load from JSON or CSV files
- Dramatically improves performance for bulk operations

### 🔍 Query/Filter
- Build OData queries with visual builder
- Filter with complex conditions
- Select specific columns
- Order results by any field
- Set result limits (1-5000 records)

### 📊 Data Export
- Export results as JSON
- Export results as CSV
- Save query templates
- Copy to clipboard
- Operation history tracking

---

## 💡 Usage Examples

### Example 1: Create an Account Record

**Table Name:** account
**Operation:** CREATE
**Data JSON:**
```json
{
  "name": "Contoso Corp",
  "websiteurl": "https://contoso.com",
  "telephone1": "555-0100"
}
```

### Example 2: Update a Record with Lookup

**Table Name:** contact
**Operation:** UPDATE
**Record ID:** 123e4567-e89b-12d3-a456-426614174000
**Data JSON:**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "parentcustomerid@odata.bind": "/accounts(987e6543-e89b-12d3-a456-426614174999)"
}
```

### Example 3: Batch Create Multiple Accounts

**Batch Operations:**
```json
[
  {
    "method": "POST",
    "url": "/api/data/v9.2/accounts",
    "data": {"name": "Account 1"}
  },
  {
    "method": "POST",
    "url": "/api/data/v9.2/accounts",
    "data": {"name": "Account 2"}
  },
  {
    "method": "POST",
    "url": "/api/data/v9.2/accounts",
    "data": {"name": "Account 3"}
  }
]
```

### Example 4: Query with Filter

**Table Name:** account
**Filter:** `revenue gt 1000000 and statecode eq 0`
**Select:** `name,revenue,websiteurl`
**Order By:** `revenue desc`
**Top:** 50

---

## 🎯 Supported Datatypes

| Datatype | Example Input | Format |
|----------|---------------|--------|
| String | "Contoso" | Text |
| Integer | 12345 | Whole number |
| Decimal | 123.45 | Number with decimals |
| Boolean | true | true or false |
| Date | "2024-01-15" | YYYY-MM-DD |
| DateTime | "2024-01-15 14:30:00" | YYYY-MM-DD HH:MM:SS |
| Lookup | "/accounts(guid)" | @odata.bind format |
| Choice | 1 | Integer value of choice |
| Memo | "Long text..." | Multi-line text |
| File | Base64 encoded | File content |

---

## 🔗 Lookup Field Format

For lookup fields (owner, parent account, etc.):

```json
{
  "ownerid@odata.bind": "/systemusers(00000000-0000-0000-0000-000000000001)",
  "parentcustomerid@odata.bind": "/accounts(00000000-0000-0000-0000-000000000002)",
  "createdbycontact@odata.bind": "/contacts(00000000-0000-0000-0000-000000000003)"
}
```

---

## 🛠️ Troubleshooting

### Issue: Authentication fails
- **Solution**: Verify TENANT_ID, CLIENT_ID, CLIENT_SECRET in .env
- Check if app registration has correct API permissions
- Ensure admin consent was granted

### Issue: "Table not found"
- **Solution**: Verify table logical name (account, not Account)
- Use lowercase and singular form
- Check table exists in your Dataverse environment

### Issue: "Invalid GUID"
- **Solution**: Record IDs must be valid UUIDs
- Format: 00000000-0000-0000-0000-000000000000
- Copy from Dataverse records directly

### Issue: Lookup field shows "unresolved"
- **Solution**: Use `@odata.bind` format with `/table(guid)`
- Ensure referenced record exists
- Verify table name is plural in the path

### Issue: Batch operation partially fails
- **Solution**: Check individual records in batch
- Validate JSON syntax
- Ensure all referenced GUIDs exist
- Check field permissions for the user

---

## 📚 Learning Resources

- [Dataverse Web API Documentation](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/)
- [OData Query Reference](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/query-data-web-api)
- [Batch Operations Guide](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api)
- [Lookup Relationships](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/create-update-entity-relationships-using-web-api)

---

## ⚡ Performance Tips

1. **Use Batch Operations** for bulk inserts/updates (100-1000x faster)
2. **Select only needed columns** to reduce payload size
3. **Use filters** to minimize record transfers
4. **Set appropriate $top** value (don't retrieve all records)
5. **Cache credentials** to avoid repeated authentication

---

## 🔒 Security Best Practices

1. **Never commit .env file** to version control
2. **Use strong client secrets** (64+ characters)
3. **Rotate secrets regularly** (every 3-6 months)
4. **Limit permissions** to minimum required
5. **Use separate app registrations** for different environments
6. **Audit API calls** in Dataverse logs

---

## 📝 CSV Format for Batch Import

```csv
method,url,data
POST,/api/data/v9.2/accounts,"{""name"":""Account 1""}"
POST,/api/data/v9.2/accounts,"{""name"":""Account 2""}"
PATCH,/api/data/v9.2/accounts(guid),"{""name"":""Updated""}"
```

---

## 🆘 Support & Contribution

For issues, feature requests, or contributions:
1. Check existing documentation
2. Verify environment setup
3. Test with simpler queries first
4. Export logs for debugging

---

## 📄 License

MIT License - Feel free to use and modify!

---

## 🎓 Next Steps

1. ✅ Setup virtual environment
2. ✅ Configure .env file
3. ✅ Test authentication
4. ✅ Create your first record
5. ✅ Explore batch operations
6. ✅ Build queries and filters
7. ✅ Export and analyze results

Happy Dataverse API Development! 🚀
