import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from data_cleaner import LeadsDataCleaner
from lead_manager import LeadManager

# Page configuration
st.set_page_config(
    page_title="Bumuk Library CRM",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-new { color: #ff7f0e; font-weight: bold; }
    .status-contacted { color: #2ca02c; font-weight: bold; }
    .status-qualified { color: #d62728; font-weight: bold; }
    .status-proposal { color: #9467bd; font-weight: bold; }
    .status-negotiation { color: #8c564b; font-weight: bold; }
    .status-closed { color: #e377c2; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'leads_data' not in st.session_state:
    st.session_state.leads_data = None
if 'lead_manager' not in st.session_state:
    st.session_state.lead_manager = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

def main():
    # Header
    st.markdown('<h1 class="main-header">📚 Bumuk Library CRM System</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'leads_data' not in st.session_state:
        st.session_state.leads_data = None
    if 'lead_manager' not in st.session_state:
        st.session_state.lead_manager = None
    
    # Try to auto-load saved data
    if not st.session_state.data_loaded:
        try:
            lead_manager = LeadManager()
            if lead_manager.load_saved_leads_data():
                st.session_state.leads_data = lead_manager.leads_data
                st.session_state.lead_manager = lead_manager
                st.session_state.data_loaded = True
                st.success("✅ Auto-loaded previously saved CRM data")
        except Exception as e:
            st.info("ℹ️ No saved data found. Upload a new file to get started.")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 System Controls")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Leads Excel File",
            type=['xlsx', 'xls'],
            help="Upload your leads Excel file with multiple sheets"
        )
        
        # AI Enrichment toggle
        enable_ai = st.checkbox(
            "Enable AI Enrichment",
            help="Use ChatGPT API to enrich lead data with industry insights"
        )
        
        if enable_ai:
            # Check if API key is in environment
            import os
            from dotenv import load_dotenv
            load_dotenv()
            env_api_key = os.getenv('OPENAI_API_KEY')
            
            if env_api_key and env_api_key != 'your_openai_api_key_here':
                st.success("✅ API key found in .env file")
                openai_key = env_api_key
            else:
                openai_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Enter your OpenAI API key or set OPENAI_API_KEY in .env file"
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
        
        # System Reset Section
        st.subheader("🔄 System Reset")
        
        if st.button("🗑️ Reset All Data", type="secondary", help="Clear all loaded data and start fresh"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear saved data files
            import os
            import glob
            
            # Remove all saved data files
            data_files = glob.glob("crm_data/*.xlsx")
            for file in data_files:
                try:
                    os.remove(file)
                    st.success(f"✅ Removed: {os.path.basename(file)}")
                except Exception as e:
                    st.error(f"❌ Error removing {os.path.basename(file)}: {str(e)}")
            
            st.success("🔄 System reset complete! Upload new data to continue.")
            st.rerun()
        
        # Data Management Section
        st.subheader("💾 Data Management")
        
        if st.button("💾 Save Current Data", help="Manually save current data to permanent storage"):
            if 'lead_manager' in st.session_state and 'leads_data' in st.session_state:
                try:
                    st.session_state.lead_manager._save_leads_data()
                    st.success("✅ Data saved successfully!")
                except Exception as e:
                    st.error(f"❌ Error saving data: {str(e)}")
            else:
                st.warning("⚠️ No data loaded to save")
        
        # Data processing buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if uploaded_file and st.button("🚀 Load & Process Data", type="primary"):
                # Clear previous session state to avoid conflicts
                if 'leads_data' in st.session_state:
                    del st.session_state.leads_data
                if 'lead_manager' in st.session_state:
                    del st.session_state.lead_manager
                if 'data_loaded' in st.session_state:
                    del st.session_state.data_loaded
                
                # Create progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: File preparation
                    status_text.text("📁 Preparing file...")
                    progress_bar.progress(10)
                    
                    # Save uploaded file temporarily with unique name
                    import uuid
                    temp_path = f"temp_{uuid.uuid4().hex}_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    progress_bar.progress(20)
                    status_text.text("🔍 Loading Excel sheets...")
                    
                    # Initialize lead manager
                    lead_manager = LeadManager()
                    
                    # Load and clean data with progress updates
                    leads_df = lead_manager.load_cleaned_leads(temp_path, enable_ai=enable_ai)
                    
                    progress_bar.progress(70)
                    status_text.text("👥 Assigning leads to sales team...")
                    
                    # Assign leads to sales team
                    if sales_team:
                        leads_df = lead_manager.assign_leads_to_sales_team(sales_team)
                    
                    progress_bar.progress(90)
                    status_text.text("💾 Finalizing data...")
                    
                    # Store in session state
                    st.session_state.leads_data = leads_df
                    st.session_state.lead_manager = lead_manager
                    st.session_state.data_loaded = True
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass  # Ignore cleanup errors
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    
                    # Show processing summary
                    st.success(f"🎉 Successfully processed {len(leads_df)} leads!")
                    
                    # Display processing summary
                    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                    with summary_col1:
                        st.metric("Total Leads", len(leads_df))
                    with summary_col2:
                        st.metric("Sales Team", len(sales_team) if sales_team else 0)
                    with summary_col3:
                        st.metric("Data Quality", f"{leads_df['lead_score'].mean():.0f}/100")
                    with summary_col4:
                        st.metric("High Priority", len(leads_df[leads_df['priority'] == 'High']))
                    
                    # Show sample of processed data
                    st.subheader("📋 Sample of Processed Leads")
                    sample_cols = ['full_name', 'phone_number', 'email', 'city', 'priority', 'assigned_to']
                    available_cols = [col for col in sample_cols if col in leads_df.columns]
                    st.dataframe(leads_df[available_cols].head(10), width='stretch')
                    
                    # Show data quality metrics
                    st.subheader("📊 Data Quality Summary")
                    metrics_col1, metrics_col2 = st.columns(2)
                    
                    with metrics_col1:
                        # Priority distribution
                        priority_counts = leads_df['priority'].value_counts()
                        st.write("**Priority Distribution:**")
                        for priority, count in priority_counts.items():
                            st.write(f"• {priority}: {count} leads")
                    
                    with metrics_col2:
                        # Sales team distribution
                        if 'assigned_to' in leads_df.columns:
                            team_counts = leads_df['assigned_to'].value_counts()
                            st.write("**Sales Team Distribution:**")
                            for member, count in team_counts.items():
                                st.write(f"• {member}: {count} leads")
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("❌ Processing failed!")
                    st.error(f"❌ Error processing data: {str(e)}")
                    st.error("Please check your file format and try again.")
                    
                    # Show detailed error for debugging
                    with st.expander("🔍 Error Details (Click to expand)"):
                        st.code(str(e))
                        st.write("**Troubleshooting tips:**")
                        st.write("• Try refreshing the page and uploading again")
                        st.write("• Check if your Excel file is not corrupted")
                        st.write("• Ensure the file is not too large (>50MB)")
                        st.write("• Try closing and reopening the dashboard")
        
        with col2:
            col2a, col2b = st.columns(2)
            with col2a:
                if st.button("💾 Save Data", help="Manually save current data to permanent storage"):
                    if st.session_state.lead_manager:
                        if st.session_state.lead_manager._save_leads_data():
                            st.success("✅ Data saved successfully!")
                        else:
                            st.error("❌ Failed to save data")
                    else:
                        st.warning("⚠️ No data to save")
            
            with col2b:
                if st.button("🔄 Reset Session", help="Clear all data and start fresh"):
                    # Clear all session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.success("✅ Session reset! Upload your file again.")
                    st.rerun()
    
    # Main content area
    if st.session_state.data_loaded and st.session_state.leads_data is not None:
        display_crm_dashboard()
    else:
        display_welcome_screen()

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
    - Use the **🗑️ Reset All Data** button in the sidebar
    - This will clear all loaded data and saved files
    - You can then upload the corrected Excel file
    
    """)
    
    # Quick Reset Section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Tip**: Use the sidebar reset button to clear data and start fresh!")
    
    with col2:
        if st.button("🗑️ Quick Reset", type="secondary", help="Quick reset from welcome screen"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear saved data files
            import os
            import glob
            
            # Remove all saved data files
            data_files = glob.glob("crm_data/*.xlsx")
            for file in data_files:
                try:
                    os.remove(file)
                except Exception as e:
                    pass
            
            st.success("🔄 System reset complete! Upload new data to continue.")
            st.rerun()

def display_crm_dashboard():
    """Display the main CRM dashboard"""
    leads_df = st.session_state.leads_data
    lead_manager = st.session_state.lead_manager
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(leads_df))
    
    with col2:
        new_leads = len(leads_df[leads_df['lead_status'] == 'New'])
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
        display_dashboard_tab(leads_df, lead_manager)
    
    with tab2:
        display_leads_management_tab(leads_df, lead_manager)
    
    with tab3:
        display_search_filter_tab(leads_df)
    
    with tab4:
        display_analytics_tab(leads_df)
    
    with tab5:
        display_ai_insights_tab(leads_df)
    
    with tab6:
        display_export_tab(leads_df, lead_manager)

def display_dashboard_tab(leads_df, lead_manager):
    """Display the main dashboard with charts and metrics"""
    st.header("📊 Sales Pipeline Dashboard")
    
    # Get pipeline summary
    summary = lead_manager.get_sales_pipeline_summary()
    
    # Two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Leads by Status
        if 'leads_by_status' in summary:
            status_data = summary['leads_by_status']
            fig_status = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Leads by Status",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_status, width='stretch')
    
    with col2:
        # Leads by Priority
        if 'leads_by_priority' in summary:
            priority_data = summary['leads_by_priority']
            fig_priority = px.bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                title="Leads by Priority",
                color=list(priority_data.values()),
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_priority, width='stretch')
    
    # Follow-up alerts
    st.subheader("🔔 Follow-up Alerts")
    follow_up_leads = lead_manager.get_leads_needing_follow_up(days_threshold=7)
    
    if not follow_up_leads.empty:
        st.warning(f"⚠️ {len(follow_up_leads)} leads need follow-up within 7 days")
        
        # Display follow-up table
        follow_up_display = follow_up_leads[['full_name', 'lead_status', 'priority', 'assigned_to']].head(10)
        st.dataframe(follow_up_display, width='stretch')
    else:
        st.success("✅ All leads are up to date with follow-ups!")

def display_leads_management_tab(leads_df, lead_manager):
    """Display leads management interface"""
    st.header("👥 Leads Management")
    
    # Status update section
    st.subheader("📝 Update Lead Status")
    
    # Method 1: Quick Update by Lead ID
    st.write("**Method 1: Quick Update by Lead ID**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lead_id = st.number_input("Lead ID", min_value=0, max_value=len(leads_df)-1, value=0)
    
    with col2:
        new_status = st.selectbox("New Status", lead_manager.lead_statuses)
    
    with col3:
        notes = st.text_input("Notes", placeholder="Add status update notes...")
    
    if st.button("Update Status"):
        if lead_manager.update_lead_status(lead_id, new_status, notes):
            st.success(f"✅ Lead {lead_id} status updated to {new_status}")
            # Refresh data
            st.session_state.leads_data = lead_manager.leads_data
            st.rerun()
        else:
            st.error("❌ Failed to update lead status")
    
    st.divider()
    
    # Method 2: Search and Update Specific Lead
    st.write("**Method 2: Search and Update Specific Lead**")
    search_name = st.text_input("Search Lead by Name", placeholder="Enter lead name...")
    
    if search_name:
        # Search for the lead
        search_results = st.session_state.lead_manager.search_leads(search_name, ['full_name'])
        if not search_results.empty:
            st.success(f"🔍 Found {len(search_results)} matching leads")
            
            # Show search results and allow selection
            for idx, lead in search_results.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{lead.get('full_name', 'Unknown')}**")
                    st.write(f"Phone: {lead.get('phone_number', 'N/A')}")
                with col2:
                    st.write(f"Current: **{lead.get('lead_status', 'N/A')}**")
                with col3:
                    st.write(f"Priority: {lead.get('priority', 'N/A')}")
                with col4:
                    if st.button(f"Update", key=f"update_{idx}"):
                        st.session_state.selected_lead_id = idx
                        st.session_state.show_update_form = True
                        st.rerun()
            
            # Show update form if lead selected
            if st.session_state.get('show_update_form', False) and st.session_state.get('selected_lead_id') is not None:
                st.write("**Update Selected Lead**")
                selected_id = st.session_state.selected_lead_id
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_status_search = st.selectbox("New Status", lead_manager.lead_statuses, key="search_status")
                with col2:
                    notes_search = st.text_input("Notes", placeholder="Add status update notes...", key="search_notes")
                with col3:
                    if st.button("Save Update"):
                        if lead_manager.update_lead_status(selected_id, new_status_search, notes_search):
                            st.success(f"✅ Lead status updated successfully!")
                            st.session_state.show_update_form = False
                            st.session_state.selected_lead_id = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to update lead status")
        else:
            st.info("No leads found matching your search term")
    
    st.divider()
    
    # Method 3: Bulk Status Updates
    st.write("**Method 3: Bulk Status Updates**")
    st.info("Select multiple leads to update their status in bulk")
    
    # Get leads by current status for bulk update
    current_status = st.selectbox("Select leads with status", lead_manager.lead_statuses, key="bulk_status")
    status_leads = lead_manager.get_leads_by_status(current_status)
    
    if not status_leads.empty:
        st.write(f"Found {len(status_leads)} leads with status: {current_status}")
        
        # Show leads with checkboxes
        selected_leads = []
        for idx, lead in status_leads.iterrows():
            if st.checkbox(f"{lead.get('full_name', 'Unknown')} - {lead.get('phone_number', 'N/A')}", key=f"bulk_{idx}"):
                selected_leads.append(idx)
        
        if selected_leads:
            st.write(f"Selected {len(selected_leads)} leads for bulk update")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                bulk_new_status = st.selectbox("New Status", lead_manager.lead_statuses, key="bulk_new_status")
            with col2:
                bulk_notes = st.text_input("Notes for all selected leads", placeholder="Bulk update notes...", key="bulk_notes")
            with col3:
                if st.button("Bulk Update"):
                    updated_count = 0
                    for lead_id in selected_leads:
                        if lead_manager.update_lead_status(lead_id, bulk_new_status, bulk_notes):
                            updated_count += 1
                    
                    if updated_count > 0:
                        st.success(f"✅ Successfully updated {updated_count} leads to {bulk_new_status}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update any leads")
    
    # Display leads table
    st.subheader("📋 All Leads")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All"] + lead_manager.lead_statuses)
    
    with col2:
        priority_filter = st.selectbox("Filter by Priority", ["All"] + lead_manager.priority_levels)
    
    with col3:
        if 'assigned_to' in leads_df.columns:
            sales_filter = st.selectbox("Filter by Sales Person", ["All"] + list(leads_df['assigned_to'].unique()))
        else:
            sales_filter = "All"
    
    # Apply filters
    filtered_df = leads_df.copy()
    
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['lead_status'] == status_filter]
    
    if priority_filter != "All":
        filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
    
    if sales_filter != "All" and 'assigned_to' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['assigned_to'] == sales_filter]
    
    # Display filtered data with quick status updates
    st.write("**Quick Status Updates: Click Update button for any lead**")
    
    # Create an interactive table with status update buttons
    for idx, lead in filtered_df.iterrows():
        with st.expander(f"📋 {lead.get('full_name', 'Unknown')} - {lead.get('lead_status', 'N/A')}", expanded=False):
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
            
            with col3:
                st.write(f"**Quick Update:**")
                new_status = st.selectbox("New Status", lead_manager.lead_statuses, key=f"status_{idx}")
                notes = st.text_input("Notes", placeholder="Add update notes...", key=f"notes_{idx}")
                
                if st.button("💾 Update Status", key=f"update_{idx}"):
                    if lead_manager.update_lead_status(idx, new_status, notes):
                        st.success(f"✅ Status updated to {new_status}")
                        # Refresh the page to show updated data
                        st.rerun()
                    else:
                        st.error("❌ Failed to update status")
    
    # Also show the original dataframe for reference
    st.write("**Full Data Table (Read-only)**")
    st.dataframe(filtered_df, width='stretch')

def display_search_filter_tab(leads_df):
    """Display search and filter functionality"""
    st.header("🔍 Search & Filter Leads")
    
    # Search functionality
    search_term = st.text_input("Search Leads", placeholder="Enter name, company, email, or phone...")
    
    if search_term:
        search_results = st.session_state.lead_manager.search_leads(search_term)
        if not search_results.empty:
            st.success(f"🔍 Found {len(search_results)} matching leads")
            st.dataframe(search_results, width='stretch')
        else:
            st.info("No leads found matching your search term")
    
    # Advanced filters
    st.subheader("🔧 Advanced Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Date range filter
        if 'cleaned_date' in leads_df.columns:
            st.date_input("From Date", value=leads_df['cleaned_date'].min())
            st.date_input("To Date", value=leads_df['cleaned_date'].max())
    
    with col2:
        # Lead score filter
        if 'lead_score' in leads_df.columns:
            min_score = st.slider("Minimum Lead Score", 0, 100, 0)
            max_score = st.slider("Maximum Lead Score", 0, 100, 100)
            
            score_filtered = leads_df[
                (leads_df['lead_score'] >= min_score) & 
                (leads_df['lead_score'] <= max_score)
            ]
            st.metric("Filtered Leads", len(score_filtered))

def display_analytics_tab(leads_df):
    """Display analytics and insights"""
    st.header("📈 Analytics & Insights")
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Lead Quality Analysis")
        
        if 'lead_score' in leads_df.columns:
            # Lead score distribution
            fig_score = px.histogram(
                leads_df, 
                x='lead_score',
                nbins=20,
                title="Lead Score Distribution"
            )
            st.plotly_chart(fig_score, width='stretch')
    
    with col2:
        st.subheader("🎯 Conversion Analysis")
        
        if 'lead_status' in leads_df.columns:
            # Status progression
            status_order = ['New', 'Contacted', 'Qualified', 'Proposal Sent', 'Negotiation', 'Closed Won', 'Closed Lost']
            status_counts = [len(leads_df[leads_df['lead_status'] == status]) for status in status_order]
            
            fig_funnel = go.Figure(data=go.Funnel(
                y=status_order,
                x=status_counts,
                textinfo="value+percent initial"
            ))
            fig_funnel.update_layout(title="Sales Funnel")
            st.plotly_chart(fig_funnel, width='stretch')
    
    # Time-based analysis
    st.subheader("⏰ Time-based Analysis")
    
    if 'cleaned_date' in leads_df.columns:
        # Leads over time
        leads_df['cleaned_date'] = pd.to_datetime(leads_df['cleaned_date'])
        daily_leads = leads_df.groupby(leads_df['cleaned_date'].dt.date).size().reset_index()
        daily_leads.columns = ['Date', 'Count']
        
        fig_timeline = px.line(
            daily_leads,
            x='Date',
            y='Count',
            title="Leads Added Over Time"
        )
        st.plotly_chart(fig_timeline, width='stretch')

def display_ai_insights_tab(leads_df):
    """Display AI-powered customer insights"""
    st.header("🤖 AI-Powered Customer Insights")
    
    # Check if AI enrichment was enabled
    ai_fields = ['ai_customer_segment', 'ai_potential_value', 'ai_engagement_strategy', 'ai_library_benefits']
    has_ai_data = any(field in leads_df.columns for field in ai_fields)
    
    if not has_ai_data:
        st.info("💡 **AI Enrichment not enabled yet!** To get customer insights:")
        st.markdown("""
        1. **Enable AI Enrichment** in the sidebar
        2. **Add your OpenAI API key**
        3. **Reload your data** to get AI insights
        
        AI will analyze each lead and provide:
        - **Customer Segment**: Parent, Student, Professional, Senior, etc.
        - **Potential Value**: Based on usage patterns and family size
        - **Engagement Strategy**: Personalized approach for each customer
        - **Library Benefits**: Most relevant features to highlight
        """)
        return
    
    # Display AI insights summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'ai_customer_segment' in leads_df.columns:
            segments = leads_df['ai_customer_segment'].value_counts()
            st.metric("Customer Segments", len(segments))
        else:
            st.metric("Customer Segments", "N/A")
    
    with col2:
        if 'ai_potential_value' in leads_df.columns:
            high_value = len(leads_df[leads_df['ai_potential_value'] == 'High'])
            st.metric("High Value Leads", high_value)
        else:
            st.metric("High Value Leads", "N/A")
    
    with col3:
        if 'ai_potential_value' in leads_df.columns:
            avg_value = leads_df['ai_potential_value'].value_counts().index.tolist()
            st.metric("Value Levels", ", ".join(avg_value[:3]))
        else:
            st.metric("Value Levels", "N/A")
    
    with col4:
        if 'ai_engagement_strategy' in leads_df.columns:
            strategies = leads_df['ai_engagement_strategy'].nunique()
            st.metric("Unique Strategies", strategies)
        else:
            st.metric("Unique Strategies", "N/A")
    
    # Customer segment analysis
    st.subheader("🎯 Customer Segment Analysis")
    
    if 'ai_customer_segment' in leads_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of customer segments
            segment_counts = leads_df['ai_customer_segment'].value_counts()
            fig_segments = px.pie(
                values=segment_counts.values,
                names=segment_counts.index,
                title="Customer Segments Distribution"
            )
            st.plotly_chart(fig_segments, width='stretch')
        
        with col2:
            # Value distribution by segment
            if 'ai_potential_value' in leads_df.columns:
                segment_value = leads_df.groupby(['ai_customer_segment', 'ai_potential_value']).size().reset_index(name='count')
                fig_value = px.bar(
                    segment_value,
                    x='ai_customer_segment',
                    y='count',
                    color='ai_potential_value',
                    title="Value Distribution by Customer Segment"
                )
                st.plotly_chart(fig_value, width='stretch')
    
    # Individual lead insights
    st.subheader("🔍 Individual Lead Insights")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        if 'ai_customer_segment' in leads_df.columns:
            segment_filter = st.selectbox("Filter by Customer Segment", ["All"] + list(leads_df['ai_customer_segment'].unique()))
        else:
            segment_filter = "All"
    
    with col2:
        if 'ai_potential_value' in leads_df.columns:
            value_filter = st.selectbox("Filter by Potential Value", ["All"] + list(leads_df['ai_potential_value'].unique()))
        else:
            value_filter = "All"
    
    # Apply filters
    filtered_ai_df = leads_df.copy()
    
    if segment_filter != "All":
        filtered_ai_df = filtered_ai_df[filtered_ai_df['ai_customer_segment'] == segment_filter]
    
    if value_filter != "All":
        filtered_ai_df = filtered_ai_df[filtered_ai_df['ai_potential_value'] == value_filter]
    
    # Display filtered leads with AI insights
    if not filtered_ai_df.empty:
        ai_display_cols = ['full_name', 'phone_number', 'email', 'city']
        ai_display_cols.extend([col for col in ai_fields if col in filtered_ai_df.columns])
        
        st.dataframe(filtered_ai_df[ai_display_cols], width='stretch')
    else:
        st.info("No leads match the selected filters.")

def display_export_tab(leads_df, lead_manager):
    """Display export functionality"""
    st.header("📤 Export & Reports")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export Data")
        
        export_format = st.selectbox("Export Format", ["Excel", "CSV"])
        
        if st.button("Export All Leads"):
            try:
                # Generate proper filename with correct extension
                if export_format.lower() == "excel":
                    filename = f"bumuk_leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                else:
                    filename = f"bumuk_leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                # Export the data
                exported_file = lead_manager.export_leads_report(filename, export_format.lower())
                
                # Create download link
                with open(exported_file, "rb") as f:
                    st.download_button(
                        label=f"Download {os.path.basename(exported_file)}",
                        data=f.read(),
                        file_name=os.path.basename(exported_file),
                        mime="application/octet-stream"
                    )
                
                # Clean up
                try:
                    os.remove(exported_file)
                except:
                    pass
                
                st.success(f"✅ Exported {len(leads_df)} leads to {os.path.basename(exported_file)}")
                
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                st.error("Please try again or contact support.")
    
    with col2:
        st.subheader("📋 Custom Reports")
        
        report_type = st.selectbox("Report Type", [
            "High Priority Leads",
            "Leads by Status",
            "Sales Team Performance",
            "Follow-up Report"
        ])
        
        if st.button("Generate Report"):
            with st.spinner("Generating report..."):
                if report_type == "High Priority Leads":
                    report_data = leads_df[leads_df['priority'].isin(['High', 'Urgent'])]
                elif report_type == "Leads by Status":
                    report_data = leads_df.groupby('lead_status').size().reset_index()
                    report_data.columns = ['Status', 'Count']
                elif report_type == "Sales Team Performance":
                    if 'assigned_to' in leads_df.columns:
                        report_data = leads_df.groupby('assigned_to').agg({
                            'lead_status': 'count',
                            'lead_score': 'mean'
                        }).reset_index()
                        report_data.columns = ['Sales Person', 'Total Leads', 'Avg Score']
                    else:
                        report_data = pd.DataFrame()
                elif report_type == "Follow-up Report":
                    report_data = lead_manager.get_leads_needing_follow_up()
                
                if not report_data.empty:
                    st.success(f"✅ Generated {report_type}")
                    st.dataframe(report_data, width='stretch')
                else:
                    st.info("No data available for this report type")

if __name__ == "__main__":
    main()
