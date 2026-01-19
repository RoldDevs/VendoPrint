"""
Payment System Module
Handles coin slot integration via GPIO on Raspberry Pi
"""

import logging
import RPi.GPIO as GPIO
import time
import threading

class PaymentSystem:
    def __init__(self, coin_slot_pin=18):
        self.coin_slot_pin = coin_slot_pin  # GPIO pin for coin slot signal
        self.coin_values = {
            'pulse_1': 1.0,   # 1 peso coin
            'pulse_5': 5.0,   # 5 peso coin
            'pulse_10': 10.0, # 10 peso coin
            'pulse_20': 20.0  # 20 peso coin
        }
        self.pulse_count = 0
        self.last_pulse_time = 0
        self.pulse_timeout = 0.5  # 500ms timeout between pulses
        self.initialized = False
        self.callback = None
        self._timer = None
    
    def initialize(self):
        """Initialize GPIO for coin slot"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.coin_slot_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.coin_slot_pin, GPIO.FALLING, 
                                 callback=self._coin_pulse_callback, 
                                 bouncetime=50)
            self.initialized = True
            logging.info("Payment system initialized")
        except Exception as e:
            logging.error(f"Error initializing payment system: {str(e)}")
            # Fallback for non-Raspberry Pi systems
            self.initialized = False
    
    def _coin_pulse_callback(self, channel):
        """Callback for coin slot pulse detection"""
        try:
            current_time = time.time()
            
            # Debounce: ignore pulses too close together (less than 10ms)
            if current_time - self.last_pulse_time < 0.01:
                return
            
            # If enough time has passed, process previous coin
            if current_time - self.last_pulse_time > self.pulse_timeout:
                # New coin sequence - process previous coin if any
                if self.pulse_count > 0:
                    coin_value = self._determine_coin_value()
                    if coin_value > 0 and self.callback:
                        logging.info(f"Coin detected: {self.pulse_count} pulses = ₱{coin_value}")
                        try:
                            self.callback(coin_value)
                        except Exception as e:
                            logging.error(f"Error in coin callback: {e}")
                # Reset for new coin
                self.pulse_count = 1
            else:
                # Continuation of same coin
                self.pulse_count += 1
            
            self.last_pulse_time = current_time
            
            # Start a timer to process the coin after timeout
            if hasattr(self, '_timer') and self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self.pulse_timeout + 0.1, self._process_coin)
            self._timer.start()
        except Exception as e:
            logging.error(f"Error in coin pulse callback: {e}")
    
    def _process_coin(self):
        """Process the completed coin after timeout"""
        try:
            if self.pulse_count > 0:
                coin_value = self._determine_coin_value()
                if coin_value > 0 and self.callback:
                    logging.info(f"Processing coin: {self.pulse_count} pulses = ₱{coin_value}")
                    try:
                        self.callback(coin_value)
                    except Exception as e:
                        logging.error(f"Error in coin callback: {e}")
                self.pulse_count = 0
        except Exception as e:
            logging.error(f"Error processing coin: {e}")
    
    def _determine_coin_value(self):
        """Determine coin value from pulse pattern"""
        # Simplified: assumes different pulse patterns for different coins
        # Actual implementation should match your coin slot's protocol
        if self.pulse_count == 1:
            return 1.0  # 1 peso
        elif self.pulse_count == 2:
            return 5.0  # 5 pesos
        elif self.pulse_count == 3:
            return 10.0  # 10 pesos
        elif self.pulse_count >= 4:
            return 20.0  # 20 pesos
        return 0.0
    
    def set_coin_callback(self, callback):
        """Set callback function for coin insertion"""
        self.callback = callback
    
    def reset(self):
        """Reset payment state"""
        self.pulse_count = 0
        self.last_pulse_time = 0
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.initialized:
            try:
                GPIO.remove_event_detect(self.coin_slot_pin)
                GPIO.cleanup()
            except Exception as e:
                logging.error(f"Error cleaning up payment system: {str(e)}")

