#!/usr/bin/env python3
"""
Debug script to check column structure
"""

import pandas as pd
from data_cleaner import LeadsDataCleaner

def debug_columns():
    """Debug the column structure"""
    print("🔍 Debugging Column Structure...")
    
    try:
        # Initialize cleaner
        cleaner = LeadsDataCleaner()
        
        # Test loading data
        print("📁 Loading Excel data...")
        df = cleaner.load_excel_data("Leads sheet for Geetika - BUKMUK.xlsx")
        print(f"✅ Loaded data: {df.shape}")
        print(f"📋 Original columns: {list(df.columns)}")
        
        # Test column cleaning
        print("\n🧹 Testing column cleaning...")
        df_cleaned_cols = cleaner.clean_column_names(df)
        print(f"✅ Columns cleaned: {df_cleaned_cols.shape}")
        print(f"📋 Cleaned columns: {list(df_cleaned_cols.columns)}")
        
        # Check specific columns
        print("\n🔍 Checking specific columns:")
        for col in ['full_name', 'phone_number', 'email', 'city']:
            if col in df_cleaned_cols.columns:
                col_data = df_cleaned_cols[col]
                print(f"  {col}: {type(col_data)} - Shape: {col_data.shape if hasattr(col_data, 'shape') else 'N/A'}")
                if hasattr(col_data, 'head'):
                    if isinstance(col_data, pd.DataFrame):
                        print(f"    Sample: {col_data.head(3).to_dict('records')}")
                    else:
                        print(f"    Sample: {col_data.head(3).tolist()}")
            else:
                print(f"  {col}: NOT FOUND")
        
        # Check for duplicate column names
        print("\n🔍 Checking for duplicate column names:")
        col_counts = {}
        for col in df_cleaned_cols.columns:
            if isinstance(col, str):
                base_col = col.split('_')[0] if '_' in col else col
                col_counts[base_col] = col_counts.get(base_col, 0) + 1
            else:
                print(f"  Warning: Non-string column name: {col} (type: {type(col)})")
        
        for base_col, count in col_counts.items():
            if count > 1:
                print(f"  {base_col}: {count} columns")
                matching_cols = [c for c in df_cleaned_cols.columns if isinstance(c, str) and (c.startswith(base_col + '_') or c == base_col)]
                print(f"    Columns: {matching_cols}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_columns()
    if success:
        print("\n🎉 Column debug completed successfully!")
    else:
        print("\n⚠️ Column debug failed. Check errors above.")
