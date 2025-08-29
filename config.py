"""
Configuration file for Bumuk Library CRM System
"""

import os
from typing import Dict, List

# System Configuration
SYSTEM_NAME = "Bumuk Library CRM"
VERSION = "1.0.0"

# Data Processing Settings
DEFAULT_SHEET_PRIORITY = {
    'Main': 1,
    'Primary': 1,
    'Leads': 2,
    'Contacts': 3,
    'Processed': 4,
    'Suspended': 5
}

# Lead Status Configuration - Library Sales Pipeline
LEAD_STATUSES = [
    'New Lead',           # Fresh lead from marketing/source
    'Initial Contact',     # First call/email made
    'Follow Up 1',        # First follow-up attempt
    'Follow Up 2',        # Second follow-up attempt
    'Follow Up 3',        # Third follow-up attempt
    'Interested',         # Showed interest in library
    'Trial Membership',   # Offered trial membership
    'Proposal Sent',      # Membership proposal shared
    'Negotiation',        # Discussing terms/pricing
    'Ready to Join',      # Agreed to join, finalizing
    'Member',             # Successfully converted
    'Lost - No Response', # No response after multiple attempts
    'Lost - Not Interested', # Explicitly declined
    'Lost - Price',       # Price was the barrier
    'Lost - Location',    # Location was the barrier
    'Re-engage Later'     # Mark for future re-engagement
]

# Priority Levels
PRIORITY_LEVELS = ['Low', 'Medium', 'High', 'Urgent']

# Lead Scoring Configuration (Updated for library context)
LEAD_SCORING = {
    'phone_number': 40,   # Most important for sales calls
    'email': 35,          # Second most important
    'city': 15,           # Location relevance
    'child_age': 10       # Target demographic
}

# Follow-up Schedule (days) - Library-specific timing
FOLLOW_UP_SCHEDULE = {
    'New Lead': 2,              # Quick first contact
    'Initial Contact': 3,       # Follow up soon after first contact
    'Follow Up 1': 5,          # 5 days after first follow-up
    'Follow Up 2': 7,          # 7 days after second follow-up
    'Follow Up 3': 10,         # 10 days after third follow-up
    'Interested': 3,            # Keep momentum with interested leads
    'Trial Membership': 2,      # Quick follow-up for trial
    'Proposal Sent': 3,         # Follow up on proposal
    'Negotiation': 2,           # Keep negotiation active
    'Ready to Join': 1,         # Close quickly
    'Member': 30,               # Monthly check-in for retention
    'Lost - No Response': 14,   # Re-engage after 2 weeks
    'Lost - Not Interested': 30, # Re-engage after 1 month
    'Lost - Price': 21,         # Re-engage with new offers
    'Lost - Location': 45,      # Re-engage with new locations
    'Re-engage Later': 60       # Re-engage after 2 months
}

# Follow-up Alert Configuration
FOLLOW_UP_ALERTS = {
    'overdue_days': 2,          # Alert if follow-up is overdue by X days
    'urgent_hours': 24,         # Urgent alerts for high-priority leads
    'daily_digest': True,       # Send daily summary of follow-ups needed
    'escalation_days': 7        # Escalate to manager after X days
}

# AI Configuration
AI_CONFIG = {
    'model': 'gpt-3.5-turbo',
    'max_tokens': 300,
    'temperature': 0.3,
    'enrichment_fields': [
        'ai_customer_segment',
        'ai_potential_value', 
        'ai_engagement_strategy',
        'ai_library_benefits'
    ]
}

# Export Configuration
EXPORT_CONFIG = {
    'default_format': 'excel',
    'supported_formats': ['excel', 'csv'],
    'filename_template': 'bumuk_leads_{timestamp}',
    'include_metadata': True
}

# Sales Team Configuration
DEFAULT_SALES_TEAM = [
    "John Doe",
    "Sarah Smith", 
    "Mike Johnson",
    "Lisa Brown"
]

# Column Mapping for Data Standardization
COLUMN_MAPPING = {
    'name': 'full_name',
    'first_name': 'first_name',
    'last_name': 'last_name',
    'email': 'email',
    'phone': 'phone_number',
    'mobile': 'phone_number',
    'telephone': 'phone_number',
    'child_age': 'child_age',
    'lead_type': 'lead_type',
    'source': 'lead_source',
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
    'date': 'created_date',
    'created': 'created_date',
    'timestamp': 'created_date'
}

# Validation Rules
VALIDATION_RULES = {
    'email': {
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'required': False
    },
    'phone': {
        'pattern': r'^[\d\s\(\)\-\+]+$',
        'required': False,
        'min_length': 10
    },
    'name': {
        'required': True,
        'min_length': 2
    }
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'refresh_interval': 30,  # seconds
    'max_display_leads': 100,
    'charts_height': 400,
    'enable_real_time': False
}

# Notification Settings
NOTIFICATION_CONFIG = {
    'follow_up_reminders': True,
    'status_change_notifications': True,
    'daily_summary': True,
    'email_notifications': False
}

# File Paths
PATHS = {
    'data_directory': 'data',
    'exports_directory': 'exports',
    'logs_directory': 'logs',
    'temp_directory': 'temp'
}

# Create directories if they don't exist
def ensure_directories():
    """Create necessary directories"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

# Environment Variables
def get_env_config() -> Dict:
    """Get configuration from environment variables"""
    return {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'max_file_size': int(os.getenv('MAX_FILE_SIZE', '50')),  # MB
    }

# Load configuration
def load_config() -> Dict:
    """Load complete configuration"""
    config = {
        'system': {
            'name': SYSTEM_NAME,
            'version': VERSION
        },
        'data_processing': {
            'sheet_priority': DEFAULT_SHEET_PRIORITY,
            'column_mapping': COLUMN_MAPPING,
            'validation_rules': VALIDATION_RULES
        },
        'lead_management': {
            'statuses': LEAD_STATUSES,
            'priorities': PRIORITY_LEVELS,
            'scoring': LEAD_SCORING,
            'follow_up_schedule': FOLLOW_UP_SCHEDULE
        },
        'ai': AI_CONFIG,
        'export': EXPORT_CONFIG,
        'sales_team': DEFAULT_SALES_TEAM,
        'dashboard': DASHBOARD_CONFIG,
        'notifications': NOTIFICATION_CONFIG,
        'paths': PATHS
    }
    
    # Add environment configuration
    config['environment'] = get_env_config()
    
    return config

if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print("Configuration loaded successfully!")
    print(f"System: {config['system']['name']} v{config['system']['version']}")
    print(f"Lead Statuses: {len(config['lead_management']['statuses'])}")
    print(f"AI Model: {config['ai']['model']}")
