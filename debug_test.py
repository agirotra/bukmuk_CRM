#!/usr/bin/env python3
"""
Debug script to isolate the pandas error
"""

import pandas as pd
import numpy as np
from data_cleaner import LeadsDataCleaner

def debug_data_cleaner():
    """Debug the data cleaner step by step"""
    print("🔍 Debugging Data Cleaner...")
    
    try:
        # Initialize cleaner
        cleaner = LeadsDataCleaner()
        
        # Test loading data
        print("📁 Loading Excel data...")
        df = cleaner.load_excel_data("Leads sheet for Geetika - BUKMUK.xlsx")
        print(f"✅ Loaded data: {df.shape}")
        
        # Test column cleaning
        print("🧹 Testing column cleaning...")
        df_cleaned_cols = cleaner.clean_column_names(df)
        print(f"✅ Columns cleaned: {df_cleaned_cols.shape}")
        
        # Test phone cleaning
        print("📱 Testing phone cleaning...")
        if 'phone_number' in df_cleaned_cols.columns:
            df_phone_cleaned = cleaner.clean_phone_numbers(df_cleaned_cols)
            print(f"✅ Phone cleaned: {df_phone_cleaned.shape}")
        else:
            print("⚠️ No phone_number column found")
            df_phone_cleaned = df_cleaned_cols
        
        # Test email cleaning
        print("📧 Testing email cleaning...")
        if 'email' in df_phone_cleaned.columns:
            df_email_cleaned = cleaner.clean_emails(df_phone_cleaned)
            print(f"✅ Email cleaned: {df_email_cleaned.shape}")
        else:
            print("⚠️ No email column found")
            df_email_cleaned = df_phone_cleaned
        
        # Test name cleaning
        print("👤 Testing name cleaning...")
        if 'full_name' in df_email_cleaned.columns:
            df_name_cleaned = cleaner.clean_names(df_email_cleaned)
            print(f"✅ Names cleaned: {df_name_cleaned.shape}")
        else:
            print("⚠️ No full_name column found")
            df_name_cleaned = df_email_cleaned
        
        # Test address cleaning
        print("🏠 Testing address cleaning...")
        df_address_cleaned = cleaner.clean_addresses(df_name_cleaned)
        print(f"✅ Addresses cleaned: {df_address_cleaned.shape}")
        
        # Test duplicate removal
        print("🔄 Testing duplicate removal...")
        try:
            df_no_duplicates = cleaner.remove_duplicates(df_address_cleaned)
            print(f"✅ Duplicates removed: {df_no_duplicates.shape}")
        except Exception as e:
            print(f"❌ Duplicate removal failed: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test metadata addition
        print("📊 Testing metadata addition...")
        df_with_metadata = cleaner.add_metadata(df_no_duplicates)
        print(f"✅ Metadata added: {df_with_metadata.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_data_cleaner()
    if success:
        print("🎉 Debug completed successfully!")
    else:
        print("⚠️ Debug failed. Check errors above.")
