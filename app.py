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
payment_system = PaymentSystem()
printer_manager = PrinterManager(CONFIG.get('PRINTER_NAME', 'Brother'))
logging_system = LoggingSystem()
error_handler = ErrorHandler()
audio_feedback = AudioFeedback()

@app.route('/')
def index():
    """Main page - choose between Print Photo or Print Document"""
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
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'document')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process file to get page count and preview
            if file_type == 'photo':
                pages = 1
                preview_path = file_processor.create_image_preview(file_path)
            else:
                pages = file_processor.count_pages(file_path)
                preview_path = file_processor.create_document_preview(file_path)
            
            # Store in session
            session['current_file'] = file_path
            session['file_type'] = file_type
            session['pages'] = pages
            
            # Reset current job
            global current_job
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
                'status': 'uploaded'
            }
            
            return jsonify({
                'success': True,
                'file_path': file_path,
                'preview_path': preview_path,
                'pages': pages,
                'file_type': file_type
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    try:
        data = request.json
        pages = data.get('pages', current_job['pages'])
        copies = data.get('copies', 1)
        color_mode = data.get('color_mode', 'grayscale')
        page_range = data.get('page_range', None)
        
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
        global current_job
        current_job['copies'] = copies
        current_job['page_range'] = page_range
        current_job['orientation'] = data.get('orientation', 'portrait')
        current_job['color_mode'] = color_mode
        current_job['cost'] = total_cost
        
        return jsonify({
            'success': True,
            'cost': total_cost,
            'pages': actual_pages,
            'price_per_page': price_per_page
        })
    
    except Exception as e:
        logging.error(f"Cost calculation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-status', methods=['GET'])
def payment_status():
    """Get current payment status"""
    global current_job
    return jsonify({
        'paid': current_job['paid'],
        'cost': current_job['cost'],
        'remaining': max(0, current_job['cost'] - current_job['paid']),
        'can_print': current_job['paid'] >= current_job['cost']
    })

@app.route('/api/coin-inserted', methods=['POST'])
def coin_inserted():
    """Handle coin insertion from coin slot"""
    try:
        data = request.json
        coin_value = float(data.get('value', 0))
        
        if coin_value not in CONFIG['COIN_VALUES']:
            return jsonify({'error': 'Invalid coin value'}), 400
        
        global current_job
        current_job['paid'] += coin_value
        
        # Log payment
        logging_system.log_payment(coin_value, current_job['paid'], current_job['cost'])
        
        # Play coin sound
        audio_feedback.play_coin_sound()
        
        can_print = current_job['paid'] >= current_job['cost']
        
        return jsonify({
            'success': True,
            'paid': current_job['paid'],
            'cost': current_job['cost'],
            'remaining': max(0, current_job['cost'] - current_job['paid']),
            'can_print': can_print
        })
    
    except Exception as e:
        logging.error(f"Coin insertion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-print', methods=['POST'])
def start_print():
    """Start printing process"""
    try:
        global current_job
        
        if current_job['paid'] < current_job['cost']:
            return jsonify({'error': 'Insufficient payment'}), 400
        
        if current_job['status'] != 'uploaded':
            return jsonify({'error': 'No file ready for printing'}), 400
        
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
    """Callback function for coin slot - updates payment"""
    global current_job
    if current_job['status'] in ['uploaded', 'idle']:
        current_job['paid'] += coin_value
        logging_system.log_payment(coin_value, current_job['paid'], current_job['cost'])
        audio_feedback.play_coin_sound()
        logging.info(f"Coin inserted: ₱{coin_value}, Total paid: ₱{current_job['paid']}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/vendoprint.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize systems
    logging.info("Initializing VendoPrint system...")
    payment_system.initialize()
    payment_system.set_coin_callback(coin_inserted_callback)
    printer_manager.initialize()
    error_handler.initialize()
    
    # Start Flask app
    logging.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
