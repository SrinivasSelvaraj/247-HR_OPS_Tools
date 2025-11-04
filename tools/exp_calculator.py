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

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date
import re

exp_calculator_bp = Blueprint('exp_calculator', __name__,
                            template_folder='templates',
                            url_prefix='/exp-calculator')

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

        if not experiences:
            return jsonify({'error': 'No experience data provided'}), 400

        # Calculate total experience
        total_exp = calculate_total_experience(experiences)

        # Detect gaps
        gaps = detect_gaps(experiences)

        # Calculate statistics
        stats = {
            'total_companies': len(experiences),
            'total_experience': total_exp,
            'gaps': gaps,
            'average_tenure': round(total_exp['total_months'] / len(experiences), 1),
            'has_gaps': len(gaps) > 0
        }

        return jsonify({
            'success': True,
            'stats': stats,
            'experiences': experiences
        })

    except Exception as e:
        return jsonify({'error': f'Calculation failed: {str(e)}'}), 500

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