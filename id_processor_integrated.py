"""
Complete ID Image Processor Flask Application
Integrates the provided backend with a modern frontend
"""

import os
import cv2
import numpy as np

import zipfile
import io
import time
import traceback
import fitz  # PyMuPDF
import base64
import sys
import tempfile
import atexit
import shutil
from flask import Flask, render_template, render_template_string, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename

def get_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- Flask App Setup ---
app = Flask(__name__, template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['SECRET_KEY'] = 'id-processor-secret-key'

# Configuration
MODEL_PATH = "face_detection_yunet_2023mar.onnx"  # Update with your actual model path
# Create a temporary directory for processed files
TEMP_DIR = tempfile.mkdtemp()
# Map temporary filenames -> user-visible download filename
TEMP_NAME_MAP = {}

# Register cleanup function to remove temporary directory on application exit
@atexit.register
def cleanup_temp_files():
    try:
        shutil.rmtree(TEMP_DIR)
    except Exception as e:
        print(f"Error cleaning up temporary files: {e}")

# Function to create a temporary file and return its path
def create_temp_file(suffix=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=suffix)
    temp_file.close()
    return temp_file.name

def rotate_image(image, angle):
    """Rotate image by specified angle"""
    if image is None:
        return None
    center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))

def process_image(cv_image, model_path):
    """Process image with face detection and cropping"""
    # Check if model file exists, fallback to basic processing if not
    if not os.path.exists(model_path):
        return cv2.resize(cv_image, (360, 480)), "Processed (fallback - no face detection model)"

    try:
        detector = cv2.FaceDetectorYN_create(model_path, "", (0, 0), score_threshold=0.6)
        best_angle, best_face, max_score, final_rotated_image = 0, None, -1.0, None

        for angle in [0, -90, -180, -270]:
            rotated_test_image = rotate_image(cv_image, angle)
            if rotated_test_image is None:
                continue

            h, w, _ = rotated_test_image.shape
            detector.setInputSize((w, h))
            _, faces = detector.detect(rotated_test_image)

            if faces is not None and len(faces) > 0 and faces[0][14] > max_score:
                max_score, best_angle, best_face, final_rotated_image = faces[0][14], angle, faces[0], rotated_test_image

        if best_face is None:
            return None, "No face detected"

        (x, y, w, h) = list(map(int, best_face[:4]))
        final_w = int(w * 1.8)
        final_h = int(final_w * (4.0 / 3.0))
        center_x = x + w // 2
        crop_y = y - int(final_h * 0.25)
        crop_x = center_x - (final_w // 2)
        crop_x, crop_y = max(0, crop_x), max(0, crop_y)

        cropped_region = final_rotated_image[crop_y:crop_y + final_h, crop_x:crop_x + final_w]

        if cropped_region.shape[0] > 0 and cropped_region.shape[1] > 0:
            return cv2.resize(cropped_region, (360, 480), interpolation=cv2.INTER_AREA), "Success"

        return None, "Cropping resulted in empty image"

    except Exception as e:
        # Fallback to basic resize if face detection fails
        return cv2.resize(cv_image, (360, 480)), "Processed with fallback (face detection failed)"

@app.route('/')
def index():
    """Main page"""
    return render_template_string(open('id_processor_frontend.html', encoding='utf-8').read())

@app.route('/process-file', methods=['POST'])
def process_file_route():
    """Process uploaded file"""
    try:
        files = request.files.getlist('file_input')
        if not files or len(files) == 0:
            return jsonify({'status': 'error', 'logs': ["❌ ERROR: No file selected."]})

        # If multiple files were uploaded (non-zip), process them as a batch
        if len(files) > 1:
            logs = [f"🚀 Processing {len(files)} uploaded files..."]
            success_count = 0
            PHOTO_LIMIT = 5
            if len(files) > PHOTO_LIMIT:
                return jsonify({'status': 'error', 'logs': [f"❌ ERROR: You uploaded {len(files)} files; the limit is {PHOTO_LIMIT}."]})

            output_zip_stream = io.BytesIO()
            # Allow client to request a specific output zip name
            requested_name = request.form.get('output_name', '').strip()
            if requested_name:
                safe_output_name = secure_filename(requested_name)
                if not safe_output_name.lower().endswith('.zip'):
                    safe_output_name = safe_output_name + '.zip'
            else:
                safe_output_name = 'processed_files.zip'

            for f in files:
                original_filename = f.filename
                base_name, extension = os.path.splitext(original_filename)
                logs.append(f"⏳ Processing '{original_filename}'...")

                # Read image bytes and convert
                try:
                    if extension.lower() == '.pdf':
                        doc = fitz.open(stream=f.read(), filetype='pdf')
                        if doc.page_count > 0:
                            page = doc[0]
                            pix = page.get_pixmap()
                            img_array = np.frombuffer(pix.tobytes('ppm'), np.uint8)
                            cv_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        else:
                            logs[-1] = f"🟡 SKIPPING: PDF '{original_filename}' is empty."
                            continue
                    else:
                        img_bytes = f.read()
                        cv_image = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)

                    if cv_image is None:
                        logs[-1] = f"🟡 SKIPPING: Cannot decode '{original_filename}'"
                        continue

                    processed_image, msg = process_image(cv_image, MODEL_PATH)
                    if processed_image is not None:
                        _, img_buffer = cv2.imencode('.jpg', processed_image)
                        base = os.path.splitext(os.path.basename(original_filename))[0]
                        with zipfile.ZipFile(output_zip_stream, 'a', zipfile.ZIP_DEFLATED, False) as output_zip:
                            output_zip.writestr(f"{base}_processed.jpg", img_buffer.tobytes())
                        logs[-1] = f"✅ SUCCESS: '{original_filename}'"
                        success_count += 1
                    else:
                        logs[-1] = f"❌ FAILED: '{original_filename}': {msg}"
                except Exception as e:
                    logs[-1] = f"❌ FAILED: '{original_filename}': {str(e)}"

            if success_count > 0:
                temp_path = create_temp_file(suffix='.zip')
                with open(temp_path, 'wb') as out_f:
                    out_f.write(output_zip_stream.getvalue())

                logs.append(f"🎉 DONE: Successfully processed {success_count} files. Click download to get the results ZIP.")
                TEMP_NAME_MAP[os.path.basename(temp_path)] = safe_output_name
                return jsonify({
                    'status': 'success',
                    'logs': logs,
                    'download_url': f'/download/{os.path.basename(temp_path)}',
                    'download_filename': safe_output_name
                })
            else:
                return jsonify({'status': 'error', 'logs': logs + ["No images were successfully processed."]})

        # Single-file handling (fallthrough)
        file = files[0]
        original_filename = file.filename
        base_name, extension = os.path.splitext(original_filename)

        # --- SINGLE FILE and PDF processing ---
        if extension.lower() in ['.jpg', '.jpeg', '.png', '.pdf']:
            cv_image = None
            logs = []

            if extension.lower() == '.pdf':
                logs.append(f"📄 Reading PDF: '{original_filename}'...")
                doc = fitz.open(stream=file.read(), filetype="pdf")
                if doc.page_count > 0:
                    page = doc[0]
                    pix = page.get_pixmap()
                    img_array = np.frombuffer(pix.tobytes("ppm"), np.uint8)
                    cv_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                else:
                    return jsonify({'status': 'error', 'logs': logs + ["❌ ERROR: PDF is empty."]})
            else:
                cv_image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

            if cv_image is None:
                return jsonify({'status': 'error', 'logs': [f"❌ ERROR: Could not read file."]})

            logs.append(f"⏳ Processing '{original_filename}'...")
            processed_image, msg = process_image(cv_image, MODEL_PATH)

            if processed_image is not None:
                _, buffer = cv2.imencode('.jpg', processed_image)
                base64_image = base64.b64encode(buffer).decode('utf-8')

                # Save to temporary file
                temp_path = create_temp_file(suffix='.jpg')
                cv2.imwrite(temp_path, processed_image)

                logs[-1] = f"✅ SUCCESS: {msg}"
                display_name = f"{base_name}_processed.jpg"
                TEMP_NAME_MAP[os.path.basename(temp_path)] = display_name
                return jsonify({
                    'status': 'success',
                    'logs': logs,
                    'image_data': base64_image,
                    'download_url': f'/download/{os.path.basename(temp_path)}',
                    'download_filename': display_name
                })
            else:
                logs[-1] = f"❌ FAILED: {msg}"
                return jsonify({'status': 'error', 'logs': logs})

        # --- BULK ZIP Processing ---
        elif extension.lower() == '.zip':
            logs = [f"🚀 Unpacking '{original_filename}'..."]
            success_count = 0
            PHOTO_LIMIT = 100
            zip_stream = io.BytesIO(file.read())
            output_zip_stream = io.BytesIO()

            with zipfile.ZipFile(zip_stream, 'r') as input_zip:
                file_list = [name for name in input_zip.namelist() if not name.startswith('__MACOSX/')]
                if len(file_list) > PHOTO_LIMIT:
                    return jsonify({
                        'status': 'error',
                        'logs': [f"❌ ERROR: ZIP contains {len(file_list)} files, which is over the limit of {PHOTO_LIMIT}."]
                    })

                for filename_in_zip in file_list:
                    if filename_in_zip.endswith('/'):
                        continue

                    logs.append(f"⏳ Processing '{os.path.basename(filename_in_zip)}'...")
                    img_bytes = input_zip.read(filename_in_zip)
                    if not img_bytes:
                        logs[-1] = f"🟡 SKIPPING: '{os.path.basename(filename_in_zip)}' is empty."
                        continue

                    cv_image = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                    if cv_image is None:
                        logs[-1] = f"🟡 SKIPPING: Cannot decode '{os.path.basename(filename_in_zip)}'"
                        continue

                    processed_image, msg = process_image(cv_image, MODEL_PATH)
                    if processed_image is not None:
                        _, img_buffer = cv2.imencode('.jpg', processed_image)
                        base, _ = os.path.splitext(os.path.basename(filename_in_zip))
                        with zipfile.ZipFile(output_zip_stream, 'a', zipfile.ZIP_DEFLATED, False) as output_zip:
                            output_zip.writestr(f"{base}_processed.jpg", img_buffer.tobytes())
                        logs[-1] = f"✅ SUCCESS: '{os.path.basename(filename_in_zip)}'"
                        success_count += 1
                    else:
                        logs[-1] = f"❌ FAILED: '{os.path.basename(filename_in_zip)}': {msg}"

            if success_count > 0:
                # Save ZIP to temporary file
                temp_path = create_temp_file(suffix='.zip')
                with open(temp_path, 'wb') as f:
                    f.write(output_zip_stream.getvalue())

                logs.append(f"🎉 DONE: Successfully processed {success_count} images. Click download to get the results ZIP.")
                # Allow optional output name override from form
                requested_name = request.form.get('output_name', '').strip()
                if requested_name:
                    safe_name = secure_filename(requested_name)
                    if not safe_name.lower().endswith('.zip'):
                        safe_name = safe_name + '.zip'
                    download_filename = safe_name
                else:
                    download_filename = f'processed_{base_name}.zip'

                # Store desired download filename for this temp file
                TEMP_NAME_MAP[os.path.basename(temp_path)] = download_filename

                return jsonify({
                    'status': 'success',
                    'logs': logs,
                    'download_url': f'/download/{os.path.basename(temp_path)}',
                    'download_filename': download_filename
                })
            else:
                return jsonify({'status': 'error', 'logs': logs + ["No images were successfully processed."]})
        else:
            return jsonify({'status': 'error', 'logs': [f"❌ ERROR: Unsupported file type '{extension}'."]})

    except Exception as e:
        error_details = traceback.format_exc()
        print(error_details)
        return jsonify({'status': 'error', 'logs': [f"❌ An unexpected server error occurred: {str(e)}"]})

@app.route('/download/<path:filename>')
def download_file(filename):
    """Serve processed files from temporary directory"""
    temp_file_path = os.path.join(TEMP_DIR, filename)
    
    if not os.path.exists(temp_file_path):
        return jsonify({'error': 'File not found'}), 404
        
    @after_this_request
    def remove_file(response):
        try:
            # Delete the temporary file after sending
            os.unlink(temp_file_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
        return response

    # Determine display filename if available
    display_name = TEMP_NAME_MAP.pop(filename, None)
    try:
        if display_name:
            # Flask >=2.0 supports download_name
            return send_file(temp_file_path, as_attachment=True, download_name=display_name)
        else:
            return send_file(temp_file_path, as_attachment=True)
    except TypeError:
        # Older Flask versions use 'attachment_filename'
        if display_name:
            return send_file(temp_file_path, as_attachment=True, attachment_filename=display_name)
        return send_file(temp_file_path, as_attachment=True)

if __name__ == '__main__':
    # Ensure temporary directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("🚀 Starting ID Image Processor...")
    print("📍 Application will be available at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")

    # If you want to use webview like your original code:
    # import webview
    # window = webview.create_window("ID Photo Processor", app, width=800, height=850, resizable=True)
    # webview.start(debug=True)

    # Or run as Flask app:
    app.run(debug=True, host='0.0.0.0', port=5000)