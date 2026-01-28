# Scripts Directory

Utility scripts for Dataverse operations and data export.

## Available Scripts

### 1. Entity Metadata Exporter
**File**: `entity_metadata_exporter.py`

Export complete entity metadata and save to files.

**Usage**:
```bash
python scripts/entity_metadata_exporter.py <entity_name> [output_file] [--record-id GUID]
```

**Examples**:
```bash
# Basic metadata export
python scripts/entity_metadata_exporter.py lmdm_location

# Export as JSON
python scripts/entity_metadata_exporter.py lmdm_location metadata.json

# Include sample record
python scripts/entity_metadata_exporter.py lmdm_location report.txt --record-id a1b2c3d4-...
```

**Output**:
- `{entity}_metadata.txt` - Human-readable report with all attributes and relationships
- `{entity}_metadata.json` - Raw JSON response for integration/automation

**Perfect for**:
- ✅ ETL teams - complete field and relationship documentation
- ✅ Data analysts - understand entity structure
- ✅ Developers - reference implementation details
- ✅ Documentation - permanent reference of entity schema

See [ENTITY_METADATA_EXPORTER_GUIDE.md](ENTITY_METADATA_EXPORTER_GUIDE.md) for detailed guide.

---

## Other Scripts

### Deep Insert POC
**File**: `article_deep_insert_poc.py`

Proof of concept for deep insert operations with nested records.

### Batch Upsert
**File**: `article_batch_upsert.py`

Batch upsert operations for bulk data updates.

### Entity Discovery
**File**: `discover_nav_props.py`

Discover navigation properties and relationships.

### Sequential Operations
**File**: `article_sequential_create.py`

Create records with dependencies in sequence.

### Multiple Children
**File**: `article_multiple_children.py`

Deep insert with multiple child records.

---

## Quick Command Reference

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/macOS

# Run entity metadata exporter
python scripts/entity_metadata_exporter.py lmdm_location

# Run with JSON output
python scripts/entity_metadata_exporter.py lmdm_location output.json

# Help
python scripts/entity_metadata_exporter.py
```

---

## Requirements
- Python 3.7+
- Virtual environment activated
- `.env` file with Dataverse credentials
- All dependencies from `requirements.txt` installed

```bash
pip install -r requirements.txt
```

---

## Documentation
- [Entity Metadata Exporter Guide](ENTITY_METADATA_EXPORTER_GUIDE.md)
- [Deep Insert Implementation](docs/DEEP_INSERT_IMPLEMENTATION.md)
- [Batch Upsert Guide](docs/BATCH_UPSERT_GUIDE.md)

---

## Support
For issues:
1. Check `.env` file is properly configured
2. Verify authentication credentials
3. Review error messages in script output
4. Check generated JSON output for API response details
