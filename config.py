import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Server Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vendo-print-secret-key-2024'
    UPLOAD_FOLDER = 'uploads'
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'doc', 'txt'}
    
    # Printing Configuration
    PRICE_PER_PAGE_BW = 5  # 5 pesos per page (B&W)
    PRICE_PER_PAGE_COLOR = 10  # 10 pesos per page (Color)
    
    # Coin Slot Configuration (GPIO pins for Raspberry Pi)
    COIN_SLOT_PIN = 18  # GPIO pin for coin slot
    COIN_VALUE = 1  # 1 peso per coin
    
    # Printer Configuration
    PRINTER_NAME = os.environ.get('PRINTER_NAME') or 'Brother_Printer'
    
    # Database/Logging
    LOG_FILE = 'logs/vendoprint.log'
    DATABASE_FILE = 'logs/vendoprint.db'
    
    # Notification Configuration
    OWNER_PHONE = os.environ.get('OWNER_PHONE') or ''
    NOTIFICATION_ENABLED = True

