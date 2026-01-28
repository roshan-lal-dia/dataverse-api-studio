# Entity Explorer - Quick Start Guide

## 🚀 3-Step Process

### 1️⃣ Select Entity
```
Entity Dropdown → Choose "lmdm_location" (or any entity)
```

### 2️⃣ Enter Record GUID
```
Record GUID field → Paste GUID → Click "🔎 Load Record"
```

### 3️⃣ View & Export
```
Explore tabs → Click "💾 Save Response" → Choose format
```

## 📦 Export Formats

| Format | Best For | File Extension |
|--------|----------|----------------|
| **JSON** | API integration, developers | `.json` |
| **HTML** | Reports, documentation | `.html` |
| **CSV** | Excel analysis, bulk ops | `.csv` |
| **TXT** | Simple sharing, email | `.txt` |
| **XML** | ETL systems, integration | `.xml` |

## 🔗 Relationship Navigation

1. Click **Relationships** tab
2. Click any relationship in the list
3. **Many-to-One**: Auto-navigates to referenced record
4. **One-to-Many/Many-to-Many**: Opens dialog with related records

## 📊 What You'll See

### Attributes Tab
- ✅ All field names and types
- ✅ Actual values (GUIDs, codes)
- ✅ Display values (resolved names)
- ✅ Required flags
- ✅ Valid for Create/Update flags

### JSON View
- Complete API response
- Raw data for technical analysis

### HTML Summary
- Formatted report
- Ready to share with stakeholders

## 🎯 Quick Tips

✅ **Fast Navigation**: Click lookup values in Relationships tab to jump to related records  
✅ **Refresh Data**: Use 🔄 Refresh button to reload without closing  
✅ **Multiple Exports**: Export the same record in different formats  
✅ **Cached Metadata**: First load takes time; subsequent loads are faster (24hr cache)  

## 🔧 Example: lmdm_location

```
1. Select: lmdm_location
2. Enter GUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
3. View:
   - Basic info (name, address)
   - Related key personnel
   - Business hours
   - All lookups resolved
4. Export as CSV for analysis
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| No entities in dropdown | Check authentication status |
| Empty display values | Related record may not exist |
| Slow loading | Normal for first load (caching metadata) |
| Save disabled | Load a record first |

## 📞 Support
See full documentation: [ENTITY_EXPLORER_GUIDE.md](ENTITY_EXPLORER_GUIDE.md)
