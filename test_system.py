#!/usr/bin/env python3
"""
Test script for Bumuk Library CRM System
"""

import pandas as pd
from data_cleaner import LeadsDataCleaner
from lead_manager import LeadManager
import os

def test_data_cleaner():
    """Test the data cleaning functionality"""
    print("🧪 Testing Data Cleaner...")
    
    try:
        # Initialize cleaner
        cleaner = LeadsDataCleaner()
        
        # Test loading data
        print("📁 Loading Excel data...")
        df = cleaner.load_excel_data("Leads sheet for Geetika - BUKMUK.xlsx")
        print(f"✅ Loaded data: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Test cleaning
        print("🧹 Cleaning data...")
        cleaned_df = cleaner.clean_all_data("Leads sheet for Geetika - BUKMUK.xlsx")
        print(f"✅ Cleaned data: {cleaned_df.shape}")
        
        # Get summary
        summary = cleaner.get_cleaning_summary()
        print(f"📊 Total records: {summary['total_records']}")
        print(f"🔧 Cleaning log: {len(summary['cleaning_log'])} steps completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Data cleaner test failed: {str(e)}")
        return False

def test_lead_manager():
    """Test the lead management functionality"""
    print("\n🧪 Testing Lead Manager...")
    
    try:
        # Initialize manager
        manager = LeadManager()
        
        # Test loading leads
        print("📥 Loading leads...")
        leads_df = manager.load_cleaned_leads("Leads sheet for Geetika - BUKMUK.xlsx")
        print(f"✅ Loaded {len(leads_df)} leads")
        
        # Test sales team assignment
        print("👥 Assigning leads to sales team...")
        sales_team = ["John", "Sarah", "Mike"]
        assigned_leads = manager.assign_leads_to_sales_team(sales_team)
        print(f"✅ Assigned leads to {len(sales_team)} team members")
        
        # Test pipeline summary
        print("📊 Getting pipeline summary...")
        summary = manager.get_sales_pipeline_summary()
        print(f"✅ Pipeline summary: {len(summary)} metrics")
        
        # Test lead status update
        print("📝 Testing lead status update...")
        if len(leads_df) > 0:
            success = manager.update_lead_status(0, "Initial Contact", "Test update")
            print(f"✅ Status update: {'Success' if success else 'Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lead manager test failed: {str(e)}")
        return False

def test_export():
    """Test export functionality"""
    print("\n🧪 Testing Export Functionality...")
    
    try:
        # Initialize manager
        manager = LeadManager()
        
        # Load data
        leads_df = manager.load_cleaned_leads("Leads sheet for Geetika - BUKMUK.xlsx")
        
        # Test Excel export
        print("📤 Testing Excel export...")
        excel_file = manager.export_leads_report("test_export.xlsx")
        print(f"✅ Excel export: {excel_file}")
        
        # Test CSV export
        print("📤 Testing CSV export...")
        csv_file = manager.export_leads_report("test_export.csv", "csv")
        print(f"✅ CSV export: {csv_file}")
        
        # Clean up test files
        if os.path.exists("test_export.xlsx"):
            os.remove("test_export.xlsx")
        if os.path.exists("test_export.csv"):
            os.remove("test_export.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ Export test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Bumuk Library CRM System Tests...\n")
    
    tests = [
        ("Data Cleaner", test_data_cleaner),
        ("Lead Manager", test_lead_manager),
        ("Export Functionality", test_export)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📋 Test Results Summary:")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("=" * 40)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
