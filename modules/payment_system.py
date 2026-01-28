"""
Payment System Module
Handles coin slot integration via GPIO on Raspberry Pi
"""

import logging
import time
import threading

# Try to import RPi.GPIO (only available on Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    GPIO = None

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
        self.pulse_timeout = 1.0  # 1 second timeout to allow for 20 pulses
        self.initialized = False
        self.callback = None
        self._timer = None
        logging.info(f"PaymentSystem created with coin_slot_pin=GPIO{coin_slot_pin}")
    
    def initialize(self):
        """Initialize GPIO for coin slot"""
        logging.info(f"Initializing payment system on GPIO pin {self.coin_slot_pin}...")
        
        # Check if GPIO is available
        if not GPIO_AVAILABLE:
            logging.warning("RPi.GPIO module not available - GPIO hardware not accessible")
            logging.info("Payment system will use manual/test coin insertion via web interface")
            self.initialized = False
            return
        
        try:
            logging.info(f"Setting up GPIO pin {self.coin_slot_pin} (BCM mode)")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.coin_slot_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logging.info(f"GPIO pin {self.coin_slot_pin} configured as INPUT with PULL_UP")
            
            GPIO.add_event_detect(self.coin_slot_pin, GPIO.FALLING, 
                                 callback=self._coin_pulse_callback, 
                                 bouncetime=50)
            logging.info(f"Event detection enabled on GPIO{self.coin_slot_pin} (FALLING edge, 50ms bounce time)")
            
            self.initialized = True
            logging.info("✓ Payment system initialized successfully - Coin slot ready on GPIO18 (Physical Pin 12)")
            logging.info("✓ Coin selector model: 1238A-PRO UNIVERSAL")
            logging.info("✓ Pulse pattern: 1₱=1 pulse, 5₱=5 pulses, 10₱=10 pulses, 20₱=20 pulses")
        except RuntimeError as e:
            # RuntimeError typically means not on Raspberry Pi or GPIO not available
            if "Cannot determine SOC peripheral base address" in str(e):
                logging.warning("GPIO hardware not detected (not running on Raspberry Pi)")
                logging.info("Payment system will use manual/test coin insertion only")
            else:
                logging.error(f"GPIO initialization failed: {str(e)}")
                logging.info("Payment system will use manual/test coin insertion only")
            self.initialized = False
        except Exception as e:
            logging.error(f"Payment system GPIO initialization failed: {str(e)}")
            logging.info("Payment system will use manual/test coin insertion only")
            # Fallback for non-Raspberry Pi systems or when GPIO is unavailable
            self.initialized = False
    
    def _coin_pulse_callback(self, channel):
        """Callback for coin slot pulse detection"""
        try:
            current_time = time.time()
            
            # Debounce: ignore pulses too close together (less than 10ms)
            if current_time - self.last_pulse_time < 0.01:
                logging.debug(f"Coin pulse ignored (debounce)")
                return
            
            # If enough time has passed, process previous coin
            if current_time - self.last_pulse_time > self.pulse_timeout:
                # New coin sequence - process previous coin if any
                if self.pulse_count > 0:
                    coin_value = self._determine_coin_value()
                    if coin_value > 0 and self.callback:
                        logging.info(f"[GPIO] Coin sequence completed: {self.pulse_count} pulses = ₱{coin_value}")
                        try:
                            self.callback(coin_value)
                        except Exception as e:
                            logging.error(f"Error in coin callback: {e}")
                # Reset for new coin
                self.pulse_count = 1
                logging.debug(f"[GPIO] New coin sequence started (pulse #1)")
            else:
                # Continuation of same coin
                self.pulse_count += 1
                logging.debug(f"[GPIO] Coin pulse #{self.pulse_count}")
            
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
                logging.info(f"[GPIO] Processing coin: {self.pulse_count} pulses detected")
                if coin_value > 0:
                    logging.info(f"[GPIO] Coin identified as ₱{coin_value}")
                    if self.callback:
                        try:
                            self.callback(coin_value)
                            logging.info(f"[GPIO] Coin callback executed successfully")
                        except Exception as e:
                            logging.error(f"Error in coin callback: {e}")
                    else:
                        logging.warning(f"[GPIO] No callback registered! Coin value: ₱{coin_value}")
                else:
                    logging.warning(f"[GPIO] Invalid coin - {self.pulse_count} pulses did not match any known coin")
                self.pulse_count = 0
        except Exception as e:
            logging.error(f"Error processing coin: {e}")
    
    def _determine_coin_value(self):
        """Determine coin value from pulse pattern"""
        # 1238A-PRO UNIVERSAL Coin Selector pulse pattern
        # This model outputs pulses equal to the coin value
        # 1 peso = 1 pulse, 5 pesos = 5 pulses, 10 pesos = 10 pulses, 20 pesos = 20 pulses
        if self.pulse_count == 1:
            return 1.0  # 1 peso
        elif self.pulse_count == 5:
            return 5.0  # 5 pesos
        elif self.pulse_count == 10:
            return 10.0  # 10 pesos
        elif self.pulse_count == 20:
            return 20.0  # 20 pesos
        else:
            # If pulse count doesn't match known values, log it
            logging.warning(f"Unknown pulse count: {self.pulse_count} - ignoring coin")
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