from flask import Flask, request, jsonify, render_template
from config import BaseConfig, config
import logging
import os
import pandas as pd
import numpy as np

def create_app(config_class=None):
    """
    Application factory pattern for Flask app.
    """
    app = Flask(__name__)

    # --- Data Loading and Preparation (module-level-like loader) ---
    # Attempt to load the Parquet data from project `data/uploads/employee_data.parquet`.
    # This mirrors the standalone `app code.py` behaviour so the UI at root can call
    # `/search_employee` and `/filter_by_dob_summary`.
    global df
    global date_columns
    date_columns = ['DOJ', 'Last Working Date', 'DOB']
    try:
        base_dir = os.path.dirname(__file__)
        data_path = os.path.normpath(os.path.join(base_dir, 'data', 'uploads', 'employee_data.parquet'))
        # Try parquet first, then CSV, then Excel
        csv_path = os.path.normpath(os.path.join(base_dir, 'data', 'uploads', 'employee_data.csv'))
        excel_path = os.path.normpath(os.path.join(base_dir, 'data', 'uploads', 'employee_data.xlsx'))
        if os.path.exists(data_path):
            df = pd.read_parquet(data_path)
        elif os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        elif os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path, engine='openpyxl')
            except Exception:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()
        if df is not None and not df.empty:
            # normalize column names
            df.columns = df.columns.astype(str).str.strip()

            # detect Employee ID column under various names
            emp_col = None
            for c in df.columns:
                lc = c.lower()
                if 'employee' in lc and 'id' in lc:
                    emp_col = c
                    break
            if emp_col is None and 'Employee ID' in df.columns:
                emp_col = 'Employee ID'

            if emp_col is not None:
                # normalize Employee ID values to strings and ensure leading zero when appropriate
                df[emp_col] = df[emp_col].astype(str).str.strip().replace('nan', '')
                df[emp_col] = df[emp_col].apply(lambda x: ('0' + x) if (x and not str(x).startswith('0')) else x)
                # rename to standard column name and set index
                if emp_col != 'Employee ID':
                    df = df.rename(columns={emp_col: 'Employee ID'})
                df.set_index('Employee ID', inplace=True)

            if 'FFS' in df.columns:
                df['FFS'] = pd.to_numeric(df['FFS'], errors='coerce')
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            df = df.fillna('Not Available')
        else:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()

    # Determine which config to use
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        config_class = config.get(env, BaseConfig)

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
    # Use the integrated standalone ID processor module's view functions
    # by wrapping them in a blueprint so the integrated processor is
    # served at the same `/id-processor` URL in this host app.
    try:
        import id_processor_integrated as integrated_module
    except Exception:
        # Fallback to the original blueprint if the integrated module isn't available
        from tools.id_processor import id_processor_bp
        integrated_module = None

    from tools.pdf_toolkit import pdf_toolkit_bp
    from tools.exit_verifier import exit_verifier_bp
    from tools.exp_calculator import exp_calculator_bp
    from tools.offer_tracker import offer_tracker_bp
    from tools.id_checker import id_checker_bp

    # If the integrated module was imported, create a blueprint wrapper
    # that routes to its functions. Otherwise register the existing blueprint.
    if integrated_module is not None:
        from flask import Blueprint

        id_processor_bp = Blueprint('id_processor_integrated', __name__, template_folder='templates')

        # The integrated module defines these functions: index, process_file_route, download_file
        # Wrap them so we catch exceptions and ensure JSON responses for the AJAX endpoint.
        from flask import current_app, jsonify

        def index_wrapper(*args, **kwargs):
            try:
                return integrated_module.index()
            except Exception as e:
                current_app.logger.exception('Error in integrated index')
                return "", 500

        def process_file_wrapper(*args, **kwargs):
            try:
                resp = integrated_module.process_file_route()
                # If the integrated function returns a Response or dict, return as-is
                return resp
            except Exception as e:
                current_app.logger.exception('Error in integrated process_file_route')
                return jsonify({'status': 'error', 'logs': [f"❌ An unexpected server error occurred: {str(e)}"]}), 500

        def download_wrapper(filename, *args, **kwargs):
            try:
                return integrated_module.download_file(filename)
            except Exception as e:
                current_app.logger.exception('Error in integrated download_file')
                return "", 500

        id_processor_bp.add_url_rule('/', endpoint='index', view_func=index_wrapper)
        id_processor_bp.add_url_rule('/process-file', endpoint='process_file_route', view_func=process_file_wrapper, methods=['POST'])
        id_processor_bp.add_url_rule('/download/<path:filename>', endpoint='download_file', view_func=download_wrapper)

        app.register_blueprint(id_processor_bp, url_prefix='/id-processor')
    else:
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

    def format_dates_in_response(records):
        """Helper to format date columns to DD-MMM-YYYY for responses."""
        for record in records:
            for col in date_columns:
                if col in record and (isinstance(record[col], (pd.Timestamp,)) or pd.notna(record[col])):
                    try:
                        dt = pd.to_datetime(record[col], errors='coerce')
                        if pd.notna(dt):
                            record[col] = dt.strftime('%d-%b-%Y')
                    except Exception:
                        pass
        return records

    @app.route('/search_employee', methods=['GET'])
    def search_employee():
        """API for fetching FULL details of a single employee using a fast index lookup."""
        employee_id = request.args.get('empid')
        if not employee_id:
            return jsonify({'error': 'Employee ID is required.'}), 400

        if df.empty:
            return jsonify({'message': 'Database not loaded.'}), 500

        try:
            # Try direct lookup; if not found, try with/without leading zero
            emp = str(employee_id).strip()
            candidates = [emp]
            if not emp.startswith('0'):
                candidates.append('0' + emp)
            else:
                # also try without leading zero
                candidates.append(emp.lstrip('0'))

            result_df = None
            for c in candidates:
                try:
                    result_df = df.loc[[c]].reset_index()
                    if not result_df.empty:
                        break
                except KeyError:
                    result_df = pd.DataFrame()

            if result_df is None or result_df.empty:
                return jsonify({'message': 'Employee not found.'}), 404

            records = result_df.to_dict('records')
            formatted_records = format_dates_in_response(records)
            return jsonify(formatted_records)
        except KeyError:
            return jsonify({'message': 'Employee not found.'}), 404

    @app.route("/health")
    def health():
    return "OK", 200


    @app.route('/filter_by_dob_summary', methods=['GET'])
    def filter_by_dob_summary():
        """API for fetching a compact SUMMARY of employees by DOB."""
        dob_str = request.args.get('dob')
        if not dob_str:
            return jsonify({'error': 'Date of Birth is required.'}), 400

        if df.empty:
            return jsonify({'message': 'Database not loaded.'}), 500

        try:
            search_date = pd.to_datetime(dob_str)
            result_df = df[df['DOB'] == search_date]
        except Exception:
            return jsonify({'error': 'Invalid date format.'}), 400

        if result_df.empty:
            return jsonify({'message': 'No employees found with this DOB.'}), 404

        # Convert the 'Employee ID' index back into a regular column
        summary_df = result_df.reset_index()
        # Select compact columns for the frontend summary
        cols = [c for c in ['Employee Name', 'Employee ID', 'Rehire', 'FFS'] if c in summary_df.columns]
        summary_df = summary_df[cols]
        records = summary_df.to_dict('records')
        return jsonify(records)

    from werkzeug.utils import secure_filename

    @app.route('/configure', methods=['GET', 'POST'])
    def configure_data():
        """Simple configure page: upload an Excel/CSV to replace the current dataset.
        Writes to `data/uploads/employee_data.parquet` and reloads `df` in-memory.
        """
        if request.method == 'GET':
            return '''
                <html><body>
                <h3>Upload Employee Data (Excel or CSV)</h3>
                <form method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".csv,.xlsx,.xls" />
                    <input type="submit" value="Upload" />
                </form>
                </body></html>
            '''

        # POST: handle file upload
        if 'file' not in request.files or request.files['file'].filename == '':
            return jsonify({'error': 'No file uploaded'}), 400

        f = request.files['file']
        filename = secure_filename(f.filename)
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext in ['.xls', '.xlsx']:
                df_new = pd.read_excel(f, engine='openpyxl')
            elif ext == '.csv':
                df_new = pd.read_csv(f)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            target_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data', 'uploads'))
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, 'employee_data.parquet')

            df_new.to_parquet(target_path, index=False)

            # reload global df so API uses new data
            try:
                global df
                df = pd.read_parquet(target_path)
                if 'Employee ID' in df.columns:
                    df.set_index('Employee ID', inplace=True)
                df.columns = df.columns.astype(str).str.strip()
                if 'FFS' in df.columns:
                    df['FFS'] = pd.to_numeric(df['FFS'], errors='coerce')
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.fillna('Not Available')
            except Exception:
                pass

            return jsonify({'success': True, 'message': f'File converted and saved to {target_path}'})
        except Exception as e:
            app.logger.exception('Configure failed')
            return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

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
