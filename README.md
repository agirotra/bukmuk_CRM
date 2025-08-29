# Bumuk Library CRM System

A comprehensive Customer Relationship Management system designed specifically for Bumuk Library to capture, manage, and track leads for potential customers.

## Features

### 🎯 Lead Management
- **Data Cleaning & Processing**: Automatically clean and standardize raw leads data
- **Lead Scoring**: Intelligent scoring system to prioritize high-value prospects
- **Status Tracking**: Track lead progression from initial contact to conversion
- **Automated Workflows**: Streamlined processes for sales team efficiency

### 📊 Analytics & Reporting
- **Lead Performance Metrics**: Conversion rates, response times, and success rates
- **Sales Pipeline Visualization**: Interactive dashboards and charts
- **Custom Reports**: Generate insights for business decision making

### 🔄 Automation
- **Google Sheets Integration**: Seamless sync with your existing data
- **Follow-up Reminders**: Automated notifications for sales team
- **Lead Assignment**: Intelligent distribution of leads to sales representatives

## System Architecture

```
Raw Leads Data → Data Cleaning → Lead Processing → CRM Dashboard → Sales Team
     ↓              ↓              ↓              ↓            ↓
Excel/Sheets → Standardization → Enrichment → Analytics → Follow-up
```

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Google Sheets API**
   - Set up Google Cloud Project
   - Enable Google Sheets API
   - Download credentials.json

3. **Run the System**
   ```bash
   streamlit run crm_dashboard.py
   ```

## Usage

### Step 1: Data Cleaning
- Upload your raw leads data
- Run automated cleaning processes
- Review and approve cleaned data

### Step 2: Lead Management
- Assign leads to sales representatives
- Track lead status and progress
- Set follow-up reminders

### Step 3: Analytics
- Monitor conversion rates
- Analyze sales performance
- Generate reports

## File Structure

```
├── crm_dashboard.py          # Main Streamlit application
├── data_cleaner.py          # Data cleaning and processing
├── lead_manager.py          # Lead management logic
├── google_sheets_integration.py  # Google Sheets API integration
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Support

For technical support or questions about the CRM system, please contact the development team.
