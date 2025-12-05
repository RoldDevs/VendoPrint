import sqlite3
import json
from datetime import datetime
from config import Config

class SystemLogger:
    def __init__(self):
        self.db_file = Config.DATABASE_FILE
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for logging"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT,
                pages INTEGER,
                color_mode TEXT,
                status TEXT,
                error_reason TEXT,
                job_id TEXT
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
    
    def log_print_job(self, filename, pages, color_mode, status, job_id=None, error_reason=None):
        """Log a print job"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO print_logs 
            (timestamp, filename, pages, color_mode, status, error_reason, job_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), filename, pages, color_mode, 
              status, error_reason, job_id))
        
        conn.commit()
        conn.close()
    
    def log_error(self, error_type, error_message):
        """Log an error"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs (timestamp, error_type, error_message)
            VALUES (?, ?, ?)
        ''', (datetime.now().isoformat(), error_type, error_message))
        
        conn.commit()
        conn.close()
    
    def get_all_logs(self, limit=100):
        """Get all print logs"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM print_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'timestamp': row[1],
                'filename': row[2],
                'pages': row[3],
                'color_mode': row[4],
                'status': row[5],
                'error_reason': row[6],
                'job_id': row[7]
            })
        
        conn.close()
        return logs
    
    def get_statistics(self):
        """Get system statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Total prints
        cursor.execute('SELECT COUNT(*) FROM print_logs WHERE status = "completed"')
        total_prints = cursor.fetchone()[0]
        
        # Failed prints
        cursor.execute('SELECT COUNT(*) FROM print_logs WHERE status = "error"')
        failed_prints = cursor.fetchone()[0]
        
        # Total pages printed
        cursor.execute('SELECT SUM(pages) FROM print_logs WHERE status = "completed"')
        total_pages = cursor.fetchone()[0] or 0
        
        # Recent errors
        cursor.execute('''
            SELECT * FROM error_logs 
            WHERE resolved = 0 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_errors = []
        for row in cursor.fetchall():
            recent_errors.append({
                'id': row[0],
                'timestamp': row[1],
                'error_type': row[2],
                'error_message': row[3]
            })
        
        conn.close()
        
        return {
            'total_prints': total_prints,
            'failed_prints': failed_prints,
            'success_rate': (total_prints / (total_prints + failed_prints) * 100) if (total_prints + failed_prints) > 0 else 0,
            'total_pages': total_pages,
            'recent_errors': recent_errors
        }

