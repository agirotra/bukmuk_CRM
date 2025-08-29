import sqlite3
import pandas as pd
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import streamlit as st

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for CRM data persistence"""
    
    def __init__(self, db_path: str = "crm_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create leads table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        full_name TEXT,
                        phone_number TEXT,
                        email TEXT,
                        city TEXT,
                        lead_status TEXT DEFAULT 'New Lead',
                        priority TEXT DEFAULT 'Medium',
                        lead_score REAL,
                        assigned_to TEXT,
                        source_sheet TEXT,
                        lead_date TEXT,
                        status_updated_date TEXT,
                        last_contact_date TEXT,
                        follow_up_date TEXT,
                        follow_up_count INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                ''')
                
                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Create audit log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        record_id INTEGER,
                        old_values TEXT,
                        new_values TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def save_leads_data(self, leads_df: pd.DataFrame, user_id: str) -> bool:
        """Save leads data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing leads for this user
                cursor = conn.cursor()
                cursor.execute("DELETE FROM leads WHERE user_id = ?", (user_id,))
                
                # Insert new leads data
                for _, row in leads_df.iterrows():
                    cursor.execute('''
                        INSERT INTO leads (
                            user_id, full_name, phone_number, email, city, 
                            lead_status, priority, lead_score, assigned_to, 
                            source_sheet, lead_date, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        row.get('full_name'),
                        row.get('phone_number'),
                        row.get('email'),
                        row.get('city'),
                        row.get('lead_status', 'New Lead'),
                        row.get('priority', 'Medium'),
                        row.get('lead_score', 0.0),
                        row.get('assigned_to'),
                        row.get('source_sheet'),
                        row.get('lead_date'),
                        row.get('notes')
                    ))
                
                conn.commit()
                logger.info(f"Saved {len(leads_df)} leads for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving leads data: {str(e)}")
            return False
    
    def load_leads_data(self, user_id: str) -> pd.DataFrame:
        """Load leads data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM leads WHERE user_id = ? ORDER BY created_at DESC"
                df = pd.read_sql_query(query, conn, params=(user_id,))
                
                if not df.empty:
                    # Convert timestamp columns
                    timestamp_columns = ['created_at', 'updated_at', 'status_updated_date', 'last_contact_date', 'follow_up_date']
                    for col in timestamp_columns:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col])
                    
                    logger.info(f"Loaded {len(df)} leads for user {user_id}")
                else:
                    logger.info(f"No leads found for user {user_id}")
                
                return df
                
        except Exception as e:
            logger.error(f"Error loading leads data: {str(e)}")
            return pd.DataFrame()
    
    def update_lead_status(self, lead_id: int, new_status: str, notes: str, user_id: str) -> bool:
        """Update lead status in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get old values for audit log
                cursor.execute("SELECT * FROM leads WHERE id = ? AND user_id = ?", (lead_id, user_id))
                old_values = cursor.fetchone()
                
                if old_values:
                    # Update lead
                    cursor.execute('''
                        UPDATE leads 
                        SET lead_status = ?, notes = ?, status_updated_date = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (new_status, notes, datetime.now().isoformat(), lead_id, user_id))
                    
                    # Log the change
                    cursor.execute('''
                        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, 'UPDATE', 'leads', lead_id,
                        json.dumps(dict(zip([col[0] for col in cursor.description], old_values))),
                        json.dumps({'lead_status': new_status, 'notes': notes})
                    ))
                    
                    conn.commit()
                    logger.info(f"Updated lead {lead_id} status to {new_status}")
                    return True
                else:
                    logger.warning(f"Lead {lead_id} not found for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            return False
    
    def get_leads_by_status(self, status: str, user_id: str) -> pd.DataFrame:
        """Get leads filtered by status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM leads WHERE lead_status = ? AND user_id = ? ORDER BY created_at DESC"
                df = pd.read_sql_query(query, conn, params=(status, user_id))
                return df
        except Exception as e:
            logger.error(f"Error getting leads by status: {str(e)}")
            return pd.DataFrame()
    
    def search_leads(self, search_term: str, user_id: str, columns: List[str] = None) -> pd.DataFrame:
        """Search leads by term across specified columns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if not columns:
                    columns = ['full_name', 'phone_number', 'email', 'city']
                
                # Build search query
                search_conditions = []
                params = [user_id]
                
                for col in columns:
                    search_conditions.append(f"{col} LIKE ?")
                    params.append(f"%{search_term}%")
                
                query = f"SELECT * FROM leads WHERE user_id = ? AND ({' OR '.join(search_conditions)}) ORDER BY created_at DESC"
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return pd.DataFrame()
    
    def export_leads_report(self, user_id: str, format: str = 'csv') -> str:
        """Export leads data in specified format"""
        try:
            df = self.load_leads_data(user_id)
            
            if df.empty:
                return "No data to export"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == 'csv':
                filename = f"leads_export_{timestamp}.csv"
                df.to_csv(filename, index=False)
            elif format.lower() == 'excel':
                filename = f"leads_export_{timestamp}.xlsx"
                df.to_excel(filename, index=False, engine='openpyxl')
            else:
                return f"Unsupported format: {format}"
            
            logger.info(f"Exported {len(df)} leads to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting leads: {str(e)}")
            return f"Export failed: {str(e)}"
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total leads
                cursor.execute("SELECT COUNT(*) FROM leads WHERE user_id = ?", (user_id,))
                total_leads = cursor.fetchone()[0]
                
                # Leads by status
                cursor.execute("""
                    SELECT lead_status, COUNT(*) 
                    FROM leads 
                    WHERE user_id = ? 
                    GROUP BY lead_status
                """, (user_id,))
                status_counts = dict(cursor.fetchall())
                
                # Leads by priority
                cursor.execute("""
                    SELECT priority, COUNT(*) 
                    FROM leads 
                    WHERE user_id = ? 
                    GROUP BY priority
                """, (user_id,))
                priority_counts = dict(cursor.fetchall())
                
                return {
                    'total_leads': total_leads,
                    'status_counts': status_counts,
                    'priority_counts': priority_counts
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up old audit log entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM audit_log 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old audit log entries")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return 0
