# 🚀 Dataverse API Studio - Quick Reference Card

## Installation (One-Time)

```bash
# 1. Clone/download project
cd dataverse-api-studio

# 2. Create venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .\.venv\Scripts\Activate.ps1  # Windows

# 3. Install packages
pip install -r requirements.txt

# 4. Setup credentials
cp .env.example .env
# Edit .env with your credentials

# 5. Run app
python dataverse_api_gui.py
```

---

## How to Get Credentials

### 🔵 Azure Portal Setup (5 minutes)

1. **Azure Portal** → Azure AD → App registrations → **New registration**
   - Name: "Dataverse API Studio"
   - Save **Application (client) ID** → `CLIENT_ID` in `.env`

2. **Certificates & secrets** → **New client secret**
   - Description: "API Access"
   - Set expiration to 12 months
   - Copy **Value** (not ID) → `CLIENT_SECRET` in `.env`

3. **API permissions** → **Add permission**
   - APIs my organization uses → "Dynamics CRM"
   - Select **user_impersonation**
   - Grant admin consent ✅

4. **Your Org URL** (from Power Apps)
   - https://make.powerapps.com → Find in address bar
   - Format: `https://your-org.crm.dynamics.com`
   - Add to `.env` as `ORG_URL_DEV`, `ORG_URL_PROD`, etc.
   - You can add multiple environments (e.g., `ORG_URL_SANDBOX`, `ORG_URL_UAT`)
   - The app will automatically detect all `ORG_URL_*` variables

5. **Tenant ID** (from Azure Portal)
   - Azure AD → Properties → Directory ID
   - Format: `00000000-0000-0000-0000-000000000000` → `TENANT_ID` in `.env`

---

## Using the GUI

### 🔑 Before Any Operation
1. **Select environment** from the dropdown (DEV, PROD, etc.)
2. **Fill credentials** on left panel (auto-loaded from .env)
3. **Click "🔗 Connect to Dataverse"**
4. **Wait for "✅ Connected" message**

### 📝 Create a Record

**Tab: CRUD Operations**

| Field | Value |
|-------|-------|
| Operation | CREATE |
| Table Name | account |
| Record ID | (leave blank) |
| Data JSON | `{"name": "My Company", "revenue": 1000000}` |

Click **✅ Execute** → Results appear in **Results** tab

### 📖 Read a Record

| Field | Value |
|-------|-------|
| Operation | READ |
| Table Name | account |
| Record ID | 00000000-0000-0000-0000-000000000001 |
| Data JSON | (ignored) |

### ✏️ Update a Record

| Field | Value |
|-------|-------|
| Operation | UPDATE |
| Table Name | account |
| Record ID | 00000000-0000-0000-0000-000000000001 |
| Data JSON | `{"name": "Updated Company"}` |

### 🗑️ Delete a Record

| Field | Value |
|-------|-------|
| Operation | DELETE |
| Table Name | account |
| Record ID | 00000000-0000-0000-0000-000000000001 |
| Data JSON | (ignored) |

### ⚡ Batch Create 100+ Records

**Tab: Batch Operations**

```json
[
  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Org 1"}},
  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Org 2"}},
  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Org 3"}}
]
```

**Why batch?** 100 records in **1 API call** instead of 100 calls!

### 🔍 Query Records with Filters

**Tab: Query**

| Field | Value |
|-------|-------|
| Table Name | account |
| Filter | `revenue gt 1000000 and statecode eq 0` |
| Select | `name,revenue,websiteurl` |
| Order By | `revenue desc` |
| Top | 50 |

Click **🔍 Execute Query** → See 50 richest accounts

---

## Common Filters (OData)

```
name eq 'Contoso'                    # Exact match
name contains 'Contoso'              # Partial match
revenue gt 1000000                   # Greater than
revenue lt 500000                    # Less than
revenue ge 1000000                   # Greater or equal
statecode eq 0                       # Status active
createdon ge 2024-01-01              # Date range
```

**Combine with `and`/`or`:**
```
revenue gt 1000000 and statecode eq 0 and name contains 'Tech'
```

---

## Field Types & JSON Format

### Standard Fields
```json
{
  "name": "Company Name",           // String
  "revenue": 1000000,               // Integer/Decimal
  "statecode": 0,                   // Choice (use number)
  "createdon": "2024-01-15",        // Date
  "description": "Long text..."     // Memo
}
```

### Lookup Fields (Owner, Parent Account, etc.)
```json
{
  "ownerid@odata.bind": "/systemusers(00000000-0000-0000-0000-000000000001)",
  "parentcustomerid@odata.bind": "/accounts(00000000-0000-0000-0000-000000000002)"
}
```

**Where to get GUIDs:**
1. Open record in Dataverse
2. Copy ID from URL or properties
3. Paste in `@odata.bind` path

---

## Export & Save Results

### Save as File
- **Results Tab** → 💾 Export JSON/CSV
- Saves results to your computer
- Auto-opens file browser

### Copy to Clipboard
- **Results Tab** → 📋 Copy
- Results ready to paste anywhere

### Save Query Template
- **CRUD Tab** → 💾 Save as Template
- Reuse later for similar operations

---

## Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Not Connected" | Not authenticated | Click 🔗 Connect first |
| "Table not found" | Wrong table name | Use logical name (account, not Account) |
| "Invalid GUID" | Bad record ID format | Use format: 00000000-0000-0000-0000-000000000000 |
| "Auth failed" | Wrong credentials | Check .env file, verify in Azure Portal |
| "JSON error" | Invalid JSON in Data field | Use [JSON validator](https://jsonlint.com/) |
| "Permission denied" | Insufficient permissions | Grant API permissions in Azure AD |

---

## Performance Tips

| Task | Method | Speed Gain |
|------|--------|-----------|
| Create 1,000 records | Batch operation | **100x faster** |
| Update multiple | Batch operation | **50-100x faster** |
| Query large table | Use $select + $filter | **10x faster** |
| Get specific columns | $select=name,revenue | Less data = faster |

### Batch Size Recommendations
- **Lookup fields**: 100-200 per batch
- **Simple fields**: 500-1000 per batch
- **File uploads**: 10-50 per batch

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Copy results |
| `Ctrl+V` | Paste JSON |
| Tab navigation | Move between fields |
| Enter (in buttons) | Execute operation |

---

## Security Checklist

- ✅ Never commit `.env` to Git
- ✅ Use `.env.example` as template
- ✅ Rotate secrets every 3 months
- ✅ Use separate apps for Dev/Test/Prod
- ✅ Add `.env` to `.gitignore`
- ✅ Use strong secrets (64+ characters)
- ✅ Test permissions on non-prod first

---

## Learning Path

1. **Day 1**: Setup credentials, test connection
2. **Day 2**: Create 1 record, read it back, update it
3. **Day 3**: Try batch creation with 10 records
4. **Day 4**: Build queries with filters
5. **Day 5**: Bulk operations with CSV import
6. **Day 6+**: Integrate into your workflows

---

## Troubleshooting Checklist

- [ ] Are credentials in `.env` file?
- [ ] Did you click "🔗 Connect"?
- [ ] Status shows "✅ Connected"?
- [ ] Table name is lowercase? (account not Account)
- [ ] Record ID is valid GUID?
- [ ] JSON is valid? (use [validator](https://jsonlint.com/))
- [ ] Permissions granted in Azure AD?
- [ ] Client secret not expired?

---

## Pro Tips

💡 **Tip 1**: Save frequently-used queries as templates for reuse

💡 **Tip 2**: Test batch operations with 10 records first, then scale up

💡 **Tip 3**: Use Operation History (left panel) to see what worked

💡 **Tip 4**: Export results regularly in case of accidental deletion

💡 **Tip 5**: Create separate app registrations for Dev/Test/Production

---

## Need Help?

- **Microsoft Docs**: https://learn.microsoft.com/power-apps/developer/
- **OData Reference**: https://learn.microsoft.com/power-apps/developer/data-platform/webapi/query-data-web-api
- **Batch API Guide**: https://learn.microsoft.com/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api

---

**Happy API Development! 🚀**
