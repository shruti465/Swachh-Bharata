"""routes/central_routes.py"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from utils.geo_utils import get_supported_cities

central_bp = Blueprint('central', __name__)


@central_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['central_admin'] = True
            return redirect(url_for('central.dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('central/central_login.html')


@central_bp.route('/dashboard')
def dashboard():
    if not session.get('central_admin'):
        return redirect(url_for('central.login'))
    cities = get_supported_cities()
    return render_template('central/central_dashboard.html', cities=cities)


@central_bp.route('/logout')
def logout():
    session.pop('central_admin', None)
    return redirect(url_for('central.login'))
