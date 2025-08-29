import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Optional, Tuple
from data_cleaner import LeadsDataCleaner

logger = logging.getLogger(__name__)

class LeadManager:
    """
    Comprehensive lead management system for Bumuk Library CRM
    """
    
    def __init__(self):
        self.leads_data = None
        self.sales_team = []
        
        # Load configurations
        from config import LEAD_STATUSES, PRIORITY_LEVELS, FOLLOW_UP_SCHEDULE, FOLLOW_UP_ALERTS
        
        self.lead_statuses = LEAD_STATUSES
        self.priority_levels = PRIORITY_LEVELS
        self.follow_up_schedule = FOLLOW_UP_SCHEDULE
        self.follow_up_alerts = FOLLOW_UP_ALERTS
        
    def load_cleaned_leads(self, file_path: str, enable_ai: bool = False) -> pd.DataFrame:
        """
        Load and clean leads data using the data cleaner
        """
        try:
            cleaner = LeadsDataCleaner()
            
            # Setup OpenAI if AI enrichment is requested
            if enable_ai:
                cleaner.setup_openai()
            
            # Clean all data from multiple sheets
            self.leads_data = cleaner.clean_all_data(file_path, enable_ai_enrichment=enable_ai)
            
            logger.info(f"Successfully loaded {len(self.leads_data)} cleaned leads")
            return self.leads_data
            
        except Exception as e:
            logger.error(f"Error loading leads: {str(e)}")
            raise
    
    def assign_leads_to_sales_team(self, sales_team_members: List[str]) -> pd.DataFrame:
        """
        Automatically assign leads to sales team members
        """
        if self.leads_data is None:
            raise ValueError("No leads data loaded. Run load_cleaned_leads() first.")
        
        df = self.leads_data.copy()
        
        # Round-robin assignment
        df['assigned_to'] = [sales_team_members[i % len(sales_team_members)] 
                           for i in range(len(df))]
        
        # Priority-based assignment for high-value leads
        high_priority_mask = df['priority'] == 'High'
        if high_priority_mask.any():
            # Assign high priority leads to top performers
            top_performers = sales_team_members[:min(2, len(sales_team_members))]
            high_priority_indices = df[high_priority_mask].index
            for idx in high_priority_indices:
                df.loc[idx, 'assigned_to'] = top_performers[idx % len(top_performers)]
        
        self.leads_data = df
        logger.info(f"Assigned {len(df)} leads to {len(sales_team_members)} sales team members")
        
        return df
    
    def update_lead_status(self, lead_id: int, new_status: str, notes: str = "") -> bool:
        """
        Update the status of a specific lead and save to permanent storage
        """
        if self.leads_data is None:
            return False
        
        if lead_id >= len(self.leads_data):
            return False
        
        if new_status not in self.lead_statuses:
            return False
        
        # Update status
        self.leads_data.loc[lead_id, 'lead_status'] = new_status
        
        # Add timestamp
        if 'status_updated_date' not in self.leads_data.columns:
            self.leads_data['status_updated_date'] = None
        
        self.leads_data.loc[lead_id, 'status_updated_date'] = datetime.now()
        
        # Add notes
        if 'status_notes' not in self.leads_data.columns:
            self.leads_data['status_notes'] = ""
        
        current_notes = self.leads_data.loc[lead_id, 'status_notes']
        new_note = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {new_status} - {notes}"
        
        if pd.isna(current_notes) or current_notes == "":
            self.leads_data.loc[lead_id, 'status_notes'] = new_note
        else:
            self.leads_data.loc[lead_id, 'status_notes'] = current_notes + "\n" + new_note
        
        # Update follow-up count if moving to follow-up status
        if 'follow_up_count' not in self.leads_data.columns:
            self.leads_data['follow_up_count'] = 0
            
        if 'follow_up' in new_status.lower():
            current_count = self.leads_data.loc[lead_id, 'follow_up_count']
            self.leads_data.loc[lead_id, 'follow_up_count'] = current_count + 1
        
        # Set last contact date
        if 'last_contact_date' not in self.leads_data.columns:
            self.leads_data['last_contact_date'] = None
        
        self.leads_data.loc[lead_id, 'last_contact_date'] = datetime.now()
        
        # Auto-advance status if needed
        self._auto_advance_status(lead_id, new_status)
        
        # Save to permanent storage
        self._save_leads_data()
        
        logger.info(f"Updated lead {lead_id} status to {new_status} and saved to storage")
        return True
    
    def _save_leads_data(self):
        """
        Save leads data to permanent storage
        """
        if self.leads_data is None:
            return False
        
        try:
            # Create data directory if it doesn't exist
            data_dir = "crm_data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Save to Excel file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crm_data/leads_data_{timestamp}.xlsx"
            
            # Save current data
            self.leads_data.to_excel(filename, index=False, engine='openpyxl')
            
            # Also save as latest version (overwrites)
            latest_filename = "crm_data/leads_data_latest.xlsx"
            self.leads_data.to_excel(latest_filename, index=False, engine='openpyxl')
            
            # Save backup (keep last 5 versions)
            self._cleanup_old_backups()
            
            logger.info(f"Leads data saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save leads data: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """
        Keep only the last 5 backup files
        """
        try:
            data_dir = "crm_data"
            if not os.path.exists(data_dir):
                return
            
            # Get all backup files
            backup_files = [f for f in os.listdir(data_dir) if f.startswith("leads_data_") and f.endswith(".xlsx")]
            backup_files.sort(reverse=True)  # Sort by name (timestamp)
            
            # Remove old backups (keep only last 5)
            if len(backup_files) > 5:
                for old_file in backup_files[5:]:
                    os.remove(os.path.join(data_dir, old_file))
                    logger.info(f"Removed old backup: {old_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
    
    def load_saved_leads_data(self):
        """
        Load leads data from permanent storage
        """
        try:
            latest_filename = "crm_data/leads_data_latest.xlsx"
            
            if os.path.exists(latest_filename):
                self.leads_data = pd.read_excel(latest_filename)
                logger.info(f"Loaded saved leads data from {latest_filename}")
                return True
            else:
                logger.info("No saved leads data found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load saved leads data: {str(e)}")
            return False
    
    def _auto_advance_status(self, lead_id: int, current_status: str):
        """
        Automatically advance lead status based on business rules
        """
        if current_status == 'New Lead':
            # New leads should be contacted within 2 days
            pass
        elif current_status == 'Initial Contact':
            # After initial contact, schedule first follow-up
            pass
        elif current_status in ['Follow Up 1', 'Follow Up 2', 'Follow Up 3']:
            # Check if we should escalate or move to next stage
            follow_up_count = self.leads_data.loc[lead_id, 'follow_up_count']
            if follow_up_count >= 3:
                # After 3 follow-ups, move to appropriate status
                if self.leads_data.loc[lead_id, 'priority'] in ['High', 'Urgent']:
                    # High priority leads get more follow-ups
                    pass
                else:
                    # Move to re-engagement later
                    self.leads_data.loc[lead_id, 'lead_status'] = 'Re-engage Later'
                    logger.info(f"Auto-advanced lead {lead_id} to 'Re-engage Later' after 3 follow-ups")
    
    def get_leads_by_status(self, status: str) -> pd.DataFrame:
        """
        Get all leads with a specific status
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        return self.leads_data[self.leads_data['lead_status'] == status]
    
    def get_leads_by_priority(self, priority: str) -> pd.DataFrame:
        """
        Get all leads with a specific priority
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        return self.leads_data[self.leads_data['priority'] == priority]
    
    def get_leads_by_assigned_to(self, sales_person: str) -> pd.DataFrame:
        """
        Get all leads assigned to a specific sales person
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        return self.leads_data[self.leads_data['assigned_to'] == sales_person]
    
    def get_leads_needing_follow_up(self, days_threshold: int = 7) -> pd.DataFrame:
        """
        Get leads that need follow-up based on status and schedule
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        df = self.leads_data.copy()
        
        # Ensure required columns exist
        if 'follow_up_date' not in df.columns:
            df['follow_up_date'] = None
        if 'last_contact_date' not in df.columns:
            df['last_contact_date'] = None
        if 'follow_up_count' not in df.columns:
            df['follow_up_count'] = 0
        if 'status_updated_date' not in df.columns:
            df['status_updated_date'] = None
        
        today = datetime.now()
        
        # Calculate follow-up dates based on current status and schedule
        for idx, row in df.iterrows():
            current_status = row['lead_status']
            
            # Get follow-up schedule for this status
            if current_status in self.follow_up_schedule:
                days_to_add = self.follow_up_schedule[current_status]
                
                # Set follow-up date based on last contact or status update
                if pd.notna(row['status_updated_date']):
                    df.loc[idx, 'follow_up_date'] = row['status_updated_date'] + timedelta(days=days_to_add)
                elif pd.notna(row['last_contact_date']):
                    df.loc[idx, 'follow_up_date'] = row['last_contact_date'] + timedelta(days=days_to_add)
                else:
                    # If no contact date, use current time + schedule
                    df.loc[idx, 'follow_up_date'] = today + timedelta(days=days_to_add)
        
        # Filter leads that need follow-up
        overdue_leads = df[df['follow_up_date'] <= today]
        upcoming_leads = df[(df['follow_up_date'] > today) & (df['follow_up_date'] <= today + timedelta(days=days_threshold))]
        
        # Combine and sort by urgency
        all_follow_ups = pd.concat([overdue_leads, upcoming_leads])
        all_follow_ups = all_follow_ups.sort_values(['follow_up_date', 'priority'], ascending=[True, False])
        
        return all_follow_ups
    
    def get_overdue_follow_ups(self) -> pd.DataFrame:
        """
        Get leads that are overdue for follow-up
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        df = self.leads_data.copy()
        
        if 'follow_up_date' not in df.columns:
            return pd.DataFrame()
        
        today = datetime.now()
        overdue_threshold = today - timedelta(days=self.follow_up_alerts['overdue_days'])
        
        overdue_leads = df[df['follow_up_date'] <= overdue_threshold]
        return overdue_leads.sort_values(['follow_up_date', 'priority'], ascending=[True, False])
    
    def get_urgent_follow_ups(self) -> pd.DataFrame:
        """
        Get leads that need urgent follow-up (high priority + overdue)
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        overdue = self.get_overdue_follow_ups()
        urgent = overdue[overdue['priority'].isin(['High', 'Urgent'])]
        return urgent.sort_values(['follow_up_date', 'priority'], ascending=[True, False])
    
    def get_follow_up_summary(self) -> Dict:
        """
        Get comprehensive follow-up summary for dashboard
        """
        if self.leads_data is None:
            return {}
        
        today = datetime.now()
        
        # Get various follow-up categories
        overdue = self.get_overdue_follow_ups()
        urgent = self.get_urgent_follow_ups()
        today_follow_ups = self.get_leads_needing_follow_up(days_threshold=1)
        week_follow_ups = self.get_leads_needing_follow_up(days_threshold=7)
        
        summary = {
            'total_leads': len(self.leads_data),
            'overdue_follow_ups': len(overdue),
            'urgent_follow_ups': len(urgent),
            'today_follow_ups': len(today_follow_ups),
            'week_follow_ups': len(week_follow_ups),
            'overdue_by_status': overdue['lead_status'].value_counts().to_dict(),
            'overdue_by_priority': overdue['priority'].value_counts().to_dict(),
            'overdue_by_assigned': overdue['assigned_to'].value_counts().to_dict() if 'assigned_to' in overdue.columns else {},
            'next_follow_up': None
        }
        
        # Get next follow-up time
        if 'follow_up_date' in self.leads_data.columns:
            valid_dates = self.leads_data[self.leads_data['follow_up_date'].notna()]
            if not valid_dates.empty:
                next_follow_up = valid_dates['follow_up_date'].min()
                if pd.notna(next_follow_up):
                    summary['next_follow_up'] = next_follow_up.strftime('%Y-%m-%d %H:%M')
        
        return summary
    
    def get_sales_pipeline_summary(self) -> Dict:
        """
        Get summary statistics for the sales pipeline
        """
        if self.leads_data is None:
            return {}
        
        summary = {}
        
        # Total leads
        summary['total_leads'] = len(self.leads_data)
        
        # Leads by status
        status_counts = self.leads_data['lead_status'].value_counts().to_dict()
        summary['leads_by_status'] = status_counts
        
        # Leads by priority
        priority_counts = self.leads_data['priority'].value_counts().to_dict()
        summary['leads_by_priority'] = priority_counts
        
        # Leads by assigned sales person
        if 'assigned_to' in self.leads_data.columns:
            assigned_counts = self.leads_data['assigned_to'].value_counts().to_dict()
            summary['leads_by_assigned_to'] = assigned_counts
        
        # Average lead score
        if 'lead_score' in self.leads_data.columns:
            summary['average_lead_score'] = self.leads_data['lead_score'].mean()
        
        # Conversion rates (if we have historical data)
        if 'lead_status' in self.leads_data.columns:
            total_contacted = len(self.leads_data[self.leads_data['lead_status'].isin(['Contacted', 'Qualified', 'Proposal Sent', 'Negotiation', 'Closed Won', 'Closed Lost'])])
            summary['contact_rate'] = (total_contacted / summary['total_leads']) * 100 if summary['total_leads'] > 0 else 0
        
        return summary
    
    def export_leads_report(self, output_path: str, format: str = 'excel') -> str:
        """
        Export leads data to a report file
        """
        if self.leads_data is None:
            raise ValueError("No leads data available. Run load_cleaned_leads() first.")
        
        if format.lower() == 'excel':
            # Ensure output path has .xlsx extension
            if not output_path.endswith('.xlsx'):
                output_path = output_path.replace('.excel', '.xlsx').replace('.csv', '.xlsx')
                if not output_path.endswith('.xlsx'):
                    output_path += '.xlsx'
            
            # Try multiple Excel engines in order of preference
            excel_engines = ['openpyxl', 'xlsxwriter', 'xlwt']
            
            for engine in excel_engines:
                try:
                    self.leads_data.to_excel(output_path, index=False, engine=engine)
                    logger.info(f"Leads report exported to {output_path} using {engine}")
                    return output_path
                except ImportError:
                    logger.warning(f"Excel engine '{engine}' not available, trying next...")
                    continue
                except Exception as e:
                    logger.warning(f"Excel engine '{engine}' failed: {str(e)}, trying next...")
                    continue
            
            # If all Excel engines fail, fallback to CSV
            logger.warning("All Excel engines failed, falling back to CSV export")
            csv_path = output_path.replace('.xlsx', '.csv')
            self.leads_data.to_csv(csv_path, index=False)
            logger.info(f"Exported to CSV instead: {csv_path}")
            return csv_path
            
        elif format.lower() == 'csv':
            self.leads_data.to_csv(output_path, index=False)
            logger.info(f"Leads report exported to {output_path}")
            return output_path
        else:
            raise ValueError("Unsupported format. Use 'excel' or 'csv'.")
    
    def add_custom_field(self, field_name: str, default_value=None) -> bool:
        """
        Add a custom field to all leads
        """
        if self.leads_data is None:
            return False
        
        self.leads_data[field_name] = default_value
        logger.info(f"Added custom field: {field_name}")
        return True
    
    def bulk_update_status(self, lead_ids: List[int], new_status: str, notes: str = "") -> int:
        """
        Bulk update status for multiple leads
        """
        if self.leads_data is None:
            return 0
        
        updated_count = 0
        for lead_id in lead_ids:
            if self.update_lead_status(lead_id, new_status, notes):
                updated_count += 1
        
        logger.info(f"Bulk updated {updated_count} leads to status: {new_status}")
        return updated_count
    
    def get_lead_details(self, lead_id: int) -> Dict:
        """
        Get detailed information for a specific lead
        """
        if self.leads_data is None or lead_id >= len(self.leads_data):
            return {}
        
        lead_data = self.leads_data.iloc[lead_id].to_dict()
        return lead_data
    
    def search_leads(self, search_term: str, search_fields: List[str] = None) -> pd.DataFrame:
        """
        Search leads by text in specified fields
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        if search_fields is None:
            search_fields = ['full_name', 'email', 'phone_number', 'city']
        
        # Filter fields that exist in the dataframe
        available_fields = [field for field in search_fields if field in self.leads_data.columns]
        
        if not available_fields:
            return pd.DataFrame()
        
        # Create search mask
        search_mask = pd.Series([False] * len(self.leads_data))
        
        for field in available_fields:
            field_mask = self.leads_data[field].astype(str).str.contains(search_term, case=False, na=False)
            search_mask = search_mask | field_mask
        
        return self.leads_data[search_mask]
    
    def get_leads_needing_immediate_attention(self) -> pd.DataFrame:
        """
        Get leads that need immediate attention (overdue + high priority)
        """
        if self.leads_data is None:
            return pd.DataFrame()
        
        # Get overdue follow-ups
        overdue = self.get_overdue_follow_ups()
        
        # Filter for high priority and urgent leads
        immediate_attention = overdue[
            (overdue['priority'].isin(['High', 'Urgent'])) |
            (overdue['lead_status'].isin(['New Lead', 'Initial Contact', 'Interested', 'Trial Membership']))
        ]
        
        return immediate_attention.sort_values(['follow_up_date', 'priority'], ascending=[True, False])
    
    def get_daily_follow_up_tasks(self) -> Dict:
        """
        Get daily follow-up tasks organized by sales person
        """
        if self.leads_data is None:
            return {}
        
        # Get all follow-ups needed today and tomorrow
        today_follow_ups = self.get_leads_needing_follow_up(days_threshold=2)
        
        if today_follow_ups.empty:
            return {'message': 'No follow-ups needed in the next 2 days'}
        
        # Group by assigned sales person
        tasks_by_person = {}
        
        for _, lead in today_follow_ups.iterrows():
            assigned_to = lead.get('assigned_to', 'Unassigned')
            
            if assigned_to not in tasks_by_person:
                tasks_by_person[assigned_to] = {
                    'total_tasks': 0,
                    'overdue': 0,
                    'urgent': 0,
                    'leads': []
                }
            
            tasks_by_person[assigned_to]['total_tasks'] += 1
            
            # Check if overdue
            if pd.notna(lead.get('follow_up_date')) and lead['follow_up_date'] <= datetime.now():
                tasks_by_person[assigned_to]['overdue'] += 1
            
            # Check if urgent
            if lead.get('priority') in ['High', 'Urgent']:
                tasks_by_person[assigned_to]['urgent'] += 1
            
            # Add lead details
            lead_info = {
                'id': lead.name,
                'name': lead.get('full_name', 'Unknown'),
                'phone': lead.get('phone_number', ''),
                'email': lead.get('email', ''),
                'status': lead.get('lead_status', ''),
                'priority': lead.get('priority', ''),
                'follow_up_date': lead.get('follow_up_date', ''),
                'overdue': pd.notna(lead.get('follow_up_date')) and lead['follow_up_date'] <= datetime.now()
            }
            
            tasks_by_person[assigned_to]['leads'].append(lead_info)
        
        return tasks_by_person

# Example usage
if __name__ == "__main__":
    # Initialize lead manager
    manager = LeadManager()
    
    # Load and clean leads data
    leads_df = manager.load_cleaned_leads("Leads sheet for Geetika - BUKMUK.xlsx")
    
    # Assign leads to sales team
    sales_team = ["John", "Sarah", "Mike", "Lisa"]
    assigned_leads = manager.assign_leads_to_sales_team(sales_team)
    
    # Get pipeline summary
    summary = manager.get_sales_pipeline_summary()
    print("Sales Pipeline Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Export report
    manager.export_leads_report("bumuk_leads_report.xlsx")
