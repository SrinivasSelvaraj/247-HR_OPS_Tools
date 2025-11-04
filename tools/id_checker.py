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

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import re

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