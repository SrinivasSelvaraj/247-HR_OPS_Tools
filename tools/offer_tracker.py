from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
from openpyxl import Workbook
from io import BytesIO

offer_tracker_bp = Blueprint(
    'offer_tracker', __name__,
    template_folder='templates',
    url_prefix='/offer-tracker'
)

offers_db = []

@offer_tracker_bp.route('/')
def index():
    return render_template('tools/offer_tracker.html')

@offer_tracker_bp.route('/add', methods=['POST'])
def add_offer():
    ic = request.form['candidate_ic']

    if any(o['candidate_ic'] == ic for o in offers_db):
        return jsonify(error='Duplicate IC No found'), 409

    offer = {
        'Sl No': len(offers_db) + 1,
        'candidate_ic': ic,
        'candidate_name': request.form['candidate_name'],
        'program': request.form['program'],
        'DOJ': request.form['DOJ'],
        'education': request.form['education'],
        'experience': request.form['experience'],
        'offered_salary': request.form['offered_salary'],
        'offer_date': datetime.now().date().isoformat(),
        'notes': request.form.get('notes', '')
    }

    offers_db.append(offer)
    return jsonify(success=True, offer=offer)

@offer_tracker_bp.route('/list')
def list_offers():
    return jsonify(success=True, offers=offers_db)

@offer_tracker_bp.route('/remove/<int:offer_id>', methods=['DELETE'])
def remove_offer(offer_id):
    global offers_db
    offers_db = [o for o in offers_db if o['id'] != offer_id]
    return jsonify(success=True)

@offer_tracker_bp.route('/export')
def export():
    wb = Workbook()
    ws = wb.active
    ws.title = "Offers"

    if not offers_db:
        ws.append(["No data"])
    else:
        headers = list(offers_db[0].keys())   # ✅ FIX
        ws.append(headers)

        for o in offers_db:
            ws.append([o.get(h, "") for h in headers])

    f = BytesIO()
    wb.save(f)
    f.seek(0)

    return send_file(
        f,
        as_attachment=True,
        download_name='offers.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )