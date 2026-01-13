"""Seed data routes for demo data management."""
from flask import Blueprint, jsonify

from app.services.seed_data import seed_demo_data, get_demo_credentials, seed_data_service


seed_bp = Blueprint('seed', __name__)


@seed_bp.route('/seed', methods=['POST'])
def seed_data():
    """
    Seed demo data into the application.
    
    Creates example user accounts, sample lesson content, and quiz examples.
    
    Returns:
        JSON response with seeding results.
    """
    result = seed_demo_data()
    return jsonify(result), 200 if result.get("status") == "success" else 200


@seed_bp.route('/seed/status', methods=['GET'])
def seed_status():
    """
    Check if demo data has been seeded.
    
    Returns:
        JSON response with seeding status.
    """
    return jsonify({
        "seeded": seed_data_service.is_seeded()
    }), 200


@seed_bp.route('/seed/credentials', methods=['GET'])
def demo_credentials():
    """
    Get demo user credentials for display on login page.
    
    Returns:
        JSON response with demo credentials.
    """
    credentials = get_demo_credentials()
    return jsonify({
        "credentials": credentials
    }), 200
