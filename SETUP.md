# 🚀 Bumuk Library CRM Setup Guide

## 📋 Prerequisites
- Python 3.8 or higher
- OpenAI API key (get from [openai.com](https://openai.com))

## 🔧 Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root (already created):

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_api_key_here

# Google Sheets Configuration (for future use)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json

# CRM Configuration
CRM_NAME=Bumuk Library CRM
CRM_VERSION=1.0.0
```

**⚠️ Important:** Replace `your_actual_api_key_here` with your real OpenAI API key!

### 3. Git Security
The `.env` file is already added to `.gitignore` to keep your API key secure.

## 🚀 Running the System

### Start the CRM Dashboard
```bash
streamlit run crm_dashboard.py
```

### Test the System
```bash
python test_system.py
```

### Run AI Enrichment Demo
```bash
python demo_ai_enrichment.py
```

## 🔐 Security Features

- **Environment Variables**: API keys stored in `.env` file
- **Git Ignore**: `.env` file automatically excluded from version control
- **Password Fields**: API key input masked in the UI
- **No Hardcoding**: No sensitive data in source code

## 📊 Features

### ✅ Data Management
- Multi-sheet Excel loading
- Intelligent duplicate removal
- Data standardization
- Contact validation

### ✅ AI Enrichment
- Customer segmentation
- Value assessment
- Engagement strategies
- Library benefits identification

### ✅ Lead Management
- Sales team assignment
- Status tracking
- Follow-up reminders
- Pipeline analytics

### ✅ Export & Reporting
- Excel/CSV export
- Custom reports
- Data visualization
- Performance metrics

## 🎯 Usage Workflow

1. **Upload Data**: Upload your leads Excel file
2. **Enable AI**: Check "Enable AI Enrichment" (API key from .env)
3. **Process**: Click "Load & Process Data"
4. **Manage**: Use the dashboard tabs to manage leads
5. **Export**: Download reports and insights

## 🆘 Troubleshooting

### API Key Issues
- Ensure `.env` file exists and has correct API key
- Check API key format and validity
- Verify OpenAI account has credits

### Data Loading Issues
- Check Excel file format (.xlsx or .xls)
- Ensure file has readable data
- Check file size (max 50MB)

### Performance Issues
- Large files may take time to process
- AI enrichment adds processing time
- Consider processing in batches for very large datasets

## 📞 Support

For issues or questions:
1. Check the logs in the dashboard
2. Run `python test_system.py` to verify functionality
3. Review error messages for specific issues

---

**🎉 Your CRM system is ready to transform your library's lead management!**
