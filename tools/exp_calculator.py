"""
Candidate Experience Calculator Tool

This tool analyzes candidate work experience.
Features:
- Work experience gap analysis
- Total experience calculation
- Experience certificate parsing
- Generate experience reports
- Compare with job requirements
"""

from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime, date
import re
import os
import csv
import json
from io import BytesIO
import calendar

exp_calculator_bp = Blueprint('exp_calculator', __name__,
                            template_folder='templates',
                            url_prefix='/exp-calculator')

# Ensure logs directory exists for export
LOGS_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_CSV_PATH = os.path.join(LOGS_DIR, 'exp_calculator.csv')

# Allowed date range for inputs
MIN_DATE = date(1947, 1, 1)
MAX_DATE = date(2099, 12, 31)

def _append_log_row(total_exp, stats, experiences):
    try:
        fieldnames = ['timestamp', 'years', 'months', 'total_months', 'total_companies', 'gaps_count', 'experiences']
        write_header = not os.path.exists(LOG_CSV_PATH)
        with open(LOG_CSV_PATH, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'years': total_exp.get('years', 0),
                'months': total_exp.get('months', 0),
                'total_months': total_exp.get('total_months', 0),
                'total_companies': stats.get('total_companies', 0),
                'gaps_count': len(stats.get('gaps', [])),
                'experiences': json.dumps(experiences, ensure_ascii=False)
            })
    except Exception:
        pass

def calculate_total_experience(experiences):
    """Calculate total experience from a list of work experiences."""
    total_days = 0
    total_months = 0
    total_years = 0

    for exp in experiences:
        start_date = datetime.strptime(exp['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(exp['end_date'], '%Y-%m-%d').date() if exp['end_date'] else date.today()

        # Calculate difference
        years = end_date.year - start_date.year
        months = end_date.month - start_date.month
        days = end_date.day - start_date.day

        if days < 0:
            months -= 1
            days += 30
        if months < 0:
            years -= 1
            months += 12

        total_years += years
        total_months += months
        total_days += days

    # Normalize months to years
    if total_months >= 12:
        total_years += total_months // 12
        total_months = total_months % 12

    return {
        'years': total_years,
        'months': total_months,
        'days': total_days,
        'total_months': (total_years * 12) + total_months
    }


def _datedif_m(start, end):
    """Calculate complete months between two dates (like Excel DATEDIF with 'M')"""
    if end < start:
        return 0
    months = 0
    current = start
    while True:
        # Try to add a month
        if current.month == 12:
            next_month_date = date(current.year + 1, 1, min(current.day, 31))
        else:
            days_in_next = calendar.monthrange(current.year, current.month + 1)[1]
            next_month_date = date(current.year, current.month + 1, min(current.day, days_in_next))
        
        if next_month_date > end:
            break
        months += 1
        current = next_month_date
    
    return months

def _datedif_md(start, end, complete_months):
    """Calculate remaining days after complete months (like Excel DATEDIF with 'MD')"""
    temp = start
    for _ in range(complete_months):
        if temp.month == 12:
            temp = date(temp.year + 1, 1, min(temp.day, 31))
        else:
            days_in_next = calendar.monthrange(temp.year, temp.month + 1)[1]
            temp = date(temp.year, temp.month + 1, min(temp.day, days_in_next))
    
    return (end - temp).days
    start = datetime.strptime(start_date_s, '%Y-%m-%d').date()
    end = datetime.strptime(end_date_s, '%Y-%m-%d').date() if end_date_s else date.today()
    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day
    if days < 0:
        months -= 1
        # get days in the previous month of start
        prev_month = start.month - 1 if start.month > 1 else 12
        prev_year = start.year if start.month > 1 else start.year - 1
        days_in_prev = calendar.monthrange(prev_year, prev_month)[1]
        days += days_in_prev
    if months < 0:
        years -= 1
        months += 12
    total_months = years * 12 + months
    return {
        'years': years,
        'months': months,
        'days': days,
        'total_months': total_months,
        'start_date': start,
        'end_date': end
    }

def detect_gaps(experiences):
    """Detect gaps between work experiences."""
    gaps = []
    sorted_exps = sorted(experiences, key=lambda x: x['start_date'])

    for i in range(len(sorted_exps) - 1):
        current_end = datetime.strptime(sorted_exps[i]['end_date'], '%Y-%m-%d').date()
        next_start = datetime.strptime(sorted_exps[i + 1]['start_date'], '%Y-%m-%d').date()

        gap_days = (next_start - current_end).days
        if gap_days > 30:  # Gap of more than 30 days
            gaps.append({
                'from_date': current_end.strftime('%Y-%m-%d'),
                'to_date': next_start.strftime('%Y-%m-%d'),
                'duration_days': gap_days,
                'duration_months': round(gap_days / 30, 1)
            })

    return gaps

@exp_calculator_bp.route('/')
def index():
    """Main page for the Candidate Experience Calculator tool."""
    return render_template('tools/exp_calculator.html')

@exp_calculator_bp.route('/calculate', methods=['POST'])
def calculate_experience():
    """Calculate candidate's total work experience."""
    try:
        experiences = []
        exp_data = request.form.getlist('experiences[]')

        for exp in exp_data:
            if exp:
                exp_dict = dict(pair.split('=') for pair in exp.split(';'))
                experiences.append(exp_dict)

        # Validate dates: start_date <= end_date when end_date provided
        for idx, exp in enumerate(experiences):
            try:
                s = datetime.strptime(exp.get('start_date', ''), '%Y-%m-%d').date()
            except Exception:
                return jsonify({'error': f'Invalid start date format for row {idx+1}'}), 400
            if s < MIN_DATE or s > MAX_DATE:
                return jsonify({'error': f'Start date out of allowed range for row {idx+1} (1947-01-01 to 2099-12-31)'}), 400
            end_s = exp.get('end_date', '')
            if end_s:
                try:
                    e = datetime.strptime(end_s, '%Y-%m-%d').date()
                except Exception:
                    return jsonify({'error': f'Invalid end date format for row {idx+1}'}), 400
                if e < MIN_DATE or e > MAX_DATE:
                    return jsonify({'error': f'End date out of allowed range for row {idx+1} (1947-01-01 to 2099-12-31)'}), 400
                if s > e:
                    return jsonify({'error': f'DOJ/start date is after relieving date for company "{exp.get("company","row %d" % (idx+1))}"'}), 400

        if not experiences:
            return jsonify({'error': 'No experience data provided'}), 400

        # Calculate total experience
        total_exp = calculate_total_experience(experiences)

        # Detect gaps
        gaps = detect_gaps(experiences)

        # Per-experience durations using DATEDIF logic (no rounding to months/days)
        per_experience = []
        parsed_exps = []
        for exp in experiences:
            start = datetime.strptime(exp['start_date'], '%Y-%m-%d').date()
            end_s = exp.get('end_date', '')
            end = datetime.strptime(end_s, '%Y-%m-%d').date() if end_s else date.today()
            
            # Use DATEDIF logic
            months = _datedif_m(start, end)
            days = _datedif_md(start, end, months)
            
            # Average: if days >= 15, add 1 month; else keep months as is
            avg_months = months + (1 if days >= 15 else 0)
            
            per_experience.append({
                'company': exp.get('company', ''),
                'start_date': exp['start_date'],
                'end_date': exp.get('end_date', '') or '',
                'months': months,
                'days': days,
                'average': avg_months
            })
            parsed_exps.append({'company': exp.get('company', ''), 'start': start, 'end': end})

        # Detect overlapping periods (dual employment)
        overlaps = []
        parsed_sorted = sorted(parsed_exps, key=lambda x: x['start'])
        for i in range(len(parsed_sorted)):
            for j in range(i + 1, len(parsed_sorted)):
                a = parsed_sorted[i]
                b = parsed_sorted[j]
                # overlap if a.start <= b.end and b.start <= a.end
                if a['start'] <= b['end'] and b['start'] <= a['end']:
                    overlap_start = max(a['start'], b['start'])
                    overlap_end = min(a['end'], b['end'])
                    overlap_days = (overlap_end - overlap_start).days
                    if overlap_days > 0:
                        overlaps.append({
                            'company_a': a['company'],
                            'company_b': b['company'],
                            'from': overlap_start.strftime('%Y-%m-%d'),
                            'to': overlap_end.strftime('%Y-%m-%d'),
                            'days': overlap_days,
                            'months': round(overlap_days / 30, 1)
                        })

        # Earliest DOJ (first company join date)
        earliest_start = min([p['start'] for p in parsed_exps]) if parsed_exps else None
        date_18 = None
        underage = False
        underage_exps = []
        if earliest_start:
            try:
                date_18 = date(earliest_start.year - 18, earliest_start.month, earliest_start.day)
            except Exception:
                # handle leap-day
                try:
                    date_18 = date(earliest_start.year - 18, earliest_start.month, 28)
                except Exception:
                    date_18 = date(earliest_start.year - 18, 1, 1)
            # check for experiences that started before the candidate turned 18
            for p in parsed_exps:
                if p['start'] < date_18:
                    underage = True
                    underage_exps.append({'company': p['company'], 'start': p['start'].strftime('%Y-%m-%d')})

        # Calculate statistics
        stats = {
            'total_companies': len(experiences),
            'total_experience': total_exp,
            'gaps': gaps,
            'average_tenure': round(total_exp['total_months'] / len(experiences), 1),
            'has_gaps': len(gaps) > 0,
            'per_experience': per_experience,
            'overlaps': overlaps,
            'earliest_start': earliest_start.strftime('%Y-%m-%d') if earliest_start else None,
            'date_18': date_18.strftime('%d-%m-%Y') if date_18 else None,
            'underage': underage,
            'underage_experiences': underage_exps
        }

        # append to CSV log for export
        try:
            _append_log_row(total_exp, stats, experiences)
        except Exception:
            pass

        return jsonify({
            'success': True,
            'stats': stats,
            'experiences': experiences
        })

    except Exception as e:
        return jsonify({'error': f'Calculation failed: {str(e)}'}), 500


@exp_calculator_bp.route('/export-log', methods=['GET'])
def export_log():
    if not os.path.exists(LOG_CSV_PATH):
        return jsonify({'error': 'No log data available'}), 404
    return send_file(LOG_CSV_PATH, as_attachment=True, download_name='exp_calculator_log.csv')


@exp_calculator_bp.route('/fetch-salary', methods=['POST'])
def fetch_salary():
    """Fetch salary based on provided brackets and candidate experience (months).

    Brackets format example: "0-12:20000,13-36:30000,37-999:50000"
    """
    try:
        program = request.form.get('program', '').strip()
        total_months = int(request.form.get('total_months', '0') or 0)
        brackets = request.form.get('brackets', '').strip()
        if not brackets:
            return jsonify({'error': 'No salary brackets provided'}), 400
        for part in brackets.split(','):
            part = part.strip()
            if not part:
                continue
            if ':' not in part:
                continue
            range_part, value_part = part.split(':', 1)
            try:
                value = float(value_part)
            except Exception:
                continue
            if '-' in range_part:
                start_s, end_s = range_part.split('-', 1)
                start = int(start_s)
                end = int(end_s)
                if start <= total_months <= end:
                    return jsonify({'program': program, 'salary': value})
        return jsonify({'error': 'No matching bracket found'}), 404
    except Exception as e:
        return jsonify({'error': 'Invalid input', 'detail': str(e)}), 400

@exp_calculator_bp.route('/compare', methods=['POST'])
def compare_with_requirements():
    """Compare experience with job requirements."""
    try:
        total_months = int(request.form.get('total_months', 0))
        required_months = int(request.form.get('required_months', 0))

        meets_requirements = total_months >= required_months
        difference = total_months - required_months

        result = {
            'meets_requirements': meets_requirements,
            'total_experience_months': total_months,
            'required_months': required_months,
            'difference_months': difference,
            'status': 'Qualified' if meets_requirements else 'Not Qualified'
        }

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500
    