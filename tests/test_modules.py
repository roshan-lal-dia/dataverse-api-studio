#!/usr/bin/env python3
"""
Test script to verify modular architecture without Dataverse connection
Tests utility modules: validators, formatters, excel_processor, json_builder, schema_cache, template_manager
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import DataTypeValidator
from utils.formatters import DataFormatter
from utils.schema_cache import SchemaCache
from utils.template_manager import TemplateManager
from utils.config import Config


def test_validators():
    """Test data type validators"""
    print("Testing Validators...")
    
    validator = DataTypeValidator()
    
    # Test string
    is_valid, msg = validator.validate_string("Hello")
    assert is_valid, f"String validation failed: {msg}"
    
    # Test integer
    is_valid, msg = validator.validate_integer("123")
    assert is_valid, f"Integer validation failed: {msg}"
    
    is_valid, msg = validator.validate_integer("abc")
    assert not is_valid, "Integer should fail for non-numeric"
    
    # Test GUID
    is_valid, msg = validator.validate_guid("550e8400-e29b-41d4-a716-446655440000")
    assert is_valid, f"GUID validation failed: {msg}"
    
    is_valid, msg = validator.validate_guid("invalid-guid")
    assert not is_valid, "GUID should fail for invalid format"
    
    # Test date
    is_valid, msg = validator.validate_date("2024-01-15")
    assert is_valid, f"Date validation failed: {msg}"
    
    print("✅ Validators passed")


def test_formatters():
    """Test data formatters"""
    print("Testing Formatters...")
    
    formatter = DataFormatter()
    
    # Test string
    result = formatter.format_string("  Hello  ")
    assert result == "Hello", "String formatting failed"
    
    # Test integer
    result = formatter.format_integer("123")
    assert result == 123, "Integer formatting failed"
    
    # Test boolean
    result = formatter.format_boolean("true")
    assert result is True, "Boolean formatting failed"
    
    result = formatter.format_boolean("no")
    assert result is False, "Boolean formatting failed"
    
    # Test date
    result = formatter.format_date("2024-01-15")
    assert result == "2024-01-15", "Date formatting failed"
    
    # Test datetime
    result = formatter.format_datetime("2024-01-15 14:30:00")
    assert result == "2024-01-15T14:30:00Z", "DateTime formatting failed"
    
    # Test GUID
    result = formatter.format_guid("{550E8400-E29B-41D4-A716-446655440000}")
    assert result == "550e8400-e29b-41d4-a716-446655440000", "GUID formatting failed"
    
    print("✅ Formatters passed")


def test_schema_cache():
    """Test schema caching"""
    print("Testing Schema Cache...")
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SchemaCache(Path(temp_dir))
        
        # Test set and get
        test_data = {"entities": ["account", "contact"]}
        cache.set("test_key", test_data)
        
        retrieved = cache.get("test_key")
        assert retrieved == test_data, "Cache get/set failed"
        
        # Test cache info
        info = cache.get_cache_info("test_key")
        assert info is not None, "Cache info failed"
        assert not info["is_expired"], "Cache should not be expired"
        
        # Test invalidation
        cache.invalidate("test_key")
        retrieved = cache.get("test_key")
        assert retrieved is None, "Cache invalidation failed"
    
    print("✅ Schema Cache passed")


def test_template_manager():
    """Test template manager"""
    print("Testing Template Manager...")
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TemplateManager(Path(temp_dir))
        
        # Create CRUD template
        template = manager.create_crud_template(
            "CREATE",
            "account",
            {"name": "${company_name}", "industry": "Technology"}
        )
        
        # Save template
        success = manager.save_template("test_template", template)
        assert success, "Template save failed"
        
        # Load template
        loaded = manager.load_template("test_template")
        assert loaded is not None, "Template load failed"
        assert loaded["operation"] == "CREATE", "Template data incorrect"
        
        # Extract placeholders
        placeholders = manager.extract_placeholders(template)
        assert "company_name" in placeholders, "Placeholder extraction failed"
        
        # Fill placeholders
        filled = manager.fill_placeholders(template, {"company_name": "Contoso"})
        assert filled["data"]["name"] == "Contoso", "Placeholder fill failed"
        
        # List templates
        templates = manager.list_templates()
        assert "test_template" in templates, "Template listing failed"
        
        # Delete template
        deleted = manager.delete_template("test_template")
        assert deleted, "Template deletion failed"
    
    print("✅ Template Manager passed")


def test_config():
    """Test configuration"""
    print("Testing Config...")
    
    config = Config()
    
    # Test environment extraction (will be empty in CI, but shouldn't error)
    envs = config.get_available_environments()
    assert isinstance(envs, dict), "Environment extraction failed"
    
    # Test directory creation
    cache_dir = config.get_cache_directory()
    assert cache_dir.exists(), "Cache directory creation failed"
    
    templates_dir = config.get_templates_directory()
    assert templates_dir.exists(), "Templates directory creation failed"
    
    print("✅ Config passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Dataverse API Studio - Modular Architecture")
    print("=" * 60)
    print()
    
    try:
        test_validators()
        test_formatters()
        test_schema_cache()
        test_template_manager()
        test_config()
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Create .env file with credentials")
        print("2. Run: python main.py")
        print("3. Test Excel mapper with sample data")
        print("4. Test metadata caching")
        print("5. Test template save/load")
        
        return 0
    
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
