import requests
from config import Config
import logging

class NotificationService:
    def __init__(self):
        self.owner_phone = Config.OWNER_PHONE
        self.enabled = Config.NOTIFICATION_ENABLED
    
    def send_notification(self, message, error_type=None):
        """Send notification to owner's phone"""
        if not self.enabled or not self.owner_phone:
            logging.warning(f"Notification: {message}")
            return
        
        try:
            # This is a placeholder - implement actual SMS/notification service
            # Options: Twilio, AWS SNS, or custom API
            logging.info(f"Sending notification to {self.owner_phone}: {message}")
            
            # Example with Twilio (uncomment and configure):
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # client.messages.create(
            #     body=message,
            #     from_=twilio_number,
            #     to=self.owner_phone
            # )
            
        except Exception as e:
            logging.error(f"Failed to send notification: {str(e)}")
    
    def notify_paper_empty(self):
        """Notify when paper is empty"""
        self.send_notification(
            "⚠️ VendoPrint Alert: Paper is empty!",
            error_type="paper_empty"
        )
    
    def notify_ink_low(self):
        """Notify when ink is low"""
        self.send_notification(
            "⚠️ VendoPrint Alert: Ink is running low!",
            error_type="ink_low"
        )
    
    def notify_paper_jam(self):
        """Notify when paper jam occurs"""
        self.send_notification(
            "⚠️ VendoPrint Alert: Paper jam detected!",
            error_type="paper_jam"
        )
    
    def notify_system_error(self, error_message):
        """Notify system error"""
        self.send_notification(
            f"⚠️ VendoPrint Alert: System error - {error_message}",
            error_type="system_error"
        )

