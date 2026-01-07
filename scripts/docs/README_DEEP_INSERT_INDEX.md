# 🗂️ Documentation Index

## 📌 Start Here

| Your Role | Read This First | Time |
|-----------|-----------------|------|
| **Manager/Stakeholder** | [README_DEEP_INSERT.md](README_DEEP_INSERT.md) | 3 min |
| **Developer** | [DEEP_INSERT_IMPLEMENTATION.md](DEEP_INSERT_IMPLEMENTATION.md) | 10 min |
| **QA/Tester** | [DEEP_INSERT_TESTING_GUIDE.md](DEEP_INSERT_TESTING_GUIDE.md) | 10 min |
| **Quick Question** | [DEEP_INSERT_QUICK_REFERENCE.md](DEEP_INSERT_QUICK_REFERENCE.md) | 3 min |

---

## 📚 All Documents

### Overview
| Document | Purpose |
|----------|---------|
| [README_DEEP_INSERT.md](README_DEEP_INSERT.md) | Executive summary, key discoveries |
| [VISUAL_SUMMARY.md](VISUAL_SUMMARY.md) | Architecture diagrams, flow charts |
| [DELIVERABLES_SUMMARY.md](DELIVERABLES_SUMMARY.md) | What was delivered |

### Technical
| Document | Purpose |
|----------|---------|
| [DEEP_INSERT_IMPLEMENTATION.md](DEEP_INSERT_IMPLEMENTATION.md) | Code walkthrough, API details |
| [DEEP_INSERT_QUICK_REFERENCE.md](DEEP_INSERT_QUICK_REFERENCE.md) | Cheat sheet, common patterns |

### Testing & Tracking
| Document | Purpose |
|----------|---------|
| [DEEP_INSERT_TESTING_GUIDE.md](DEEP_INSERT_TESTING_GUIDE.md) | Test procedures, expected outputs |
| [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) | Progress tracking |

---

## 🚀 Quick Start

```bash
# 1. Navigate to project
cd api-studio

# 2. Activate environment
.\.venv\Scripts\Activate.ps1

# 3. Run working POC - Option 1: GUID binding
python scripts/article_sequential_create.py --env=DEV --auto-confirm

# 3. Run working POC - Option 2: Alternate Keys (NO GUID!) ✨
python scripts/article_alternate_key_create.py --env=DEV --auto-confirm

# 4. (Optional) Discover navigation properties
python scripts/discover_nav_props.py
```

---

## 📁 Scripts

| Script | Status | Purpose |
|--------|--------|---------|
| `article_sequential_create.py` | ✅ WORKING | 3 POSTs with GUID binding |
| `article_alternate_key_create.py` | ✅ WORKING | 3 POSTs with Alternate Keys (NO GUID!) ✨ |
| `discover_nav_props.py` | ✅ Utility | Find nav prop names & keys |
| `article_deep_insert_poc.py` | ⚠️ DEPRECATED | Batch approach (linking issues) |

---

## 🔑 Key Information

### Navigation Property Names (PascalCase!)
```python
# Option 1: GUID binding
"mdm_ParentArticle@odata.bind": "/mdm_articles(guid)"
"mdm_ChildArticle@odata.bind": "/mdm_articles(guid)"

# Option 2: Alternate Key binding (NO GUID!) ✨
"mdm_ParentArticle@odata.bind": "/mdm_articles(mdm_itemcode='PARENT001')"
"mdm_ChildArticle@odata.bind": "/mdm_articles(mdm_itemcode='CHILD001')"
```

### Alternate Keys on mdm_article (All Verified!)
- `mdm_itemcode` ✅ Tested & Working
- `mdm_productcode`
- `mdm_supplierarticlecode` + `mdm_supplierid`

### GUID Extraction
```python
guid = response.headers["OData-EntityId"].split("(")[-1].rstrip(")")
```

---

## ✅ Success Criteria

- 3 records created (2 articles + 1 relationship)
- 0 read operations
- Parent/child properly linked in Dataverse UI
- All operations complete in ~3 seconds

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Undeclared property" | Use PascalCase nav prop names |
| Authentication failed | Check .env credentials |
| "Resource not found" | Verify GUID extracted correctly |
| Linking not working | Use `mdm_ParentArticle`, not `mdm_parentarticle` |
