"""
Logging System Module
Handles user activity logging and statistics
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

class LoggingSystem:
    def __init__(self):
        self.db_path = 'vendoprint.db'
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS print_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_type TEXT,
                    file_name TEXT,
                    pages INTEGER,
                    copies INTEGER,
                    color_mode TEXT,
                    orientation TEXT,
                    cost REAL,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            # Create payment logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    coin_value REAL,
                    total_paid REAL,
                    total_cost REAL
                )
            ''')
            
            # Create error logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    resolved INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized")
        
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
    
    def log_print_start(self, job):
        """Log print job start"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO print_logs 
                (timestamp, file_type, file_name, pages, copies, color_mode, orientation, cost, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                job.get('file_type', 'unknown'),
                Path(job.get('file_path', '')).name,
                job.get('pages', 0),
                job.get('copies', 1),
                job.get('color_mode', 'grayscale'),
                job.get('orientation', 'portrait'),
                job.get('cost', 0.0),
                'started'
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error logging print start: {str(e)}")
    
    def log_print_complete(self, job, success, error_message=None):
        """Log print job completion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            status = 'completed' if success else 'failed'
            
            cursor.execute('''
                UPDATE print_logs 
                SET status = ?, error_message = ?
                WHERE id = (SELECT MAX(id) FROM print_logs)
            ''', (status, error_message))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error logging print complete: {str(e)}")
    
    def log_payment(self, coin_value, total_paid, total_cost):
        """Log payment transaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payment_logs (timestamp, coin_value, total_paid, total_cost)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                coin_value,
                total_paid,
                total_cost
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error logging payment: {str(e)}")
    
    def log_error(self, error_type, error_message):
        """Log system error"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO error_logs (timestamp, error_type, error_message)
                VALUES (?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                error_type,
                error_message
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error logging error: {str(e)}")
    
    def get_recent_logs(self, limit=100):
        """Get recent print logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM print_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return logs
        
        except Exception as e:
            logging.error(f"Error getting recent logs: {str(e)}")
            return []
    
    def get_statistics(self):
        """Get system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total prints
            cursor.execute('SELECT COUNT(*) FROM print_logs WHERE status = "completed"')
            total_prints = cursor.fetchone()[0]
            
            # Failed prints
            cursor.execute('SELECT COUNT(*) FROM print_logs WHERE status = "failed"')
            failed_prints = cursor.fetchone()[0]
            
            # Total revenue
            cursor.execute('SELECT SUM(cost) FROM print_logs WHERE status = "completed"')
            total_revenue = cursor.fetchone()[0] or 0.0
            
            # Today's prints
            cursor.execute('''
                SELECT COUNT(*) FROM print_logs 
                WHERE date(timestamp) = date('now') AND status = "completed"
            ''')
            today_prints = cursor.fetchone()[0]
            
            # Error count
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE resolved = 0')
            unresolved_errors = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_prints': total_prints,
                'failed_prints': failed_prints,
                'total_revenue': round(total_revenue, 2),
                'today_prints': today_prints,
                'unresolved_errors': unresolved_errors,
                'success_rate': round((total_prints / (total_prints + failed_prints) * 100) if (total_prints + failed_prints) > 0 else 0, 2)
            }
        
        except Exception as e:
            logging.error(f"Error getting statistics: {str(e)}")
            return {}

