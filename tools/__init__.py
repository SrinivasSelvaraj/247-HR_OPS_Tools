"""
HR Operations Tools Package

This package contains all the tool blueprints for the HR Operations Toolkit.
Each tool is implemented as a Flask blueprint with its own routes, templates, and logic.
"""

from flask import Blueprint

# Tool metadata for registration
TOOLS_METADATA = {
    'id_processor': {
        'name': 'ID Image Processor',
        'description': 'Crop candidate Images for ID cards or HRMS either single or bulk.',
        'icon': 'fa-solid fa-id-card',
        'category': 'document',
        'url_prefix': '/id-processor'
    },
    'pdf_toolkit': {
        'name': 'Complete PDF Toolkit',
        'description': 'A complete offline PDF toolkit for all your PDF needs.',
        'icon': 'fa-solid fa-file-pdf',
        'category': 'document',
        'url_prefix': '/pdf-toolkit'
    },
    'exit_verifier': {
        'name': 'Employee Exit Verifier',
        'description': 'Instantaneous check candidates exit status and FFS details.',
        'icon': 'fa-solid fa-person-walking-arrow-right',
        'category': 'employee',
        'url_prefix': '/exit-verifier'
    },
    'exp_calculator': {
        'name': 'Candidate Experience Calculator',
        'description': 'Analyze the candidate work experience of previous companies.',
        'icon': 'fa-solid fa-calculator',
        'category': 'analytics',
        'url_prefix': '/exp-calculator'
    },
    'offer_tracker': {
        'name': 'Offer Release Tracker',
        'description': 'User friendly Tracker for logging offer releases.',
        'icon': 'fa-solid fa-clipboard-check',
        'category': 'employee',
        'url_prefix': '/offer-tracker'
    },
    'id_checker': {
        'name': 'Employee ID Availability',
        'description': 'Check EMP ID availability for EMP ID allocation.',
        'icon': 'fa-solid fa-magnifying-glass-plus',
        'category': 'employee',
        'url_prefix': '/id-checker'
    }
}

def get_tool_metadata(tool_name):
    """Get metadata for a specific tool."""
    return TOOLS_METADATA.get(tool_name, {})

def get_all_tools():
    """Get metadata for all tools."""
    return TOOLS_METADATA

def get_tools_by_category(category):
    """Get tools filtered by category."""
    return {k: v for k, v in TOOLS_METADATA.items() if v.get('category') == category}