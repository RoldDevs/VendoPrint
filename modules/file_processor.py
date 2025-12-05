"""
File Processing Module
Handles file uploads, page counting, and preview generation
"""

import os
import logging
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF for PDF processing
from docx import Document

class FileProcessor:
    def __init__(self):
        self.preview_dir = 'static/previews'
        os.makedirs(self.preview_dir, exist_ok=True)
    
    def count_pages(self, file_path):
        """Count pages in a document"""
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext == '.pdf':
                doc = fitz.open(file_path)
                pages = len(doc)
                doc.close()
                return pages
            
            elif ext in ['.docx', '.doc']:
                # For Word documents, estimate pages (rough calculation)
                doc = Document(file_path)
                # Approximate: 1 page per 500 words or 30 paragraphs
                paragraphs = len(doc.paragraphs)
                pages = max(1, paragraphs // 30)
                return pages
            
            elif ext in ['.png', '.jpg', '.jpeg']:
                return 1
            
            else:
                return 1
        
        except Exception as e:
            logging.error(f"Error counting pages: {str(e)}")
            return 1
    
    def create_image_preview(self, file_path):
        """Create preview thumbnail for image"""
        try:
            img = Image.open(file_path)
            
            # Create thumbnail
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save preview
            preview_path = os.path.join(self.preview_dir, f"preview_{os.path.basename(file_path)}.jpg")
            img.save(preview_path, 'JPEG', quality=85)
            
            return preview_path
        
        except Exception as e:
            logging.error(f"Error creating image preview: {str(e)}")
            return file_path
    
    def create_document_preview(self, file_path):
        """Create preview for document (PDF)"""
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext == '.pdf':
                doc = fitz.open(file_path)
                page = doc[0]  # First page
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
                
                preview_path = os.path.join(self.preview_dir, f"preview_{os.path.basename(file_path)}.png")
                pix.save(preview_path)
                doc.close()
                
                return preview_path
            
            elif ext in ['.png', '.jpg', '.jpeg']:
                return self.create_image_preview(file_path)
            
            else:
                # Return original file path for other types
                return file_path
        
        except Exception as e:
            logging.error(f"Error creating document preview: {str(e)}")
            return file_path
    
    def validate_file(self, file_path):
        """Validate uploaded file"""
        try:
            if not os.path.exists(file_path):
                return False, "File not found"
            
            ext = Path(file_path).suffix.lower()
            if ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.docx', '.doc']:
                return False, "Unsupported file type"
            
            # Check file size (50MB max)
            size = os.path.getsize(file_path)
            if size > 50 * 1024 * 1024:
                return False, "File too large (max 50MB)"
            
            return True, "Valid"
        
        except Exception as e:
            logging.error(f"Error validating file: {str(e)}")
            return False, str(e)

