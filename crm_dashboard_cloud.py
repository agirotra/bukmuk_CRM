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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")
    
    with col2:
        st.subheader("🎯 Priority Distribution")
        if user_stats.get('priority_counts'):
            priority_data = pd.DataFrame(list(user_stats['priority_counts'].items()), columns=['Priority', 'Count'])
            fig = px.bar(priority_data, x='Priority', y='Count', title="Leads by Priority")
            st.plotly_chart(fig, use_container_width=True)
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
                        st.dataframe(follow_up_leads[available_columns], use_container_width=True)
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
    """Display leads management interface"""
    st.header("👥 Leads Management")
    
    # Status update section
    st.subheader("📝 Update Lead Status")
    
    # Method 1: Quick Update by Lead ID
    st.write("**Method 1: Quick Update by Lead ID**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Use actual database IDs if available, otherwise use index
        if 'id' in leads_df.columns:
            available_ids = leads_df['id'].dropna().astype(int).tolist()
            if available_ids:
                lead_id = st.selectbox("Lead ID", available_ids, help="Select the lead ID to update")
            else:
                lead_id = st.number_input("Lead ID", min_value=0, max_value=len(leads_df)-1, value=0)
        else:
            lead_id = st.number_input("Lead ID", min_value=0, max_value=len(leads_df)-1, value=0)
    
    with col2:
        new_status = st.selectbox("New Status", LEAD_STATUSES)
    
    with col3:
        notes = st.text_input("Notes", placeholder="Add status update notes...")
    
    if st.button("Update Status"):
        if lead_id < len(leads_df):
            # Debug logging
            st.write(f"🔍 **Debug Info:**")
            st.write(f"- Lead ID: {lead_id} (type: {type(lead_id)})")
            st.write(f"- User ID: {user_id} (type: {type(user_id)})")
            st.write(f"- New Status: {new_status}")
            st.write(f"- Notes: {notes}")
            
            # Update in database
            success = db_manager.update_lead_status(lead_id, new_status, notes, user_id)
            if success:
                st.success(f"✅ Lead {lead_id} status updated to {new_status}")
                # Refresh data
                st.rerun()
            else:
                st.error("❌ Failed to update lead status in database")
        else:
            st.error("❌ Invalid lead ID")
    
    st.divider()
    
    # Method 2: Interactive Table Updates
    st.write("**Method 2: Interactive Table Updates**")
    
    # Display leads table with quick status updates
    for idx, lead in leads_df.iterrows():
        # Get the actual database ID or use index as fallback
        db_id = lead.get('id', idx)
        display_id = f"DB:{db_id}" if 'id' in leads_df.columns else f"Index:{idx}"
        
        with st.expander(f"📋 {lead.get('full_name', 'Unknown')} - {lead.get('lead_status', 'N/A')} ({display_id})", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                st.write(f"**Contact Info:**")
                st.write(f"📱 Phone: {lead.get('phone_number', 'N/A')}")
                st.write(f"📧 Email: {lead.get('email', 'N/A')}")
                st.write(f"🏙️ City: {lead.get('city', 'N/A')}")
            
            with col2:
                st.write(f"**Lead Details:**")
                st.write(f"🎯 Priority: {lead.get('priority', 'N/A')}")
                st.write(f"👤 Assigned: {lead.get('assigned_to', 'N/A')}")
                st.write(f"📅 Status: **{lead.get('lead_status', 'N/A')}**")
                st.write(f"🆔 ID: {display_id}")
            
            with col3:
                st.write(f"**Quick Update:**")
                new_status = st.selectbox("New Status", LEAD_STATUSES, key=f"status_{idx}")
                notes = st.text_input("Notes", placeholder="Add update notes...", key=f"notes_{idx}")
                
                if st.button("💾 Update Status", key=f"update_{idx}"):
                    try:
                        if 'id' in leads_df.columns and pd.notna(lead.get('id')):
                            # Use actual database ID
                            actual_id = int(lead['id'])
                            success = db_manager.update_lead_status(actual_id, new_status, notes, user_id)
                            if success:
                                st.success(f"✅ Status updated to {new_status}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update status in database")
                        else:
                            st.warning("⚠️ Cannot update: Database ID not available")
                    except Exception as e:
                        st.error(f"❌ Error updating status: {str(e)}")
    
    # Also show the original dataframe for reference
    st.write("**Full Data Table (Read-only)**")
    
    # Add a note about IDs
    if 'id' in leads_df.columns:
        st.info("💡 **Note**: Use the 'ID' column for accurate lead identification. The database ID ensures proper updates.")
    
    st.dataframe(leads_df, use_container_width=True)

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
            st.dataframe(search_results, use_container_width=True)
        else:
            st.info("No leads found matching your search term")
    
    # Filter by status
    st.subheader("📊 Filter by Status")
    status_filter = st.selectbox("Select Status", ["All"] + LEAD_STATUSES)
    
    if status_filter != "All":
        filtered_df = leads_df[leads_df['lead_status'] == status_filter]
        st.write(f"**Leads with status: {status_filter}**")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.write("**All Leads**")
        st.dataframe(leads_df, use_container_width=True)

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
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Priority Distribution")
            if user_stats.get('priority_counts'):
                priority_data = pd.DataFrame(list(user_stats['priority_counts'].items()), columns=['Priority', 'Count'])
                fig = px.bar(priority_data, x='Priority', y='Count')
                st.plotly_chart(fig, use_container_width=True)
    
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
                st.plotly_chart(fig, use_container_width=True)
                
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
