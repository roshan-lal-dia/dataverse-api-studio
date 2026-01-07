# Deep Insert Implementation - Technical Details

## Overview

This document explains the technical implementation of creating two article records and relating them via `mdm_articlerelationship` **without any read operations**.

## Two Working Solutions

### Option 1: Sequential POSTs with GUID Binding
Extract GUIDs from response headers, use in relationship binding.

### Option 2: Sequential POSTs with Alternate Keys (NO GUID!) ✨
Reference articles by business key (e.g., `mdm_itemcode`), no GUID extraction needed.

---

## The Solution: 3 Sequential POSTs with GUID Binding

### Why This Works (And Batch Didn't)

| Approach | Issue |
|----------|-------|
| Batch Content-ID (`$1`, `$2`) | Content-ID references not resolvable as navigation property bindings |
| Batch @odata.bind with `/$1` | "Undeclared property" error - nav props need full URIs |
| **Sequential + GUID binding** | ✅ Full control, clear error messages, **works perfectly** |

### The Key Discovery

Navigation property names use **PascalCase**, not the lowercase lookup field names:

```python
# ❌ WRONG (lowercase - these are lookup FIELD names)
"mdm_parentarticle@odata.bind": "/mdm_articles(guid)"
"mdm_childarticle@odata.bind": "/mdm_articles(guid)"

# ✅ CORRECT (PascalCase - these are NAVIGATION PROPERTY names)
"mdm_ParentArticle@odata.bind": "/mdm_articles(guid)"
"mdm_ChildArticle@odata.bind": "/mdm_articles(guid)"
```

---

## Implementation Details

### Script: `article_sequential_create.py`

```python
class ArticleSequentialCreate:
    # Navigation property names (from metadata discovery)
    PARENT_NAV_PROP = "mdm_ParentArticle"  # PascalCase!
    CHILD_NAV_PROP = "mdm_ChildArticle"    # PascalCase!
    
    def create_relationship(self, parent_guid: str, child_guid: str):
        data = {
            "mdm_relationshipname": "...",
            f"{self.PARENT_NAV_PROP}@odata.bind": f"/mdm_articles({parent_guid})",
            f"{self.CHILD_NAV_PROP}@odata.bind": f"/mdm_articles({child_guid})",
        }
        # POST to /mdm_articlerelationships
```

### GUID Extraction from Response Headers

When you POST a record, Dataverse returns the GUID in the `OData-EntityId` header:

```http
HTTP/1.1 201 Created
OData-EntityId: https://org.crm.dynamics.com/api/data/v9.2/mdm_articles(567df30a-d6eb-f011-8407-7c1e52759e27)
```

Python extraction:
```python
entity_id = response.headers.get("OData-EntityId", "")
guid = entity_id.split("(")[-1].rstrip(")")
# Result: "567df30a-d6eb-f011-8407-7c1e52759e27"
```

---

## Metadata Discovery

### Script: `discover_nav_props.py`

Queries Dataverse metadata to find navigation property names:

```python
# Query ManyToOne relationships from mdm_articlerelationship
url = f"{org_url}/api/data/v9.2/EntityDefinitions(LogicalName='mdm_articlerelationship')"
    + "?$expand=ManyToOneRelationships($select=SchemaName,ReferencingEntityNavigationPropertyName)"
```

### Discovery Results

```
MANY-TO-ONE RELATIONSHIPS FROM mdm_articlerelationship
================================================================================

📌 Schema Name: mdm_articlerelationship_ParentArticle_mdm_article
   Referenced Entity (parent): mdm_article
   Referencing Attribute (FK): mdm_parentarticle
   Nav Prop on Relationship: mdm_ParentArticle        ← USE THIS!
   Nav Prop on Article: mdm_articlerelationship_ParentArticle_mdm_article

📌 Schema Name: mdm_articlerelationship_ChildArticle_mdm_article
   Referenced Entity (parent): mdm_article
   Referencing Attribute (FK): mdm_childarticle
   Nav Prop on Relationship: mdm_ChildArticle         ← USE THIS!
   Nav Prop on Article: mdm_articlerelationship_ChildArticle_mdm_article
```

---

## Alternate Keys - VERIFIED WORKING! ✅

The `mdm_article` table has alternate keys configured:

```
🔑 Key: mdm_KeyItemCode       ✅ Tested & Working!
   Attributes: ['mdm_itemcode']

🔑 Key: mdm_keySupplierArticleCodeSupplierId
   Attributes: ['mdm_supplierarticlecode', 'mdm_supplierid']

🔑 Key: mdm_KeyProdctCode
   Attributes: ['mdm_productcode']
```

### Using Alternate Keys (No GUID Needed!) ✨

**Script:** `article_alternate_key_create.py`

Reference articles by business key instead of GUID:

```json
{
  "mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='PARENT_20260107')",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(mdm_itemcode='CHILD_20260107')"
}
```

**Manager's Dream:** Business keys are known BEFORE creation, so no need to read or store GUIDs!

```bash
python scripts/article_alternate_key_create.py --env=DEV --auto-confirm
```
```

---

## Complete Request Flow

### Step 1: Create Parent Article

```http
POST /api/data/v9.2/mdm_articles
Content-Type: application/json
Prefer: return=representation

{
  "mdm_article_id": "SEQ_ART_001_20260107",
  "mdm_description": "Sequential Create Test Article 1"
}
```

**Response:**
```http
HTTP/1.1 201 Created
OData-EntityId: https://org.crm.dynamics.com/api/data/v9.2/mdm_articles(567df30a-d6eb-f011-8407-7c1e52759e27)
```

### Step 2: Create Child Article

```http
POST /api/data/v9.2/mdm_articles
Content-Type: application/json

{
  "mdm_article_id": "SEQ_ART_002_20260107",
  "mdm_description": "Sequential Create Test Article 2"
}
```

**Response:**
```http
HTTP/1.1 201 Created
OData-EntityId: https://org.crm.dynamics.com/api/data/v9.2/mdm_articles(637df30a-d6eb-f011-8407-7c1e52759e27)
```

### Step 3: Create Relationship with @odata.bind

```http
POST /api/data/v9.2/mdm_articlerelationships
Content-Type: application/json

{
  "mdm_relationshipname": "SeqCreate Rel 20260107_200505",
  "mdm_baseunit": "Test Unit",
  "mdm_unit": "Test Unit",
  "mdm_ParentArticle@odata.bind": "/mdm_articles(567df30a-d6eb-f011-8407-7c1e52759e27)",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(637df30a-d6eb-f011-8407-7c1e52759e27)"
}
```

**Response:**
```http
HTTP/1.1 201 Created
OData-EntityId: https://org.crm.dynamics.com/api/data/v9.2/mdm_articlerelationships(6a7df30a-d6eb-f011-8407-7c1e52759e27)
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Undeclared property 'mdm_parentarticle'" | Using lowercase field name | Use PascalCase: `mdm_ParentArticle` |
| "Resource not found" | Invalid GUID | Verify GUID extracted correctly |
| "A record with matching key values already exists" | Duplicate article ID | Use unique timestamps in IDs |

---

## Files Modified

### client/dataverse_client.py
- Enhanced `_build_batch_body()` with Content-ID support
- Backward compatible (used for batch operations if needed)

### New Files Created
| File | Purpose | Lines |
|------|---------|-------|
| `scripts/article_sequential_create.py` | GUID binding POC | ~220 |
| `scripts/article_alternate_key_create.py` | Alternate key POC (NO GUID!) ✨ | ~280 |
| `scripts/discover_nav_props.py` | Metadata discovery | ~100 |
| `scripts/docs/*.md` | Documentation | ~1500 |

---

## Summary

**Two working solutions** using **3 sequential POST operations**:

### Option 1: GUID Binding
1. **POST Article 1** → Extract GUID from `OData-EntityId` header
2. **POST Article 2** → Extract GUID from `OData-EntityId` header
3. **POST Relationship** → Use `@odata.bind` with captured GUIDs

### Option 2: Alternate Keys (NO GUID!) ✨
1. **POST Article 1** with `mdm_itemcode='PARENT_xxx'`
2. **POST Article 2** with `mdm_itemcode='CHILD_xxx'`
3. **POST Relationship** → Reference by `mdm_itemcode` instead of GUID

**Key Insight:** Navigation property names (`mdm_ParentArticle`, `mdm_ChildArticle`) differ from lookup field names (`mdm_parentarticle`, `mdm_childarticle`). Use the metadata discovery script to find correct names.
