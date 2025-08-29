import streamlit as st
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages user authentication and session management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Create users table if not exists
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
                
                # Create sessions table if not exists
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
                
                # Insert default admin user if no users exist
                cursor.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()[0] == 0:
                    admin_password = self.hash_password("admin123")
                    cursor.execute('''
                        INSERT INTO users (username, email, password_hash, role)
                        VALUES (?, ?, ?, ?)
                    ''', ("admin", "admin@bumuk.com", admin_password, "admin"))
                    logger.info("Default admin user created: admin/admin123")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing auth tables: {str(e)}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Register a new user"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if username or email already exists
                cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
                if cursor.fetchone():
                    return {"success": False, "message": "Username or email already exists"}
                
                # Hash password and create user
                password_hash = self.hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, role))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"User {username} registered successfully")
                return {
                    "success": True, 
                    "message": "User registered successfully",
                    "user_id": user_id
                }
                
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and create session"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user by username
                cursor.execute("SELECT id, username, email, password_hash, role FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                
                if not user:
                    return {"success": False, "message": "Invalid username or password"}
                
                user_id, username, email, password_hash, role = user
                
                # Verify password
                if not self.verify_password(password, password_hash):
                    return {"success": False, "message": "Invalid username or password"}
                
                # Generate session token
                session_token = self.generate_session_token()
                expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
                
                # Create session
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, session_token, expires_at.isoformat()))
                
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                
                logger.info(f"User {username} logged in successfully")
                return {
                    "success": True,
                    "message": "Login successful",
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "role": role,
                    "session_token": session_token
                }
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return {"success": False, "message": f"Login failed: {str(e)}"}
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verify session token and return user info"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Get session with user info
                cursor.execute('''
                    SELECT u.id, u.username, u.email, u.role, s.expires_at
                    FROM users u
                    JOIN user_sessions s ON u.id = s.user_id
                    WHERE s.session_token = ?
                ''', (session_token,))
                
                session = cursor.fetchone()
                if not session:
                    return None
                
                user_id, username, email, role, expires_at = session
                
                # Check if session expired
                if datetime.fromisoformat(expires_at) < datetime.now():
                    # Remove expired session
                    cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
                    conn.commit()
                    return None
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "role": role
                }
                
        except Exception as e:
            logger.error(f"Error verifying session: {str(e)}")
            return None
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user by removing session"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
                conn.commit()
                
                logger.info("User logged out successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by ID"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, role, created_at, last_login FROM users WHERE id = ?", (user_id,))
                user = cursor.fetchone()
                
                if user:
                    return {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "role": user[3],
                        "created_at": user[4],
                        "last_login": user[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user_role(self, user_id: int, new_role: str, admin_user_id: int) -> bool:
        """Update user role (admin only)"""
        try:
            # Verify admin permissions
            admin_user = self.get_user_by_id(admin_user_id)
            if not admin_user or admin_user["role"] != "admin":
                return False
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
                conn.commit()
                
                logger.info(f"User {user_id} role updated to {new_role}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP")
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} expired sessions")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0
    
    def get_all_users(self, admin_user_id: int) -> list:
        """Get all users (admin only)"""
        try:
            # Verify admin permissions
            admin_user = self.get_user_by_id(admin_user_id)
            if not admin_user or admin_user["role"] != "admin":
                return []
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, role, created_at, last_login FROM users ORDER BY created_at DESC")
                users = cursor.fetchall()
                
                return [
                    {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "role": user[3],
                        "created_at": user[4],
                        "last_login": user[5]
                    }
                    for user in users
                ]
                
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []
