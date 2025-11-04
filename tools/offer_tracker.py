"""
Offer Release Tracker Tool

This tool tracks offer releases and candidate communication.
Features:
- Offer logging with timestamps
- Status tracking (pending, accepted, rejected)
- Candidate communication logs
- Generate offer reports
- Email notification integration
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json

offer_tracker_bp = Blueprint('offer_tracker', __name__,
                           template_folder='templates',
                           url_prefix='/offer-tracker')

# Mock database for offers
offers_db = []

@offer_tracker_bp.route('/')
def index():
    """Main page for the Offer Release Tracker tool."""
    return render_template('tools/offer_tracker.html')

@offer_tracker_bp.route('/add', methods=['POST'])
def add_offer():
    """Add a new offer to the tracker."""
    try:
        offer_data = {
            'id': len(offers_db) + 1,
            'candidate_name': request.form.get('candidate_name'),
            'position': request.form.get('position'),
            'department': request.form.get('department'),
            'offered_salary': request.form.get('offered_salary'),
            'offer_date': request.form.get('offer_date'),
            'recruiter': request.form.get('recruiter'),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'notes': request.form.get('notes', ''),
            'communications': []
        }

        offers_db.append(offer_data)

        return jsonify({
            'success': True,
            'offer': offer_data,
            'message': 'Offer added successfully'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to add offer: {str(e)}'}), 500

@offer_tracker_bp.route('/list')
def list_offers():
    """List all offers with optional filtering."""
    try:
        status_filter = request.args.get('status')
        department_filter = request.args.get('department')

        filtered_offers = offers_db

        if status_filter:
            filtered_offers = [o for o in filtered_offers if o['status'] == status_filter]

        if department_filter:
            filtered_offers = [o for o in filtered_offers if o['department'] == department_filter]

        return jsonify({
            'success': True,
            'offers': filtered_offers,
            'total': len(filtered_offers)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to list offers: {str(e)}'}), 500

@offer_tracker_bp.route('/update-status/<int:offer_id>', methods=['POST'])
def update_offer_status(offer_id):
    """Update the status of an offer."""
    try:
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')

        if new_status not in ['pending', 'accepted', 'rejected', 'withdrawn']:
            return jsonify({'error': 'Invalid status'}), 400

        # Find and update offer
        offer = next((o for o in offers_db if o['id'] == offer_id), None)
        if not offer:
            return jsonify({'error': 'Offer not found'}), 404

        old_status = offer['status']
        offer['status'] = new_status
        offer['updated_at'] = datetime.now().isoformat()

        # Add status change to communications
        if old_status != new_status:
            offer['communications'].append({
                'type': 'status_change',
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes,
                'timestamp': datetime.now().isoformat()
            })

        return jsonify({
            'success': True,
            'offer': offer,
            'message': f'Offer status updated to {new_status}'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to update status: {str(e)}'}), 500

@offer_tracker_bp.route('/add-communication/<int:offer_id>', methods=['POST'])
def add_communication(offer_id):
    """Add a communication log for an offer."""
    try:
        comm_type = request.form.get('type')
        notes = request.form.get('notes')
        contact_method = request.form.get('contact_method', 'phone')

        offer = next((o for o in offers_db if o['id'] == offer_id), None)
        if not offer:
            return jsonify({'error': 'Offer not found'}), 404

        communication = {
            'type': comm_type,
            'contact_method': contact_method,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }

        offer['communications'].append(communication)

        return jsonify({
            'success': True,
            'communication': communication,
            'message': 'Communication logged successfully'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to add communication: {str(e)}'}), 500

@offer_tracker_bp.route('/dashboard')
def dashboard():
    """Get dashboard statistics."""
    try:
        stats = {
            'total_offers': len(offers_db),
            'pending': len([o for o in offers_db if o['status'] == 'pending']),
            'accepted': len([o for o in offers_db if o['status'] == 'accepted']),
            'rejected': len([o for o in offers_db if o['status'] == 'rejected']),
            'withdrawn': len([o for o in offers_db if o['status'] == 'withdrawn']),
            'this_month': len([o for o in offers_db
                             if datetime.fromisoformat(o['created_at']).month == datetime.now().month])
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard: {str(e)}'}), 500