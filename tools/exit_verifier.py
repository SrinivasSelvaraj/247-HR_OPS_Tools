"""
Employee Exit Verifier Tool

This tool verifies employee exit status and FFS details.
Features:
- Integration with HR database
- Exit status lookup
- FFS (Full and Final Settlement) details
- Generate exit reports
- Bulk verification for multiple employees
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime

exit_verifier_bp = Blueprint('exit_verifier', __name__,
                            template_folder='templates',
                            url_prefix='/exit-verifier')

@exit_verifier_bp.route('/')
def index():
    """Main page for the Employee Exit Verifier tool."""
    return render_template('tools/exit_verifier.html')

@exit_verifier_bp.route('/verify', methods=['POST'])
def verify_exit():
    """Verify employee exit status."""
    try:
        employee_id = request.form.get('employee_id')
        email = request.form.get('email')

        if not employee_id and not email:
            return jsonify({'error': 'Please provide employee ID or email'}), 400

        # Mock data for demonstration
        mock_data = {
            'found': True,
            'employee_id': employee_id or 'EMP1234',
            'name': 'John Doe',
            'email': email or 'john.doe@247-inc.com',
            'exit_date': '2024-10-15',
            'exit_status': 'Completed',
            'ffs_status': 'Processed',
            'ffs_amount': '₹45,678.00',
            'final_settlement_date': '2024-10-20',
            'notice_period_served': 'Yes',
            'clearances': {
                'it_clearance': 'Completed',
                'finance_clearance': 'Completed',
                'hr_clearance': 'Completed',
                'assets_returned': 'Yes'
            }
        }

        return jsonify({'success': True, 'data': mock_data})

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500

@exit_verifier_bp.route('/bulk-verify', methods=['POST'])
def bulk_verify():
    """Bulk verify multiple employees."""
    try:
        employee_ids = request.form.getlist('employee_ids')

        if not employee_ids:
            return jsonify({'error': 'No employee IDs provided'}), 400

        results = []
        for emp_id in employee_ids:
            # Mock verification for each employee
            mock_result = {
                'employee_id': emp_id,
                'status': 'Found',
                'exit_status': 'Completed',
                'ffs_status': 'Processed'
            }
            results.append(mock_result)

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })

    except Exception as e:
        return jsonify({'error': f'Bulk verification failed: {str(e)}'}), 500