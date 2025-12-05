import os
import PyPDF2
from PIL import Image
from config import Config

class FileProcessor:
    def __init__(self):
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def process_file(self, filepath, file_type='document'):
        """Process uploaded file and extract information"""
        file_info = {
            'type': file_type,
            'pages': 1,
            'width': 0,
            'height': 0,
            'format': None
        }
        
        try:
            ext = filepath.rsplit('.', 1)[1].lower()
            
            if ext == 'pdf':
                file_info = self._process_pdf(filepath)
            elif ext in ['png', 'jpg', 'jpeg', 'gif']:
                file_info = self._process_image(filepath)
            else:
                # For other file types, assume 1 page
                file_info['format'] = ext
                file_info['pages'] = 1
            
            return file_info
        
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _process_pdf(self, filepath):
        """Process PDF file and count pages"""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Get first page dimensions
                first_page = pdf_reader.pages[0]
                width = float(first_page.mediabox.width)
                height = float(first_page.mediabox.height)
                
                return {
                    'type': 'document',
                    'pages': num_pages,
                    'width': width,
                    'height': height,
                    'format': 'pdf'
                }
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def _process_image(self, filepath):
        """Process image file"""
        try:
            img = Image.open(filepath)
            width, height = img.size
            
            return {
                'type': 'photo',
                'pages': 1,
                'width': width,
                'height': height,
                'format': img.format.lower()
            }
        except Exception as e:
            raise Exception(f"Error reading image: {str(e)}")

