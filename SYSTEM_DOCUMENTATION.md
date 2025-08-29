# 🏛️ Bumuk Library CRM - System Documentation

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [Data Processing Pipeline](#data-processing-pipeline)
4. [Expected Data Formats](#expected-data-formats)
5. [Configuration & Settings](#configuration--settings)
6. [API Integration](#api-integration)
7. [User Interface Guide](#user-interface-guide)
8. [Data Management](#data-management)
9. [Troubleshooting](#troubleshooting)
10. [Development & Customization](#development--customization)

---

## 🎯 System Overview

### **What is the Bumuk Library CRM?**
A comprehensive Customer Relationship Management system designed specifically for library lead management, built with Python and Streamlit. The system automatically processes, cleans, and manages leads from multiple Excel sheets with intelligent data standardization.

### **Key Features**
- 🔄 **Multi-Sheet Excel Processing** - Handles different column formats automatically
- 🧹 **Intelligent Data Cleaning** - Standardizes data across various input formats
- 🤖 **AI-Powered Enrichment** - Enhances leads with ChatGPT API insights
- 📊 **Comprehensive Dashboard** - Multiple views for different use cases
- 💾 **Data Persistence** - Automatic saving and backup system
- 📱 **Responsive Interface** - Works on desktop and mobile devices

---

## 🏗️ Architecture & Components

### **Core Components**

#### **1. Data Cleaner (`data_cleaner.py`)**
- **Purpose**: Handles Excel file loading, data cleaning, and standardization
- **Key Methods**:
  - `load_excel_data()` - Loads and combines multiple Excel sheets
  - `clean_column_names()` - Standardizes column names across sheets
  - `clean_phone_numbers()` - Formats phone numbers consistently
  - `clean_emails()` - Validates and standardizes email addresses
  - `remove_duplicates()` - Eliminates duplicate leads using smart criteria

#### **2. Lead Manager (`lead_manager.py`)**
- **Purpose**: Manages lead lifecycle, status updates, and business logic
- **Key Methods**:
  - `update_lead_status()` - Updates lead status with tracking
  - `get_leads_needing_follow_up()` - Identifies leads requiring attention
  - `assign_leads_to_sales_team()` - Distributes leads among team members
  - `export_leads_report()` - Generates reports in Excel/CSV format

#### **3. CRM Dashboard (`crm_dashboard.py`)**
- **Purpose**: Streamlit web interface for user interaction
- **Key Features**:
  - File upload and processing
  - Interactive lead management
  - Status updates and filtering
  - Analytics and reporting

#### **4. Configuration (`config.py`)**
- **Purpose**: Centralized system configuration
- **Contains**:
  - Lead status definitions
  - Priority levels
  - Follow-up schedules
  - AI configuration

---

## 🔄 Data Processing Pipeline

### **Step-by-Step Data Flow**

#### **Phase 1: Data Loading**
```
Excel File → Multiple Sheets → Individual DataFrames → Column Standardization → Combined Dataset
```

1. **Sheet Detection**: Identifies all sheets in Excel file
2. **Individual Loading**: Loads each sheet as separate DataFrame
3. **Column Standardization**: Maps different column names to standard format
4. **Concatenation**: Combines all sheets into single dataset

#### **Phase 2: Data Cleaning**
```
Raw Data → Column Cleanup → Data Standardization → Duplicate Removal → Metadata Addition
```

1. **Column Cleanup**: Removes empty, unnamed, and problematic columns
2. **Data Standardization**: Cleans phone numbers, emails, names, addresses
3. **Duplicate Removal**: Eliminates duplicates using phone/email priority
4. **Metadata Addition**: Adds lead status, priority, scores, and tracking fields

#### **Phase 3: AI Enrichment (Optional)**
```
Clean Data → OpenAI API → Customer Insights → Enhanced Dataset
```

1. **API Integration**: Connects to ChatGPT API for lead analysis
2. **Intelligent Analysis**: Generates customer segments and engagement strategies
3. **Data Enhancement**: Adds AI-generated insights to each lead

---

## 📊 Expected Data Formats

### **Supported Input Formats**

#### **Standard Library Lead Format**
```csv
full_name,phone_number,email,city,lead_source,lead_type,notes
John Doe,9876543210,john@email.com,Delhi,Website,Hot,Interested in children's books
```

#### **Alternative Formats (Automatically Detected)**
```csv
# Format 1: Quiz/Event Registration
Email Address,Parent Mobile no.,Child Name and Age,City
john@email.com,9876543210,Emma (8 years),Delhi

# Format 2: Contact Forms
Name,Contact Number,Email Address,Location
John Doe,9876543210,john@email.com,Delhi

# Format 3: Custom Formats
Customer Name,Mobile,Email ID,City Location
John Doe,9876543210,john@email.com,Delhi
```

### **Column Mapping Rules**

| **Standard Column** | **Recognized Variations** | **Data Type** | **Required** |
|---------------------|---------------------------|----------------|--------------|
| `full_name` | `name`, `Name `, `Customer Name`, `Child Name and Age` | String | ✅ Yes |
| `phone_number` | `phone`, `mobile`, `Number `, `Phone number `, `Parent Mobile no.` | String/Number | ✅ Yes |
| `email` | `email`, `Email id `, `Email Address` | String | ⚠️ Recommended |
| `city` | `city`, `City `, `Location`, `City Location` | String | ⚠️ Recommended |
| `lead_date` | `date`, `Date`, `Date contacted `, `Timestamp` | Date | ❌ Optional |
| `status` | `status`, `Status`, `Any response ` | String | ❌ Optional |
| `lead_source` | `source`, `Lead source `, `origin` | String | ❌ Optional |

### **Data Quality Requirements**

#### **Minimum Viable Lead**
- **Phone Number**: Must be present and valid
- **Name**: Should be present for identification
- **Email**: Recommended for follow-up communication

#### **Data Validation Rules**
- **Phone Numbers**: Automatically formatted to (XXX) XXX-XXXX
- **Emails**: Basic format validation (user@domain.com)
- **Names**: Title case formatting applied
- **Dates**: Multiple format support (DD/MM/YY, YYYY-MM-DD, etc.)

---

## ⚙️ Configuration & Settings

### **Environment Variables (`.env`)**
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
CRM_NAME=Bumuk Library CRM
CRM_VERSION=1.0.0
```

### **Lead Status Configuration (`config.py`)**
```python
LEAD_STATUSES = [
    'New Lead',           # Initial state
    'Initial Contact',     # First contact made
    'Follow Up 1',        # First follow-up
    'Follow Up 2',        # Second follow-up
    'Follow Up 3',        # Third follow-up
    'Interested',         # Customer shows interest
    'Member',             # Converted to member
    'Lost - No Response', # No response after follow-ups
    'Re-engage Later'     # To be contacted later
]
```

### **Priority Levels**
```python
PRIORITY_LEVELS = ['Low', 'Medium', 'High', 'Urgent']
```

### **Follow-up Schedule**
```python
FOLLOW_UP_SCHEDULE = {
    'New Lead': 2,           # Follow up in 2 days
    'Initial Contact': 3,    # Follow up in 3 days
    'Follow Up 1': 5,        # Follow up in 5 days
    'Follow Up 2': 7,        # Follow up in 7 days
    'Follow Up 3': 14,       # Follow up in 14 days
    'Interested': 7,         # Follow up in 7 days
    'Member': 30,            # Follow up in 30 days
    'Lost - No Response': 90, # Re-engage in 90 days
    'Re-engage Later': 60    # Re-engage in 60 days
}
```

---

## 🤖 API Integration

### **OpenAI ChatGPT Integration**

#### **API Requirements**
- **Version**: OpenAI Python library v1.0.0+
- **Model**: gpt-3.5-turbo or gpt-4
- **Rate Limits**: Respect OpenAI's usage limits

#### **AI Enrichment Fields**
```python
AI_CONFIG = {
    'enrichment_fields': [
        'customer_segment',      # Target audience classification
        'potential_value',       # Estimated customer value
        'engagement_strategy',   # Recommended approach
        'library_benefits'      # Relevant library offerings
    ]
}
```

#### **Sample AI Prompt**
```
Analyze this library lead:
Name: {full_name}
Phone: {phone_number}
Email: {email}
City: {city}

Provide insights on:
1. Customer segment (age group, interests)
2. Potential value to library
3. Engagement strategy
4. Relevant library benefits
```

---

## 🖥️ User Interface Guide

### **Main Dashboard Tabs**

#### **📊 Dashboard Tab**
- **Lead Distribution**: Status-based pie charts
- **Priority Overview**: High/Medium/Low priority breakdown
- **Follow-up Alerts**: Overdue and upcoming follow-ups
- **Quick Actions**: Status updates and assignments

#### **👥 Leads Management Tab**
- **Status Updates**: Multiple methods for updating leads
- **Bulk Operations**: Update multiple leads simultaneously
- **Interactive Table**: Expandable lead details with quick updates
- **Filtering**: By status, priority, sales person

#### **🔍 Search & Filter Tab**
- **Name Search**: Find leads by name
- **Advanced Filters**: Date range, lead score, source
- **Export Options**: Download filtered results

#### **📈 Analytics Tab**
- **Sales Funnel**: Lead progression visualization
- **Lead Score Distribution**: Performance metrics
- **Time Trends**: Monthly/quarterly patterns

#### **🤖 AI Insights Tab**
- **Customer Segments**: AI-generated classifications
- **Engagement Strategies**: Recommended approaches
- **Individual Insights**: Lead-specific AI analysis

### **Data Update Methods**

#### **Method 1: Quick Update by Lead ID**
- Input lead ID, select new status, add notes
- Immediate status change with tracking

#### **Method 2: Search and Update**
- Search leads by name
- Select specific lead for detailed update

#### **Method 3: Bulk Updates**
- Filter leads by current status
- Select multiple leads for batch update

#### **Method 4: Interactive Table**
- Click expand button on any lead
- Update status directly from table view

### **System Reset & Data Management**

#### **🔄 Complete System Reset**
- **🗑️ Reset All Data Button** (Sidebar): Clears all loaded data and saved files
- **🗑️ Quick Reset Button** (Welcome Screen): Alternative reset option
- **What Gets Reset**:
  - All session state data
  - All saved Excel files in `crm_data/` directory
  - All loaded lead data
  - All configuration settings

#### **💾 Manual Data Management**
- **💾 Save Current Data Button**: Manually trigger data saving
- **Automatic Saving**: Data saved after every status update
- **Backup System**: Last 5 backups automatically maintained

#### **📁 File Management**
- **Data Location**: `crm_data/leads_data_latest.xlsx`
- **Backup Naming**: `leads_data_YYYYMMDD_HHMMSS.xlsx`
- **Automatic Cleanup**: Old backups removed automatically

---

## 💾 Data Management

### **Data Persistence System**

#### **Automatic Saving**
- **Trigger**: Every status update
- **Location**: `crm_data/leads_data_latest.xlsx`
- **Backup**: Timestamped backups in `crm_data/` directory

#### **Backup Management**
- **Retention**: Last 5 backups kept
- **Naming**: `leads_data_YYYYMMDD_HHMMSS.xlsx`
- **Cleanup**: Automatic removal of old backups

#### **Data Loading**
- **Startup**: Automatically loads previous data
- **Manual**: "💾 Save Data" button in sidebar
- **Refresh**: Automatic page refresh after updates

### **Export Options**

#### **Supported Formats**
- **Excel (.xlsx)**: Primary format with multiple engines
- **CSV (.csv)**: Fallback format for compatibility

#### **Export Engines**
1. **openpyxl** (Primary)
2. **xlsxwriter** (Alternative)
3. **xlwt** (Legacy support)
4. **CSV** (Universal fallback)

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. "Date showing as full name" Error**
- **Cause**: Column mapping confusion between sheets
- **Solution**: ✅ **FIXED** - Improved column standardization logic

#### **2. "Update button not working" Error**
- **Cause**: Complex session state management
- **Solution**: ✅ **FIXED** - Simplified update interface with expandable sections

#### **3. "Export failed: No engine for filetype: 'excel'"**
- **Cause**: Missing Excel export libraries
- **Solution**: Ensure `openpyxl` and `xlsxwriter` are installed

#### **4. "KeyError: 'status_updated_date'"**
- **Cause**: Missing tracking columns
- **Solution**: ✅ **FIXED** - Automatic column initialization

#### **5. "OpenAI API connection failed"**
- **Cause**: API version incompatibility
- **Solution**: ✅ **FIXED** - Migrated to OpenAI v1.0.0+ syntax

#### **6. "Need to reset system after loading wrong data"**
- **Cause**: Incorrect data loaded or corrupted session
- **Solution**: ✅ **NEW FEATURE** - Use "🗑️ Reset All Data" button in sidebar
- **What it does**: Clears all session data and removes saved files
- **When to use**: After loading wrong data, before uploading corrected file

### **Debug Mode**
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.INFO)

# Check data at each step
df = cleaner.load_excel_data('file.xlsx')
print(f"Loaded data shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
```

---

## 🚀 Development & Customization

### **Adding New Sheet Formats**

#### **1. Extend Column Mapping**
```python
# In data_cleaner.py, add new patterns
elif any(name in col_str for name in ['customer', 'client', 'member']):
    std_df['full_name'] = sheet_df[col]
elif any(name in col_str for name in ['whatsapp', 'contact_number']):
    std_df['phone_number'] = sheet_df[col]
```

#### **2. Add New Status Types**
```python
# In config.py, extend LEAD_STATUSES
LEAD_STATUSES = [
    # ... existing statuses ...
    'New Status',           # Add your custom status
]
```

#### **3. Custom Follow-up Rules**
```python
# In config.py, extend FOLLOW_UP_SCHEDULE
FOLLOW_UP_SCHEDULE = {
    # ... existing rules ...
    'New Status': 5,        # Follow up in 5 days
}
```

### **Performance Optimization**

#### **Large Dataset Handling**
- **Chunk Processing**: Process sheets in batches
- **Memory Management**: Clean up intermediate DataFrames
- **Progress Indicators**: Show processing status for large files

#### **Caching Strategy**
- **Session State**: Store processed data in Streamlit session
- **File Validation**: Check file modification before reprocessing
- **Incremental Updates**: Only process new/changed data

---

## 📚 Best Practices

### **Data Preparation**
1. **Consistent Naming**: Use clear, descriptive column names
2. **Data Validation**: Ensure phone numbers and emails are valid
3. **Sheet Organization**: Group related data in logical sheets
4. **Backup Strategy**: Keep original files as backup

### **System Usage**
1. **Regular Backups**: Use the save data button periodically
2. **Status Updates**: Update lead status after each interaction
3. **Follow-up Management**: Monitor the follow-up alerts regularly
4. **Data Export**: Export reports for external analysis

### **Maintenance**
1. **API Key Rotation**: Regularly update OpenAI API keys
2. **Backup Cleanup**: Monitor backup directory size
3. **Performance Monitoring**: Watch for slow processing with large files
4. **User Training**: Ensure team members understand the system

---

## 🌐 Web Deployment & Remote Access

### **🚀 Deployment Options**

#### **1. Streamlit Cloud (Recommended for Small Teams)**
- **Cost**: Free
- **Setup**: 5 minutes
- **Maintenance**: Zero
- **URL**: `https://your-app.streamlit.app`
- **Best for**: Teams of 5-20 users

#### **2. Docker Deployment (Recommended for Medium Teams)**
- **Cost**: VPS costs (~$5-20/month)
- **Setup**: 15 minutes
- **Maintenance**: Low
- **URL**: `http://your-server-ip:8501`
- **Best for**: Teams of 20-100 users

#### **3. Cloud Platform (Recommended for Large Teams)**
- **Cost**: $50-500+/month
- **Setup**: 30 minutes
- **Maintenance**: Medium
- **URL**: Custom domain
- **Best for**: Teams of 100+ users

### **📋 Quick Deployment Commands**

#### **Docker Deployment**
```bash
# Quick start
./deploy.sh

# Manual deployment
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### **Streamlit Cloud Deployment**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Deploy in 2 minutes

### **🔒 Security for Remote Access**
- **HTTPS**: Always use in production
- **Firewall**: Restrict access to port 8501
- **VPN**: Consider for internal team access
- **IP Whitelisting**: Restrict to known IP addresses

## 📞 Support & Maintenance

### **System Requirements**
- **Python**: 3.8+
- **Memory**: 4GB+ RAM for large datasets
- **Storage**: 1GB+ free space for data and backups
- **Internet**: Required for AI enrichment features
- **Docker**: 20.10+ (for containerized deployment)

### **Dependencies**
```bash
# Core requirements
pandas==2.1.4
streamlit==1.29.0
openpyxl==3.1.2

# AI and advanced features
openai==1.3.7
plotly==5.17.0

# Export and utilities
xlsxwriter
python-dateutil==2.8.2
```

### **Getting Help**
1. **Check Logs**: Look for INFO/WARNING/ERROR messages
2. **Test with Sample Data**: Use small files to isolate issues
3. **Review Configuration**: Verify settings in `config.py`
4. **Check Dependencies**: Ensure all packages are installed

---

## 🎯 Conclusion

The Bumuk Library CRM system is designed to be:
- **🔄 Adaptive**: Handles various Excel formats automatically
- **💪 Robust**: Built-in error handling and data validation
- **📈 Scalable**: Processes large datasets efficiently
- **🔧 Customizable**: Easy to extend for new requirements
- **📱 User-Friendly**: Intuitive interface for daily operations

This documentation provides a comprehensive guide to understanding, using, and maintaining your CRM system. For additional support or customization requests, refer to the troubleshooting section or contact your development team.

---

*Last Updated: August 2025*  
*Version: 1.0.0*  
*System: Bumuk Library CRM*
