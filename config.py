import os
from datetime import timedelta

class BaseConfig:
    """
    Base configuration class with default settings.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///data/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'data/uploads'
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER') or 'data/exports'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

    # Security configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
    }

    # Tool configuration
    TOOLS = {
        'id_processor': {
            'max_images': 50,
            'supported_formats': ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'],
            'max_image_size': 5 * 1024 * 1024,  # 5MB per image
            'output_formats': ['png', 'jpg'],
            'default_output_size': (200, 250)  # Width, Height in pixels
        },
        'pdf_toolkit': {
            'max_pdf_size': 50 * 1024 * 1024,  # 50MB
            'max_pages': 1000,
            'supported_operations': ['merge', 'split', 'compress', 'watermark', 'convert', 'extract']
        },
        'exit_verifier': {
            'cache_duration': 3600,  # 1 hour cache
            'bulk_limit': 100
        },
        'exp_calculator': {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'supported_formats': ['pdf', 'doc', 'docx', 'txt']
        },
        'offer_tracker': {
            'export_formats': ['excel', 'csv', 'pdf'],
            'auto_save': True
        },
        'id_checker': {
            'id_patterns': [
                'EMP####',
                'USER####',
                'STF####'
            ],
            'reserved_ids': ['EMP0000', 'USER0000', 'STF0000']
        }
    }

class DevelopmentConfig(BaseConfig):
    """
    Development configuration.
    """
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/database_dev.db'

    # Development-specific settings
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class ProductionConfig(BaseConfig):
    """
    Production configuration.
    """
    DEBUG = False
    TESTING = False

    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Production database (can be overridden by environment variables)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///data/database.db'

    # Production file handling
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

class TestingConfig(BaseConfig):
    """
    Testing configuration.
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}