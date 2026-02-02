#!/usr/bin/env python3
"""
Test script for custom-api-product.py

This script runs basic validation tests on the product API implementation
to ensure the metadata-driven updates are working correctly.

Author: GitHub Copilot
Date: 2026-02-02
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Test data - sample article IDs and alternate keys for testing
TEST_CASES = {
    "guid_test": {
        "description": "Test GUID format validation",
        "input": "12345678-1234-1234-1234-123456789abc",
        "expected": "Valid GUID format"
    },
    "aimscode_test": {
        "description": "Test AIMS code alternate key",
        "input": "aimscode:AIMS12345",
        "expected": "Valid alternate key format"
    },
    "itemcode_test": {
        "description": "Test Item Code alternate key", 
        "input": "itemcode:ITEM98765",
        "expected": "Valid alternate key format"
    },
    "barcode_test": {
        "description": "Test Barcode alternate key",
        "input": "barcode:1234567890123",
        "expected": "Valid alternate key format"
    }
}

def test_imports():
    """Test if all required imports are available"""
    print("Testing imports...")
    try:
        import requests
        import msal
        from dotenv import load_dotenv
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        return False

def test_script_syntax():
    """Test if the script has valid Python syntax"""
    print("Testing script syntax...")
    script_path = Path(__file__).parent / "scripts" / "custom-api-product.py"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "py_compile", str(script_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Script syntax is valid")
            return True
        else:
            print(f"✗ Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error checking syntax: {e}")
        return False

def test_help_output():
    """Test if the script can display help without errors"""
    print("Testing help output...")
    script_path = Path(__file__).parent / "scripts" / "custom-api-product.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ Help output works correctly")
            if "Article/Product details" in result.stdout:
                print("✓ Help text mentions Article/Product (updated correctly)")
            return True
        else:
            print(f"✗ Help output error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Help output timed out")
        return False
    except Exception as e:
        print(f"✗ Error testing help: {e}")
        return False

def validate_metadata_mappings():
    """Validate that field mappings align with metadata analysis"""
    print("Validating metadata field mappings...")
    
    # Read the script to check field definitions
    script_path = Path(__file__).parent / "scripts" / "custom-api-product.py"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key field updates
        required_fields = [
            "mdm_articleid",
            "mdm_article_id", 
            "mdm_aimscode",
            "mdm_itemcode",
            "mdm_barcode",
            "mdm_articledescription",
            "_mdm_brand_value",
            "_mdm_articlestatus_value"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if not missing_fields:
            print("✓ All required metadata fields are present")
            return True
        else:
            print(f"✗ Missing fields: {', '.join(missing_fields)}")
            return False
            
    except Exception as e:
        print(f"✗ Error validating metadata: {e}")
        return False

def validate_alternate_keys():
    """Validate alternate key configurations"""
    print("Validating alternate key configurations...")
    
    script_path = Path(__file__).parent / "scripts" / "custom-api-product.py"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for updated alternate keys based on metadata analysis
        expected_keys = [
            '"aimscode": "mdm_aimscode"',
            '"itemcode": "mdm_itemcode"', 
            '"barcode": "mdm_barcode"',
            '"articledescription": "mdm_articledescription"'
        ]
        
        missing_keys = []
        for key in expected_keys:
            if key not in content:
                missing_keys.append(key)
        
        if not missing_keys:
            print("✓ All alternate keys are properly configured")
            return True
        else:
            print(f"✗ Missing alternate keys: {', '.join(missing_keys)}")
            return False
            
    except Exception as e:
        print(f"✗ Error validating alternate keys: {e}")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("="*70)
    print(" CUSTOM-API-PRODUCT.PY VALIDATION TESTS")
    print("="*70)
    
    tests = [
        test_imports,
        test_script_syntax,
        test_help_output,
        validate_metadata_mappings,
        validate_alternate_keys
    ]
    
    results = []
    for test in tests:
        print(f"\n[TEST] {test.__name__}")
        print("-" * 50)
        result = test()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("="*70)
    print(" TEST RESULTS SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The product API is ready for use.")
        print("\nNext steps:")
        print("1. Ensure .env file is configured with proper credentials")
        print("2. Test with a real article/product GUID or alternate key")
        print("3. Run: python custom-api-product.py --help")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)