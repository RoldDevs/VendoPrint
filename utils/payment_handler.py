import RPi.GPIO as GPIO
from config import Config
import time

class PaymentHandler:
    def __init__(self):
        self.paid_amount = 0.0
        self.required_amount = 0.0
        self.coin_value = Config.COIN_VALUE
        self.coin_slot_pin = Config.COIN_SLOT_PIN
        
        # Initialize GPIO for coin slot (if on Raspberry Pi)
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.coin_slot_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.coin_slot_pin, GPIO.FALLING, 
                                 callback=self._coin_detected, bouncetime=200)
        except:
            # If not on Raspberry Pi, use software simulation
            self.simulate_mode = True
        else:
            self.simulate_mode = False
    
    def set_required_amount(self, amount):
        """Set the required payment amount"""
        self.required_amount = float(amount)
        self.paid_amount = 0.0
    
    def _coin_detected(self, channel):
        """Callback when coin is detected (hardware interrupt)"""
        if not self.simulate_mode:
            time.sleep(0.05)  # Debounce
            if GPIO.input(self.coin_slot_pin) == GPIO.LOW:
                self.insert_coin()
    
    def insert_coin(self):
        """Handle coin insertion"""
        self.paid_amount += self.coin_value
        return self.coin_value
    
    def get_paid_amount(self):
        """Get current paid amount"""
        return self.paid_amount
    
    def get_required_amount(self):
        """Get required amount"""
        return self.required_amount
    
    def get_remaining_amount(self):
        """Get remaining amount to pay"""
        return max(0, self.required_amount - self.paid_amount)
    
    def is_payment_complete(self):
        """Check if payment is complete"""
        return self.paid_amount >= self.required_amount
    
    def reset(self):
        """Reset payment state"""
        self.paid_amount = 0.0
        self.required_amount = 0.0

