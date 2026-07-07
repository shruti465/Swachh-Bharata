"""routes/worker_routes.py"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash

worker_bp = Blueprint('worker', __name__)


@worker_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        worker_id = request.form.get('worker_id')
        password  = request.form.get('password')
        try:
            from app import mysql
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT * FROM workers WHERE worker_id=%s AND password=MD5(%s)",
                (worker_id, password)
            )
            worker = cur.fetchone()
            cur.close()
            if worker:
                session['worker_id']   = worker['worker_id']
                session['worker_name'] = worker['name']
                session['worker_ward'] = worker.get('ward_id', '')
                session['worker_city'] = worker.get('city', '')
                return redirect(url_for('worker.dashboard'))
            flash('Invalid credentials', 'error')
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('worker/worker_login.html')


@worker_bp.route('/dashboard')
def dashboard():
    if 'worker_id' not in session:
        return redirect(url_for('worker.login'))
    return render_template('worker/worker_dashboard.html')


@worker_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('worker.login'))
