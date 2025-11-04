"""
ID Image Processor Tool

This tool processes candidate images for ID cards and HRMS systems.
Features:
- Single image upload and processing
- Bulk image upload with zip file support
- Automatic face detection and cropping
- Size optimization for ID cards
- Preview and download functionality
- Support for multiple image formats
"""

import os
import zipfile
import tempfile
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import cv2
import numpy as np
from datetime import datetime

id_processor_bp = Blueprint('id_processor', __name__,
                           template_folder='templates',
                           url_prefix='/id-processor')

# Global variables for processed images
processed_images = []

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def detect_face(image_path):
    """
    Detect faces in an image using OpenCV.
    Returns the coordinates of the largest face found.
    """
    try:
        # Load the cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Read the image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            # Return the largest face
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            return largest_face

        return None
    except Exception as e:
        print(f"Face detection error: {e}")
        return None

def crop_to_id_size(image, face_coords=None, target_size=(200, 250)):
    """
    Crop image to ID card size with face detection or center cropping.
    """
    try:
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)

        if face_coords:
            x, y, w, h = face_coords
            # Add padding around the face
            padding = int(min(w, h) * 0.3)
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(img_array.shape[1], x + w + padding)
            y_end = min(img_array.shape[0], y + h + padding)

            # Crop around the face
            face_img = img_array[y_start:y_end, x_start:x_end]
        else:
            # Use center cropping if no face detected
            height, width = img_array.shape[:2]
            target_ratio = target_size[0] / target_size[1]

            if width / height > target_ratio:
                # Image is wider than needed
                new_width = int(height * target_ratio)
                x_start = (width - new_width) // 2
                face_img = img_array[:, x_start:x_start + new_width]
            else:
                # Image is taller than needed
                new_height = int(width / target_ratio)
                y_start = (height - new_height) // 2
                face_img = img_array[y_start:y_start + new_height, :]

        # Convert back to PIL Image
        face_img_pil = Image.fromarray(face_img)

        # Resize to target size
        resized_img = face_img_pil.resize(target_size, Image.Resampling.LANCZOS)

        return resized_img

    except Exception as e:
        print(f"Cropping error: {e}")
        # Fallback to simple center crop and resize
        return ImageOps.fit(image, target_size, Image.Resampling.LANCZOS)

def process_single_image(image_path, output_size=(200, 250), detect_face_enabled=True):
    """
    Process a single image for ID card use.
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Auto-orient the image
            img = ImageOps.exif_transpose(img)

            # Detect face if enabled
            face_coords = None
            if detect_face_enabled:
                face_coords = detect_face(image_path)

            # Crop to ID size
            processed_img = crop_to_id_size(img, face_coords, output_size)

            return processed_img, face_coords is not None

    except Exception as e:
        print(f"Error processing image: {e}")
        raise

@id_processor_bp.route('/')
def index():
    """Main page for the ID Image Processor tool."""
    return render_template('tools/id_processor.html')

@id_processor_bp.route('/upload', methods=['POST'])
def upload_images():
    """Handle image upload and processing."""
    global processed_images
    processed_images = []

    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images uploaded'}), 400

        files = request.files.getlist('images')
        output_size = (
            int(request.form.get('width', 200)),
            int(request.form.get('height', 250))
        )
        detect_face_enabled = request.form.get('detect_face', 'true').lower() == 'true'

        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        processed_count = 0
        errors = []

        for file in files:
            if file and allowed_file(file.filename):
                try:
                    # Save uploaded file temporarily
                    filename = secure_filename(file.filename)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        file.save(temp_file.name)

                        # Process the image
                        processed_img, face_detected = process_single_image(
                            temp_file.name, output_size, detect_face_enabled
                        )

                        # Save processed image to memory
                        img_buffer = BytesIO()
                        processed_img.save(img_buffer, format='PNG', quality=95)
                        img_buffer.seek(0)

                        # Store processed image info
                        processed_images.append({
                            'filename': f"processed_{filename}",
                            'original_name': filename,
                            'size': output_size,
                            'face_detected': face_detected,
                            'data': img_buffer.getvalue(),
                            'dimensions': processed_img.size,
                            'file_size': len(img_buffer.getvalue())
                        })

                        processed_count += 1

                        # Clean up temporary file
                        os.unlink(temp_file.name)

                except Exception as e:
                    errors.append(f"Error processing {file.filename}: {str(e)}")
            else:
                errors.append(f"Invalid file type: {file.filename}")

        response_data = {
            'success': True,
            'processed_count': processed_count,
            'total_uploaded': len(files),
            'images': processed_images,
            'errors': errors
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@id_processor_bp.route('/download/<int:index>')
def download_image(index):
    """Download a processed image."""
    global processed_images

    try:
        if 0 <= index < len(processed_images):
            image_data = processed_images[index]
            img_buffer = BytesIO(image_data['data'])

            return send_file(
                img_buffer,
                as_attachment=True,
                download_name=image_data['filename'],
                mimetype='image/png'
            )
        else:
            return jsonify({'error': 'Image not found'}), 404

    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@id_processor_bp.route('/download-all')
def download_all_images():
    """Download all processed images as a ZIP file."""
    global processed_images

    try:
        if not processed_images:
            return jsonify({'error': 'No images to download'}), 400

        # Create ZIP file in memory
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, image_data in enumerate(processed_images):
                zip_file.writestr(
                    image_data['filename'],
                    image_data['data']
                )

        zip_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"id_images_processed_{timestamp}.zip"

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': f'ZIP creation failed: {str(e)}'}), 500

@id_processor_bp.route('/preview/<int:index>')
def preview_image(index):
    """Serve a processed image for preview."""
    global processed_images

    try:
        if 0 <= index < len(processed_images):
            image_data = processed_images[index]
            img_buffer = BytesIO(image_data['data'])

            return send_file(
                img_buffer,
                mimetype='image/png'
            )
        else:
            return jsonify({'error': 'Image not found'}), 404

    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@id_processor_bp.route('/clear')
def clear_images():
    """Clear all processed images."""
    global processed_images
    processed_images = []
    return jsonify({'success': True, 'message': 'Images cleared'})

@id_processor_bp.route('/status')
def processing_status():
    """Get current processing status."""
    global processed_images

    return jsonify({
        'processed_count': len(processed_images),
        'total_size': sum(img['file_size'] for img in processed_images),
        'images': [
            {
                'filename': img['filename'],
                'dimensions': img['dimensions'],
                'file_size': img['file_size'],
                'face_detected': img['face_detected']
            }
            for img in processed_images
        ]
    })

# Error handlers
@id_processor_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@id_processor_bp.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400