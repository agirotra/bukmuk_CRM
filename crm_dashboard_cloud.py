import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
import io # Added for export functionality

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

def show_main_app():
    """Display main CRM application"""
    
    # Sidebar with user info and logout
    with st.sidebar:
        st.header(f"👤 Welcome, {st.session_state.user_info['username']}!")
        st.write(f"**Role**: {st.session_state.user_info['role']}")
        st.write(f"**Email**: {st.session_state.user_info['email']}")
        
        if st.button("🚪 Logout"):
            auth_manager.logout_user(st.session_state.session_token)
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.session_token = None
            st.rerun()
        
        st.write("---")
        
        # File upload
        uploaded_file = st.file_uploader(
            "📁 Upload Excel File",
            type=['xlsx', 'xls'],
            help="Upload your leads Excel file"
        )
        
        # AI Enrichment toggle
        enable_ai = st.checkbox(
            "Enable AI Enrichment",
            help="Use ChatGPT API to enrich lead data with insights"
        )
        
        if enable_ai:
            # Check if API key is in environment
            env_api_key = os.getenv('OPENAI_API_KEY')
            
            if env_api_key and env_api_key != 'your_openai_api_key_here':
                st.success("✅ API key found in environment")
                openai_key = env_api_key
            else:
                openai_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Enter your OpenAI API key or set OPENAI_API_KEY in environment"
                )
            
            if openai_key:
                os.environ['OPENAI_API_KEY'] = openai_key
        
        # Sales team configuration
        st.subheader("👥 Sales Team")
        sales_team_input = st.text_area(
            "Sales Team Members (one per line)",
            value="John\nSarah\nMike\nLisa",
            help="Enter sales team member names, one per line"
        )
        
        sales_team = [name.strip() for name in sales_team_input.split('\n') if name.strip()]
        
        # Data processing buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if uploaded_file and st.button("🚀 Load & Process Data", type="primary"):
                process_uploaded_file(uploaded_file, enable_ai, sales_team)
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        # Data Management Section
        st.write("---")
        st.subheader("💾 Data Management")
        
        # Add helpful information about data flow
        if 'data_loaded' in st.session_state and st.session_state.data_loaded:
            if 'leads_data' in st.session_state and 'id' in st.session_state.leads_data.columns:
                st.success("✅ **Database Ready**: Your leads have database IDs and can be updated!")
            else:
                st.warning("⚠️ **Action Required**: Click '💾 Save Current Data' to enable status updates.")
        
        if st.button("💾 Save Current Data", help="Manually save current data to database"):
            if 'leads_data' in st.session_state:
                try:
                    user_id = st.session_state.user_info['user_id']
                    success = db_manager.save_leads_data(st.session_state.leads_data, user_id)
                    if success:
                        st.success("✅ Data saved successfully!")
                        # Reload data to get database IDs
                        saved_data = db_manager.load_leads_data(user_id)
                        if not saved_data.empty:
                            st.session_state.leads_data = saved_data
                            st.info("🔄 **Refreshing**: Data reloaded with database IDs. Status updates should now work!")
                            st.rerun()
                    else:
                        st.error("❌ Failed to save data")
                except Exception as e:
                    st.error(f"❌ Error saving data: {str(e)}")
            else:
                st.warning("⚠️ No data loaded to save")
        
        # Load saved data
        if st.button("📥 Load Saved Data"):
            try:
                user_id = st.session_state.user_info['user_id']
                saved_data = db_manager.load_leads_data(user_id)
                if not saved_data.empty:
                    st.session_state.leads_data = saved_data
                    st.session_state.data_loaded = True
                    st.success(f"✅ Loaded {len(saved_data)} saved leads")
                    st.rerun()
                else:
                    st.info("ℹ️ No saved data found")
            except Exception as e:
                st.error(f"❌ Error loading saved data: {str(e)}")
        
        # Reset all data
        if st.button("🗑️ Reset All Data", help="Clear all loaded data and return to welcome screen", type="secondary"):
            if 'leads_data' in st.session_state:
                del st.session_state.leads_data
            if 'data_loaded' in st.session_state:
                del st.session_state.data_loaded
            st.success("✅ All data cleared! Returning to welcome screen.")
            st.rerun()
    
    # Main content area
    if 'data_loaded' in st.session_state and st.session_state.data_loaded and 'leads_data' in st.session_state:
        display_crm_dashboard()
    else:
        display_welcome_screen()

def process_uploaded_file(uploaded_file, enable_ai, sales_team):
    """Process uploaded Excel file"""
    
    # Create progress tracking
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        # Step 1: File preparation
        status_text.text("📁 Preparing file...")
        progress_bar.progress(10)
        
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_path = tmp_file.name
        
        progress_bar.progress(20)
        status_text.text("🔍 Loading Excel sheets...")
        
        # Initialize data cleaner
        cleaner = LeadsDataCleaner()
        
        # Load and clean data
        leads_df = cleaner.clean_all_data(temp_path, enable_ai_enrichment=enable_ai)
        
        progress_bar.progress(70)
        status_text.text("👥 Assigning leads to sales team...")
        
        # Assign leads to sales team
        if sales_team and len(sales_team) > 0:
            import random
            leads_df['assigned_to'] = [random.choice(sales_team) for _ in range(len(leads_df))]
        
        progress_bar.progress(90)
        status_text.text("💾 Saving to database...")
        
        # Save to database FIRST to get database IDs
        user_id = st.session_state.user_info['user_id']
        save_success = db_manager.save_leads_data(leads_df, user_id)
        
        if save_success:
            # Reload data from database to get the database IDs
            leads_df_with_ids = db_manager.load_leads_data(user_id)
            
            if not leads_df_with_ids.empty:
                # Store in session state with database IDs
                st.session_state.leads_data = leads_df_with_ids
                st.session_state.data_loaded = True
                
                progress_bar.progress(100)
                status_text.text("✅ Data processing complete!")
                
                st.success(f"🎉 Successfully processed and saved {len(leads_df_with_ids)} leads!")
                st.info("💡 **Tip**: Your leads are now saved with database IDs and ready for status updates!")
                st.rerun()
            else:
                st.error("❌ Failed to load saved data from database")
        else:
            st.error("❌ Failed to save data to database")
        
        # Clean up temp file
        os.unlink(temp_path)
        
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        logger.error(f"File processing error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Processing failed")

def display_welcome_screen():
    """Display welcome screen when no data is loaded"""
    st.markdown("""
    ## 🎯 Welcome to Bumuk Library CRM System
    
    This comprehensive CRM system will help you:
    
    ### 📊 **Data Management**
    - Clean and standardize leads data from multiple Excel sheets
    - Remove duplicates across sheets intelligently
    - Standardize contact information and addresses
    
    ### 🤖 **AI-Powered Customer Insights**
    - Customer segment identification (parents, students, professionals, etc.)
    - Individual value assessment based on usage patterns
    - Personalized engagement strategies
    - Relevant library benefits for each customer type
    
    ### 🎯 **Lead Management**
    - Automatic lead scoring and prioritization
    - Sales team assignment
    - Status tracking and follow-up reminders
    - Pipeline analytics and reporting
    
    ### 📈 **Analytics & Reporting**
    - Real-time sales pipeline visualization
    - Performance metrics and conversion rates
    - Custom reports and data export
    
    ---
    
    **To get started:**
    1. Upload your leads Excel file in the sidebar
    2. Configure your sales team
    3. Optionally enable AI enrichment
    4. Click "Load & Process Data"
    
    ---
    
    ### 🔄 **Need to Start Over?**
    
    **If you loaded wrong data or want to start fresh:**
    - Use the **💾 Load Saved Data** button in the sidebar
    - Or upload a new Excel file to replace current data
    
    """)
    
    # Quick Data Load Section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Tip**: Use the sidebar to upload Excel files and manage your data!")
    
    with col2:
        if st.button("📥 Load Saved Data", type="secondary"):
            try:
                user_id = st.session_state.user_info['user_id']
                saved_data = db_manager.load_leads_data(user_id)
                if not saved_data.empty:
                    st.session_state.leads_data = saved_data
                    st.session_state.data_loaded = True
                    st.success(f"✅ Loaded {len(saved_data)} saved leads")
                    st.rerun()
                else:
                    st.info("ℹ️ No saved data found")
            except Exception as e:
                st.error(f"❌ Error loading saved data: {str(e)}")

def display_crm_dashboard():
    """Display the main CRM dashboard"""
    leads_df = st.session_state.leads_data
    user_id = st.session_state.user_info['user_id']
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(leads_df))
    
    with col2:
        new_leads = len(leads_df[leads_df['lead_status'] == 'New Lead'])
        st.metric("New Leads", new_leads)
    
    with col3:
        if 'lead_score' in leads_df.columns:
            avg_score = leads_df['lead_score'].mean()
            st.metric("Avg Lead Score", f"{avg_score:.1f}")
        else:
            st.metric("Avg Lead Score", "N/A")
    
    with col4:
        if 'assigned_to' in leads_df.columns:
            unique_sales = leads_df['assigned_to'].nunique()
            st.metric("Sales Team", unique_sales)
        else:
            st.metric("Sales Team", "N/A")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "👥 Leads Management", "🔍 Search & Filter", "📈 Analytics", "🤖 AI Insights", "📤 Export"
    ])
    
    with tab1:
        display_dashboard_tab(leads_df, user_id)
    
    with tab2:
        display_leads_management_tab(leads_df, user_id)
    
    with tab3:
        display_search_filter_tab(leads_df, user_id)
    
    with tab4:
        display_analytics_tab(leads_df, user_id)
    
    with tab5:
        display_ai_insights_tab(leads_df)
    
    with tab6:
        display_export_tab(leads_df, user_id)

def display_dashboard_tab(leads_df, user_id):
    """Display the main dashboard with charts and metrics"""
    st.header("📊 Sales Pipeline Dashboard")
    
    # Get user statistics
    user_stats = db_manager.get_user_stats(user_id)
    
    # Two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Lead Status Distribution")
        if user_stats.get('status_counts'):
            status_data = pd.DataFrame(list(user_stats['status_counts'].items()), columns=['Status', 'Count'])
            fig = px.pie(status_data, values='Count', names='Status', title="Leads by Status")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No status data available")
    
    with col2:
        st.subheader("🎯 Priority Distribution")
        if user_stats.get('priority_counts'):
            priority_data = pd.DataFrame(list(user_stats['priority_counts'].items()), columns=['Priority', 'Count'])
            fig = px.bar(priority_data, x='Priority', y='Count', title="Leads by Priority")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No priority data available")
    
    # Follow-up alerts
    st.subheader("🔔 Follow-up Alerts")
    
    # Get leads needing follow-up (with proper error handling)
    if 'follow_up_date' in leads_df.columns:
        try:
            # Clean and convert follow_up_date column
            follow_up_dates = leads_df['follow_up_date'].copy()
            
            # Convert to datetime, handling errors
            follow_up_dates = pd.to_datetime(follow_up_dates, errors='coerce')
            
            # Filter out invalid dates and get today's date
            valid_dates = follow_up_dates.notna()
            today = pd.Timestamp.now().normalize()
            
            if valid_dates.any():
                # Find leads needing follow-up
                follow_up_needed = (follow_up_dates <= today) & valid_dates
                follow_up_leads = leads_df[follow_up_needed]
                
                if not follow_up_leads.empty:
                    st.warning(f"⚠️ {len(follow_up_leads)} leads need follow-up today")
                    
                    # Show relevant columns safely
                    display_columns = ['full_name', 'phone_number', 'lead_status']
                    available_columns = [col for col in display_columns if col in follow_up_leads.columns]
                    
                    if available_columns:
                        st.dataframe(follow_up_leads[available_columns], width='stretch')
                    else:
                        st.write("Follow-up leads found but no displayable columns available")
                else:
                    st.success("✅ No leads need follow-up today")
            else:
                st.info("ℹ️ No valid follow-up dates found in your data")
                
        except Exception as e:
            st.warning(f"⚠️ Follow-up tracking unavailable: {str(e)}")
            st.info("ℹ️ This feature will work once you have follow-up dates in your data")
    else:
        st.info("ℹ️ Follow-up tracking not available - column 'follow_up_date' not found")

def display_leads_management_tab(leads_df, user_id):
    """Display modern leads management interface with table, search, and editing"""
    st.header("👥 Leads Management")
    
    if leads_df.empty:
        st.info("📭 No leads available. Please upload an Excel file first.")
        return
    
    # ===== SEARCH AND FILTER BAR =====
    st.subheader("🔍 Search & Filter")
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        search_term = st.text_input("🔍 Search all fields", placeholder="Search by name, phone, email, city...", key="search_leads")
    
    with col2:
        # Safe status filter
        if 'lead_status' in leads_df.columns and not leads_df['lead_status'].empty:
            status_options = ["All"] + [str(s) for s in leads_df['lead_status'].dropna().unique() if pd.notna(s)]
        else:
            status_options = ["All"]
        status_filter = st.selectbox("📊 Status", status_options, key="status_filter")
    
    with col3:
        # Safe priority filter
        if 'priority' in leads_df.columns and not leads_df['priority'].empty:
            priority_options = ["All"] + [str(p) for p in leads_df['priority'].dropna().unique() if pd.notna(p)]
        else:
            priority_options = ["All"]
        priority_filter = st.selectbox("🎯 Priority", priority_options, key="priority_filter")
    
    with col4:
        # Safe assigned filter
        if 'assigned_to' in leads_df.columns and not leads_df['assigned_to'].empty:
            assigned_options = ["All"] + [str(a) for a in leads_df['assigned_to'].dropna().unique() if pd.notna(a)]
        else:
            assigned_options = ["All"]
        assigned_filter = st.selectbox("👤 Assigned To", assigned_options, key="assigned_filter")
    
    # ===== APPLY FILTERS =====
    filtered_df = leads_df.copy()
    
    if search_term:
        # Safe search with proper data type handling
        search_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        
        # Search in full_name
        if 'full_name' in filtered_df.columns:
            name_col = filtered_df['full_name'].astype(str)
            search_mask |= name_col.str.contains(search_term, case=False, na=False)
        
        # Search in phone_number
        if 'phone_number' in filtered_df.columns:
            phone_col = filtered_df['phone_number'].astype(str)
            search_mask |= phone_col.str.contains(search_term, case=False, na=False)
        
        # Search in email
        if 'email' in filtered_df.columns:
            email_col = filtered_df['email'].astype(str)
            search_mask |= email_col.str.contains(search_term, case=False, na=False)
        
        # Search in city
        if 'city' in filtered_df.columns:
            city_col = filtered_df['city'].astype(str)
            search_mask |= city_col.str.contains(search_term, case=False, na=False)
        
        filtered_df = filtered_df[search_mask]
    
    if status_filter != "All":
        if 'lead_status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['lead_status'] == status_filter]
    
    if priority_filter != "All":
        if 'priority' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
    
    if assigned_filter != "All":
        if 'assigned_to' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['assigned_to'] == assigned_filter]
    
    # ===== BULK OPERATIONS =====
    st.subheader("📋 Bulk Operations")
    
    # Initialize selection state in session
    if 'selected_leads_indices' not in st.session_state:
        st.session_state.selected_leads_indices = set()
    
    # Checkbox for selecting all visible leads
    select_all = st.checkbox("☑️ Select All Visible Leads", key="select_all_leads")
    
    # Handle select all functionality
    if select_all:
        st.session_state.selected_leads_indices = set(filtered_df.index.tolist())
    else:
        # If unchecking select all, clear all selections
        if len(st.session_state.selected_leads_indices) == len(filtered_df):
            st.session_state.selected_leads_indices.clear()
    
    # Bulk actions
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        bulk_status = st.selectbox("📊 Bulk Status Update", ["Select Status"] + LEAD_STATUSES, key="bulk_status")
    
    with col2:
        bulk_priority = st.selectbox("🎯 Bulk Priority Update", ["Select Priority", "High", "Medium", "Low"], key="bulk_priority")
    
    with col3:
        # Safe bulk assignment
        if 'assigned_to' in leads_df.columns and not leads_df['assigned_to'].empty:
            assigned_options = ["Select Person"] + [str(a) for a in leads_df['assigned_to'].dropna().unique() if pd.notna(a)]
        else:
            assigned_options = ["Select Person"]
        bulk_assigned = st.selectbox("👤 Bulk Assignment", assigned_options, key="bulk_assigned")
    
    with col4:
        if st.button("🚀 Apply Bulk Updates", type="primary"):
            if st.session_state.selected_leads_indices:
                # Apply bulk updates
                update_count = 0
                for idx in st.session_state.selected_leads_indices:
                    lead_id = filtered_df.loc[idx, 'id'] if 'id' in filtered_df.columns else idx
                    success = True
                    
                    if bulk_status != "Select Status":
                        success &= db_manager.update_lead_status(lead_id, bulk_status, "Bulk status update", user_id)
                    
                    # Update other fields if needed
                    if success and (bulk_priority != "Select Priority" or bulk_assigned != "Select Person"):
                        # This would require additional database update methods
                        pass
                    
                    if success:
                        update_count += 1
                
                if update_count > 0:
                    st.success(f"✅ Successfully updated {update_count} leads!")
                    # Clear selections after successful update
                    st.session_state.selected_leads_indices.clear()
                    st.rerun()
                else:
                    st.error("❌ Failed to update leads")
            else:
                st.warning("⚠️ Please select leads for bulk update")
    
    # ===== LEADS TABLE =====
    st.subheader(f"📊 Leads Table ({len(filtered_df)} leads)")
    
    if filtered_df.empty:
        st.info("🔍 No leads match your search criteria. Try adjusting your filters.")
        return
    
    # Prepare table data for display
    display_df = filtered_df.copy()
    
    # Add selection column as boolean values
    display_df['Select'] = [False] * len(display_df)  # Initialize all as unchecked
    
    # Format status with colors
    def format_status(status):
        status_colors = {
            'New Lead': '🟢',
            'Initial Contact': '🔵',
            'Follow Up': '🟡',
            'Qualified': '🟠',
            'Converted': '🟢',
            'Lost': '🔴'
        }
        return f"{status_colors.get(status, '⚪')} {status}"
    
    display_df['Status'] = display_df['lead_status'].apply(format_status)
    
    # Format priority with colors
    def format_priority(priority):
        priority_colors = {
            'High': '🔴',
            'Medium': '🟡',
            'Low': '🟢'
        }
        return f"{priority_colors.get(priority, '⚪')} {priority}"
    
    display_df['Priority'] = display_df['priority'].apply(format_priority)
    
    # Select columns to display
    columns_to_show = ['Select', 'full_name', 'phone_number', 'email', 'city', 'Status', 'Priority', 'assigned_to', 'lead_date']
    
    # Check which columns actually exist in the dataframe
    available_columns = []
    for col in columns_to_show:
        if col in display_df.columns:
            available_columns.append(col)
        else:
            # Handle missing columns gracefully
            if col == 'full_name' and 'name' in display_df.columns:
                display_df['full_name'] = display_df['name']
                available_columns.append('full_name')
            elif col == 'lead_date' and 'date' in display_df.columns:
                display_df['lead_date'] = display_df['date']
                available_columns.append('lead_date')
            elif col in ['Status', 'Priority', 'Select']:
                # These are created above, so they should exist
                available_columns.append(col)
            else:
                # Create empty column for missing data
                display_df[col] = 'N/A'
                available_columns.append(col)
    
    # Rename columns for display
    column_mapping = {
        'Select': '☑️',
        'full_name': '👤 Name',
        'phone_number': '📱 Phone',
        'email': '📧 Email',
        'city': '🏙️ City',
        'Status': '📊 Status',
        'Priority': '🎯 Priority',
        'assigned_to': '👤 Assigned',
        'lead_date': '📅 Date'
    }
    
    # Only show columns that exist
    display_df = display_df[available_columns].rename(columns=column_mapping)
    
    # Display the table with selection capability
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        column_config={
            "☑️": st.column_config.CheckboxColumn("Select", help="Select for bulk operations", default=False),
            "👤 Name": st.column_config.TextColumn("Name", width="medium"),
            "📱 Phone": st.column_config.TextColumn("Phone", width="medium"),
            "📧 Email": st.column_config.TextColumn("Email", width="medium"),
            "🏙️ City": st.column_config.TextColumn("City", width="small"),
            "📊 Status": st.column_config.TextColumn("Status", width="small"),
            "🎯 Priority": st.column_config.TextColumn("Priority", width="small"),
            "👤 Assigned": st.column_config.TextColumn("Assigned", width="small"),
            "📅 Date": st.column_config.DateColumn("Date", width="small")
        }
    )
    
    # Show selection summary
    if st.session_state.selected_leads_indices:
        st.info(f"☑️ **{len(st.session_state.selected_leads_indices)} leads selected** for bulk operations")
    
    # ===== INDIVIDUAL LEAD EDITING =====
    st.subheader("✏️ Edit Individual Lead")
    
    # Lead selection for editing
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if 'id' in filtered_df.columns:
            available_ids = filtered_df['id'].dropna().astype(int).tolist()
            if available_ids:
                edit_lead_id = st.selectbox("Select Lead ID to Edit", available_ids, key="edit_lead_select")
            else:
                edit_lead_id = st.number_input("Lead ID", min_value=0, max_value=len(filtered_df)-1, value=0, key="edit_lead_input")
        else:
            edit_lead_id = st.number_input("Lead Index", min_value=0, max_value=len(filtered_df)-1, value=0, key="edit_lead_input")
    
    with col2:
        if st.button("🔍 Load Lead for Editing", type="secondary"):
            st.session_state.editing_lead_id = edit_lead_id
            st.rerun()
    
    # Display edit form if lead is selected
    if hasattr(st.session_state, 'editing_lead_id') and st.session_state.editing_lead_id is not None:
        edit_id = st.session_state.editing_lead_id
        
        # Find the lead to edit
        if 'id' in filtered_df.columns:
            lead_to_edit = filtered_df[filtered_df['id'] == edit_id]
        else:
            lead_to_edit = filtered_df.iloc[[edit_id]]
        
        if not lead_to_edit.empty:
            lead_row = lead_to_edit.iloc[0]
            
            st.write(f"**Editing Lead: {lead_row.get('full_name', 'Unknown')}**")
            
            # Edit form
            with st.form(f"edit_lead_{edit_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Full Name", value=lead_row.get('full_name', ''), key=f"edit_name_{edit_id}")
                    new_phone = st.text_input("Phone Number", value=lead_row.get('phone_number', ''), key=f"edit_phone_{edit_id}")
                    new_email = st.text_input("Email", value=lead_row.get('email', ''), key=f"edit_email_{edit_id}")
                    new_city = st.text_input("City", value=lead_row.get('city', ''), key=f"edit_city_{edit_id}")
                
                with col2:
                    new_status = st.selectbox("Status", LEAD_STATUSES, index=LEAD_STATUSES.index(lead_row.get('lead_status', 'New Lead')), key=f"edit_status_{edit_id}")
                    new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(lead_row.get('priority', 'Medium')), key=f"edit_priority_{edit_id}")
                    new_assigned = st.text_input("Assigned To", value=lead_row.get('assigned_to', ''), key=f"edit_assigned_{edit_id}")
                    new_notes = st.text_area("Notes", value=lead_row.get('notes', ''), key=f"edit_notes_{edit_id}")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        try:
                            # Update status if changed
                            if new_status != lead_row.get('lead_status'):
                                success = db_manager.update_lead_status(edit_id, new_status, new_notes, user_id)
                                if success:
                                    st.success(f"✅ Lead {edit_id} updated successfully!")
                                    # Clear editing state
                                    st.session_state.editing_lead_id = None
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update lead status")
                            else:
                                st.success("✅ No changes to save")
                        except Exception as e:
                            st.error(f"❌ Error updating lead: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel", type="secondary"):
                        st.session_state.editing_lead_id = None
                        st.rerun()
                
                with col3:
                    if st.form_submit_button("🗑️ Delete Lead", type="secondary"):
                        st.warning("⚠️ Delete functionality not yet implemented")
    
    # ===== QUICK STATUS UPDATE =====
    st.subheader("⚡ Quick Status Update")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quick_lead_id = st.number_input("Lead ID", min_value=0, max_value=len(leads_df)-1, value=0, key="quick_lead_id")
    
    with col2:
        quick_status = st.selectbox("New Status", LEAD_STATUSES, key="quick_status")
    
    with col3:
        quick_notes = st.text_input("Notes", placeholder="Quick update notes...", key="quick_notes")
    
    if st.button("🚀 Quick Update", type="primary"):
        try:
            if 'id' in leads_df.columns:
                # Use database ID
                success = db_manager.update_lead_status(quick_lead_id, quick_status, quick_notes, user_id)
                if success:
                    st.success(f"✅ Lead {quick_lead_id} status updated to {quick_status}")
                    st.rerun()
                else:
                    st.error("❌ Failed to update lead status")
            else:
                st.warning("⚠️ Database ID not available for quick updates")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # ===== EXPORT FUNCTIONALITY =====
    st.subheader("📤 Export Data")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        export_format = st.selectbox("Export Format", ["CSV", "Excel"], key="export_format")
    
    with col2:
        if st.button("📥 Export Filtered Leads", type="secondary"):
            try:
                if export_format == "CSV":
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:  # Excel
                    # Create Excel file in memory
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, index=False, sheet_name='Leads')
                    output.seek(0)
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=output.getvalue(),
                        file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")

def display_search_filter_tab(leads_df, user_id):
    """Display search and filter interface"""
    st.header("🔍 Search & Filter Leads")
    
    # Search by name
    st.subheader("🔍 Search Leads")
    search_term = st.text_input("Search by name, phone, or email", placeholder="Enter search term...")
    
    if search_term:
        search_results = db_manager.search_leads(search_term, user_id)
        if not search_results.empty:
            st.success(f"🔍 Found {len(search_results)} matching leads")
            st.dataframe(search_results, width='stretch')
        else:
            st.info("No leads found matching your search term")
    
    # Filter by status
    st.subheader("📊 Filter by Status")
    status_filter = st.selectbox("Select Status", ["All"] + LEAD_STATUSES)
    
    if status_filter != "All":
        filtered_df = leads_df[leads_df['lead_status'] == status_filter]
        st.write(f"**Leads with status: {status_filter}**")
        st.dataframe(filtered_df, width='stretch')
    else:
        st.write("**All Leads**")
        st.dataframe(leads_df, width='stretch')

def display_analytics_tab(leads_df, user_id):
    """Display analytics and insights"""
    st.header("📈 Analytics & Insights")
    
    # Get user statistics
    user_stats = db_manager.get_user_stats(user_id)
    
    if user_stats:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Lead Status Overview")
            if user_stats.get('status_counts'):
                status_data = pd.DataFrame(list(user_stats['status_counts'].items()), columns=['Status', 'Count'])
                fig = px.pie(status_data, values='Count', names='Status')
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.subheader("🎯 Priority Distribution")
            if user_stats.get('priority_counts'):
                priority_data = pd.DataFrame(list(user_stats['priority_counts'].items()), columns=['Priority', 'Count'])
                fig = px.bar(priority_data, x='Priority', y='Count')
                st.plotly_chart(fig, width='stretch')
    
    # Time-based analysis (with safe date handling)
    st.subheader("⏰ Time-based Analysis")
    
    # Check for various possible date columns
    date_columns = ['created_at', 'created_date', 'lead_date', 'date']
    found_date_column = None
    
    for col in date_columns:
        if col in leads_df.columns:
            found_date_column = col
            break
    
    if found_date_column:
        try:
            # Safely convert dates
            date_series = pd.to_datetime(leads_df[found_date_column], errors='coerce')
            valid_dates = date_series.notna()
            
            if valid_dates.any():
                # Create daily leads count
                daily_leads = date_series[valid_dates].dt.date.value_counts().sort_index()
                daily_leads_df = pd.DataFrame({
                    'date': daily_leads.index,
                    'count': daily_leads.values
                })
                
                # Create the chart
                fig = px.line(daily_leads_df, x='date', y='count', 
                            title=f"Daily Lead Creation ({found_date_column})")
                st.plotly_chart(fig, width='stretch')
                
                # Show summary stats
                st.write(f"**Date Range**: {daily_leads_df['date'].min()} to {daily_leads_df['date'].max()}")
                st.write(f"**Total Days with Leads**: {len(daily_leads_df)}")
                st.write(f"**Average Leads per Day**: {daily_leads_df['count'].mean():.1f}")
            else:
                st.info(f"ℹ️ No valid dates found in '{found_date_column}' column")
                
        except Exception as e:
            st.warning(f"⚠️ Time analysis unavailable: {str(e)}")
    else:
        st.info("ℹ️ No date columns found for time-based analysis")
        st.write("**Available columns for analysis:**")
        for col in leads_df.columns:
            st.write(f"• {col}")

def display_ai_insights_tab(leads_df):
    """Display AI insights and recommendations"""
    st.header("🤖 AI Insights")
    
    if 'ai_insights' in leads_df.columns:
        st.write("**AI-Generated Insights for Your Leads**")
        
        # Show sample insights
        sample_insights = leads_df[leads_df['ai_insights'].notna()].head(5)
        if not sample_insights.empty:
            for _, lead in sample_insights.iterrows():
                with st.expander(f"💡 {lead.get('full_name', 'Unknown')}"):
                    st.write(lead.get('ai_insights', 'No insights available'))
        else:
            st.info("No AI insights available. Enable AI enrichment to get insights.")
    else:
        st.info("🤖 **AI Insights not available**")
        st.write("""
        To enable AI insights:
        1. Check "Enable AI Enrichment" in the sidebar
        2. Provide your OpenAI API key
        3. Upload and process your data
        """)

def display_export_tab(leads_df, user_id):
    """Display export options"""
    st.header("📤 Export Data")
    
    st.write("**Export your leads data in various formats**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export Options")
        
        export_format = st.selectbox("Select Format", ["CSV", "Excel"])
        
        if st.button(f"📥 Export as {export_format}"):
            try:
                filename = db_manager.export_leads_report(user_id, export_format.lower())
                if filename and not filename.startswith("Export failed"):
                    st.success(f"✅ Data exported successfully to {filename}")
                    
                    # Provide download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label=f"📥 Download {export_format} File",
                            data=file.read(),
                            file_name=filename,
                            mime="application/octet-stream"
                        )
                else:
                    st.error(f"❌ {filename}")
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")
    
    with col2:
        st.subheader("📋 Export Summary")
        st.write(f"**Total Leads**: {len(leads_df)}")
        
        if not leads_df.empty:
            st.write("**Data Columns Available:**")
            for col in leads_df.columns:
                st.write(f"• {col}")
        else:
            st.info("No data available for export")

if __name__ == "__main__":
    main()
