# Quick Reference - Article Relationship Creation

## TL;DR

**3 POST calls. No reads. Parent/child linked. Two options:**

```bash
# Option 1: GUID from headers
python scripts/article_sequential_create.py --env=DEV --auto-confirm

# Option 2: Alternate Keys (NO GUID!) ✨
python scripts/article_alternate_key_create.py --env=DEV --auto-confirm
```

---

## The Working Pattern

```python
# Step 1: Create Article 1
response1 = POST /mdm_articles { "mdm_article_id": "ART001", ... }
guid1 = response1.headers["OData-EntityId"].split("(")[-1].rstrip(")")

# Step 2: Create Article 2
response2 = POST /mdm_articles { "mdm_article_id": "ART002", ... }
guid2 = response2.headers["OData-EntityId"].split("(")[-1].rstrip(")")

# Step 3: Create Relationship with @odata.bind
POST /mdm_articlerelationships {
    "mdm_relationshipname": "Link ART001 to ART002",
    "mdm_ParentArticle@odata.bind": f"/mdm_articles({guid1})",  # PascalCase!
    "mdm_ChildArticle@odata.bind": f"/mdm_articles({guid2})"    # PascalCase!
}
```

---

## ⚠️ Critical: Navigation Property Names

| ❌ Wrong (Lowercase) | ✅ Correct (PascalCase) |
|---------------------|------------------------|
| `mdm_parentarticle@odata.bind` | `mdm_ParentArticle@odata.bind` |
| `mdm_childarticle@odata.bind` | `mdm_ChildArticle@odata.bind` |

**Lowercase = lookup field names. PascalCase = navigation property names.**

---

## GUID Extraction

```python
# From response headers
entity_id = response.headers.get("OData-EntityId")
# Example: "https://org.crm.dynamics.com/api/data/v9.2/mdm_articles(567df30a-...)"

guid = entity_id.split("(")[-1].rstrip(")")
# Result: "567df30a-d6eb-f011-8407-7c1e52759e27"
```

---

## Alternate Key Option - VERIFIED WORKING! ✅

Reference articles by alternate key instead of GUID:

```json
{
  "mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='PARENT001')",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(mdm_itemcode='CHILD001')"
}
```

**Manager's Dream:** NO GUID needed! Business keys known upfront.

Available alternate keys on `mdm_article`:
- `mdm_itemcode` (single key) ✅ Verified
- `mdm_productcode` (single key)
- `mdm_supplierarticlecode` + `mdm_supplierid` (composite key)

---

## Command Line Options

```bash
# Basic run (prompts for confirmation)
python scripts/article_sequential_create.py

# Auto-confirm (no prompts)
python scripts/article_sequential_create.py --auto-confirm

# Specify environment
python scripts/article_sequential_create.py --env=DEV
python scripts/article_sequential_create.py --env=PROD  # Shows warning!

# Combined
python scripts/article_sequential_create.py --env=DEV --auto-confirm
```

---

## Discover Navigation Properties

```bash
python scripts/discover_nav_props.py
```

Output shows:
- ManyToOne relationships
- Navigation property names (use for @odata.bind)
- Alternate keys defined on the table

---

## Success Output

```
============================================================
✅ SUCCESS! All 3 records created and linked!
============================================================

   Parent Article:  567df30a-d6eb-f011-8407-7c1e52759e27
   Child Article:   637df30a-d6eb-f011-8407-7c1e52759e27
   Relationship:    6a7df30a-d6eb-f011-8407-7c1e52759e27

🎯 Key Achievement:
   ✓ 3 sequential POST calls
   ✓ GUID binding via @odata.bind
   ✓ Parent/Child properly linked!
   ✓ No read operations needed
============================================================
```

---

## Common Errors

| Error | Fix |
|-------|-----|
| "Undeclared property" | Use PascalCase nav prop names |
| "Resource not found" | Check GUID is valid |
| "Record exists" | Use unique article IDs (script uses timestamps) |
| Authentication failed | Check .env credentials |

---

## Files

| Script | Purpose |
|--------|---------|
| `article_sequential_create.py` | ✅ Working POC (3 POSTs, GUID binding) |
| `article_alternate_key_create.py` | ✅ Working POC (3 POSTs, NO GUID!) ✨ |
| `discover_nav_props.py` | Find nav prop names & keys |
| `article_deep_insert_poc.py` | ⚠️ Deprecated (batch issues) |
