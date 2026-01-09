# Batch Upsert Guide: Parent + Children + Relationships

**Version:** 1.0.0  
**Date:** January 9, 2026  
**Audience:** Databricks Team  
**Script:** `scripts/article_batch_upsert.py`

---

## Executive Summary

### The Problem
- **Deep Insert with PATCH (upsert) doesn't work** in Dataverse
- Error: `"Deep update of navigation properties is not allowed."` (0x80060888)
- We need idempotent operations (safe to re-run) for Excel uploads

### The Solution
Use `$batch` with:
1. **PATCH** for parent and children (upsert behavior)
2. **POST** for relationships (with `@odata.bind` using alternate keys)

### Key Benefit
| Metric | Value |
|--------|-------|
| **HTTP Requests** | 1 |
| **Billable API Calls** | 1 |
| **Operations Inside** | 11 (for 1 REG + 5 LVs) |
| **GUIDs Needed** | 0 |
| **READ Calls** | 0 |

---

## Why $batch?

### Microsoft's API Limits
From Microsoft Learn:
> **"Batch requests are counted as a single request toward the API limits"**

| Approach | API Calls | Rate Limit Impact | Atomic? |
|----------|-----------|-------------------|---------|
| 11 separate requests | 11 | High | ❌ No |
| Deep Insert (POST) | 1 | Low | ✅ Yes |
| **$batch** | **1** | **Low** | ✅ **Yes** |

### Billing Advantage
```
┌─────────────────────────────────────────────────┐
│  1 $batch request with 11 operations            │
│                                                 │
│  Billing:        1 API call ✅                  │
│  Rate Limits:    1 API call ✅                  │
│  Network:        1 HTTP request ✅              │
│  Atomicity:      All or nothing ✅              │
└─────────────────────────────────────────────────┘
```

---

## Approach Comparison

| Approach | Method | Deep Insert? | Upsert? | Works? |
|----------|--------|--------------|---------|--------|
| Deep Insert | POST | ✅ Yes | ❌ No | ✅ Yes |
| Deep Insert | PATCH | ✅ Yes | ✅ Yes | ❌ **No** (limitation) |
| **$batch** | PATCH + POST | ❌ No | ✅ Yes | ✅ **Yes** |

### Dataverse Limitation
From Microsoft Docs:
> Deep insert is only supported with **POST** (create).  
> **PATCH** (update/upsert) does not support nested navigation properties.

---

## $batch Request Structure

### Visual Overview
```
┌─────────────────────────────────────────────────────────────────┐
│  1 HTTP Request: POST /api/data/v9.2/$batch                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Content-ID: 1  PATCH parent (upsert)                    │   │
│  │ Content-ID: 2  PATCH child 1 (upsert)                   │   │
│  │ Content-ID: 3  PATCH child 2 (upsert)                   │   │
│  │ Content-ID: 4  PATCH child 3 (upsert)                   │   │
│  │ Content-ID: 5  PATCH child 4 (upsert)                   │   │
│  │ Content-ID: 6  PATCH child 5 (upsert)                   │   │
│  │ Content-ID: 7  POST relationship 1                       │   │
│  │ Content-ID: 8  POST relationship 2                       │   │
│  │ Content-ID: 9  POST relationship 3                       │   │
│  │ Content-ID: 10 POST relationship 4                       │   │
│  │ Content-ID: 11 POST relationship 5                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ✅ Atomic: All 11 succeed or all fail                         │
└─────────────────────────────────────────────────────────────────┘
```

### Operation Types

| # | Operation | Method | URL | Purpose |
|---|-----------|--------|-----|---------|
| 1 | Upsert Parent | PATCH | `/mdm_articles(mdm_itemcode='REG_001')` | Creates or updates |
| 2-6 | Upsert Children | PATCH | `/mdm_articles(mdm_itemcode='LV1_001')` | Creates or updates |
| 7-11 | Create Relationships | POST | `/mdm_articlerelationships` | Links parent to children |

---

## Key Innovation: @odata.bind with Alternate Keys

**No GUIDs needed!** Use alternate keys directly in `@odata.bind`:

```json
{
  "mdm_relationshipname": "REG_001-to-LV1_001",
  "mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='REG_001')",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(mdm_itemcode='LV1_001')"
}
```

### Why This Works
1. PATCH operations create/update the articles first
2. Alternate keys are immediately available
3. POST relationships can reference them without knowing GUIDs
4. All in one atomic batch!

---

## Raw $batch Request Example

```http
POST /api/data/v9.2/$batch HTTP/1.1
Host: org.crm4.dynamics.com
Authorization: Bearer {token}
Content-Type: multipart/mixed; boundary=batch_abc123
OData-MaxVersion: 4.0
OData-Version: 4.0

--batch_abc123
Content-Type: multipart/mixed; boundary=changeset_xyz789

--changeset_xyz789
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 1

PATCH /api/data/v9.2/mdm_articles(mdm_itemcode='REG_BATCH_20260109') HTTP/1.1
Content-Type: application/json

{"mdm_itemcode":"REG_BATCH_20260109","mdm_article_id":"REG Article","mdm_sellablestatus":true}

--changeset_xyz789
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 2

PATCH /api/data/v9.2/mdm_articles(mdm_itemcode='LV1_20260109') HTTP/1.1
Content-Type: application/json

{"mdm_itemcode":"LV1_20260109","mdm_article_id":"LV1 Article","mdm_sellablestatus":true}

--changeset_xyz789
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 7

POST /api/data/v9.2/mdm_articlerelationships HTTP/1.1
Content-Type: application/json

{"mdm_relationshipname":"REG-to-LV1","mdm_ParentArticle@odata.bind":"/mdm_articles(mdm_itemcode='REG_BATCH_20260109')","mdm_ChildArticle@odata.bind":"/mdm_articles(mdm_itemcode='LV1_20260109')"}

--changeset_xyz789--
--batch_abc123--
```

---

## Python Implementation

### Core Function
```python
def _build_batch_request(self, reg_itemcode: str, num_children: int) -> tuple:
    """Build the $batch request body."""
    
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    changeset_id = f"changeset_{uuid.uuid4().hex[:8]}"
    
    parts = []
    
    # Start changeset (for atomicity)
    parts.append(f"--{batch_id}")
    parts.append(f"Content-Type: multipart/mixed; boundary={changeset_id}")
    parts.append("")
    
    content_id = 0
    
    # === 1. PATCH Parent Article (Upsert) ===
    content_id += 1
    parent_payload = {
        "mdm_itemcode": reg_itemcode,
        "mdm_article_id": f"REG Article",
        # ... other fields
    }
    
    parts.append(f"--{changeset_id}")
    parts.append("Content-Type: application/http")
    parts.append("Content-Transfer-Encoding: binary")
    parts.append(f"Content-ID: {content_id}")
    parts.append("")
    parts.append(f"PATCH {self.org_url}/api/data/v9.2/mdm_articles(mdm_itemcode='{reg_itemcode}') HTTP/1.1")
    parts.append("Content-Type: application/json")
    parts.append("")
    parts.append(json.dumps(parent_payload))
    
    # === 2. PATCH Each Child (Upsert) ===
    for i in range(1, num_children + 1):
        content_id += 1
        lv_itemcode = f"LV{i}_{timestamp}"
        # ... similar pattern
    
    # === 3. POST Each Relationship ===
    for i, lv_itemcode in enumerate(child_itemcodes, 1):
        content_id += 1
        relationship_payload = {
            "mdm_relationshipname": f"{reg_itemcode}-to-{lv_itemcode}",
            "mdm_ParentArticle@odata.bind": f"/mdm_articles(mdm_itemcode='{reg_itemcode}')",
            "mdm_ChildArticle@odata.bind": f"/mdm_articles(mdm_itemcode='{lv_itemcode}')"
        }
        # ... similar pattern with POST
    
    # End changeset and batch
    parts.append(f"--{changeset_id}--")
    parts.append(f"--{batch_id}--")
    
    return "\r\n".join(parts), changeset_id, batch_id
```

### Execute Batch
```python
url = f"{self.org_url}/api/data/v9.2/$batch"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": f"multipart/mixed; boundary={batch_id}",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0"
}

response = requests.post(url, headers=headers, data=batch_body)

if response.status_code in [200, 202]:
    print("Batch completed!")
```

---

## Databricks Implementation

### PySpark Example
```python
def process_reg_with_lvs_batch(df_row, org_url, headers):
    """
    Process one REG with its LVs using $batch.
    
    Args:
        df_row: Spark Row with REG and LV data
        org_url: Dataverse org URL
        headers: Auth headers with token
    
    Returns:
        dict with success status
    """
    import uuid
    import requests
    
    reg_code = df_row['reg_itemcode']
    lv_codes = df_row['lv_itemcodes']  # List of LV codes
    
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    changeset_id = f"changeset_{uuid.uuid4().hex[:8]}"
    
    parts = []
    
    # Start batch and changeset
    parts.append(f"--{batch_id}")
    parts.append(f"Content-Type: multipart/mixed; boundary={changeset_id}")
    parts.append("")
    
    content_id = 0
    
    # PATCH parent
    content_id += 1
    parts.extend([
        f"--{changeset_id}",
        "Content-Type: application/http",
        "Content-Transfer-Encoding: binary",
        f"Content-ID: {content_id}",
        "",
        f"PATCH {org_url}/api/data/v9.2/mdm_articles(mdm_itemcode='{reg_code}') HTTP/1.1",
        "Content-Type: application/json",
        "",
        json.dumps({"mdm_itemcode": reg_code, "mdm_sellablestatus": True})
    ])
    
    # PATCH each child
    for lv_code in lv_codes:
        content_id += 1
        parts.extend([
            f"--{changeset_id}",
            "Content-Type: application/http",
            "Content-Transfer-Encoding: binary",
            f"Content-ID: {content_id}",
            "",
            f"PATCH {org_url}/api/data/v9.2/mdm_articles(mdm_itemcode='{lv_code}') HTTP/1.1",
            "Content-Type: application/json",
            "",
            json.dumps({"mdm_itemcode": lv_code, "mdm_sellablestatus": True})
        ])
    
    # POST each relationship
    for lv_code in lv_codes:
        content_id += 1
        rel_payload = {
            "mdm_relationshipname": f"{reg_code}-to-{lv_code}",
            "mdm_ParentArticle@odata.bind": f"/mdm_articles(mdm_itemcode='{reg_code}')",
            "mdm_ChildArticle@odata.bind": f"/mdm_articles(mdm_itemcode='{lv_code}')"
        }
        parts.extend([
            f"--{changeset_id}",
            "Content-Type: application/http",
            "Content-Transfer-Encoding: binary",
            f"Content-ID: {content_id}",
            "",
            f"POST {org_url}/api/data/v9.2/mdm_articlerelationships HTTP/1.1",
            "Content-Type: application/json",
            "",
            json.dumps(rel_payload)
        ])
    
    # End changeset and batch
    parts.append(f"--{changeset_id}--")
    parts.append(f"--{batch_id}--")
    
    batch_body = "\r\n".join(parts)
    
    # Execute
    batch_headers = headers.copy()
    batch_headers["Content-Type"] = f"multipart/mixed; boundary={batch_id}"
    
    response = requests.post(
        f"{org_url}/api/data/v9.2/$batch",
        headers=batch_headers,
        data=batch_body
    )
    
    return {
        "reg_code": reg_code,
        "status_code": response.status_code,
        "success": response.status_code in [200, 202]
    }
```

---

## Usage

### Command Line
```powershell
# Basic usage (5 children)
python scripts/article_batch_upsert.py --env=DEV --auto-confirm

# Custom number of children
python scripts/article_batch_upsert.py --env=DEV --children=10 --auto-confirm

# Production environment
python scripts/article_batch_upsert.py --env=PROD --children=5
```

### Expected Output
```
======================================================================
BATCH UPSERT: 1 REG + 5 LVs + 5 Relationships
======================================================================

📦 Operations in this batch:
   1. PATCH (upsert) parent: REG_BATCH_20260109
   2. PATCH (upsert) child: LV1_20260109
   3. PATCH (upsert) child: LV2_20260109
   4. PATCH (upsert) child: LV3_20260109
   5. PATCH (upsert) child: LV4_20260109
   6. PATCH (upsert) child: LV5_20260109
   7. POST relationship: REG_BATCH_20260109 → LV1_20260109
   8. POST relationship: REG_BATCH_20260109 → LV2_20260109
   9. POST relationship: REG_BATCH_20260109 → LV3_20260109
   10. POST relationship: REG_BATCH_20260109 → LV4_20260109
   11. POST relationship: REG_BATCH_20260109 → LV5_20260109

   📊 Total operations: 11 (in 1 atomic batch)
   ✅ Idempotent: Parent and children use UPSERT

🚀 Executing batch request...
   URL: https://org.crm4.dynamics.com/api/data/v9.2/$batch
   Batch ID: batch_abc12345
   Total operations: 11

📡 Response: HTTP 200

✅ BATCH COMPLETED SUCCESSFULLY!

   Summary:
   ├─ Parent Upserts: 1
   ├─ Child Upserts: 5
   ├─ Relationships Created: 5
   ├─ Total Operations: 11
   ├─ API Calls: 1 ($batch)
   ├─ GUIDs Used: 0 (alternate keys only!)
   └─ READ Calls: 0
```

---

## Important Notes

### Relationship Handling
⚠️ Relationships use `POST` (not upsert). If a relationship with the same name already exists, it will fail.

**Solutions:**
1. Use unique relationship names (include timestamp)
2. Delete existing relationships before creating new ones
3. Check for existing relationships first

### Batch Limits
| Limit | Value |
|-------|-------|
| Max operations per batch | 1000 |
| Max payload size | 16 MB |
| Recommended per batch | 100-500 operations |

### Error Handling
```python
if response.status_code in [200, 202]:
    # Check for individual operation failures
    if "HTTP/1.1 4" in response.text or "HTTP/1.1 5" in response.text:
        print("Some operations failed!")
        # Parse response to find failures
    else:
        print("All operations succeeded!")
```

---

## Comparison Summary

| Feature | Deep Insert (POST) | $batch (PATCH+POST) |
|---------|-------------------|---------------------|
| HTTP Requests | 1 | 1 |
| Upsert (idempotent) | ❌ No | ✅ Yes (for articles) |
| Atomic | ✅ Yes | ✅ Yes |
| GUIDs needed | 0 | 0 |
| Re-run safe | ❌ Fails on duplicate | ✅ Updates existing |
| Complexity | Simple | Moderate |

---

## References

- [Microsoft Learn: Execute batch operations](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api)
- [Microsoft Learn: Upsert a table row](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/update-delete-entities-using-web-api#upsert-a-table-row)
- [Microsoft Learn: Create a table row](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/create-entity-web-api)
- Script: `scripts/article_batch_upsert.py`
