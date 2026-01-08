# Dataverse Web API Reference - Knowledge Transfer Document

**Version:** 3.1.0  
**Date:** January 8, 2026  
**Audience:** Databricks Team  
**Purpose:** Complete API reference for creating Article records with relationships in Dataverse

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Authentication](#2-authentication)
3. [Base Configuration](#3-base-configuration)
4. [API Approaches Overview](#4-api-approaches-overview)
5. [Approach A: TRUE Deep Insert (RECOMMENDED)](#5-approach-a-true-deep-insert-recommended)
6. [Approach A+: Multiple Children Deep Insert](#6-approach-a-multiple-children-deep-insert)
7. [Approach B: Batch Upsert (Idempotent)](#7-approach-b-batch-upsert-idempotent)
8. [Approach C: Sequential POSTs](#8-approach-c-sequential-posts)
9. [Navigation Properties Reference](#9-navigation-properties-reference)
10. [Alternate Keys Reference](#10-alternate-keys-reference)
11. [Error Handling](#11-error-handling)
12. [Databricks Implementation Notes](#12-databricks-implementation-notes)

---

## 1. Executive Summary

### Goal
Create **Article records** and **Relationship records** linking them, without any GET/READ operations.

### Use Cases Supported

| Scenario | Records Created | API Calls |
|----------|-----------------|----------|
| 1 Parent + 1 Child + 1 Relationship | 3 | 1 |
| **1 REG + 5 LVs + 5 Relationships** | **11** | **1** |
| 1 REG + N LVs + N Relationships | 1 + 2N | 1 |

### Working Solutions

| Approach | API Calls | Idempotent | Transactional | Recommended |
|----------|-----------|------------|---------------|-------------|
| **TRUE Deep Insert** | 1 | No | Yes | ✅ **YES** |
| **Multiple Children Deep Insert** | 1 | No | Yes | ✅ **For 1:N** |
| Batch Upsert | 1 (batch) | ✅ Yes | Yes | For re-runs |
| Sequential POSTs | 3+ | No | No | Legacy |

### Key Discovery
Navigation properties use **PascalCase** (e.g., `mdm_ParentArticle`), not lowercase field names (e.g., `mdm_parentarticle`).

---

## 2. Authentication

### OAuth 2.0 Client Credentials Flow

Dataverse uses Azure AD (Entra ID) for authentication via OAuth 2.0.

#### Token Request

```http
POST https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&scope={ORG_URL}/.default
&grant_type=client_credentials
```

#### Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `TENANT_ID` | Azure AD Tenant GUID | `12345678-1234-1234-1234-123456789012` |
| `CLIENT_ID` | App Registration Client ID | `abcdef12-3456-7890-abcd-ef1234567890` |
| `CLIENT_SECRET` | App Registration Secret | `~secret~value~here` |
| `ORG_URL` | Dataverse Organization URL | `https://org.crm4.dynamics.com` |

#### Token Response

```json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."
}
```

#### Python Example (using MSAL)

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}"
)

result = app.acquire_token_for_client(
    scopes=[f"{ORG_URL}/.default"]
)

access_token = result["access_token"]
```

#### Databricks (Spark/Python)

```python
import requests

def get_dataverse_token(tenant_id, client_id, client_secret, org_url):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": f"{org_url}/.default",
        "grant_type": "client_credentials"
    }
    
    response = requests.post(token_url, data=payload)
    return response.json()["access_token"]
```

---

## 3. Base Configuration

### Environment URLs

| Environment | URL Pattern |
|-------------|-------------|
| Production | `https://{org}.crm.dynamics.com` |
| Europe | `https://{org}.crm4.dynamics.com` |
| UK | `https://{org}.crm11.dynamics.com` |
| Australia | `https://{org}.crm6.dynamics.com` |

### API Base URL

```
{ORG_URL}/api/data/v9.2/
```

Example: `https://org6d60c202.crm4.dynamics.com/api/data/v9.2/`

### Required Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `Bearer {access_token}` | OAuth 2.0 token |
| `Content-Type` | `application/json` | For JSON payloads |
| `OData-MaxVersion` | `4.0` | OData protocol version |
| `OData-Version` | `4.0` | OData protocol version |
| `Accept` | `application/json` | Response format |
| `Prefer` | `return=representation` | Return created record (optional) |

### Python Headers Example

```python
def get_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Prefer": "return=representation"
    }
```

---

## 4. API Approaches Overview

### Entity Names (Plural for API)

| Entity | Logical Name | API Endpoint |
|--------|--------------|--------------|
| Article | `mdm_article` | `mdm_articles` |
| Article Relationship | `mdm_articlerelationship` | `mdm_articlerelationships` |

### Relationship Structure

```
┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────┐
│  mdm_article    │◄─────│ mdm_articlerelationship │─────►│  mdm_article    │
│  (Parent)       │      │                         │      │  (Child)        │
│                 │      │ mdm_ParentArticle (FK)  │      │                 │
│                 │      │ mdm_ChildArticle (FK)   │      │                 │
└─────────────────┘      └─────────────────────────┘      └─────────────────┘
```

---

## 5. Approach A: TRUE Deep Insert (RECOMMENDED)

### Overview

Create **all 3 records in a single atomic POST request** by nesting the child article inside the relationship, which is nested inside the parent article.

### HTTP Request

```http
POST {ORG_URL}/api/data/v9.2/mdm_articles
Authorization: Bearer {access_token}
Content-Type: application/json
OData-MaxVersion: 4.0
OData-Version: 4.0
Accept: application/json
Prefer: return=representation
```

### Request Payload

```json
{
  "mdm_itemcode": "PARENT_20260108",
  "mdm_article_id": "Parent Article",
  "mdm_articledescription": "Parent Article Description",
  "mdm_description": "Created via TRUE Deep Insert",
  "mdm_casesperpallet": 1,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_logisticalvariantdescription": "Parent LV",
  "mdm_sellablestatus": true,
  
  "mdm_articlerelationship_ParentArticle_mdm_article": [
    {
      "mdm_relationshipname": "Parent-Child Link",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      
      "mdm_ChildArticle": {
        "mdm_itemcode": "CHILD_20260108",
        "mdm_article_id": "Child Article",
        "mdm_articledescription": "Child Article Description",
        "mdm_description": "Created via nested Deep Insert",
        "mdm_casesperpallet": 1,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_logisticalvariantdescription": "Child LV",
        "mdm_sellablestatus": true
      }
    }
  ]
}
```

### Payload Structure Explained

```
{
  // LEVEL 1: Parent Article fields
  "mdm_itemcode": "...",              // Alternate key (business ID)
  "mdm_article_id": "...",            // Display name
  ... other article fields ...
  
  // LEVEL 2: Collection navigation property (1:N from Article to Relationship)
  "mdm_articlerelationship_ParentArticle_mdm_article": [
    {
      // Relationship record fields
      "mdm_relationshipname": "...",
      "mdm_baseunit": "...",
      "mdm_unit": "...",
      
      // LEVEL 3: Single-valued navigation property (creates child article)
      "mdm_ChildArticle": {
        // Child Article fields (NESTED CREATION!)
        "mdm_itemcode": "...",
        "mdm_article_id": "...",
        ... other article fields ...
      }
    }
  ]
}
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `mdm_articlerelationship_ParentArticle_mdm_article` | Collection Navigation | 1:N relationship from Article to Relationships where this article is parent |
| `mdm_ChildArticle` | Single-Valued Navigation | N:1 relationship from Relationship to the child Article |

### Response (HTTP 201 Created)

```json
{
  "@odata.context": "https://org.crm4.dynamics.com/api/data/v9.2/$metadata#mdm_articles/$entity",
  "mdm_articleid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "mdm_itemcode": "PARENT_20260108",
  "mdm_article_id": "Parent Article",
  ...
}
```

### Response Headers

```http
HTTP/1.1 201 Created
OData-EntityId: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articles(a1b2c3d4-e5f6-7890-abcd-ef1234567890)
```

### Python Implementation

```python
import requests

def true_deep_insert(org_url, access_token, parent_data, child_data, relationship_name):
    """
    Create Parent Article + Relationship + Child Article in ONE API call.
    
    Args:
        org_url: Dataverse organization URL
        access_token: OAuth 2.0 Bearer token
        parent_data: Dict with parent article fields
        child_data: Dict with child article fields
        relationship_name: Name for the relationship record
    
    Returns:
        Response object
    """
    
    url = f"{org_url}/api/data/v9.2/mdm_articles"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Prefer": "return=representation"
    }
    
    # Build nested payload
    payload = {
        **parent_data,  # Parent article fields
        
        # Nested relationship with nested child
        "mdm_articlerelationship_ParentArticle_mdm_article": [
            {
                "mdm_relationshipname": relationship_name,
                "mdm_baseunit": "EA",
                "mdm_unit": "EA",
                
                # Nested child article
                "mdm_ChildArticle": child_data
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print("SUCCESS: All 3 records created!")
        return {"success": True, "data": response.json()}
    else:
        print(f"FAILED: {response.status_code} - {response.text}")
        return {"success": False, "error": response.text}


# Usage Example
parent = {
    "mdm_itemcode": "PARENT_001",
    "mdm_article_id": "Parent Article",
    "mdm_articledescription": "Parent Description",
    "mdm_description": "Created via deep insert",
    "mdm_casesperpallet": 1,
    "mdm_expenseitem": False,
    "mdm_fooditem": True,
    "mdm_hazard": False,
    "mdm_sellablestatus": True
}

child = {
    "mdm_itemcode": "CHILD_001",
    "mdm_article_id": "Child Article",
    "mdm_articledescription": "Child Description",
    "mdm_description": "Created nested",
    "mdm_casesperpallet": 1,
    "mdm_expenseitem": False,
    "mdm_fooditem": True,
    "mdm_hazard": False,
    "mdm_sellablestatus": True
}

result = true_deep_insert(org_url, token, parent, child, "Parent-Child Link")
```

---

## 6. Approach A+: Multiple Children Deep Insert

### Overview

Create **1 Parent + N Children + N Relationships** in a **SINGLE API call**!

**Real Use Case:** "If we have 5 LV (Logistical Variants) that we need to associate with 1 REG (Regular Article)"

### Result: 11 Records in 1 API Call!

| Created | Count |
|---------|-------|
| REG (Parent Article) | 1 |
| LV (Child Articles) | 5 |
| Relationships | 5 |
| **Total** | **11** |
| **API Calls** | **1** |

### HTTP Request

```http
POST {ORG_URL}/api/data/v9.2/mdm_articles
Authorization: Bearer {access_token}
Content-Type: application/json
OData-MaxVersion: 4.0
OData-Version: 4.0
Prefer: return=representation
```

### Request Payload (1 REG + 5 LVs)

```json
{
  "mdm_itemcode": "REG_001",
  "mdm_article_id": "Regular Article",
  "mdm_articledescription": "REG with 5 LVs",
  "mdm_description": "Parent article with 5 logistical variants",
  "mdm_casesperpallet": 100,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_sellablestatus": true,
  
  "mdm_articlerelationship_ParentArticle_mdm_article": [
    {
      "mdm_relationshipname": "REG-to-LV1",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      "mdm_ChildArticle": {
        "mdm_itemcode": "LV1_001",
        "mdm_article_id": "Logistical Variant 1",
        "mdm_articledescription": "LV1 Description",
        "mdm_casesperpallet": 10,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_sellablestatus": true
      }
    },
    {
      "mdm_relationshipname": "REG-to-LV2",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      "mdm_ChildArticle": {
        "mdm_itemcode": "LV2_001",
        "mdm_article_id": "Logistical Variant 2",
        "mdm_articledescription": "LV2 Description",
        "mdm_casesperpallet": 20,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_sellablestatus": true
      }
    },
    {
      "mdm_relationshipname": "REG-to-LV3",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      "mdm_ChildArticle": {
        "mdm_itemcode": "LV3_001",
        "mdm_article_id": "Logistical Variant 3",
        "mdm_articledescription": "LV3 Description",
        "mdm_casesperpallet": 30,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_sellablestatus": true
      }
    },
    {
      "mdm_relationshipname": "REG-to-LV4",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      "mdm_ChildArticle": {
        "mdm_itemcode": "LV4_001",
        "mdm_article_id": "Logistical Variant 4",
        "mdm_articledescription": "LV4 Description",
        "mdm_casesperpallet": 40,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_sellablestatus": true
      }
    },
    {
      "mdm_relationshipname": "REG-to-LV5",
      "mdm_baseunit": "EA",
      "mdm_unit": "EA",
      "mdm_ChildArticle": {
        "mdm_itemcode": "LV5_001",
        "mdm_article_id": "Logistical Variant 5",
        "mdm_articledescription": "LV5 Description",
        "mdm_casesperpallet": 50,
        "mdm_expenseitem": false,
        "mdm_fooditem": true,
        "mdm_hazard": false,
        "mdm_sellablestatus": true
      }
    }
  ]
}
```

### Payload Structure Explained

```
{
  // LEVEL 1: Parent Article (REG)
  "mdm_itemcode": "REG_001",
  ... other article fields ...
  
  // LEVEL 2: Array of relationships (one per child)
  "mdm_articlerelationship_ParentArticle_mdm_article": [
    
    // Relationship 1 + Nested Child 1
    {
      "mdm_relationshipname": "REG-to-LV1",
      "mdm_ChildArticle": {           ← NESTED LV1 CREATION
        "mdm_itemcode": "LV1_001",
        ... child fields ...
      }
    },
    
    // Relationship 2 + Nested Child 2
    {
      "mdm_relationshipname": "REG-to-LV2",
      "mdm_ChildArticle": {           ← NESTED LV2 CREATION
        "mdm_itemcode": "LV2_001",
        ... child fields ...
      }
    },
    
    // ... more relationships ...
  ]
}
```

### Python Implementation

```python
import requests

def create_reg_with_multiple_lvs(org_url, access_token, reg_data, lv_list):
    """
    Create 1 REG + N LVs + N Relationships in ONE API call!
    
    Args:
        org_url: Dataverse organization URL
        access_token: OAuth 2.0 Bearer token
        reg_data: Dict with REG article fields
        lv_list: List of dicts, each containing LV fields and relationship name
                 [{"lv_data": {...}, "relationship_name": "..."}, ...]
    
    Returns:
        Response dict with success status
    """
    
    url = f"{org_url}/api/data/v9.2/mdm_articles"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Prefer": "return=representation"
    }
    
    # Build nested relationships array
    relationships = []
    for item in lv_list:
        relationship = {
            "mdm_relationshipname": item["relationship_name"],
            "mdm_baseunit": "EA",
            "mdm_unit": "EA",
            "mdm_ChildArticle": item["lv_data"]  # Nested child creation!
        }
        relationships.append(relationship)
    
    # Full payload
    payload = {
        **reg_data,
        "mdm_articlerelationship_ParentArticle_mdm_article": relationships
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        total_records = 1 + len(lv_list) + len(lv_list)  # REG + LVs + Relationships
        print(f"SUCCESS: {total_records} records created in 1 API call!")
        return {"success": True, "data": response.json()}
    else:
        print(f"FAILED: {response.status_code} - {response.text}")
        return {"success": False, "error": response.text}


# Usage Example
reg = {
    "mdm_itemcode": "REG_001",
    "mdm_article_id": "Regular Article",
    "mdm_articledescription": "REG with multiple LVs",
    "mdm_casesperpallet": 100,
    "mdm_expenseitem": False,
    "mdm_fooditem": True,
    "mdm_hazard": False,
    "mdm_sellablestatus": True
}

lvs = [
    {
        "relationship_name": "REG-to-LV1",
        "lv_data": {
            "mdm_itemcode": "LV1_001",
            "mdm_article_id": "Logistical Variant 1",
            "mdm_casesperpallet": 10,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_sellablestatus": True
        }
    },
    {
        "relationship_name": "REG-to-LV2",
        "lv_data": {
            "mdm_itemcode": "LV2_001",
            "mdm_article_id": "Logistical Variant 2",
            "mdm_casesperpallet": 20,
            "mdm_expenseitem": False,
            "mdm_fooditem": True,
            "mdm_hazard": False,
            "mdm_sellablestatus": True
        }
    },
    # Add more LVs as needed...
]

result = create_reg_with_multiple_lvs(org_url, token, reg, lvs)
```

### Databricks Implementation

```python
def process_reg_with_lvs_from_dataframe(reg_row, lv_rows):
    """
    Process one REG with its associated LVs from DataFrame rows.
    
    reg_row: Single row for the REG article
    lv_rows: DataFrame rows for LVs associated with this REG
    """
    
    reg_data = {
        "mdm_itemcode": reg_row["reg_itemcode"],
        "mdm_article_id": reg_row["reg_name"],
        "mdm_articledescription": reg_row["reg_description"],
        "mdm_casesperpallet": int(reg_row["cases_per_pallet"]),
        "mdm_expenseitem": False,
        "mdm_fooditem": True,
        "mdm_hazard": False,
        "mdm_sellablestatus": True
    }
    
    relationships = []
    for lv_row in lv_rows.collect():
        relationship = {
            "mdm_relationshipname": f"{reg_row['reg_itemcode']}-to-{lv_row['lv_itemcode']}",
            "mdm_baseunit": "EA",
            "mdm_unit": "EA",
            "mdm_ChildArticle": {
                "mdm_itemcode": lv_row["lv_itemcode"],
                "mdm_article_id": lv_row["lv_name"],
                "mdm_articledescription": lv_row["lv_description"],
                "mdm_casesperpallet": int(lv_row["lv_cases"]),
                "mdm_expenseitem": False,
                "mdm_fooditem": True,
                "mdm_hazard": False,
                "mdm_sellablestatus": True
            }
        }
        relationships.append(relationship)
    
    payload = {
        **reg_data,
        "mdm_articlerelationship_ParentArticle_mdm_article": relationships
    }
    
    # Make API call
    response = requests.post(
        f"{org_url}/api/data/v9.2/mdm_articles",
        headers=headers,
        json=payload
    )
    
    return {
        "reg_itemcode": reg_row["reg_itemcode"],
        "lv_count": len(relationships),
        "success": response.status_code == 201,
        "total_records": 1 + len(relationships) * 2
    }
```

### Script Reference

```bash
# Create 1 REG + 5 LVs (default)
python scripts/article_multiple_children.py --env=DEV --auto-confirm

# Create 1 REG + 10 LVs
python scripts/article_multiple_children.py --env=DEV --children=10 --auto-confirm
```

---

## 7. Approach B: Batch Upsert (Idempotent)

### Overview

Use a **$batch** request with **PATCH** (upsert) for articles and **POST** for relationship. This approach is **idempotent** - re-running won't fail on duplicate keys.

### Why Upsert?

- **PATCH with alternate key** = Upsert behavior
- If record exists → Update
- If record doesn't exist → Create
- Re-processing Excel rows won't fail!

### HTTP Request

```http
POST {ORG_URL}/api/data/v9.2/$batch
Authorization: Bearer {access_token}
Content-Type: multipart/mixed; boundary=batch_123
OData-MaxVersion: 4.0
OData-Version: 4.0
```

### Request Body

```http
--batch_123
Content-Type: multipart/mixed; boundary=changeset_456

--changeset_456
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 1

PATCH {ORG_URL}/api/data/v9.2/mdm_articles(mdm_itemcode='PARENT_001') HTTP/1.1
Content-Type: application/json

{
  "mdm_article_id": "Parent Article",
  "mdm_articledescription": "Parent Description",
  "mdm_description": "Created via batch upsert",
  "mdm_casesperpallet": 1,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_sellablestatus": true
}

--changeset_456
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 2

PATCH {ORG_URL}/api/data/v9.2/mdm_articles(mdm_itemcode='CHILD_001') HTTP/1.1
Content-Type: application/json

{
  "mdm_article_id": "Child Article",
  "mdm_articledescription": "Child Description",
  "mdm_description": "Created via batch upsert",
  "mdm_casesperpallet": 1,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_sellablestatus": true
}

--changeset_456
Content-Type: application/http
Content-Transfer-Encoding: binary
Content-ID: 3

POST {ORG_URL}/api/data/v9.2/mdm_articlerelationships HTTP/1.1
Content-Type: application/json

{
  "mdm_relationshipname": "Parent-Child Link",
  "mdm_baseunit": "EA",
  "mdm_unit": "EA",
  "mdm_ParentArticle@odata.bind": "mdm_articles(mdm_itemcode='PARENT_001')",
  "mdm_ChildArticle@odata.bind": "mdm_articles(mdm_itemcode='CHILD_001')"
}

--changeset_456--
--batch_123--
```

### Key Components Explained

| Component | Description |
|-----------|-------------|
| `--batch_123` | Batch boundary (unique identifier) |
| `--changeset_456` | Changeset boundary (all operations in changeset are atomic) |
| `Content-ID: n` | Identifier for each operation (1, 2, 3) |
| `PATCH ...mdm_articles(mdm_itemcode='...')` | Upsert via alternate key |
| `@odata.bind` | Reference to existing/just-created record |

### Alternate Key Syntax in PATCH URL

```
PATCH /mdm_articles(mdm_itemcode='PARENT_001')
                    ↑
                    Alternate key field = value
```

### @odata.bind Syntax

```json
"mdm_ParentArticle@odata.bind": "mdm_articles(mdm_itemcode='PARENT_001')"
                                ↑              ↑
                                Entity set     Alternate key reference
```

### Response (HTTP 200 OK)

```http
--batchresponse_guid
Content-Type: multipart/mixed; boundary=changesetresponse_guid

--changesetresponse_guid
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 204 No Content
OData-EntityId: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articles(guid1)

--changesetresponse_guid
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 204 No Content
OData-EntityId: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articles(guid2)

--changesetresponse_guid
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 204 No Content
OData-EntityId: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articlerelationships(guid3)

--changesetresponse_guid--
--batchresponse_guid--
```

### Python Implementation

```python
import requests
import json

def batch_upsert(org_url, access_token, parent_itemcode, child_itemcode, 
                 parent_data, child_data, relationship_name):
    """
    Create/Update 2 Articles + Create Relationship in ONE atomic batch.
    
    Idempotent: Safe to re-run without duplicate errors.
    """
    
    url = f"{org_url}/api/data/v9.2/$batch"
    
    batch_id = "batch_" + str(int(time.time()))
    changeset_id = "changeset_" + str(int(time.time()))
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": f"multipart/mixed; boundary={batch_id}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }
    
    # Build batch body
    lines = []
    
    # Batch start
    lines.append(f"--{batch_id}")
    lines.append(f"Content-Type: multipart/mixed; boundary={changeset_id}")
    lines.append("")
    
    # Operation 1: Upsert Parent Article
    lines.append(f"--{changeset_id}")
    lines.append("Content-Type: application/http")
    lines.append("Content-Transfer-Encoding: binary")
    lines.append("Content-ID: 1")
    lines.append("")
    lines.append(f"PATCH {org_url}/api/data/v9.2/mdm_articles(mdm_itemcode='{parent_itemcode}') HTTP/1.1")
    lines.append("Content-Type: application/json")
    lines.append("")
    lines.append(json.dumps(parent_data))
    lines.append("")
    
    # Operation 2: Upsert Child Article
    lines.append(f"--{changeset_id}")
    lines.append("Content-Type: application/http")
    lines.append("Content-Transfer-Encoding: binary")
    lines.append("Content-ID: 2")
    lines.append("")
    lines.append(f"PATCH {org_url}/api/data/v9.2/mdm_articles(mdm_itemcode='{child_itemcode}') HTTP/1.1")
    lines.append("Content-Type: application/json")
    lines.append("")
    lines.append(json.dumps(child_data))
    lines.append("")
    
    # Operation 3: Create Relationship
    relationship_data = {
        "mdm_relationshipname": relationship_name,
        "mdm_baseunit": "EA",
        "mdm_unit": "EA",
        "mdm_ParentArticle@odata.bind": f"mdm_articles(mdm_itemcode='{parent_itemcode}')",
        "mdm_ChildArticle@odata.bind": f"mdm_articles(mdm_itemcode='{child_itemcode}')"
    }
    
    lines.append(f"--{changeset_id}")
    lines.append("Content-Type: application/http")
    lines.append("Content-Transfer-Encoding: binary")
    lines.append("Content-ID: 3")
    lines.append("")
    lines.append(f"POST {org_url}/api/data/v9.2/mdm_articlerelationships HTTP/1.1")
    lines.append("Content-Type: application/json")
    lines.append("")
    lines.append(json.dumps(relationship_data))
    lines.append("")
    
    # Close changeset and batch
    lines.append(f"--{changeset_id}--")
    lines.append(f"--{batch_id}--")
    
    body = "\r\n".join(lines)
    
    response = requests.post(url, headers=headers, data=body.encode('utf-8'))
    
    if response.status_code == 200:
        # Check for errors in response body
        if "HTTP/1.1 4" in response.text or "HTTP/1.1 5" in response.text:
            return {"success": False, "error": response.text}
        return {"success": True, "data": response.text}
    else:
        return {"success": False, "error": f"{response.status_code}: {response.text}"}
```

---

## 8. Approach C: Sequential POSTs

### Overview

Create records one at a time. Simple but requires 3 separate API calls.

### Request 1: Create Parent Article

```http
POST {ORG_URL}/api/data/v9.2/mdm_articles
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "mdm_itemcode": "PARENT_001",
  "mdm_article_id": "Parent Article",
  "mdm_articledescription": "Parent Description",
  "mdm_casesperpallet": 1,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_sellablestatus": true
}
```

**Response Header:**
```http
OData-EntityId: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articles(a1b2c3d4-...)
```

### Request 2: Create Child Article

```http
POST {ORG_URL}/api/data/v9.2/mdm_articles
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "mdm_itemcode": "CHILD_001",
  "mdm_article_id": "Child Article",
  "mdm_articledescription": "Child Description",
  "mdm_casesperpallet": 1,
  "mdm_expenseitem": false,
  "mdm_fooditem": true,
  "mdm_hazard": false,
  "mdm_sellablestatus": true
}
```

### Request 3: Create Relationship

**Option A: Using GUIDs (extracted from response headers)**

```http
POST {ORG_URL}/api/data/v9.2/mdm_articlerelationships
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "mdm_relationshipname": "Parent-Child Link",
  "mdm_baseunit": "EA",
  "mdm_unit": "EA",
  "mdm_ParentArticle@odata.bind": "/mdm_articles(a1b2c3d4-e5f6-7890-abcd-ef1234567890)",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(f6e5d4c3-b2a1-0987-dcba-0987654321fe)"
}
```

**Option B: Using Alternate Keys (NO GUID needed!)**

```http
POST {ORG_URL}/api/data/v9.2/mdm_articlerelationships
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "mdm_relationshipname": "Parent-Child Link",
  "mdm_baseunit": "EA",
  "mdm_unit": "EA",
  "mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='PARENT_001')",
  "mdm_ChildArticle@odata.bind": "/mdm_articles(mdm_itemcode='CHILD_001')"
}
```

### GUID Extraction from Response Header

```python
def extract_guid_from_response(response):
    """Extract GUID from OData-EntityId header."""
    entity_id = response.headers.get("OData-EntityId", "")
    # Example: https://org.crm4.dynamics.com/api/data/v9.2/mdm_articles(a1b2c3d4-...)
    
    if "(" in entity_id and ")" in entity_id:
        guid = entity_id.split("(")[-1].rstrip(")")
        return guid
    return None
```

---

## 9. Navigation Properties Reference

### Understanding Navigation Properties

Navigation properties are the OData way to represent relationships. They have different names than the underlying lookup fields.

### mdm_articlerelationship Entity

| Lookup Field (Schema) | Navigation Property | Direction | Description |
|----------------------|---------------------|-----------|-------------|
| `mdm_parentarticle` | `mdm_ParentArticle` | N:1 | Points to parent article |
| `mdm_childarticle` | `mdm_ChildArticle` | N:1 | Points to child article |

### mdm_article Entity

| Navigation Property | Direction | Description |
|---------------------|-----------|-------------|
| `mdm_articlerelationship_ParentArticle_mdm_article` | 1:N | All relationships where this article is parent |
| `mdm_articlerelationship_ChildArticle_mdm_article` | 1:N | All relationships where this article is child |

### CRITICAL: Use PascalCase!

```python
# ❌ WRONG - These are lookup FIELD names (lowercase)
"mdm_parentarticle@odata.bind": "..."
"mdm_childarticle@odata.bind": "..."

# ✅ CORRECT - These are NAVIGATION PROPERTY names (PascalCase)
"mdm_ParentArticle@odata.bind": "..."
"mdm_ChildArticle@odata.bind": "..."
```

### How to Discover Navigation Properties

```http
GET {ORG_URL}/api/data/v9.2/EntityDefinitions(LogicalName='mdm_articlerelationship')?$expand=ManyToOneRelationships($select=SchemaName,ReferencingEntityNavigationPropertyName,ReferencedEntityNavigationPropertyName)
```

---

## 10. Alternate Keys Reference

### What Are Alternate Keys?

Alternate keys let you reference records by **business identifiers** instead of GUIDs.

### Available Alternate Keys on mdm_article

| Key Name | Attribute(s) | Usage |
|----------|-------------|-------|
| `mdm_KeyItemCode` | `mdm_itemcode` | `/mdm_articles(mdm_itemcode='VALUE')` |
| `mdm_KeyProdctCode` | `mdm_productcode` | `/mdm_articles(mdm_productcode='VALUE')` |
| `mdm_keySupplierArticleCodeSupplierId` | `mdm_supplierarticlecode`, `mdm_supplierid` | Composite key |

### Alternate Key Syntax

**Single Key:**
```
/mdm_articles(mdm_itemcode='ITEM001')
```

**Composite Key:**
```
/mdm_articles(mdm_supplierarticlecode='SAC001',mdm_supplierid='SUP001')
```

### Using Alternate Keys in @odata.bind

```json
{
  "mdm_ParentArticle@odata.bind": "mdm_articles(mdm_itemcode='PARENT001')",
  "mdm_ChildArticle@odata.bind": "mdm_articles(mdm_itemcode='CHILD001')"
}
```

### Using Alternate Keys in PATCH (Upsert)

```http
PATCH /api/data/v9.2/mdm_articles(mdm_itemcode='ITEM001')
Content-Type: application/json

{
  "mdm_article_id": "Updated Article Name"
}
```

- If record with `mdm_itemcode='ITEM001'` exists → **UPDATE**
- If record doesn't exist → **CREATE** with that itemcode

---

## 11. Error Handling

### Common Errors and Solutions

| HTTP Code | Error | Cause | Solution |
|-----------|-------|-------|----------|
| 400 | `Undeclared property 'mdm_parentarticle'` | Lowercase nav prop name | Use PascalCase: `mdm_ParentArticle` |
| 400 | `The property 'field' does not exist` | Wrong field name | Check EntityDefinitions metadata |
| 404 | `Resource not found` | Invalid GUID or alternate key | Verify record exists |
| 401 | `Unauthorized` | Token expired or invalid | Refresh OAuth token |
| 403 | `Forbidden` | Insufficient permissions | Check app registration permissions |
| 412 | `Precondition Failed` | Concurrent modification | Retry with fresh ETag |
| 429 | `Too Many Requests` | Rate limit hit | Implement exponential backoff |

### Error Response Format

```json
{
  "error": {
    "code": "0x80040217",
    "message": "A record with matching key values already exists.",
    "innererror": {
      "message": "A record with matching key values already exists.",
      "type": "Microsoft.Crm.CrmException",
      "stacktrace": "..."
    }
  }
}
```

### Python Error Handling

```python
def handle_dataverse_response(response):
    if response.status_code in [200, 201, 204]:
        return {"success": True, "data": response.json() if response.text else None}
    
    error_info = {
        "success": False,
        "status_code": response.status_code,
        "error": response.text
    }
    
    try:
        error_json = response.json()
        if "error" in error_json:
            error_info["error_code"] = error_json["error"].get("code")
            error_info["error_message"] = error_json["error"].get("message")
    except:
        pass
    
    return error_info
```

---

## 12. Databricks Implementation Notes

### PySpark Integration

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import requests
import json

# Configuration (use Databricks secrets)
tenant_id = dbutils.secrets.get("dataverse", "tenant_id")
client_id = dbutils.secrets.get("dataverse", "client_id")
client_secret = dbutils.secrets.get("dataverse", "client_secret")
org_url = dbutils.secrets.get("dataverse", "org_url")

def get_token():
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": f"{org_url}/.default",
        "grant_type": "client_credentials"
    }
    response = requests.post(token_url, data=payload)
    return response.json()["access_token"]

# Broadcast token to all workers
token = spark.sparkContext.broadcast(get_token())
```

### Processing DataFrame Rows

```python
def create_article_relationship(row):
    """Process a single row - create parent, child, and relationship."""
    
    access_token = token.value
    
    payload = {
        "mdm_itemcode": row["parent_itemcode"],
        "mdm_article_id": row["parent_name"],
        "mdm_articledescription": row["parent_description"],
        "mdm_casesperpallet": 1,
        "mdm_expenseitem": False,
        "mdm_fooditem": True,
        "mdm_hazard": False,
        "mdm_sellablestatus": True,
        
        "mdm_articlerelationship_ParentArticle_mdm_article": [
            {
                "mdm_relationshipname": row["relationship_name"],
                "mdm_baseunit": "EA",
                "mdm_unit": "EA",
                "mdm_ChildArticle": {
                    "mdm_itemcode": row["child_itemcode"],
                    "mdm_article_id": row["child_name"],
                    "mdm_articledescription": row["child_description"],
                    "mdm_casesperpallet": 1,
                    "mdm_expenseitem": False,
                    "mdm_fooditem": True,
                    "mdm_hazard": False,
                    "mdm_sellablestatus": True
                }
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }
    
    response = requests.post(
        f"{org_url}/api/data/v9.2/mdm_articles",
        headers=headers,
        json=payload
    )
    
    return {
        "parent_itemcode": row["parent_itemcode"],
        "child_itemcode": row["child_itemcode"],
        "success": response.status_code == 201,
        "status_code": response.status_code,
        "error": response.text if response.status_code != 201 else None
    }

# Apply to DataFrame
results = df.rdd.map(create_article_relationship).collect()
```

### Rate Limiting Considerations

```python
import time
from functools import wraps

def rate_limited(max_per_second=10):
    """Decorator to rate limit API calls."""
    min_interval = 1.0 / max_per_second
    
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        
        return wrapper
    return decorator

@rate_limited(max_per_second=5)
def create_record_rate_limited(payload):
    # API call here
    pass
```

### Batch Processing for Large Datasets

```python
def process_in_batches(df, batch_size=100):
    """Process DataFrame in batches to avoid overwhelming API."""
    
    total_rows = df.count()
    results = []
    
    for offset in range(0, total_rows, batch_size):
        batch = df.limit(batch_size).offset(offset)
        batch_results = batch.rdd.map(create_article_relationship).collect()
        results.extend(batch_results)
        
        # Log progress
        print(f"Processed {min(offset + batch_size, total_rows)}/{total_rows}")
        
        # Pause between batches
        time.sleep(1)
    
    return results
```

---

## Summary Table

| Feature | TRUE Deep Insert | Batch Upsert | Sequential |
|---------|------------------|--------------|------------|
| API Calls | 1 | 1 (batch) | 3 |
| Records Created | 3 | 3 | 3 |
| Transactional | ✅ Yes | ✅ Yes | ❌ No |
| Idempotent | ❌ No | ✅ Yes | ❌ No |
| GUIDs Needed | ❌ No | ❌ No | Optional |
| Best For | New records | Re-processable loads | Simple cases |

---

## Quick Reference Card

```python
# === AUTHENTICATION ===
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
scope = f"{ORG_URL}/.default"

# === HEADERS ===
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0"
}

# === ENDPOINTS ===
articles_url = f"{ORG_URL}/api/data/v9.2/mdm_articles"
relationships_url = f"{ORG_URL}/api/data/v9.2/mdm_articlerelationships"
batch_url = f"{ORG_URL}/api/data/v9.2/$batch"

# === NAVIGATION PROPERTIES ===
# On Relationship → Article (single-valued):
#   mdm_ParentArticle, mdm_ChildArticle

# On Article → Relationship (collection):
#   mdm_articlerelationship_ParentArticle_mdm_article
#   mdm_articlerelationship_ChildArticle_mdm_article

# === ALTERNATE KEY ===
# /mdm_articles(mdm_itemcode='VALUE')

# === @odata.bind SYNTAX ===
# "mdm_ParentArticle@odata.bind": "mdm_articles(mdm_itemcode='PARENT001')"
```

---

**Document End**

For questions, contact the API Studio development team.
