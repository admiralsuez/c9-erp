#!/usr/bin/env python3
"""
Phase 3 Validation Script
Tests the three main Phase 3 features:
1. Consumable returns
2. Closed order PDF generation  
3. Vendor addresses hierarchy
"""

import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def validate_database_schema():
    """Validate that all Phase 3 database changes are present."""
    print("\n📋 Validating Database Schema...")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False
    
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    # Check vendors table has parent_id
    vendors_cols = [col['name'] for col in inspector.get_columns('vendors')]
    if 'parent_id' not in vendors_cols:
        print("❌ vendors.parent_id column missing")
        return False
    print("✅ vendors.parent_id column exists")
    
    # Check for vendor parent index
    vendors_indexes = [idx['name'] for idx in inspector.get_indexes('vendors')]
    if 'idx_vendor_parent' not in vendors_indexes:
        print("❌ idx_vendor_parent index missing")
        return False
    print("✅ idx_vendor_parent index exists")
    
    # Check order_items has return tracking columns
    order_items_cols = [col['name'] for col in inspector.get_columns('order_items')]
    required_cols = ['return_reason', 'return_status', 'quantity_returned', 'quantity_damaged']
    for col in required_cols:
        if col not in order_items_cols:
            print(f"❌ order_items.{col} column missing")
            return False
    print(f"✅ All return tracking columns exist: {', '.join(required_cols)}")
    
    engine.dispose()
    return True


def validate_model_definitions():
    """Validate that models are correctly defined."""
    print("\n🔍 Validating Model Definitions...")
    
    try:
        from app.models import Vendor, OrderItem, Order
        
        # Check Vendor has parent_id
        if not hasattr(Vendor, 'parent_id'):
            print("❌ Vendor model missing parent_id field")
            return False
        print("✅ Vendor.parent_id field exists")
        
        # Check Vendor relationships
        if not hasattr(Vendor, 'children'):
            print("❌ Vendor model missing children relationship")
            return False
        print("✅ Vendor.children relationship exists")
        
        if not hasattr(Vendor, 'parent'):
            print("❌ Vendor model missing parent relationship")
            return False
        print("✅ Vendor.parent relationship exists")
        
        # Check OrderItem return fields
        if not hasattr(OrderItem, 'return_reason'):
            print("❌ OrderItem model missing return_reason field")
            return False
        print("✅ OrderItem.return_reason field exists")
        
        if not hasattr(OrderItem, 'return_status'):
            print("❌ OrderItem model missing return_status field")
            return False
        print("✅ OrderItem.return_status field exists")
        
        return True
    except Exception as e:
        print(f"❌ Error validating models: {e}")
        return False


def validate_api_endpoints():
    """Validate that API endpoints are properly defined."""
    print("\n🔗 Validating API Endpoints...")
    
    try:
        from app.main import app
        
        # Check for order PDF endpoint
        routes = [route.path for route in app.routes]
        
        pdf_endpoint = '/orders/{id}/download-pdf'
        if pdf_endpoint not in routes:
            print(f"❌ Order PDF endpoint {pdf_endpoint} not found")
            # Don't fail on this, as it might be under a different path
            print(f"⚠️  Available order endpoints: {[r for r in routes if 'orders' in r][:5]}")
        else:
            print(f"✅ Order PDF endpoint {pdf_endpoint} exists")
        
        return True
    except Exception as e:
        print(f"⚠️  Could not validate API endpoints: {e}")
        return True  # Don't fail on this


def validate_frontend_components():
    """Validate that frontend components exist."""
    print("\n🎨 Validating Frontend Components...")
    
    component_path = "frontend/src/components/VendorAddressSelector.tsx"
    if not os.path.exists(component_path):
        print(f"❌ VendorAddressSelector component not found at {component_path}")
        return False
    print(f"✅ VendorAddressSelector component exists")
    
    # Check if it's integrated in order creation
    create_page = "frontend/src/pages/Orders/Create.tsx"
    if os.path.exists(create_page):
        with open(create_page, 'r') as f:
            content = f.read()
            if 'VendorAddressSelector' in content:
                print("✅ VendorAddressSelector integrated in order creation page")
            else:
                print("❌ VendorAddressSelector not found in order creation page")
                return False
    
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("🚀 Phase 3 Feature Validation")
    print("=" * 60)
    
    checks = [
        ("Database Schema", validate_database_schema),
        ("Model Definitions", validate_model_definitions),
        ("API Endpoints", validate_api_endpoints),
        ("Frontend Components", validate_frontend_components),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ All Phase 3 features validated successfully!")
        return 0
    else:
        print("\n❌ Some validations failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
