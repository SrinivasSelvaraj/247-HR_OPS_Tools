#!/usr/bin/env python3
"""
Minimal Flask Application for HR Operations Toolkit
Works without OpenCV, NumPy, or other heavy dependencies
"""

import os
from flask import Flask, render_template

def create_minimal_app():
    """Create a minimal Flask app that works with basic dependencies only."""
    app = Flask(__name__)

    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Create necessary directories
    for directory in ['data/uploads', 'data/exports', 'logs']:
        os.makedirs(directory, exist_ok=True)

    @app.route('/')
    def index():
        """Main page with tools."""
        tools = [
            {
                "name": "ID Image Processor",
                "icon": "fa-solid fa-id-card",
                "description": "Crop candidate Images for ID cards or HRMS either single or bulk.",
                "url": "#",  # Disabled for now
                "status": "maintenance"
            },
            {
                "name": "Complete PDF Toolkit",
                "icon": "fa-solid fa-file-pdf",
                "description": "A complete offline PDF toolkit for all your PDF needs.",
                "url": "#",  # Disabled for now
                "status": "maintenance"
            },
            {
                "name": "Employee Exit Verifier",
                "icon": "fa-solid fa-person-walking-arrow-right",
                "description": "Instantaneous check candidates exit status and FFS details.",
                "url": "/exit-verifier-demo",
                "status": "available"
            },
            {
                "name": "Candidate Experience Calculator",
                "icon": "fa-solid fa-calculator",
                "description": "Analyze the candidate work experience of previous companies.",
                "url": "/exp-calculator-demo",
                "status": "available"
            },
            {
                "name": "Offer Release Tracker",
                "icon": "fa-solid fa-clipboard-check",
                "description": "User friendly Tracker for logging offer releases.",
                "url": "/offer-tracker-demo",
                "status": "available"
            },
            {
                "name": "Employee ID Availability",
                "icon": "fa-solid fa-magnifying-glass-plus",
                "description": "Check EMP ID availability for EMP ID allocation.",
                "url": "/id-checker-demo",
                "status": "available"
            }
        ]
        return render_template('index.html', tools=tools)

    @app.route('/exit-verifier-demo')
    def exit_verifier_demo():
        """Demo page for Employee Exit Verifier."""
        return render_template('demo_tool.html',
                             tool_name="Employee Exit Verifier",
                             tool_description="Verify employee exit status and FFS details")

    @app.route('/exp-calculator-demo')
    def exp_calculator_demo():
        """Demo page for Candidate Experience Calculator."""
        return render_template('demo_tool.html',
                             tool_name="Candidate Experience Calculator",
                             tool_description="Analyze and calculate candidate work experience")

    @app.route('/offer-tracker-demo')
    def offer_tracker_demo():
        """Demo page for Offer Release Tracker."""
        return render_template('demo_tool.html',
                             tool_name="Offer Release Tracker",
                             tool_description="Track offer releases and candidate communication")

    @app.route('/id-checker-demo')
    def id_checker_demo():
        """Demo page for Employee ID Availability."""
        return render_template('demo_tool.html',
                             tool_name="Employee ID Availability",
                             tool_description="Check and generate available employee IDs")

    return app

if __name__ == '__main__':
    app = create_minimal_app()
    print("🚀 Starting Minimal HR Operations Toolkit...")
    print("📍 Application will be available at: http://localhost:5000")
    print("💡 This is a demo version - some features may be limited")
    print("🔧 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)