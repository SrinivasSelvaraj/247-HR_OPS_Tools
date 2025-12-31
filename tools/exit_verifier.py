"""
Employee Exit Verifier Tool
REPLICATED from old working project
"""

from flask import Blueprint, render_template, request, jsonify, current_app, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

exit_verifier_bp = Blueprint(
    'exit_verifier',
    __name__,
    template_folder='templates',
    url_prefix='/exit-verifier'
)

DATA_DF = None
DATE_COLUMNS = ['DOJ', 'Last Working Date', 'DOB']


# -------------------- LOAD DATA (OLD PROJECT STYLE) --------------------
def load_data():
    global DATA_DF
    if DATA_DF is not None:
        return DATA_DF

    base = os.path.join(current_app.root_path, 'data', 'uploads')
    parquet = os.path.join(base, 'employee_data.parquet')
    csv = os.path.join(base, 'employee_data.csv')

    if os.path.exists(parquet):
        df = pd.read_parquet(parquet)
    elif os.path.exists(csv):
        # 🔴 CRITICAL FIX: force Employee ID as STRING
        df = pd.read_csv(csv, dtype={'Employee ID': str})
    else:
        DATA_DF = pd.DataFrame()
        return DATA_DF

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    if 'Employee ID' not in df.columns:
        DATA_DF = pd.DataFrame()
        return DATA_DF

    # 🔴 CRITICAL FIX: ensure string + preserve leading zero
    df['Employee ID'] = df['Employee ID'].astype(str).str.strip()

    # EXACTLY like old project
    df.set_index('Employee ID', inplace=True)

    # Parse dates
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df.fillna('Not Available')

    DATA_DF = df
    return DATA_DF
def append_and_save_data(new_df):
    base = os.path.join(current_app.root_path, 'data', 'uploads')
    parquet = os.path.join(base, 'employee_data.parquet')
    csv = os.path.join(base, 'employee_data.csv')

    # Load existing
    if os.path.exists(parquet):
        existing_df = pd.read_parquet(parquet)
    elif os.path.exists(csv):
        existing_df = pd.read_csv(csv)
    else:
        existing_df = pd.DataFrame()

    # Normalize columns
    existing_df.columns = existing_df.columns.astype(str).str.strip()
    new_df.columns = new_df.columns.astype(str).str.strip()

    # Ensure Employee ID exists
    if 'Employee ID' not in new_df.columns:
        raise ValueError('Employee ID column missing')

    # Normalize Employee ID as STRING (DO NOT STRIP 0)
    new_df['Employee ID'] = new_df['Employee ID'].astype(str).str.strip()
    if not existing_df.empty:
        existing_df['Employee ID'] = existing_df['Employee ID'].astype(str).str.strip()

    # Remove duplicates (Employee ID based)
    if not existing_df.empty:
        new_df = new_df[~new_df['Employee ID'].isin(existing_df['Employee ID'])]

    # Append
    final_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Save
    try:
        final_df.to_parquet(parquet, index=False)
        return 'parquet'
    except Exception:
        final_df.to_csv(csv, index=False)
        return 'csv'


# -------------------- ROUTES --------------------

@exit_verifier_bp.route('/')
def index():
    return render_template('tools/exit_verifier.html')


@exit_verifier_bp.route('/verify', methods=['POST'])
def verify_exit():
    raw_id = request.form.get('employee_id', '').strip()

    if not raw_id:
        return jsonify({'error': 'Employee ID is required'}), 400

    df = load_data()
    if df.empty:
        return jsonify({'error': 'Employee database not loaded'}), 500

    # 🔑 SEARCH KEYS (do NOT mutate data)
    search_ids = {raw_id}
    if raw_id.startswith('0'):
        search_ids.add(raw_id.lstrip('0'))

    found_id = None
    for sid in search_ids:
        if sid in df.index:
            found_id = sid
            break

    if not found_id:
        return jsonify({'message': 'EMP ID is not active or not found'}), 404

    record = df.loc[found_id].to_dict()
    record['Employee ID'] = found_id  # display real ID only

    for col in DATE_COLUMNS:
        if col in record and isinstance(record[col], pd.Timestamp):
            record[col] = record[col].strftime('%d-%b-%Y')

    return jsonify({'success': True, 'data': record})



@exit_verifier_bp.route('/filter_by_dob_summary', methods=['GET'])
def filter_by_dob_summary():
    dob = request.args.get('dob')
    if not dob:
        return jsonify({'error': 'Date of Birth is required'}), 400

    df = load_data()
    if df.empty:
        return jsonify({'error': 'Employee database not loaded'}), 500

    try:
        search_date = pd.to_datetime(dob)
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    if 'DOB' not in df.columns:
        return jsonify({'error': 'DOB column not found'}), 500

    result_df = df[df['DOB'] == search_date]

    if result_df.empty:
        return jsonify({'message': 'No employees found with this DOB'}), 404

    # 🔴 EXACT OLD PROJECT FIX
    summary_df = result_df.reset_index()[['Employee Name', 'Employee ID', 'Rehire', 'FFS']]
    return jsonify({'success': True, 'data': summary_df.to_dict('records')})


@exit_verifier_bp.route('/configure', methods=['POST'])
def configure_data():
    global DATA_DF
    DATA_DF = None  # force reload

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    f = request.files['file']
    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.xls', '.xlsx', '.csv']:
        return jsonify({'error': 'Unsupported file type'}), 400

    try:
        new_df = pd.read_excel(f) if ext != '.csv' else pd.read_csv(f)
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 400

    try:
        saved_type = append_and_save_data(new_df)
        return jsonify({
            'success': True,
            'message': f'Data appended successfully and saved as {saved_type.upper()}.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@exit_verifier_bp.route('/download-template', methods=['GET'])
def download_template():
    sample_data = pd.DataFrame([
        {
            'Employee ID': '010123456',
            'Employee Name': 'Sample Name',
            'DOJ': '2023-01-15',
            'Last Working Date': '2024-12-31',
            'DOB': '2000-05-20',
            'Designation': 'Executive',
            'Department': 'Operations',
            'Location': 'Bangalore',
            'Exit Type': 'Resignation',
            'Rehire': 'Yes',
            'FFS': 0,
            'Level': 'Contract',
            'Grade': 'G3'
        }
    ])

    output = os.path.join(current_app.root_path, 'data', 'uploads', 'employee_upload_template.xlsx')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    sample_data.to_excel(output, index=False)

    return send_file(
        output,
        as_attachment=True,
        download_name='employee_upload_template.xlsx'
    )
@exit_verifier_bp.route('/reset-data', methods=['POST'])
def reset_data():
    base = os.path.join(current_app.root_path, 'data', 'uploads')
    parquet = os.path.join(base, 'employee_data.parquet')
    csv = os.path.join(base, 'employee_data.csv')

    try:
        if os.path.exists(parquet):
            os.remove(parquet)
        if os.path.exists(csv):
            os.remove(csv)

        global DATA_DF
        DATA_DF = None  # reset in-memory data

        return jsonify({'success': True, 'message': 'Employee data has been reset.'})
    except Exception as e:
        return jsonify({'error': f'Failed to reset data: {str(e)}'}), 500