"""
Employee ID Availability Checker Tool

This tool checks and manages employee ID availability.
Features:
- Real-time ID availability check
- ID pattern generation
- Reserved ID management
- Bulk ID allocation
- ID assignment history
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime
import re
import pandas as pd
import os
import zipfile
from io import BytesIO

id_checker_bp = Blueprint('id_checker', __name__,
                         template_folder='templates',
                         url_prefix='/id-checker')

# Mock database for used IDs
used_ids = {
    'EMP0001', 'EMP0002', 'EMP0003', 'EMP0005', 'EMP0010',
    'USER0001', 'USER0002', 'STF0001', 'STF0003'
}

# Reserved IDs
reserved_ids = {
    'EMP0000', 'USER0000', 'STF0000'
}

def generate_next_available_id(prefix='EMP', start=1):
    """Generate the next available ID with given prefix."""
    pattern = re.compile(f'^{prefix}(\\d+)$')

    # Find existing IDs with this prefix
    existing_numbers = []
    for used_id in used_ids:
        match = pattern.match(used_id)
        if match:
            existing_numbers.append(int(match.group(1)))

    if not existing_numbers:
        return f"{prefix}{start:04d}"

    # Find next available number
    max_number = max(existing_numbers)
    next_number = max(max_number + 1, start)

    while f"{prefix}{next_number:04d}" in used_ids:
        next_number += 1

    return f"{prefix}{next_number:04d}"

@id_checker_bp.route('/')
def index():
    """Main page for the Employee ID Availability Checker tool."""
    return render_template('tools/id_checker.html')

@id_checker_bp.route('/check', methods=['POST'])
def check_availability():
    """Check availability of specific IDs."""
    try:
        ids_to_check = request.form.getlist('ids')
        results = []

        for emp_id in ids_to_check:
            is_available = emp_id not in used_ids and emp_id not in reserved_ids
            status = 'available' if is_available else 'used' if emp_id in used_ids else 'reserved'

            results.append({
                'id': emp_id,
                'available': is_available,
                'status': status
            })

        return jsonify({
            'success': True,
            'results': results,
            'total_checked': len(results),
            'available_count': len([r for r in results if r['available']])
        })

    except Exception as e:
        return jsonify({'error': f'Check failed: {str(e)}'}), 500

@id_checker_bp.route('/generate', methods=['POST'])
def generate_ids():
    """Generate available IDs based on pattern."""
    try:
        prefix = request.form.get('prefix', 'EMP')
        count = int(request.form.get('count', 1))
        start_number = int(request.form.get('start_number', 1))

        generated_ids = []
        current_number = start_number

        for _ in range(count):
            while True:
                candidate_id = f"{prefix}{current_number:04d}"

                if candidate_id not in used_ids and candidate_id not in reserved_ids:
                    generated_ids.append(candidate_id)
                    current_number += 1
                    break
                else:
                    current_number += 1

                    # Safety check to prevent infinite loop
                    if current_number > start_number + 10000:
                        break

        return jsonify({
            'success': True,
            'generated_ids': generated_ids,
            'prefix': prefix,
            'count': len(generated_ids)
        })

    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

@id_checker_bp.route('/reserve', methods=['POST'])
def reserve_id():
    """Reserve an ID for future use."""
    try:
        emp_id = request.form.get('id')
        reason = request.form.get('reason', 'Manual reservation')
        reserved_by = request.form.get('reserved_by', 'User')

        if not emp_id:
            return jsonify({'error': 'ID is required'}), 400

        if emp_id in used_ids:
            return jsonify({'error': 'ID is already in use'}), 400

        if emp_id in reserved_ids:
            return jsonify({'error': 'ID is already reserved'}), 400

        reserved_ids.add(emp_id)

        return jsonify({
            'success': True,
            'id': emp_id,
            'message': f'ID {emp_id} reserved successfully'
        })

    except Exception as e:
        return jsonify({'error': f'Reservation failed: {str(e)}'}), 500

@id_checker_bp.route('/allocate', methods=['POST'])
def allocate_id():
    """Allocate an ID to an employee."""
    try:
        emp_id = request.form.get('id')
        employee_name = request.form.get('employee_name')
        department = request.form.get('department')
        allocated_by = request.form.get('allocated_by', 'User')

        if not emp_id:
            return jsonify({'error': 'ID is required'}), 400

        if emp_id in used_ids:
            return jsonify({'error': 'ID is already allocated'}), 400

        if emp_id in reserved_ids:
            reserved_ids.remove(emp_id)

        used_ids.add(emp_id)

        return jsonify({
            'success': True,
            'allocation': {
                'id': emp_id,
                'employee_name': employee_name,
                'department': department,
                'allocated_by': allocated_by,
                'allocated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': f'ID {emp_id} allocated successfully'
        })

    except Exception as e:
        return jsonify({'error': f'Allocation failed: {str(e)}'}), 500

@id_checker_bp.route('/stats')
def get_statistics():
    """Get ID allocation statistics."""
    try:
        stats = {
            'total_used': len(used_ids),
            'total_reserved': len(reserved_ids),
            'by_prefix': {}
        }

        # Count by prefix
        prefixes = ['EMP', 'USER', 'STF']
        for prefix in prefixes:
            pattern = re.compile(f'^{prefix}(\\d+)$')
            count = len([id for id in used_ids if pattern.match(id)])
            stats['by_prefix'][prefix] = count

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': f'Stats failed: {str(e)}'}), 500


def _safe_str(v):
    if pd.isna(v):
        return ''
    return str(v).strip()


@id_checker_bp.route('/analyze', methods=['POST'])
def analyze_file():
    """Analyze uploaded Excel file or server path and return next available IDs per location."""
    try:
        # accept uploaded file
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = (file.filename or '').lower()
            # read into bytes buffer for possible zip handling
            buf = BytesIO(file.read())
            buf.seek(0)
            # handle zip containing xlsx
            if zipfile.is_zipfile(buf) or filename.endswith('.zip'):
                z = zipfile.ZipFile(buf)
                # find first xlsx/xls file
                target_name = None
                for name in z.namelist():
                    if name.lower().endswith('.xlsx') or name.lower().endswith('.xls'):
                        target_name = name
                        break
                if not target_name:
                    return jsonify({'success': False, 'error': 'No Excel file found in ZIP'}), 400
                with z.open(target_name) as f:
                    data = f.read()
                    df = pd.read_excel(BytesIO(data), header=None, skiprows=3, engine='openpyxl')
            else:
                buf.seek(0)
                df = pd.read_excel(buf, header=None, skiprows=3, engine='openpyxl')
        else:
            server_path = request.form.get('server_path')
            if not server_path or not os.path.exists(server_path):
                return jsonify({'success': False, 'error': 'No file uploaded and server_path missing or not found'}), 400
            df = pd.read_excel(server_path, header=None, skiprows=3, engine='openpyxl')

        # ensure sufficient columns (we expect at least up to column S)
        if df.shape[1] <= 18:
            df = df.reindex(columns=range(19))

        emp_col = 0
        loc_col = 18
        doj_col = 5

        # group Bangalore + Shillong together in results (both use prefix 010)
        GROUPS = {
            'bangalore_shillong': '010',
            'hyderabad': '030'
        }

        # initialize results for groups
        results = {k: {'prefix': GROUPS[k], 'max_found': None, 'found_count': 0, 'next_id': None, 'last_doj': None} for k in GROUPS}

        for _, row in df.iterrows():
            empv = _safe_str(row[emp_col])
            locv = _safe_str(row[loc_col]).lower()
            if not empv or not locv:
                continue

            # map location text to a group
            if 'bangalore' in locv or 'blr' in locv or 'bengaluru' in locv or 'shillong' in locv:
                group_key = 'bangalore_shillong'
            elif 'hyderabad' in locv or 'hyd' in locv:
                group_key = 'hyderabad'
            else:
                continue

            prefix = GROUPS[group_key]
            digits = ''.join(ch for ch in empv if ch.isdigit())
            if not digits:
                continue

            # try to parse numeric portion and track max
            if digits.startswith(prefix):
                suffix = digits[len(prefix):]
                try:
                    val = int(suffix) if suffix != '' else 0
                except Exception:
                    continue
                rec = results[group_key]
                rec['found_count'] += 1
                if rec['max_found'] is None or val > rec['max_found']:
                    rec['max_found'] = val

            # capture DOJ from column F (doj_col)
            try:
                raw = row[doj_col]
                dt = pd.to_datetime(raw, errors='coerce')
                if not pd.isna(dt):
                    # keep the most recent DOJ per group
                    if rec.get('last_doj') is None or dt > rec.get('last_doj'):
                        rec['last_doj'] = dt
            except Exception:
                pass

        # compute next ids with padding and last_id full string
        for k, rec in results.items():
            if rec['max_found'] is None:
                next_val = 1
                suffix_len = 6
                rec['last_id'] = None
            else:
                next_val = rec['max_found'] + 1
                suffix_len = max(len(str(rec['max_found'])), 6)
                rec['last_id'] = rec['prefix'] + str(rec['max_found']).zfill(suffix_len)
            rec['next_id'] = rec['prefix'] + str(next_val).zfill(suffix_len)

        # prepare clean results, include last_doj as ISO date string if available
        clean_results = {}
        for k, rec in results.items():
            last_doj = None
            if rec.get('last_doj') is not None:
                try:
                    last_doj = rec['last_doj'].strftime('%Y-%m-%d')
                except Exception:
                    last_doj = str(rec['last_doj'])
            clean_results[k] = {
                'last_id': rec.get('last_id'),
                'next_id': rec.get('next_id'),
                'last_doj': last_doj
            }

        return jsonify({'success': True, 'results': clean_results})

    except Exception as e:
        current_app.logger.exception('Error analyzing file')
        return jsonify({'success': False, 'error': str(e)}), 500