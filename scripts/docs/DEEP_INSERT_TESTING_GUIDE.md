# Testing Guide - Article Relationship Creation

## Pre-Test Checklist

- [ ] `.env` file configured with valid Dataverse credentials
- [ ] Network connectivity to Dataverse
- [ ] Python environment activated (`.venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)

---

## Test 1: Sequential Create with GUID Binding

**Objective:** Create 2 articles + 1 relationship with proper linking

**Command:**
```bash
python scripts/article_sequential_create.py --env=DEV --auto-confirm
```

**Expected Output:**
```
============================================================
🚀 ARTICLE SEQUENTIAL CREATE POC
   3 POST operations with GUID binding
============================================================

🔐 Authenticating with Dataverse...
✅ Authenticated to DEV
   https://org.crm.dynamics.com/

⚠️  Target: DEV (https://org.crm.dynamics.com/)
   ✓ Auto-confirmed

----------------------------------------
STEP 1/3: Create Parent Article
----------------------------------------

📝 Creating Article 1...
   Payload: {...}
   ✅ Created! GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

----------------------------------------
STEP 2/3: Create Child Article
----------------------------------------

📝 Creating Article 2...
   Payload: {...}
   ✅ Created! GUID: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy

----------------------------------------
STEP 3/3: Create Relationship with @odata.bind
----------------------------------------
   Parent GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Child GUID:  yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy

📝 Creating Relationship (with parent/child binding)...
   Payload: {...}
   ✅ Created! GUID: zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz

============================================================
✅ SUCCESS! All 3 records created and linked!
============================================================
```

**Success Criteria:**
- ✅ All 3 records created (3 GUIDs displayed)
- ✅ No errors
- ✅ "Parent/Child properly linked!" message

---

## Test 2: Verify in Dataverse UI

**Objective:** Confirm records exist and are linked in Dataverse

**Steps:**

1. Open Power Apps / Dataverse
2. Navigate to `mdm_articlerelationship` table
3. Find the relationship record created (use timestamp in name)
4. Verify:
   - Parent Article lookup shows Article 1
   - Child Article lookup shows Article 2

**Success Criteria:**
- ✅ Relationship record exists
- ✅ Parent Article field populated correctly
- ✅ Child Article field populated correctly

---

## Test 3: Environment Safety

**Objective:** Verify PROD environment shows warning

**Command:**
```bash
python scripts/article_sequential_create.py --env=PROD
```

**Expected Output:**
```
⚠️  Target: PROD (https://org.crm.dynamics.com/)
🚨 WARNING: PRODUCTION environment!

Proceed? (yes/no): 
```

**Success Criteria:**
- ✅ Warning message displayed
- ✅ Confirmation prompt appears
- ✅ Typing "no" aborts execution

---

## Test 4: Metadata Discovery

**Objective:** Verify navigation property discovery works

**Command:**
```bash
python scripts/discover_nav_props.py
```

**Expected Output:**
```
✅ Authenticated

================================================================================
MANY-TO-ONE RELATIONSHIPS FROM mdm_articlerelationship
================================================================================

📌 Schema Name: mdm_articlerelationship_ParentArticle_mdm_article
   Nav Prop on Relationship: mdm_ParentArticle

📌 Schema Name: mdm_articlerelationship_ChildArticle_mdm_article
   Nav Prop on Relationship: mdm_ChildArticle

================================================================================
ALTERNATE KEYS ON mdm_article
================================================================================

🔑 Key: mdm_KeyItemCode
   Attributes: ['mdm_itemcode']
```

**Success Criteria:**
- ✅ Navigation properties listed
- ✅ Shows `mdm_ParentArticle` and `mdm_ChildArticle`
- ✅ Alternate keys displayed

---

## Test 5: Error Handling

**Objective:** Verify helpful error messages

### Test 5a: Invalid Environment

**Command:**
```bash
python scripts/article_sequential_create.py --env=INVALID
```

**Expected:**
```
❌ Environment 'INVALID' not found. Available: ['DEV', 'PROD']
```

### Test 5b: Network Error

**Setup:** Disconnect from network

**Expected:**
```
❌ Auth error: [connection error message]
```

---

## Test 6: Idempotency

**Objective:** Verify running twice creates new records (timestamps ensure uniqueness)

**Command:**
```bash
python scripts/article_sequential_create.py --env=DEV --auto-confirm
python scripts/article_sequential_create.py --env=DEV --auto-confirm
```

**Expected:**
- First run: 3 new records
- Second run: 3 NEW records (different GUIDs, different article IDs)

**Success Criteria:**
- ✅ No "duplicate key" errors
- ✅ Each run creates fresh records

---

## Test 6b: Alternate Key Approach (NO GUID!) ✨

**Objective:** Create articles + relationship using business keys instead of GUIDs

**Command:**
```bash
python scripts/article_alternate_key_create.py --env=DEV --auto-confirm
```

**Expected Output:**
```
======================================================================
🚀 ALTERNATE KEY APPROACH - NO GUID NEEDED!
======================================================================

📌 Manager's Concern Addressed:
   ✓ No need to READ GUIDs
   ✓ No need to STORE response
   ✓ Reference by BUSINESS KEY instead!

🔑 Business Keys (known upfront):
   Parent Article: mdm_itemcode='PARENT_20260107202616'
   Child Article:  mdm_itemcode='CHILD_20260107202616'

...

✅ SUCCESS! All 3 records created and linked!
```

**Success Criteria:**
- ✅ Articles created with known business keys
- ✅ Relationship uses `mdm_itemcode` binding (not GUID!)
- ✅ No GUID extraction or storage needed
- ✅ Parent/Child properly linked

---

## Test 7: Verify No Read Operations

**Objective:** Confirm ZERO read API calls

**Method:** Use browser dev tools or Fiddler to trace network

**Expected Traffic:**
```
POST /api/data/v9.2/mdm_articles           (Article 1)
POST /api/data/v9.2/mdm_articles           (Article 2)
POST /api/data/v9.2/mdm_articlerelationships  (Relationship)
```

**NOT Expected:**
```
GET /api/data/v9.2/mdm_articles(...)       ❌ Should not exist
```

**Success Criteria:**
- ✅ Only POST requests
- ✅ No GET requests for articles
- ✅ GUIDs extracted from response headers only

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| "Undeclared property" | Wrong nav prop name | Use PascalCase: `mdm_ParentArticle` |
| Authentication failed | Invalid credentials | Check `.env` file |
| "Resource not found" | Bad GUID | Check GUID extraction logic |
| Connection timeout | Network issue | Check VPN/firewall |
| 403 Forbidden | Insufficient permissions | Check app registration permissions |

---

## Test Summary Checklist

- [ ] Test 1: Sequential create with GUID binding
- [ ] Test 2: Verify in Dataverse UI
- [ ] Test 3: Environment safety (PROD warning)
- [ ] Test 4: Metadata discovery
- [ ] Test 5: Error handling
- [ ] Test 6: Idempotency (multiple runs)
- [ ] Test 6b: Alternate key approach (NO GUID!) ✨
- [ ] Test 7: No read operations (network trace)
