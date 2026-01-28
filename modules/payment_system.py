"""
Payment System Module
Handles coin slot integration via GPIO on Raspberry Pi
Supports 1238A-PRO UNIVERSAL Coin Selector
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
        self.pulse_count = 0
        self.last_pulse_time = 0
        self.pulse_timeout = 1.5  # 1.5 seconds to allow for 20 pulses + margin
        self.initialized = False
        self.callback = None
        self._timer = None
        self._lock = threading.Lock()  # Thread safety
        self.test_mode = False  # Flag for testing
        logging.info(f"PaymentSystem created with coin_slot_pin=GPIO{coin_slot_pin}")
    
    def initialize(self):
        """Initialize GPIO for coin slot"""
        logging.info("="*60)
        logging.info(f"INITIALIZING PAYMENT SYSTEM - GPIO{self.coin_slot_pin}")
        logging.info("="*60)
        
        # Check if GPIO is available
        if not GPIO_AVAILABLE:
            logging.warning("⚠ RPi.GPIO module not available - GPIO hardware not accessible")
            logging.info("→ Payment system will use manual/test coin insertion via web interface")
            self.initialized = False
            return
        
        try:
            # Clean up any previous GPIO setup
            try:
                GPIO.cleanup()
                logging.info("Cleaned up previous GPIO state")
            except:
                pass
            
            logging.info(f"Setting up GPIO pin {self.coin_slot_pin} (BCM mode)")
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)  # Suppress warnings about channels already in use
            
            # Configure as input with pull-up resistor
            GPIO.setup(self.coin_slot_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logging.info(f"✓ GPIO{self.coin_slot_pin} configured as INPUT with PULL_UP resistor")
            
            # Read initial state
            initial_state = GPIO.input(self.coin_slot_pin)
            logging.info(f"✓ Initial GPIO{self.coin_slot_pin} state: {'HIGH' if initial_state else 'LOW'}")
            
            # Add event detection on FALLING edge (coin slot pulses LOW)
            GPIO.add_event_detect(self.coin_slot_pin, GPIO.FALLING, 
                                 callback=self._coin_pulse_callback, 
                                 bouncetime=30)  # Reduced bounce time for faster pulse detection
            logging.info(f"✓ Event detection enabled on GPIO{self.coin_slot_pin} (FALLING edge, 30ms debounce)")
            
            self.initialized = True
            logging.info("="*60)
            logging.info("✓ PAYMENT SYSTEM READY")
            logging.info(f"✓ Hardware: Raspberry Pi GPIO{self.coin_slot_pin} (Physical Pin 12)")
            logging.info("✓ Coin Selector: 1238A-PRO UNIVERSAL")
            logging.info("✓ Detection: 1₱=1 pulse, 5₱=5 pulses, 10₱=10 pulses, 20₱=20 pulses")
            logging.info("✓ Waiting for coin insertion...")
            logging.info("="*60)
        except RuntimeError as e:
            # RuntimeError typically means not on Raspberry Pi or GPIO not available
            if "Cannot determine SOC peripheral base address" in str(e):
                logging.error("⚠ GPIO hardware not detected (not running on Raspberry Pi)")
                logging.info("→ Payment system will use manual/test coin insertion only")
            else:
                logging.error(f"⚠ GPIO initialization failed: {str(e)}")
                logging.info("→ Payment system will use manual/test coin insertion only")
            self.initialized = False
        except Exception as e:
            logging.error(f"⚠ Payment system GPIO initialization failed: {str(e)}", exc_info=True)
            logging.info("→ Payment system will use manual/test coin insertion only")
            self.initialized = False
    
    def _coin_pulse_callback(self, channel):
        """Callback for coin slot pulse detection"""
        with self._lock:
            try:
                current_time = time.time()
                time_since_last = current_time - self.last_pulse_time
                
                # Log every pulse for debugging
                logging.info(f"[GPIO{self.coin_slot_pin}] ▼ PULSE DETECTED! Time since last: {time_since_last:.3f}s")
                
                # If this is a new coin sequence (timeout passed)
                if time_since_last > self.pulse_timeout:
                    # Process previous coin if any
                    if self.pulse_count > 0:
                        logging.info(f"[COIN] Previous coin timeout - processing {self.pulse_count} pulses")
                        self._process_coin_now()
                    
                    # Start new coin sequence
                    self.pulse_count = 1
                    logging.info(f"[COIN] NEW coin sequence started - Pulse #1")
                else:
                    # Continue current coin sequence
                    self.pulse_count += 1
                    logging.info(f"[COIN] Pulse #{self.pulse_count} (continuing sequence)")
                
                self.last_pulse_time = current_time
                
                # Cancel existing timer and start new one
                if self._timer:
                    self._timer.cancel()
                self._timer = threading.Timer(self.pulse_timeout, self._process_coin)
                self._timer.start()
                
            except Exception as e:
                logging.error(f"[GPIO] Error in coin pulse callback: {e}", exc_info=True)
    
    def _process_coin(self):
        """Process the completed coin after timeout (called by timer)"""
        with self._lock:
            self._process_coin_now()
    
    def _process_coin_now(self):
        """Actually process the coin (assumes lock is held)"""
        try:
            if self.pulse_count > 0:
                logging.info(f"[COIN] ═══════════════════════════════════════")
                logging.info(f"[COIN] Processing coin: {self.pulse_count} pulses detected")
                
                coin_value = self._determine_coin_value()
                
                if coin_value > 0:
                    logging.info(f"[COIN] ✓ Identified: ₱{coin_value:.2f}")
                    
                    if self.callback:
                        try:
                            logging.info(f"[COIN] → Calling callback function...")
                            self.callback(coin_value)
                            logging.info(f"[COIN] ✓ Callback executed successfully!")
                        except Exception as e:
                            logging.error(f"[COIN] ✗ Error in coin callback: {e}", exc_info=True)
                    else:
                        logging.error(f"[COIN] ✗ NO CALLBACK REGISTERED! Coin value: ₱{coin_value}")
                        logging.error(f"[COIN] ✗ The coin was detected but cannot be processed!")
                else:
                    logging.warning(f"[COIN] ✗ Unknown pulse count: {self.pulse_count}")
                    logging.warning(f"[COIN] ✗ Expected: 1, 5, 10, or 20 pulses")
                
                logging.info(f"[COIN] ═══════════════════════════════════════")
                self.pulse_count = 0
        except Exception as e:
            logging.error(f"[COIN] Error processing coin: {e}", exc_info=True)
    
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
        logging.info(f"[COIN] Callback function registered: {callback.__name__ if callback else 'None'}")
        logging.info(f"[COIN] System is now ready to process coin insertions!")
    
    def reset(self):
        """Reset payment state"""
        with self._lock:
            self.pulse_count = 0
            self.last_pulse_time = 0
            logging.info("[COIN] Payment state reset")
    
    def test_pulse(self, num_pulses=5):
        """Simulate pulses for testing (simulates 5 peso coin by default)"""
        logging.info(f"[TEST] Simulating {num_pulses} pulses...")
        for i in range(num_pulses):
            self._coin_pulse_callback(self.coin_slot_pin)
            time.sleep(0.05)  # 50ms between pulses
        logging.info(f"[TEST] Finished simulating {num_pulses} pulses")
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.initialized:
            try:
                GPIO.remove_event_detect(self.coin_slot_pin)
                GPIO.cleanup()
            except Exception as e:
                logging.error(f"Error cleaning up payment system: {str(e)}")