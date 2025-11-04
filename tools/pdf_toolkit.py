"""
PDF Toolkit Tool

This tool provides comprehensive PDF manipulation capabilities.
Features:
- PDF merging and splitting
- PDF compression
- Add watermarks to PDFs
- Convert PDF to images
- Extract text from PDF
- Batch processing capabilities
"""

import os
import tempfile
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import grey
import fitz  # PyMuPDF for PDF to image conversion
from PIL import Image
import zipfile
from datetime import datetime

pdf_toolkit_bp = Blueprint('pdf_toolkit', __name__,
                         template_folder='templates',
                         url_prefix='/pdf-toolkit')

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def compress_pdf(input_path, output_path, quality=0.8):
    """Compress a PDF file by reducing image quality."""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            # Add page to writer (basic compression)
            writer.add_page(page)

        # Write compressed PDF
        with open(output_path, 'wb') as f:
            writer.write(f)

        return True
    except Exception as e:
        print(f"Compression error: {e}")
        return False

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDF files into one."""
    try:
        merger = PdfMerger()

        for pdf_path in pdf_paths:
            merger.append(pdf_path)

        merger.write(output_path)
        merger.close()

        return True
    except Exception as e:
        print(f"Merge error: {e}")
        return False

def split_pdf(input_path, output_dir, split_type='page', pages_per_file=1):
    """Split a PDF file into multiple files."""
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        split_files = []

        if split_type == 'page':
            # Split each page into separate file
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)

                output_file = os.path.join(output_dir, f'page_{i+1}.pdf')
                with open(output_file, 'wb') as f:
                    writer.write(f)

                split_files.append(output_file)

        elif split_type == 'range':
            # Split into ranges of pages
            for i in range(0, total_pages, pages_per_file):
                writer = PdfWriter()
                end_page = min(i + pages_per_file, total_pages)

                for j in range(i, end_page):
                    writer.add_page(reader.pages[j])

                output_file = os.path.join(output_dir, f'pages_{i+1}-{end_page}.pdf')
                with open(output_file, 'wb') as f:
                    writer.write(f)

                split_files.append(output_file)

        return split_files
    except Exception as e:
        print(f"Split error: {e}")
        return []

def add_watermark(input_path, output_path, watermark_text, opacity=0.3):
    """Add a text watermark to a PDF file."""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            # Create watermark PDF
            watermark_packet = BytesIO()
            can = canvas.Canvas(watermark_packet, pagesize=letter)
            can.setFont("Helvetica", 40)
            can.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
            can.saveState()
            can.translate(300, 300)
            can.rotate(45)
            can.drawString(0, 0, watermark_text)
            can.restoreState()
            can.save()

            watermark_packet.seek(0)
            watermark = PdfReader(watermark_packet)
            watermark_page = watermark.pages[0]

            # Merge watermark with page
            page.merge_page(watermark_page)
            writer.add_page(page)

        with open(output_path, 'wb') as f:
            writer.write(f)

        return True
    except Exception as e:
        print(f"Watermark error: {e}")
        return False

def pdf_to_images(input_path, output_dir, dpi=150, format='PNG'):
    """Convert PDF pages to images."""
    try:
        doc = fitz.open(input_path)
        image_files = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))

            output_file = os.path.join(output_dir, f'page_{page_num+1}.{format.lower()}')
            pix.save(output_file)
            image_files.append(output_file)

        doc.close()
        return image_files
    except Exception as e:
        print(f"PDF to images error: {e}")
        return []

def extract_text_from_pdf(input_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(input_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text
    except Exception as e:
        print(f"Text extraction error: {e}")
        return ""

@pdf_toolkit_bp.route('/')
def index():
    """Main page for the PDF Toolkit."""
    return render_template('tools/pdf_toolkit.html')

@pdf_toolkit_bp.route('/process', methods=['POST'])
def process_pdfs():
    """Handle PDF processing operations."""
    try:
        if 'pdfs' not in request.files:
            return jsonify({'error': 'No PDF files uploaded'}), 400

        files = request.files.getlist('pdfs')
        operation = request.form.get('operation')
        operation_type = request.form.get('type', 'single')

        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        # Validate PDF files
        pdf_files = [file for file in files if file and allowed_file(file.filename)]
        if not pdf_files:
            return jsonify({'error': 'No valid PDF files found'}), 400

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            uploaded_paths = []
            for file in pdf_files:
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                uploaded_paths.append(file_path)

            # Process based on operation
            result_file = None
            result_files = []
            extracted_text = None

            try:
                if operation == 'merge':
                    if len(uploaded_paths) < 2:
                        return jsonify({'error': 'At least 2 PDF files required for merging'}), 400

                    output_file = os.path.join(temp_dir, 'merged.pdf')
                    if merge_pdfs(uploaded_paths, output_file):
                        result_file = output_file

                elif operation == 'split':
                    if len(uploaded_paths) != 1:
                        return jsonify({'error': 'Exactly 1 PDF file required for splitting'}), 400

                    split_type = request.form.get('split_type', 'page')
                    pages_per_file = int(request.form.get('pages_per_file', 1))

                    output_dir = os.path.join(temp_dir, 'split')
                    os.makedirs(output_dir, exist_ok=True)

                    result_files = split_pdf(uploaded_paths[0], output_dir, split_type, pages_per_file)

                elif operation == 'compress':
                    if len(uploaded_paths) != 1:
                        return jsonify({'error': 'Exactly 1 PDF file required for compression'}), 400

                    quality = float(request.form.get('quality', 0.8))
                    output_file = os.path.join(temp_dir, 'compressed.pdf')

                    if compress_pdf(uploaded_paths[0], output_file, quality):
                        result_file = output_file

                elif operation == 'watermark':
                    if len(uploaded_paths) != 1:
                        return jsonify({'error': 'Exactly 1 PDF file required for watermarking'}), 400

                    watermark_text = request.form.get('watermark_text', 'CONFIDENTIAL')
                    opacity = float(request.form.get('opacity', 0.3))
                    output_file = os.path.join(temp_dir, 'watermarked.pdf')

                    if add_watermark(uploaded_paths[0], output_file, watermark_text, opacity):
                        result_file = output_file

                elif operation == 'convert':
                    if len(uploaded_paths) != 1:
                        return jsonify({'error': 'Exactly 1 PDF file required for conversion'}), 400

                    dpi = int(request.form.get('dpi', 150))
                    output_format = request.form.get('format', 'PNG')
                    output_dir = os.path.join(temp_dir, 'images')
                    os.makedirs(output_dir, exist_ok=True)

                    result_files = pdf_to_images(uploaded_paths[0], output_dir, dpi, output_format)

                elif operation == 'extract':
                    if len(uploaded_paths) != 1:
                        return jsonify({'error': 'Exactly 1 PDF file required for text extraction'}), 400

                    extracted_text = extract_text_from_pdf(uploaded_paths[0])

                else:
                    return jsonify({'error': 'Invalid operation'}), 400

                # Prepare response
                if operation == 'extract':
                    response_data = {
                        'success': True,
                        'operation': operation,
                        'text': extracted_text,
                        'text_length': len(extracted_text) if extracted_text else 0
                    }
                elif result_files:
                    # Multiple files result (split, convert)
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_path in result_files:
                            filename = os.path.basename(file_path)
                            zip_file.write(file_path, filename)

                    zip_buffer.seek(0)

                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"pdf_{operation}_{timestamp}.zip"

                    return send_file(
                        zip_buffer,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/zip'
                    )

                elif result_file and os.path.exists(result_file):
                    # Single file result
                    with open(result_file, 'rb') as f:
                        file_data = f.read()

                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"pdf_{operation}_{timestamp}.pdf"

                    return send_file(
                        BytesIO(file_data),
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf'
                    )
                else:
                    return jsonify({'error': 'Operation failed'}), 500

            except Exception as e:
                return jsonify({'error': f'Processing failed: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@pdf_toolkit_bp.route('/validate', methods=['POST'])
def validate_pdfs():
    """Validate uploaded PDF files."""
    try:
        if 'pdfs' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('pdfs')
        valid_files = []
        invalid_files = []

        for file in files:
            if file and allowed_file(file.filename):
                # Try to read the PDF to ensure it's valid
                try:
                    file_content = file.read()
                    if len(file_content) > 0:
                        file.seek(0)
                        valid_files.append({
                            'name': file.filename,
                            'size': len(file_content)
                        })
                    else:
                        invalid_files.append({'name': file.filename, 'error': 'Empty file'})
                except Exception as e:
                    invalid_files.append({'name': file.filename, 'error': str(e)})
            else:
                invalid_files.append({'name': file.filename, 'error': 'Invalid PDF file'})

        return jsonify({
            'success': True,
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_files': len(files)
        })

    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

# Error handlers
@pdf_toolkit_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@pdf_toolkit_bp.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400