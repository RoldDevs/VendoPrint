#!/usr/bin/env python3
"""
VendoPrint - Automated Vending Machine Printer System
Main Flask Application for Raspberry Pi 5
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import json
import sqlite3
from datetime import datetime
import threading
import time
from pathlib import Path
import logging

from modules.file_processor import FileProcessor
from modules.payment_system import PaymentSystem
from modules.printer_manager import PrinterManager
from modules.logging_system import LoggingSystem
from modules.error_handler import ErrorHandler
from modules.audio_feedback import AudioFeedback

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Initialize modules (will be configured after CONFIG is loaded)
file_processor = None
payment_system = None
printer_manager = None
logging_system = None
error_handler = None
audio_feedback = None

# Global state for current print job
current_job = {
    'file_path': None,
    'file_type': None,
    'pages': 0,
    'copies': 1,
    'page_range': None,
    'orientation': 'portrait',
    'color_mode': 'grayscale',
    'cost': 0.0,
    'paid': 0.0,
    'status': 'idle'
}

# Load configuration
CONFIG = {
    'PRICE_PER_PAGE_BW': 5.0,  # 5 pesos per page (B&W)
    'PRICE_PER_PAGE_COLOR': 10.0,  # 10 pesos per page (Color)
    'PRINTER_NAME': 'Brother',  # Default printer name
    'COIN_VALUES': [1, 5, 10, 20],  # Accepted coin values in pesos
}

# Load config from file if it exists
if os.path.exists('config.json'):
    try:
        with open('config.json', 'r') as f:
            file_config = json.load(f)
            CONFIG.update(file_config)
    except Exception as e:
        logging.warning(f"Error loading config.json: {e}, using defaults")

# Initialize modules with config
file_processor = FileProcessor()
coin_slot_pin = CONFIG.get('COIN_SLOT_GPIO_PIN', 18)
payment_system = PaymentSystem(coin_slot_pin=coin_slot_pin)
printer_manager = PrinterManager(CONFIG.get('PRINTER_NAME', 'Brother'))
logging_system = LoggingSystem()
error_handler = ErrorHandler()
audio_feedback = AudioFeedback()

@app.route('/')
def index():
    """Main page - choose between Print Photo or Print Document"""
    return render_template('index.html')

# Captive Portal Detection Routes
@app.route('/generate_204')
@app.route('/gen_204')
def generate_204():
    """Android captive portal detection - returns 204 No Content"""
    return '', 204

@app.route('/hotspot-detect.html')
@app.route('/connectivity-check.html')
@app.route('/check_network_status.txt')
@app.route('/ncsi.txt')
@app.route('/success.txt')
def captive_portal_detection():
    """Handle captive portal detection from various devices"""
    # Return a simple HTML page that redirects
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="0; url=/">
    <title>VendoPrint - WiFi Portal</title>
</head>
<body>
    <script>window.location.href = "/";</script>
    <p>Redirecting to VendoPrint... <a href="/">Click here</a></p>
</body>
</html>'''

@app.route('/redirect')
def captive_redirect():
    """Redirect page for captive portal"""
    return render_template('index.html')

@app.route('/print-photo')
def print_photo():
    """Print Photo interface"""
    return render_template('print_photo.html')

@app.route('/print-document')
def print_document():
    """Print Document interface"""
    return render_template('print_document.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    global current_job
    try:
        logging.info("File upload request received")
        
        if 'file' not in request.files:
            logging.warning("No file in upload request")
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'document')
        
        logging.info(f"Upload - Filename: {file.filename}, Type: {file_type}")
        
        if file.filename == '':
            logging.warning("Empty filename in upload request")
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            logging.info(f"File saved: {file_path}")
            
            # Process file to get page count and preview
            if file_type == 'photo':
                pages = 1
                preview_path = file_processor.create_image_preview(file_path)
            else:
                pages = file_processor.count_pages(file_path)
                preview_path = file_processor.create_document_preview(file_path)
            
            logging.info(f"File processed - Pages: {pages}, Preview: {preview_path}")
            
            # Store in session
            session['current_file'] = file_path
            session['file_type'] = file_type
            session['pages'] = pages
            
            # Reset current job and payment state completely
            current_job = {
                'file_path': file_path,
                'file_type': file_type,
                'pages': pages,
                'copies': 1,
                'page_range': None,
                'orientation': 'portrait',
                'color_mode': 'grayscale',
                'cost': 0.0,
                'paid': 0.0,
                'status': 'uploaded',
                'current_page': 0,
                'total_pages': 0,
                'pending_coin': None,
                'pending_coin_time': 0
            }
            
            # Also reset payment system if it exists
            if payment_system:
                payment_system.reset()
            
            logging.info(f"Upload successful - Job initialized with {pages} page(s)")
            
            return jsonify({
                'success': True,
                'file_path': file_path,
                'preview_path': preview_path,
                'pages': pages,
                'file_type': file_type
            }), 200
        
        logging.warning(f"Invalid file type: {file.filename}")
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    except Exception as e:
        logging.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/preview')
def get_preview():
    """Get preview image"""
    file_path = request.args.get('file_path')
    if file_path and os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'Preview not found'}), 404

@app.route('/api/calculate-cost', methods=['POST'])
def calculate_cost():
    """Calculate printing cost based on settings"""
    global current_job
    try:
        # Check if request has JSON content
        if not request.is_json:
            logging.error("Calculate cost request is not JSON")
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if data is None:
            logging.error("Failed to parse JSON data in calculate cost request")
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        pages = data.get('pages', current_job.get('pages', 1))
        copies = data.get('copies', 1)
        color_mode = data.get('color_mode', 'grayscale')
        page_range = data.get('page_range', None)
        
        logging.info(f"Calculating cost - Pages: {pages}, Copies: {copies}, Color: {color_mode}, Range: {page_range}")
        
        # Calculate actual pages to print
        if page_range and page_range != 'all':
            start_page = int(page_range.get('start', 1))
            end_page = int(page_range.get('end', pages))
            actual_pages = (end_page - start_page + 1) * copies
        else:
            actual_pages = pages * copies
        
        # Calculate cost
        price_per_page = CONFIG['PRICE_PER_PAGE_COLOR'] if color_mode == 'color' else CONFIG['PRICE_PER_PAGE_BW']
        total_cost = actual_pages * price_per_page
        
        # Update current job
        current_job['copies'] = copies
        current_job['page_range'] = page_range
        current_job['orientation'] = data.get('orientation', 'portrait')
        current_job['color_mode'] = color_mode
        current_job['cost'] = total_cost
        
        # Initialize paid amount if not set
        if 'paid' not in current_job:
            current_job['paid'] = 0.0
        
        logging.info(f"Cost calculated: P{total_cost:.2f} ({actual_pages} pages x P{price_per_page:.2f})")
        
        return jsonify({
            'success': True,
            'cost': total_cost,
            'pages': actual_pages,
            'price_per_page': price_per_page
        }), 200
    
    except Exception as e:
        logging.error(f"Cost calculation error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payment-status', methods=['GET'])
def payment_status():
    """Get current payment status"""
    global current_job
    # Only allow printing if cost is set, paid amount is sufficient, and file is uploaded
    can_print = (
        current_job.get('cost', 0) > 0 and 
        current_job.get('paid', 0) >= current_job.get('cost', 0) and
        current_job.get('file_path') is not None and
        current_job.get('status') == 'uploaded'
    )
    
    return jsonify({
        'paid': current_job.get('paid', 0.0),
        'cost': current_job.get('cost', 0.0),
        'remaining': max(0, current_job.get('cost', 0.0) - current_job.get('paid', 0.0)),
        'can_print': can_print
    })

@app.route('/api/pending-coin', methods=['GET'])
def get_pending_coin():
    """Check if there's a pending coin from the physical coin slot"""
    global current_job
    try:
        pending_coin = current_job.get('pending_coin')
        pending_time = current_job.get('pending_coin_time', 0)
        
        # Clear pending coin if it's older than 30 seconds
        if pending_coin and (time.time() - pending_time) > 30:
            logging.info(f"Pending coin P{pending_coin} expired after 30 seconds")
            current_job['pending_coin'] = None
            pending_coin = None
        
        return jsonify({
            'pending_coin': pending_coin,
            'has_pending': pending_coin is not None
        }), 200
    except Exception as e:
        logging.error(f"Error checking pending coin: {str(e)}")
        return jsonify({'pending_coin': None, 'has_pending': False}), 200

@app.route('/api/gpio-test', methods=['GET'])
def gpio_test():
    """Test GPIO status and coin slot detection"""
    try:
        status = {
            'gpio_available': payment_system is not None,
            'initialized': payment_system.initialized if payment_system else False,
            'pin': payment_system.coin_slot_pin if payment_system else None,
            'callback_set': payment_system.callback is not None if payment_system else False,
            'pulse_count': payment_system.pulse_count if payment_system else 0,
            'test_mode': payment_system.test_mode if payment_system else False
        }
        
        # Try to read GPIO state if initialized
        if payment_system and payment_system.initialized:
            try:
                import RPi.GPIO as GPIO
                pin_state = GPIO.input(payment_system.coin_slot_pin)
                status['pin_state'] = 'HIGH' if pin_state else 'LOW'
            except Exception as e:
                status['pin_state'] = f'Error: {str(e)}'
        
        logging.info(f"GPIO Test Status: {status}")
        return jsonify(status), 200
    except Exception as e:
        logging.error(f"GPIO test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate-coin', methods=['POST'])
def simulate_coin():
    """Simulate a coin insertion for testing (bypasses GPIO)"""
    global current_job
    try:
        data = request.get_json()
        value = float(data.get('value', 5))
        
        logging.info(f"[TEST] Simulating coin insertion: ₱{value}")
        
        # Call the callback directly (simulates hardware detection)
        if payment_system and payment_system.callback:
            coin_inserted_callback(value)
            return jsonify({'success': True, 'message': f'Simulated ₱{value} coin insertion'}), 200
        else:
            return jsonify({'success': False, 'error': 'Payment system not initialized'}), 400
    except Exception as e:
        logging.error(f"Simulate coin error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/coin-inserted', methods=['POST'])
def coin_inserted():
    """Handle coin confirmation from web (after physical coin detected)"""
    global current_job
    try:
        # Check if request has JSON content
        if not request.is_json:
            logging.error("Coin insertion request is not JSON")
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if data is None:
            logging.error("Failed to parse JSON data in coin insertion request")
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        # Validate that a file is uploaded
        if not current_job.get('file_path'):
            logging.warning("Coin confirmation attempted but no file uploaded")
            return jsonify({'success': False, 'error': 'Please upload a file first'}), 400
        
        # Validate that cost is calculated
        if current_job.get('cost', 0) <= 0:
            logging.warning("Coin confirmation attempted but cost not calculated")
            return jsonify({'success': False, 'error': 'Cost not calculated. Please wait.'}), 400
        
        # Validate job status
        if current_job.get('status') != 'uploaded':
            logging.warning(f"Coin confirmation attempted but status is {current_job.get('status')}")
            return jsonify({'success': False, 'error': 'Cannot accept coins at this time'}), 400
        
        # Parse coin value from request
        try:
            requested_value = float(data.get('value', 0))
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid coin value format: {data.get('value')}")
            return jsonify({'success': False, 'error': 'Invalid coin value format'}), 400
        
        # Check if there's a pending coin from the physical slot
        pending_coin = current_job.get('pending_coin')
        
        if pending_coin:
            # Verify the requested value matches the pending coin
            if requested_value != pending_coin:
                logging.warning(f"Coin mismatch: Requested P{requested_value} but pending is P{pending_coin}")
                return jsonify({'success': False, 'error': f'Please confirm the detected coin value: P{pending_coin}'}), 400
            
            # Clear the pending coin
            current_job['pending_coin'] = None
            coin_value = pending_coin
            logging.info(f"Physical coin confirmed: P{coin_value}")
        else:
            # No pending coin - this is a manual/test insertion
            # Allow for development/testing purposes
            if requested_value <= 0:
                logging.error(f"Invalid coin value: {requested_value}")
                return jsonify({'success': False, 'error': 'Invalid coin value'}), 400
            
            coin_value = requested_value
            logging.info(f"Manual coin insertion (test mode): P{coin_value}")
        
        # Accept any positive value (for testing), but log if not in configured values
        if coin_value not in CONFIG.get('COIN_VALUES', [1, 5, 10, 20]):
            logging.warning(f"Coin value {coin_value} not in configured values, accepting anyway")
        
        # Initialize paid amount if not set
        if 'paid' not in current_job:
            current_job['paid'] = 0.0
        
        # Add payment
        current_job['paid'] += coin_value
        
        # Log payment
        logging_system.log_payment(coin_value, current_job['paid'], current_job['cost'])
        
        # Only allow printing if fully paid
        can_print = (
            current_job['paid'] >= current_job['cost'] and 
            current_job['cost'] > 0 and
            current_job['status'] == 'uploaded'
        )
        
        logging.info(f"Payment processed: P{coin_value:.2f}, Total: P{current_job['paid']:.2f}, Required: P{current_job['cost']:.2f}, Can print: {can_print}")
        
        return jsonify({
            'success': True,
            'paid': current_job['paid'],
            'cost': current_job['cost'],
            'required': current_job['cost'],
            'remaining': max(0, current_job['cost'] - current_job['paid']),
            'can_print': can_print
        }), 200
    
    except ValueError as e:
        logging.error(f"Invalid coin value: {str(e)}")
        return jsonify({'success': False, 'error': 'Invalid coin value provided'}), 400
    except Exception as e:
        logging.error(f"Coin confirmation error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-print', methods=['POST'])
def start_print():
    """Start printing process"""
    global current_job
    try:
        # Validate cost is set
        if current_job.get('cost', 0) <= 0:
            return jsonify({'error': 'Cost not calculated'}), 400
        
        # Validate sufficient payment
        if current_job.get('paid', 0) < current_job.get('cost', 0):
            return jsonify({'error': 'Insufficient payment'}), 400
        
        # Validate file and status
        if current_job.get('status') != 'uploaded':
            return jsonify({'error': 'No file ready for printing'}), 400
        
        if not current_job.get('file_path'):
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Start printing in background thread
        thread = threading.Thread(target=print_job_thread, args=(current_job.copy(),))
        thread.daemon = True
        thread.start()
        
        current_job['status'] = 'printing'
        
        # Log print start
        logging_system.log_print_start(current_job)
        
        # Play printing sound
        audio_feedback.play_printing_sound()
        
        return jsonify({
            'success': True,
            'status': 'printing',
            'message': 'Printing started'
        })
    
    except Exception as e:
        logging.error(f"Print start error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/print-status', methods=['GET'])
def print_status():
    """Get current print job status"""
    global current_job
    return jsonify({
        'status': current_job['status'],
        'current_page': current_job.get('current_page', 0),
        'total_pages': current_job.get('total_pages', 0)
    })

@app.route('/api/dashboard')
def dashboard():
    """Owner dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    stats = logging_system.get_statistics()
    return jsonify(stats)

@app.route('/api/dashboard/logs', methods=['GET'])
def dashboard_logs():
    """Get activity logs"""
    limit = request.args.get('limit', 100, type=int)
    logs = logging_system.get_recent_logs(limit)
    return jsonify(logs)

@app.route('/api/printer-status', methods=['GET'])
def printer_status():
    """Get printer status (paper, ink, errors)"""
    status = printer_manager.get_printer_status()
    return jsonify(status)

def print_job_thread(job):
    """Background thread for printing"""
    global current_job
    
    try:
        # Calculate pages to print
        pages = job['pages']
        copies = job['copies']
        page_range = job['page_range']
        
        if page_range and page_range != 'all':
            start_page = int(page_range.get('start', 1))
            end_page = int(page_range.get('end', pages))
            pages_to_print = end_page - start_page + 1
        else:
            pages_to_print = pages
        
        total_pages = pages_to_print * copies
        current_job['total_pages'] = total_pages
        current_job['current_page'] = 0
        
        # Print the document
        result = printer_manager.print_document(
            job['file_path'],
            copies=copies,
            page_range=page_range,
            orientation=job['orientation'],
            color_mode=job['color_mode']
        )
        
        if result['success']:
            current_job['status'] = 'completed'
            current_job['current_page'] = total_pages
            
            # Log successful print
            logging_system.log_print_complete(job, True, None)
            
            # Play completion sound
            audio_feedback.play_completion_sound()
            
            # Reset payment
            time.sleep(2)  # Give time for user to see completion
            current_job['paid'] = 0.0
            current_job['status'] = 'idle'
        else:
            current_job['status'] = 'error'
            error_msg = result.get('error', 'Unknown error')
            
            # Log failed print
            logging_system.log_print_complete(job, False, error_msg)
            
            # Play error sound
            audio_feedback.play_error_sound()
            
            # Send notification
            error_handler.handle_error(error_msg)
    
    except Exception as e:
        logging.error(f"Print job error: {str(e)}")
        current_job['status'] = 'error'
        logging_system.log_print_complete(job, False, str(e))
        error_handler.handle_error(str(e))

def coin_inserted_callback(coin_value):
    """Callback function for coin slot - stores pending coin for web confirmation"""
    global current_job
    try:
        logging.info("="*60)
        logging.info(f"[CALLBACK] COIN CALLBACK TRIGGERED!")
        logging.info(f"[CALLBACK] Coin value: ₱{coin_value}")
        logging.info(f"[CALLBACK] Current job status: {current_job.get('status', 'unknown')}")
        logging.info(f"[CALLBACK] File uploaded: {current_job.get('file_path') is not None}")
        logging.info("="*60)
        
        # Store the detected coin as pending (waiting for web confirmation)
        if 'pending_coin' not in current_job:
            current_job['pending_coin'] = None
        
        current_job['pending_coin'] = coin_value
        current_job['pending_coin_time'] = time.time()
        
        logging.info(f"[CALLBACK] ✓ Pending coin stored: ₱{coin_value}")
        logging.info(f"[CALLBACK] ✓ Waiting for user to confirm via web interface...")
        
        try:
            audio_feedback.play_coin_sound()
            logging.info(f"[CALLBACK] ✓ Audio feedback played")
        except Exception as audio_error:
            logging.debug(f"[CALLBACK] Audio feedback not available: {audio_error}")
        
        logging.info(f"[CALLBACK] ✓ Callback completed successfully")
        
    except Exception as e:
        logging.error(f"[CALLBACK] ✗ Error in coin_inserted_callback: {e}", exc_info=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/vendoprint.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize systems
    logging.info("")
    logging.info("="*70)
    logging.info("VENDOPRINT SYSTEM STARTUP")
    logging.info("="*70)
    
    # Initialize payment system
    logging.info("")
    logging.info("Step 1: Initializing Payment System...")
    payment_system.initialize()
    
    if payment_system.initialized:
        logging.info("")
        logging.info("Step 2: Registering coin callback...")
        payment_system.set_coin_callback(coin_inserted_callback)
        logging.info("✓ Hardware coin slot ENABLED - GPIO detection active")
        logging.info("✓ Coins will be detected automatically from coin slot")
    else:
        logging.warning("⚠ Hardware coin slot NOT available")
        logging.info("→ Using manual/test coin insertion mode")
        logging.info("→ Users can use test buttons (₱1, ₱5, ₱10, ₱20) in the web interface")
    
    logging.info("")
    logging.info("Step 3: Initializing printer...")
    printer_manager.initialize()
    
    logging.info("")
    logging.info("Step 4: Initializing error handler...")
    error_handler.initialize()
    
    # Start HTTP redirect server on port 80 (in background thread)
    logging.info("")
    logging.info("Step 5: Starting HTTP redirect server...")
    try:
        import sys
        import os
        # Import the redirect server module
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from http_redirect_server import run_redirect_server
        
        # Wrap in a function to catch exceptions in the thread
        def start_redirect():
            try:
                run_redirect_server(silent=True)
            except (PermissionError, OSError):
                pass  # Silently fail - main thread already logged the info
        
        redirect_thread = threading.Thread(target=start_redirect, daemon=True)
        redirect_thread.start()
        # Give it a moment to start or fail
        time.sleep(0.1)
        logging.info("✓ HTTP redirect server started on port 80 (or skipped if permission denied)")
    except Exception as e:
        if "Permission denied" in str(e) or "port 80" in str(e).lower():
            logging.info("→ HTTP redirect server skipped (requires sudo for port 80)")
            logging.info("→ For full WiFi portal support, run: sudo python3 app.py")
        else:
            logging.debug(f"→ HTTP redirect server not started: {e}")
    
    # Start Flask app
    logging.info("")
    logging.info("="*70)
    logging.info("SYSTEM READY - Starting web server...")
    logging.info("="*70)
    logging.info("")
    logging.info("→ Flask server: http://0.0.0.0:5000")
    logging.info("→ WiFi portal: http://192.168.4.1:5000")
    logging.info("")
    if payment_system.initialized:
        logging.info("→ Hardware coin detection: ACTIVE (GPIO18)")
        logging.info("→ Insert a coin to test the system!")
    else:
        logging.info("→ Hardware coin detection: DISABLED")
        logging.info("→ Use web interface test buttons instead")
    logging.info("")
    logging.info("="*70)
    logging.info("")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
