from flask import Flask
from config import BaseConfig, config
import logging
import os

def create_app(config_class=BaseConfig):
    """
    Application factory pattern for Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/hr_toolkit.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('HR Operations Toolkit startup')

    # Register blueprints
    from tools.id_processor import id_processor_bp
    from tools.pdf_toolkit import pdf_toolkit_bp
    from tools.exit_verifier import exit_verifier_bp
    from tools.exp_calculator import exp_calculator_bp
    from tools.offer_tracker import offer_tracker_bp
    from tools.id_checker import id_checker_bp

    app.register_blueprint(id_processor_bp, url_prefix='/id-processor')
    app.register_blueprint(pdf_toolkit_bp, url_prefix='/pdf-toolkit')
    app.register_blueprint(exit_verifier_bp, url_prefix='/exit-verifier')
    app.register_blueprint(exp_calculator_bp, url_prefix='/exp-calculator')
    app.register_blueprint(offer_tracker_bp, url_prefix='/offer-tracker')
    app.register_blueprint(id_checker_bp, url_prefix='/id-checker')

    # Main route
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

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)