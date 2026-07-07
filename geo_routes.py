"""
routes/geo_routes.py  (NEW FILE)
=================================
REST endpoints for dynamic location & ward data.

Endpoints:
  POST /geo/detect-city       – coords → city name
  GET  /geo/wards/<city>      – city name → ward list
  GET  /geo/coverage          – coords → coverage status
  GET  /geo/cities            – list all supported cities
  POST /geo/set-city          – manually set city in session
"""

from flask import Blueprint, request, jsonify, session
from utils.geo_utils import (
    detect_city_from_coords,
    detect_city_from_ip,
    get_ward_data,
    check_coverage,
    get_supported_cities,
)

geo_bp = Blueprint('geo', __name__)


@geo_bp.route('/detect-city', methods=['POST'])
def detect_city():
    """
    Body: { "latitude": 15.85, "longitude": 74.50 }
    Returns city info and saves to session.
    """
    data = request.get_json(silent=True) or {}
    lat = data.get('latitude')
    lon = data.get('longitude')

    if lat is None or lon is None:
        # Fallback to IP-based detection
        result = detect_city_from_ip()
    else:
        result = detect_city_from_coords(float(lat), float(lon))

    if result.get('found'):
        session['detected_city'] = result['city']
        session['detected_state'] = result.get('state', '')

    return jsonify(result)


@geo_bp.route('/wards/<city_name>', methods=['GET'])
def get_wards(city_name):
    """
    GET /geo/wards/belagavi
    Returns ward list for any city.
    """
    result = get_ward_data(city_name)
    return jsonify(result), (200 if result['found'] else 404)


@geo_bp.route('/coverage', methods=['GET'])
def coverage_check():
    """
    GET /geo/coverage?lat=15.85&lon=74.50
    Returns whether the location is covered and ward count.
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)

    if lat is None or lon is None:
        # Use session city if already detected
        city = session.get('detected_city')
        if city:
            ward_data = get_ward_data(city)
            return jsonify({
                "covered":    ward_data['found'],
                "city":       city,
                "ward_count": len(ward_data.get('wards', [])),
                "message":    f"Using session city: {city}",
            })
        return jsonify({"covered": False, "message": "No location provided"}), 400

    result = check_coverage(lat, lon)
    if result.get('city') and result['city'] != 'Unknown':
        session['detected_city'] = result['city']

    return jsonify(result)


@geo_bp.route('/cities', methods=['GET'])
def list_cities():
    """GET /geo/cities – returns all cities with local ward data."""
    cities = get_supported_cities()
    return jsonify({"cities": cities, "count": len(cities)})


@geo_bp.route('/set-city', methods=['POST'])
def set_city_manually():
    """
    POST /geo/set-city  Body: { "city": "Belagavi" }
    Allows user to manually override detected city.
    """
    data = request.get_json(silent=True) or {}
    city = data.get('city', '').strip()
    if not city:
        return jsonify({"error": "City name required"}), 400

    ward_data = get_ward_data(city)
    session['detected_city'] = city

    return jsonify({
        "city":       city,
        "found":      ward_data['found'],
        "ward_count": len(ward_data.get('wards', [])),
        "message":    f"City set to {city}" if ward_data['found']
                      else f"City set to {city}, but ward data not yet available.",
    })
