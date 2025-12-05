"""
Printer Manager Module
Handles printing via CUPS (Common Unix Printing System)
"""

import subprocess
import logging
import os
import time

class PrinterManager:
    def __init__(self, printer_name='Brother'):
        self.printer_name = printer_name
        self.paper_status = 'ok'
        self.ink_status = 'ok'
        self.error_status = None
    
    def initialize(self):
        """Initialize printer connection"""
        try:
            # Check if printer is available
            result = subprocess.run(['lpstat', '-p', self.printer_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"Printer {self.printer_name} is available")
            else:
                logging.warning(f"Printer {self.printer_name} not found, using default")
                # Try to use default printer
                result = subprocess.run(['lpstat', '-d'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # Extract default printer name
                    default_line = result.stdout.split('\n')[0]
                    if ':' in default_line:
                        self.printer_name = default_line.split(':')[1].strip()
                        logging.info(f"Using default printer: {self.printer_name}")
            
            # Check printer status
            self._check_printer_status()
            
        except Exception as e:
            logging.error(f"Error initializing printer: {str(e)}")
    
    def print_document(self, file_path, copies=1, page_range=None, 
                      orientation='portrait', color_mode='grayscale'):
        """Print a document"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            # Build print command
            cmd = ['lp', '-d', self.printer_name]
            
            # Add copies
            cmd.extend(['-n', str(copies)])
            
            # Add orientation
            if orientation == 'landscape':
                cmd.extend(['-o', 'orientation-requested=4'])
            else:
                cmd.extend(['-o', 'orientation-requested=3'])
            
            # Add color mode
            if color_mode == 'grayscale':
                cmd.extend(['-o', 'ColorMode=Grayscale'])
            else:
                cmd.extend(['-o', 'ColorMode=Color'])
            
            # Add page range if specified
            if page_range and page_range != 'all':
                start = page_range.get('start', 1)
                end = page_range.get('end', 999)
                cmd.extend(['-o', f'page-ranges={start}-{end}'])
            
            # Add file
            cmd.append(file_path)
            
            # Execute print command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                job_id = result.stdout.strip().split()[-1] if result.stdout else None
                
                # Wait for print job to complete
                self._wait_for_job_completion(job_id)
                
                return {'success': True, 'job_id': job_id}
            else:
                error_msg = result.stderr.strip() if result.stderr else 'Unknown print error'
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            logging.error(f"Error printing document: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _wait_for_job_completion(self, job_id, timeout=300):
        """Wait for print job to complete"""
        if not job_id:
            return
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(['lpstat', '-o', job_id], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0 or not result.stdout.strip():
                    # Job completed or not found
                    return
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Error checking job status: {str(e)}")
                return
    
    def get_printer_status(self):
        """Get current printer status"""
        try:
            # Check for paper jams, low ink, etc.
            result = subprocess.run(['lpstat', '-p', self.printer_name, '-l'], 
                                  capture_output=True, text=True)
            
            status = {
                'printer_name': self.printer_name,
                'paper_status': self.paper_status,
                'ink_status': self.ink_status,
                'error_status': self.error_status,
                'online': True
            }
            
            # Parse status output for errors
            if 'idle' in result.stdout.lower():
                status['state'] = 'idle'
            elif 'printing' in result.stdout.lower():
                status['state'] = 'printing'
            elif 'stopped' in result.stdout.lower() or 'error' in result.stdout.lower():
                status['state'] = 'error'
                status['error_status'] = 'Printer error detected'
            else:
                status['state'] = 'unknown'
            
            return status
        
        except Exception as e:
            logging.error(f"Error getting printer status: {str(e)}")
            return {
                'printer_name': self.printer_name,
                'paper_status': 'unknown',
                'ink_status': 'unknown',
                'error_status': str(e),
                'online': False,
                'state': 'error'
            }
    
    def _check_printer_status(self):
        """Check printer status and update internal state"""
        status = self.get_printer_status()
        self.paper_status = status.get('paper_status', 'ok')
        self.ink_status = status.get('ink_status', 'ok')
        self.error_status = status.get('error_status')

