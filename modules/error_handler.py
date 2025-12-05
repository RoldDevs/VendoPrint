"""
Error Handler Module
Handles error detection and notifications
"""

import os
import logging
import requests
import json
from datetime import datetime
from modules.logging_system import LoggingSystem

class ErrorHandler:
    def __init__(self):
        self.logging_system = LoggingSystem()
        self.notification_url = None  # Set this to your notification service URL
        self.owner_phone = None  # Set owner's phone number for SMS notifications
    
    def initialize(self):
        """Initialize error handler"""
        try:
            # Load configuration
            config_path = 'config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.notification_url = config.get('notification_url')
                    self.owner_phone = config.get('owner_phone')
            
            logging.info("Error handler initialized")
        
        except Exception as e:
            logging.error(f"Error initializing error handler: {str(e)}")
    
    def handle_error(self, error_message):
        """Handle system error"""
        try:
            # Determine error type
            error_type = self._classify_error(error_message)
            
            # Log error
            self.logging_system.log_error(error_type, error_message)
            
            # Send notification
            self._send_notification(error_type, error_message)
            
            logging.warning(f"Error handled: {error_type} - {error_message}")
        
        except Exception as e:
            logging.error(f"Error in error handler: {str(e)}")
    
    def _classify_error(self, error_message):
        """Classify error type"""
        error_lower = error_message.lower()
        
        if 'paper' in error_lower and ('empty' in error_lower or 'out' in error_lower):
            return 'no_paper'
        elif 'paper' in error_lower and ('jam' in error_lower or 'jammed' in error_lower):
            return 'paper_jam'
        elif 'ink' in error_lower and ('low' in error_lower or 'empty' in error_lower or 'out' in error_lower):
            return 'low_ink'
        elif 'connection' in error_lower or 'network' in error_lower:
            return 'connection_error'
        else:
            return 'system_error'
    
    def _send_notification(self, error_type, error_message):
        """Send error notification to owner"""
        try:
            if self.notification_url:
                # Send HTTP notification
                payload = {
                    'error_type': error_type,
                    'error_message': error_message,
                    'timestamp': datetime.now().isoformat()
                }
                
                response = requests.post(self.notification_url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    logging.info("Notification sent successfully")
                else:
                    logging.warning(f"Notification failed: {response.status_code}")
            
            # Also log to console for immediate visibility
            print(f"\n⚠️ ERROR ALERT: {error_type} - {error_message}\n")
        
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")
    
    def check_printer_errors(self, printer_status):
        """Check printer status for errors"""
        try:
            if printer_status.get('error_status'):
                self.handle_error(printer_status['error_status'])
            
            if printer_status.get('paper_status') == 'empty':
                self.handle_error("No bond paper - Paper tray is empty")
            
            if printer_status.get('ink_status') == 'low':
                self.handle_error("Low ink - Ink level is below threshold")
            elif printer_status.get('ink_status') == 'empty':
                self.handle_error("Out of ink - Ink cartridge is empty")
        
        except Exception as e:
            logging.error(f"Error checking printer errors: {str(e)}")
