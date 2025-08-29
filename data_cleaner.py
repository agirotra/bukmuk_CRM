import pandas as pd
import numpy as np
import re
from datetime import datetime
import logging
import openai
import os
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeadsDataCleaner:
    """
    Comprehensive data cleaning class for Bumuk Library leads data
    """
    
    def __init__(self):
        self.cleaned_data = None
        self.cleaning_log = []
        
    def load_excel_data(self, file_path, sheet_name=None):
        """
        Load data from Excel file - can load specific sheet or all sheets
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Available sheets: {sheet_names}")
            
            if sheet_name:
                if sheet_name not in sheet_names:
                    raise ValueError(f"Sheet '{sheet_name}' not found. Available sheets: {sheet_names}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                logger.info(f"Loaded sheet: {sheet_name}")
            else:
                # Load all sheets and combine them
                all_dfs = []
                for sheet in sheet_names:
                    try:
                        sheet_df = pd.read_excel(file_path, sheet_name=sheet)
                        if not sheet_df.empty:
                            # Ensure all columns are Series, not DataFrames
                            for col in sheet_df.columns:
                                if isinstance(sheet_df[col], pd.DataFrame):
                                    # If a column is a DataFrame, flatten it
                                    logger.warning(f"Column '{col}' in sheet '{sheet}' is a DataFrame, flattening...")
                                    # Take the first column of the DataFrame
                                    sheet_df[col] = sheet_df[col].iloc[:, 0]
                            
                            sheet_df['source_sheet'] = sheet
                            all_dfs.append(sheet_df)
                            logger.info(f"Loaded sheet '{sheet}' with {len(sheet_df)} rows")
                    except Exception as e:
                        logger.warning(f"Could not load sheet '{sheet}': {str(e)}")
                
                if not all_dfs:
                    raise ValueError("No valid data found in any sheet")
                
                # Standardize column names before concatenation to avoid misalignment
                logger.info("Standardizing column names before concatenation...")
                standardized_dfs = []
                
                for sheet_df in all_dfs:
                    # Create a standardized version of each sheet
                    std_df = pd.DataFrame()
                    
                    # Map columns to standard names based on content and position
                    for col in sheet_df.columns:
                        col_str = str(col).lower().strip()
                        
                        # Map to standard column names
                        if any(name in col_str for name in ['name', 'full_name', 'first_name', 'last_name']):
                            std_df['full_name'] = sheet_df[col]
                        elif any(name in col_str for name in ['phone', 'mobile', 'telephone', 'contact', 'number']):
                            std_df['phone_number'] = sheet_df[col]
                        elif any(name in col_str for name in ['email', 'e-mail', 'mail']):
                            std_df['email'] = sheet_df[col]
                        elif any(name in col_str for name in ['city', 'town', 'location']):
                            std_df['city'] = sheet_df[col]
                        elif any(name in col_str for name in ['date', 'created', 'timestamp', 'contacted']):
                            std_df['lead_date'] = sheet_df[col]
                        elif any(name in col_str for name in ['status', 'lead_status', 'stage', 'response']):
                            std_df['status'] = sheet_df[col]
                        elif any(name in col_str for name in ['source', 'lead_source', 'origin']):
                            std_df['lead_source'] = sheet_df[col]
                        elif any(name in col_str for name in ['age', 'child_age', 'group']):
                            std_df['child_age'] = sheet_df[col]
                        elif any(name in col_str for name in ['type', 'lead_type']):
                            std_df['lead_type'] = sheet_df[col]
                        elif any(name in col_str for name in ['notes', 'comments', 'description']):
                            std_df['notes'] = sheet_df[col]
                        else:
                            # Keep other columns with original names
                            std_df[col] = sheet_df[col]
                    
                    # Special handling for sheets with different structures
                    sheet_name = sheet_df.get('source_sheet', 'unknown')
                    if 'brightr lead' in str(sheet_name):
                        # Handle brightr lead sheet specifically
                        if 'Unnamed: 0' in sheet_df.columns:
                            std_df['full_name'] = sheet_df['Unnamed: 0']
                        if 'Number ' in sheet_df.columns:
                            std_df['phone_number'] = sheet_df['Number ']
                        if 'Any response ' in sheet_df.columns:
                            std_df['status'] = sheet_df['Any response ']
                        if 'Date contacted ' in sheet_df.columns:
                            std_df['lead_date'] = sheet_df['Date contacted ']
                        if 'Age group ' in sheet_df.columns:
                            std_df['child_age'] = sheet_df['Age group ']
                    
                    # Add source sheet information
                    std_df['source_sheet'] = sheet_df.get('source_sheet', 'unknown')
                    standardized_dfs.append(std_df)
                    logger.info(f"Standardized sheet with columns: {list(std_df.columns)}")
                
                # Combine standardized sheets
                df = pd.concat(standardized_dfs, ignore_index=True)
                logger.info(f"Combined {len(standardized_dfs)} standardized sheets into single dataset")
                
                # Ensure all columns are Series, not DataFrames
                logger.info("Checking for DataFrame columns after concatenation...")
                for col in df.columns:
                    if isinstance(df[col], pd.DataFrame):
                        logger.warning(f"Column '{col}' is a DataFrame after concatenation, flattening...")
                        df[col] = df[col].iloc[:, 0]
                
                logger.info("All columns are now Series")
            
            logger.info(f"Final data shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def clean_column_names(self, df):
        """
        Clean and standardize column names, and automatically remove problematic columns
        """
        cleaned_df = df.copy()
        
        # Step 1: Remove completely empty columns
        logger.info("Step 1: Removing completely empty columns...")
        empty_columns = []
        for col in cleaned_df.columns:
            if cleaned_df[col].isna().all() or (cleaned_df[col] == '').all():
                empty_columns.append(col)
        
        if empty_columns:
            logger.info(f"Removing {len(empty_columns)} completely empty columns: {empty_columns}")
            cleaned_df = cleaned_df.drop(columns=empty_columns)
        
        # Step 2: Remove columns with only None/NaN values (95%+ empty)
        logger.info("Step 2: Removing columns with no meaningful data...")
        meaningless_columns = []
        important_columns = ['date', 'created', 'timestamp', 'date_contacted', 'lead_date', 'contact_date']
        
        for col in cleaned_df.columns:
            col_str = str(col).lower().strip()
            
            # Skip important columns even if they have many empty values
            if any(important in col_str for important in important_columns):
                logger.info(f"Preserving important column: {col}")
                continue
                
            # Check if column has only None, NaN, or empty string values
            empty_count = cleaned_df[col].isna().sum() + (cleaned_df[col] == '').sum() + (cleaned_df[col] == 'None').sum()
            if empty_count >= len(cleaned_df) * 0.95:  # 95% or more empty
                meaningless_columns.append(col)
        
        if meaningless_columns:
            logger.info(f"Removing {len(meaningless_columns)} columns with no meaningful data: {meaningless_columns}")
            cleaned_df = cleaned_df.drop(columns=meaningless_columns)
        
        # Step 3: Remove Unnamed columns (pandas artifacts)
        logger.info("Step 3: Removing Unnamed columns...")
        unnamed_columns = [col for col in cleaned_df.columns if 'unnamed' in str(col).lower()]
        if unnamed_columns:
            logger.info(f"Removing {len(unnamed_columns)} unnamed columns: {unnamed_columns}")
            cleaned_df = cleaned_df.drop(columns=unnamed_columns)
        
        # Step 4: Remove special characters and standardize
        cleaned_df.columns = cleaned_df.columns.str.strip()
        cleaned_df.columns = cleaned_df.columns.str.replace('\n', ' ')
        cleaned_df.columns = cleaned_df.columns.str.replace('\r', ' ')
        cleaned_df.columns = cleaned_df.columns.str.replace('\t', ' ')
        
        # Convert to lowercase and replace spaces with underscores
        cleaned_df.columns = cleaned_df.columns.str.lower().str.replace(' ', '_')
        
        # Remove any remaining special characters
        cleaned_df.columns = cleaned_df.columns.str.replace('[^a-zA-Z0-9_]', '', regex=True)
        
        # Handle duplicate column names by adding suffixes
        seen = {}
        new_columns = []
        for col in cleaned_df.columns:
            if col in seen:
                seen[col] += 1
                new_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_columns.append(col)
        cleaned_df.columns = new_columns
        
        # If we still have duplicate column names (which can happen with DataFrames), 
        # ensure uniqueness by adding more specific suffixes
        final_columns = []
        for i, col in enumerate(cleaned_df.columns):
            if col in final_columns:
                final_columns.append(f"{col}_col_{i}")
            else:
                final_columns.append(col)
        cleaned_df.columns = final_columns
        
        # Standardize common column names
        column_mapping = {
            'name': 'full_name',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'phone': 'phone_number',
            'mobile': 'phone_number',
            'telephone': 'phone_number',
            'company': 'company_name',
            'organization': 'company_name',
            'business': 'company_name',
            'address': 'address',
            'city': 'city',
            'state': 'state',
            'country': 'country',
            'zip': 'postal_code',
            'postal_code': 'postal_code',
            'notes': 'notes',
            'comments': 'notes',
            'description': 'notes',
            'source': 'lead_source',
            'origin': 'lead_source',
            'date': 'lead_date',
            'created': 'lead_date',
            'timestamp': 'lead_date',
            'date_contacted': 'contact_date'
        }
        
        # Handle duplicate columns by keeping the first occurrence and renaming others
        for old_name, new_name in column_mapping.items():
            matching_cols = [col for col in cleaned_df.columns if isinstance(col, str) and (col == old_name or col.startswith(old_name + '_'))]
            if len(matching_cols) > 1:
                # Keep the first one with the standard name, rename others
                for i, col in enumerate(matching_cols):
                    if i == 0:
                        cleaned_df = cleaned_df.rename(columns={col: new_name})
                    else:
                        cleaned_df = cleaned_df.rename(columns={col: f"{new_name}_{i+1}"})
            elif len(matching_cols) == 1:
                cleaned_df = cleaned_df.rename(columns={matching_cols[0]: new_name})
        
        # Additional specific mappings for your Excel sheets
        additional_mappings = {
            'name ': 'full_name',
            'email id ': 'email',
            'phone number ': 'phone_number',
            'child age ': 'child_age',
            'city ': 'city',
            'lead type ': 'lead_type',
            'comments ': 'notes',
            'pending action ': 'pending_action',
            'further action comments ': 'further_action',
            'storytelling event - julia donaldson by shefali malhotra ': 'event_name',
            'swati agarwal': 'contact_person',
            'shared details about the library': 'library_details',
            'date': 'lead_date',
            'date contacted ': 'contact_date'
        }
        
        # Apply additional mappings
        for old_name, new_name in additional_mappings.items():
            if old_name in cleaned_df.columns:
                cleaned_df = cleaned_df.rename(columns={old_name: new_name})
        
        # After renaming, check if we have any duplicate column names that could create DataFrames
        logger.info("Checking for duplicate column names after mapping...")
        duplicate_cols = cleaned_df.columns[cleaned_df.columns.duplicated()].tolist()
        if duplicate_cols:
            logger.warning(f"Found duplicate column names after mapping: {duplicate_cols}")
            # Rename duplicates to ensure uniqueness
            seen = {}
            new_columns = []
            for col in cleaned_df.columns:
                if col in seen:
                    seen[col] += 1
                    new_columns.append(f"{col}_dup_{seen[col]}")
                else:
                    seen[col] = 0
                    new_columns.append(col)
            cleaned_df.columns = new_columns
            logger.info("Renamed duplicate columns to ensure uniqueness")
        
        # Final cleanup - remove any remaining problematic columns
        logger.info("Final step: Removing remaining problematic columns...")
        final_columns = []
        for col in cleaned_df.columns:
            # Convert column name to string and check if it's valid
            col_str = str(col)
            
            # Keep columns that have meaningful names and data
            if (isinstance(col, str) and  # Must be string type
                not col_str.startswith('unnamed') and 
                not col_str.startswith('col_') and 
                len(col_str) < 50 and  # Avoid extremely long column names
                cleaned_df[col].notna().sum() > 0):  # At least some non-null values
                final_columns.append(col)
        
        cleaned_df = cleaned_df[final_columns]
        
        logger.info(f"Column cleanup complete. Final columns: {list(cleaned_df.columns)}")
        self.cleaning_log.append("Column names cleaned and standardized")
        return cleaned_df
    
    def clean_phone_numbers(self, df):
        """
        Clean and standardize phone numbers
        """
        if 'phone_number' not in df.columns:
            return df
            
        cleaned_df = df.copy()
        
        def clean_phone(phone):
            # Handle pandas Series vs scalar
            if isinstance(phone, pd.Series):
                return phone
            
            if pd.isna(phone):
                return phone
            
            phone_str = str(phone)
            
            # Remove all non-digit characters
            digits_only = re.sub(r'[^\d]', '', phone_str)
            
            # Handle different phone number formats
            if len(digits_only) == 10:
                return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
            elif len(digits_only) == 11 and digits_only[0] == '1':
                return f"({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
            elif len(digits_only) > 0:
                return digits_only
            else:
                return None
        
        cleaned_df['phone_number'] = cleaned_df['phone_number'].apply(clean_phone)
        self.cleaning_log.append("Phone numbers cleaned and standardized")
        
        return cleaned_df
    
    def clean_emails(self, df):
        """
        Clean and validate email addresses
        """
        if 'email' not in df.columns:
            return df
            
        cleaned_df = df.copy()
        
        def clean_email(email):
            # Handle pandas Series vs scalar
            if isinstance(email, pd.Series):
                return email
            
            if pd.isna(email):
                return email
            
            email_str = str(email).strip().lower()
            
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if re.match(email_pattern, email_str):
                return email_str
            else:
                return None
        
        cleaned_df['email'] = cleaned_df['email'].apply(clean_email)
        self.cleaning_log.append("Email addresses cleaned and validated")
        
        return cleaned_df
    
    def clean_names(self, df):
        """
        Clean and standardize names
        """
        if 'full_name' not in df.columns:
            return df
            
        cleaned_df = df.copy()
        
        def clean_name(name):
            # Handle pandas Series vs scalar
            if isinstance(name, pd.Series):
                return name
            
            if pd.isna(name):
                return name
            
            name_str = str(name).strip()
            
            # Remove extra spaces and standardize
            name_str = re.sub(r'\s+', ' ', name_str)
            name_str = name_str.title()
            
            return name_str
        
        cleaned_df['full_name'] = cleaned_df['full_name'].apply(clean_name)
        
        # Split full name into first and last name if not already present
        if 'first_name' not in cleaned_df.columns:
            # Use vectorized operations instead of apply
            cleaned_df['first_name'] = cleaned_df['full_name'].astype(str).str.split().str[0]
        
        if 'last_name' not in cleaned_df.columns:
            # Use vectorized operations instead of apply
            cleaned_df['last_name'] = cleaned_df['full_name'].astype(str).str.split().str[1:].str.join(' ')
        
        self.cleaning_log.append("Names cleaned and standardized")
        return cleaned_df
    
    def clean_addresses(self, df):
        """
        Clean and standardize addresses
        """
        address_columns = ['address', 'city', 'state', 'country', 'postal_code']
        
        cleaned_df = df.copy()
        
        for col in address_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].apply(
                    lambda x: str(x).strip().title() if pd.notna(x) else None
                )
        
        self.cleaning_log.append("Addresses cleaned and standardized")
        return cleaned_df
    
    def remove_duplicates(self, df):
        """
        Remove duplicate records across all sheets based on multiple criteria
        """
        logger.info("Starting duplicate removal process...")
        cleaned_df = df.copy()
        initial_count = len(cleaned_df)
        logger.info(f"Initial count: {initial_count}")
        
        # Create priority-based duplicate detection keys
        # Priority 1: Phone number (most important)
        # Priority 2: Email (second most important)
        # Priority 3: Full name (fallback)
        
        if 'phone_number' in cleaned_df.columns:
            # Phone number is the primary deduplication field
            cleaned_df['duplicate_key'] = cleaned_df['phone_number'].fillna('')
            logger.info("Using phone number as primary deduplication field")
        elif 'email' in cleaned_df.columns:
            # Email as secondary deduplication field
            cleaned_df['duplicate_key'] = cleaned_df['email'].fillna('')
            logger.info("Using email as deduplication field (phone not available)")
        else:
            # Fallback to name-based duplicate detection
            cleaned_df['duplicate_key'] = cleaned_df['full_name'].fillna('')
            logger.info("Using full name as deduplication field (phone/email not available)")
        
        # Create secondary keys for enhanced duplicate detection
        if 'phone_number' in cleaned_df.columns and 'email' in cleaned_df.columns:
            # Secondary key: email + phone combination for cross-validation
            cleaned_df['secondary_key'] = cleaned_df['email'].fillna('') + '|' + cleaned_df['phone_number'].fillna('')
        elif 'phone_number' in cleaned_df.columns and 'full_name' in cleaned_df.columns:
            # Secondary key: phone + name combination
            cleaned_df['secondary_key'] = cleaned_df['phone_number'].fillna('') + '|' + cleaned_df['full_name'].fillna('')
        elif 'email' in cleaned_df.columns and 'full_name' in cleaned_df.columns:
            # Secondary key: email + name combination
            cleaned_df['secondary_key'] = cleaned_df['email'].fillna('') + '|' + cleaned_df['full_name'].fillna('')
        
        # Remove duplicates, keeping the record with most complete information
        # Prioritize phone numbers and emails heavily in scoring
        def get_completeness_score(row):
            score = 0
            
            # Phone number gets highest weight (40 points)
            if 'phone_number' in row.index and pd.notna(row['phone_number']) and str(row['phone_number']).strip() != '':
                score += 40
            
            # Email gets second highest weight (35 points)
            if 'email' in row.index and pd.notna(row['email']) and str(row['email']).strip() != '':
                score += 35
            
            # Other fields get lower weights
            if 'city' in row.index and pd.notna(row['city']) and str(row['city']).strip() != '':
                score += 15
            
            if 'full_name' in row.index and pd.notna(row['full_name']) and str(row['full_name']).strip() != '':
                score += 10
            
            return score
        
        # Sort by completeness score (descending) and source sheet priority
        cleaned_df['completeness_score'] = cleaned_df.apply(get_completeness_score, axis=1)
        
        # Prioritize certain sheets (you can customize this order)
        sheet_priority = {
            'Main': 1,
            'Primary': 1,
            'Leads': 2,
            'Contacts': 3
        }
        
        def get_sheet_priority(sheet_name):
            for key, priority in sheet_priority.items():
                if key.lower() in str(sheet_name).lower():
                    return priority
            return 999  # Default low priority
        
        # Add sheet priority column
        if 'source_sheet' in cleaned_df.columns:
            cleaned_df['sheet_priority'] = cleaned_df['source_sheet'].apply(get_sheet_priority)
            
            # Sort by completeness score (descending) and sheet priority (ascending)
            cleaned_df = cleaned_df.sort_values(['completeness_score', 'sheet_priority'], ascending=[False, True])
        else:
            # If no source sheet, just sort by completeness score
            cleaned_df = cleaned_df.sort_values(['completeness_score'], ascending=[False])
        
        # Remove duplicates based on duplicate key
        logger.info("Removing duplicates based on duplicate key...")
        cleaned_df = cleaned_df.drop_duplicates(subset=['duplicate_key'], keep='first')
        
        # Clean up temporary columns
        logger.info("Cleaning up temporary columns...")
        if 'duplicate_key' in cleaned_df.columns:
            cleaned_df = cleaned_df.drop(['duplicate_key'], axis=1)
        if 'completeness_score' in cleaned_df.columns:
            cleaned_df = cleaned_df.drop(['completeness_score'], axis=1)
        if 'sheet_priority' in cleaned_df.columns:
            cleaned_df = cleaned_df.drop(['sheet_priority'], axis=1)
        
        removed_count = initial_count - len(cleaned_df)
        if removed_count > 0:
            self.cleaning_log.append(f"Removed {removed_count} duplicate records across all sheets")
        
        return cleaned_df
    
    def add_metadata(self, df):
        """
        Add metadata columns for CRM tracking
        """
        cleaned_df = df.copy()
        
        # Add creation timestamp
        cleaned_df['cleaned_date'] = datetime.now()
        
        # Add lead status
        cleaned_df['lead_status'] = 'New Lead'
        
        # Add tracking columns for follow-ups
        cleaned_df['status_updated_date'] = datetime.now()
        cleaned_df['last_contact_date'] = None
        cleaned_df['follow_up_date'] = None
        cleaned_df['follow_up_count'] = 0
        
        # Add lead score (prioritizing phone and email heavily)
        def calculate_lead_score(row):
            score = 0
            
            # Phone number gets highest weight (40 points) - most important for sales
            if pd.notna(row.get('phone_number', None)) and str(row.get('phone_number', '')).strip() != '':
                score += 40
            
            # Email gets second highest weight (35 points) - second most important
            if pd.notna(row.get('email', None)) and str(row.get('email', '')).strip() != '':
                score += 35
            
            # Other fields get lower weights
            if pd.notna(row.get('city', None)) and str(row.get('city', '')).strip() != '':
                score += 15
            
            if pd.notna(row.get('child_age', None)) or pd.notna(row.get('lead_type', None)):
                score += 10
            
            return score
        
        cleaned_df['lead_score'] = cleaned_df.apply(calculate_lead_score, axis=1)
        
        # Add priority based on score (adjusted for new scoring system)
        def assign_priority(score):
            if score >= 70:  # Phone + Email = 75 points
                return 'High'
            elif score >= 40:  # Phone only = 40 points
                return 'Medium'
            else:
                return 'Low'
        
        cleaned_df['priority'] = cleaned_df['lead_score'].apply(assign_priority)
        
        self.cleaning_log.append("Added metadata columns for CRM tracking")
        return cleaned_df
    
    def setup_openai(self, api_key: Optional[str] = None):
        """
        Setup OpenAI API for AI-powered data enrichment
        """
        if api_key:
            self.openai_api_key = api_key
        else:
            # Try to get from environment, loading .env file if needed
            from dotenv import load_dotenv
            load_dotenv()
            env_api_key = os.getenv('OPENAI_API_KEY')
            if env_api_key:
                self.openai_api_key = env_api_key
            else:
                logger.warning("OpenAI API key not found in .env file. AI features will be disabled.")
                return False
        
        try:
            # Test the API connection using new OpenAI API format
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info("OpenAI API connection successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI API connection failed: {str(e)}")
            return False
    
    def enrich_lead_with_ai(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to enrich lead data with additional insights
        """
        if not hasattr(self, 'openai_api_key') or not self.openai_api_key:
            logger.warning("OpenAI API not configured. Skipping AI enrichment.")
            return lead_data
        
        try:
            # Prepare lead information for AI analysis
            lead_info = f"""
            Lead Information:
            Name: {lead_data.get('full_name', 'N/A')}
            Email: {lead_data.get('email', 'N/A')}
            Phone: {lead_data.get('phone_number', 'N/A')}
            City: {lead_data.get('city', 'N/A')}
            Child Age: {lead_data.get('child_age', 'N/A')}
            Lead Type: {lead_data.get('lead_type', 'N/A')}
            Source Sheet: {lead_data.get('source_sheet', 'N/A')}
            """
            
            prompt = f"""
            Analyze this individual lead data for a library business and provide:
            1. Customer segment (parent, student, professional, senior, family, individual, etc.)
            2. Potential value (Low/Medium/High based on usage patterns and family size)
            3. Recommended engagement strategy
            4. Key library benefits to highlight for this customer type
            
            {lead_info}
            
            Respond in JSON format:
            {{
                "customer_segment": "string",
                "potential_value": "Low/Medium/High",
                "engagement_strategy": "string",
                "library_benefits": ["benefit1", "benefit2", "benefit3"]
            }}
            """
            
            # Use new OpenAI API format
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            try:
                import json
                ai_insights = json.loads(ai_content)
                
                # Add AI insights to lead data
                lead_data['ai_customer_segment'] = ai_insights.get('customer_segment', 'Unknown')
                lead_data['ai_potential_value'] = ai_insights.get('potential_value', 'Medium')
                lead_data['ai_engagement_strategy'] = ai_insights.get('engagement_strategy', 'Standard')
                lead_data['ai_library_benefits'] = '; '.join(ai_insights.get('library_benefits', []))
                
                logger.info(f"AI enrichment completed for {lead_data.get('full_name', 'Unknown')}")
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response")
                
        except Exception as e:
            logger.error(f"AI enrichment failed: {str(e)}")
        
        return lead_data
    
    def enrich_all_leads_with_ai(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich all leads with AI insights
        """
        if not hasattr(self, 'openai_api_key') or not self.openai_api_key:
            logger.warning("OpenAI API not configured. Skipping AI enrichment.")
            return df
        
        logger.info("Starting AI enrichment for all leads...")
        total_leads = len(df)
        
        enriched_data = []
        for idx, row in df.iterrows():
            lead_dict = row.to_dict()
            enriched_lead = self.enrich_lead_with_ai(lead_dict)
            enriched_data.append(enriched_lead)
            
            # Progress update every 5 leads for better visibility
            if (idx + 1) % 5 == 0:
                progress = ((idx + 1) / total_leads) * 100
                logger.info(f"AI Progress: {progress:.1f}% - Processed {idx + 1}/{total_leads} leads")
        
        enriched_df = pd.DataFrame(enriched_data)
        self.cleaning_log.append("AI enrichment completed for all leads")
        logger.info(f"AI enrichment completed for {total_leads} leads!")
        
        return enriched_df
    
    def clean_all_data(self, file_path, enable_ai_enrichment: bool = False):
        """
        Complete data cleaning pipeline with optional AI enrichment
        """
        logger.info("Starting data cleaning process...")
        
        # Load data
        logger.info("Step 1/7: Loading Excel data...")
        df = self.load_excel_data(file_path)
        
        # Apply all cleaning functions
        logger.info("Step 2/7: Cleaning column names...")
        df = self.clean_column_names(df)
        
        logger.info("Step 3/7: Cleaning phone numbers...")
        df = self.clean_phone_numbers(df)
        
        logger.info("Step 4/7: Cleaning emails...")
        df = self.clean_emails(df)
        
        logger.info("Step 5/7: Cleaning names...")
        df = self.clean_names(df)
        
        logger.info("Step 6/7: Cleaning addresses...")
        df = self.clean_addresses(df)
        
        logger.info("Step 7/7: Removing duplicates and adding metadata...")
        df = self.remove_duplicates(df)
        df = self.add_metadata(df)
        
        # AI enrichment if enabled
        if enable_ai_enrichment:
            logger.info("Starting AI enrichment...")
            df = self.enrich_all_leads_with_ai(df)
        
        self.cleaned_data = df
        logger.info("Data cleaning completed successfully!")
        
        return df
    
    def get_cleaning_summary(self):
        """
        Get a summary of the cleaning process
        """
        if self.cleaned_data is None:
            return "No data has been cleaned yet."
        
        summary = {
            'total_records': len(self.cleaned_data),
            'columns': list(self.cleaned_data.columns),
            'cleaning_log': self.cleaning_log,
            'data_types': self.cleaned_data.dtypes.to_dict(),
            'missing_values': self.cleaned_data.isnull().sum().to_dict()
        }
        
        return summary
    
    def export_cleaned_data(self, output_path, format='excel'):
        """
        Export cleaned data to file
        """
        if self.cleaned_data is None:
            raise ValueError("No cleaned data available. Run clean_all_data() first.")
        
        if format.lower() == 'excel':
            self.cleaned_data.to_excel(output_path, index=False)
        elif format.lower() == 'csv':
            self.cleaned_data.to_csv(output_path, index=False)
        else:
            raise ValueError("Unsupported format. Use 'excel' or 'csv'.")
        
        logger.info(f"Cleaned data exported to {output_path}")
        return output_path

# Example usage
if __name__ == "__main__":
    cleaner = LeadsDataCleaner()
    
    # Clean the leads data
    cleaned_df = cleaner.clean_all_data("Leads sheet for Geetika - BUKMUK.xlsx")
    
    # Get summary
    summary = cleaner.get_cleaning_summary()
    print("Cleaning Summary:")
    print(f"Total records: {summary['total_records']}")
    print(f"Columns: {summary['columns']}")
    
    # Export cleaned data
    cleaner.export_cleaned_data("cleaned_leads.xlsx")
