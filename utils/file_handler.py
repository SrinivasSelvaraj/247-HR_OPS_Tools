"""
File Handler Utilities

This module provides utilities for file handling, validation, and processing.
"""

import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import magic
from datetime import datetime, timedelta

class FileHandler:
    """Handles file operations including upload, validation, and cleanup."""

    def __init__(self, upload_folder=None, max_content_length=16*1024*1024):
        self.upload_folder = upload_folder or 'data/uploads'
        self.max_content_length = max_content_length
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
            'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
        }

    def ensure_upload_folder(self):
        """Ensure upload folder exists."""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def is_allowed_file(self, filename, file_type='all'):
        """Check if file has allowed extension."""
        if '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()

        if file_type == 'all':
            all_ext = set()
            for exts in self.allowed_extensions.values():
                all_ext.update(exts)
            return ext in all_ext
        else:
            return ext in self.allowed_extensions.get(file_type, set())

    def validate_file(self, file, file_type='all'):
        """Validate uploaded file."""
        validation_result = {
            'valid': False,
            'errors': [],
            'file_info': {}
        }

        if not file or not file.filename:
            validation_result['errors'].append('No file provided')
            return validation_result

        # Check filename
        filename = secure_filename(file.filename)
        if not filename:
            validation_result['errors'].append('Invalid filename')
            return validation_result

        # Check file extension
        if not self.is_allowed_file(filename, file_type):
            validation_result['errors'].append(f'File type not allowed for {file_type}')
            return validation_result

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to beginning

        if file_size > self.max_content_length:
            validation_result['errors'].append(f'File too large (max {self.max_content_length // (1024*1024)}MB)')
            return validation_result

        # Check actual file type (mime type)
        try:
            file_content = file.read(1024)
            file.seek(0)
            mime_type = magic.from_buffer(file_content, mime=True)

            # Basic mime type validation
            allowed_mimes = {
                'images': ['image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp'],
                'documents': ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                'archives': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']
            }

            if file_type != 'all' and mime_type not in allowed_mimes.get(file_type, []):
                validation_result['errors'].append(f'File content type ({mime_type}) does not match extension')
                return validation_result

        except Exception as e:
            validation_result['errors'].append(f'File type detection failed: {str(e)}')

        if not validation_result['errors']:
            validation_result['valid'] = True
            validation_result['file_info'] = {
                'filename': filename,
                'size': file_size,
                'mime_type': mime_type if 'mime_type' in locals() else 'unknown'
            }

        return validation_result

    def save_uploaded_file(self, file, subfolder='', custom_name=None):
        """Save uploaded file and return file path."""
        self.ensure_upload_folder()

        # Generate unique filename
        if custom_name:
            filename = secure_filename(custom_name)
        else:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            filename = f"{uuid.uuid4().hex}.{ext}"

        # Create subfolder if specified
        if subfolder:
            upload_path = os.path.join(self.upload_folder, subfolder)
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
        else:
            upload_path = self.upload_folder

        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)

        return file_path

    def create_temp_file(self, content, suffix='', prefix='tmp_'):
        """Create temporary file with given content."""
        with tempfile.NamedTemporaryFile(mode='w+b', suffix=suffix, prefix=prefix, delete=False) as tmp_file:
            if isinstance(content, str):
                tmp_file.write(content.encode())
            else:
                tmp_file.write(content)
            return tmp_file.name

    def cleanup_old_files(self, days_old=1):
        """Clean up files older than specified days."""
        if not os.path.exists(self.upload_folder):
            return

        cutoff_time = datetime.now() - timedelta(days=days_old)

        for root, dirs, files in os.walk(self.upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                except OSError:
                    continue

    def get_image_dimensions(self, image_path):
        """Get image dimensions."""
        try:
            with Image.open(image_path) as img:
                return img.size  # (width, height)
        except Exception:
            return None

    def resize_image(self, image_path, output_path, size=(200, 250), quality=85):
        """Resize image to specified dimensions."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize image
                resized_img = img.resize(size, Image.Resampling.LANCZOS)

                # Save resized image
                resized_img.save(output_path, 'JPEG', quality=quality)
                return True
        except Exception:
            return False

class FileManager:
    """Manages file operations with tracking and cleanup."""

    def __init__(self):
        self.active_files = {}  # Track active files for cleanup

    def register_file(self, file_path, session_id=None):
        """Register a file for tracking."""
        file_id = str(uuid.uuid4())
        self.active_files[file_id] = {
            'path': file_path,
            'session_id': session_id,
            'created_at': datetime.now()
        }
        return file_id

    def unregister_file(self, file_id):
        """Unregister and optionally cleanup file."""
        if file_id in self.active_files:
            file_info = self.active_files.pop(file_id)
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
            except OSError:
                pass
            return True
        return False

    def cleanup_session_files(self, session_id):
        """Clean up all files for a session."""
        files_to_remove = [
            file_id for file_id, file_info in self.active_files.items()
            if file_info.get('session_id') == session_id
        ]

        for file_id in files_to_remove:
            self.unregister_file(file_id)

        return len(files_to_remove)