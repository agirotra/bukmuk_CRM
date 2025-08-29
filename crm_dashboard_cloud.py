import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Import our custom modules
from data_cleaner import LeadsDataCleaner
from database_manager import DatabaseManager
from auth_manager import AuthManager
from config import LEAD_STATUSES, PRIORITY_LEVELS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🏛️ Bumuk Library CRM",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and auth managers
@st.cache_resource
def init_managers():
    """Initialize database and authentication managers"""
    db_manager = DatabaseManager()
    auth_manager = AuthManager(db_manager)
    return db_manager, auth_manager

# Initialize managers
db_manager, auth_manager = init_managers()

def main():
    """Main application function"""
    
    # Check authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

def show_login_page():
    """Display login/registration page"""
    st.title("🏛️ Bumuk Library CRM")
    st.write("---")
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to Your CRM")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if username and password:
                    result = auth_manager.login_user(username, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_info = {
                            "user_id": result["user_id"],
                            "username": result["username"],
                            "email": result["email"],
                            "role": result["role"]
                        }
                        st.session_state.session_token = result["session_token"]
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Please fill in all fields")
        
        # Show default admin credentials
        st.info("💡 **Default Admin Account**: admin / admin123")
    
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_username and new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        result = auth_manager.register_user(new_username, new_email, new_password)
                        if result["success"]:
                            st.success("✅ Registration successful! You can now login.")
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.error("❌ Passwords do not match")
                else:
                    st.warning("⚠️ Please fill in all fields")

if __name__ == "__main__":
    main()
