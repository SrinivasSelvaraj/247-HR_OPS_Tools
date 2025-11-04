#!/usr/bin/env python3
"""
Simple Flask application runner for HR Operations Toolkit
This script handles the app creation and provides a simple way to run the application.
"""

import os
from flask import Flask

def create_simple_app():
    """Create a simplified Flask app for easy testing."""
    app = Flask(__name__)

    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'data/uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Simple main route
    @app.route('/')
    def index():
        """
        Renders the main page of the HR Toolkit.
        """
        tools = [
            {
                "name": "ID Image Processor",
                "icon": "fa-solid fa-id-card",
                "description": "Crop candidate Images for ID cards or HRMS either single or bulk.",
                "url": "/id-processor"
            },
            {
                "name": "Complete PDF Toolkit",
                "icon": "fa-solid fa-file-pdf",
                "description": "A complete offline PDF toolkit for all your PDF needs.",
                "url": "/pdf-toolkit"
            },
            {
                "name": "Employee Exit Verifier",
                "icon": "fa-solid fa-person-walking-arrow-right",
                "description": "Instantaneous check candidates exit status and FFS details.",
                "url": "/exit-verifier"
            },
            {
                "name": "Candidate Experience Calculator",
                "icon": "fa-solid fa-calculator",
                "description": "Analyze the candidate work experience of previous companies.",
                "url": "/exp-calculator"
            },
            {
                "name": "Offer Release Tracker",
                "icon": "fa-solid fa-clipboard-check",
                "description": "User friendly Tracker for logging offer releases.",
                "url": "/offer-tracker"
            },
            {
                "name": "Employee ID Availability",
                "icon": "fa-solid fa-magnifying-glass-plus",
                "description": "Check EMP ID availability for EMP ID allocation.",
                "url": "/id-checker"
            },
        ]
        from flask import render_template
        return render_template('index.html', tools=tools)

    return app

if __name__ == '__main__':
    # Create necessary directories
    for directory in ['data/uploads', 'data/exports', 'logs']:
        os.makedirs(directory, exist_ok=True)

    # Try to use the full app first, fallback to simple app
    try:
        from app import create_app
        app = create_app()
        print("✅ Using full HR Operations Toolkit application")
    except ImportError as e:
        print(f"⚠️  Import error in full app: {e}")
        print("🔄 Using simplified application")
        app = create_simple_app()

    print("🚀 Starting HR Operations Toolkit...")
    print("📍 Application will be available at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 HR Operations Toolkit stopped successfully")