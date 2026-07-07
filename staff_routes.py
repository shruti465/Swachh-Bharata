"""
routes/staff_routes.py - Full staff admin routes
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from utils.geo_utils import get_supported_cities
from datetime import datetime
from functools import wraps
import os, uuid

staff_bp = Blueprint('staff', __name__)

def get_db():
    from app import get_db as _get_db
    return _get_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'staff_id' not in session:
            return redirect(url_for('staff.login'))
        return f(*args, **kwargs)
    return decorated

@staff_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT * FROM staff WHERE username=%s AND password=MD5(%s)", (username, password))
            staff = cur.fetchone()
            cur.close(); conn.close()
            if staff:
                session['staff_id']   = staff['staff_id']
                session['staff_name'] = staff['name']
                session['staff_city'] = staff.get('city', '')
                return redirect(url_for('staff.dashboard'))
            flash('Invalid username or password.', 'error')
        except Exception as e:
            flash(f'Database error: {e}', 'error')
    return render_template('staff/login.html')

@staff_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('staff.login'))

@staff_bp.route('/dashboard')
@login_required
def dashboard():
    city = request.args.get('city') or session.get('staff_city') or ''
    complaints = []
    stats = {'total': 0, 'pending': 0, 'in_progress': 0, 'resolved': 0}
    try:
        conn = get_db(); cur = conn.cursor()
        if city:
            cur.execute("SELECT * FROM complaints WHERE city=%s ORDER BY created_at DESC", (city,))
        else:
            cur.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints = cur.fetchall()
        stats['total']       = len(complaints)
        stats['pending']     = sum(1 for c in complaints if c['status'] == 'Pending')
        stats['in_progress'] = sum(1 for c in complaints if c['status'] == 'In Progress')
        stats['resolved']    = sum(1 for c in complaints if c['status'] == 'Resolved')
        # Fetch images for each complaint
        for c in complaints:
            cur.execute("SELECT filename FROM complaint_images WHERE complaint_id=%s", (c['complaint_id'],))
            c['images'] = [row['filename'] for row in cur.fetchall()]
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/admin_dashboard.html', complaints=complaints, city=city, stats=stats, supported_cities=get_supported_cities())

@staff_bp.route('/new-complaints')
@login_required
def new_complaints():
    city = session.get('staff_city', '')
    complaints = []
    try:
        conn = get_db(); cur = conn.cursor()
        if city:
            cur.execute("SELECT * FROM complaints WHERE status='Pending' AND city=%s ORDER BY created_at DESC", (city,))
        else:
            cur.execute("SELECT * FROM complaints WHERE status='Pending' ORDER BY created_at DESC")
        complaints = cur.fetchall()
        for c in complaints:
            cur.execute("SELECT filename FROM complaint_images WHERE complaint_id=%s", (c['complaint_id'],))
            c['images'] = [row['filename'] for row in cur.fetchall()]
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/new_complaints.html', complaints=complaints)

@staff_bp.route('/solved-complaints')
@login_required
def solved_complaints():
    city = session.get('staff_city', '')
    complaints = []
    try:
        conn = get_db(); cur = conn.cursor()
        if city:
            cur.execute("SELECT * FROM complaints WHERE status='Resolved' AND city=%s ORDER BY created_at DESC", (city,))
        else:
            cur.execute("SELECT * FROM complaints WHERE status='Resolved' ORDER BY created_at DESC")
        complaints = cur.fetchall()
        for c in complaints:
            try:
                cur.execute("SELECT filename FROM resolved_images WHERE complaint_id=%s", (c['complaint_id'],))
                c['resolved_images'] = [row['filename'] for row in cur.fetchall()]
            except Exception:
                c['resolved_images'] = []
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/solved_complaints.html', complaints=complaints)

@staff_bp.route('/update-status/<int:complaint_id>', methods=['POST'])
@login_required
def update_status(complaint_id):
    new_status = request.form.get('status')
    try:
        conn = get_db(); cur = conn.cursor()
        if new_status == 'Resolved':
            cur.execute("UPDATE complaints SET status=%s, resolved_at=%s WHERE complaint_id=%s", (new_status, datetime.now(), complaint_id))
            # Handle resolved photo upload
            resolved_photo = request.files.get('resolved_photo')
            if resolved_photo and resolved_photo.filename:
                from app import app as _app
                upload_folder = _app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads'))
                os.makedirs(upload_folder, exist_ok=True)
                ext = os.path.splitext(resolved_photo.filename)[1].lower()
                filename = uuid.uuid4().hex + ext
                resolved_photo.save(os.path.join(upload_folder, filename))
                cur.execute("INSERT INTO resolved_images (complaint_id, filename) VALUES (%s, %s)", (complaint_id, filename))
        else:
            cur.execute("UPDATE complaints SET status=%s WHERE complaint_id=%s", (new_status, complaint_id))
        conn.commit(); cur.close(); conn.close()
        flash(f'Complaint #{complaint_id} marked as {new_status}.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('staff.new_complaints'))

@staff_bp.route('/staff-list')
@login_required
def staff_table():
    staff_list = []
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM staff ORDER BY staff_id")
        staff_list = cur.fetchall()
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/staff_table.html', staff_list=staff_list)

@staff_bp.route('/add-staff', methods=['GET', 'POST'])
@login_required
def add_staff():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        city = request.form.get('city','').strip()
        role = request.form.get('role','inspector')
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        if not all([name, username, password]):
            flash('Name, username and password required.', 'error')
        else:
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("INSERT INTO staff (name,username,password,city,role,phone,email) VALUES (%s,%s,MD5(%s),%s,%s,%s,%s)",
                            (name, username, password, city or None, role, phone or None, email or None))
                conn.commit(); cur.close(); conn.close()
                flash(f'Staff "{name}" added.', 'success')
                return redirect(url_for('staff.staff_table'))
            except Exception as e:
                flash(f'Error: {e}', 'error')
    return render_template('staff/add_staff.html', supported_cities=get_supported_cities())

@staff_bp.route('/edit-staff/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def edit_staff(staff_id):
    staff = None
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM staff WHERE staff_id=%s", (staff_id,))
        staff = cur.fetchone()
        cur.close(); conn.close()
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('staff.staff_table'))
    if not staff:
        flash('Staff not found.', 'error')
        return redirect(url_for('staff.staff_table'))
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        city = request.form.get('city','').strip()
        role = request.form.get('role','inspector')
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        try:
            conn = get_db(); cur = conn.cursor()
            if password:
                cur.execute("UPDATE staff SET name=%s,username=%s,password=MD5(%s),city=%s,role=%s,phone=%s,email=%s WHERE staff_id=%s",
                            (name, username, password, city or None, role, phone or None, email or None, staff_id))
            else:
                cur.execute("UPDATE staff SET name=%s,username=%s,city=%s,role=%s,phone=%s,email=%s WHERE staff_id=%s",
                            (name, username, city or None, role, phone or None, email or None, staff_id))
            conn.commit(); cur.close(); conn.close()
            flash('Staff updated.', 'success')
            return redirect(url_for('staff.staff_table'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('staff/edit_staff.html', staff=staff, supported_cities=get_supported_cities())

@staff_bp.route('/delete-staff/<int:staff_id>')
@login_required
def delete_staff(staff_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("DELETE FROM staff WHERE staff_id=%s", (staff_id,))
        conn.commit(); cur.close(); conn.close()
        flash('Staff deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('staff.staff_table'))

@staff_bp.route('/workers')
@login_required
def worker_details():
    workers = []
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM workers ORDER BY worker_id")
        workers = cur.fetchall()
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/worker_details.html', workers=workers, supported_cities=get_supported_cities())

@staff_bp.route('/add-worker', methods=['POST'])
@login_required
def add_worker():
    name = request.form.get('name','').strip()
    password = request.form.get('password','').strip()
    city = request.form.get('city','').strip()
    ward_id = request.form.get('ward_id','').strip()
    phone = request.form.get('phone','').strip()
    vehicle_no = request.form.get('vehicle_no','').strip()
    if not all([name, password]):
        flash('Name and password required.', 'error')
    else:
        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("INSERT INTO workers (name,password,city,ward_id,phone,vehicle_no) VALUES (%s,MD5(%s),%s,%s,%s,%s)",
                        (name, password, city or None, ward_id or None, phone or None, vehicle_no or None))
            conn.commit(); cur.close(); conn.close()
            flash(f'Worker "{name}" added.', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return redirect(url_for('staff.worker_details'))

@staff_bp.route('/delete-worker/<int:worker_id>')
@login_required
def delete_worker(worker_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("DELETE FROM workers WHERE worker_id=%s", (worker_id,))
        conn.commit(); cur.close(); conn.close()
        flash('Worker deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('staff.worker_details'))

@staff_bp.route('/working-staff')
@login_required
def working_staff():
    workers = []
    complaints_in_progress = 0
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM workers WHERE active=1 ORDER BY worker_id")
        workers = cur.fetchall()
        cur.execute("SELECT COUNT(*) as cnt FROM complaints WHERE status='In Progress'")
        row = cur.fetchone()
        complaints_in_progress = row['cnt'] if row else 0
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/working_staff.html', workers=workers, complaints_in_progress=complaints_in_progress)

@staff_bp.route('/user-data')
@login_required
def user_data():
    complaints = []
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints = cur.fetchall()
        cur.close(); conn.close()
    except Exception:
        pass
    return render_template('staff/user_data.html', complaints=complaints)
