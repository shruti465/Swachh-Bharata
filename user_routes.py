from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, current_app
from utils.geo_utils import get_ward_data
from datetime import datetime
import os
import uuid

user_bp = Blueprint('user', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_IMAGES = 5

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_images(files):
    """Save uploaded images and return list of saved filenames."""
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    saved = []
    for file in files[:MAX_IMAGES]:
        if file and file.filename and allowed_file(file.filename):
            ext      = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(upload_folder, filename))
            saved.append(filename)
    return saved


@user_bp.route('/form', methods=['GET', 'POST'])
def user_form():
    city     = session.get('detected_city', '')
    wards    = []
    coverage = None

    if city:
        ward_data = get_ward_data(city)
        wards     = ward_data.get('wards', [])
        coverage  = ward_data.get('found', False)

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        phone     = request.form.get('phone', '').strip()
        ward_id   = request.form.get('ward_id', '').strip()
        complaint = request.form.get('complaint', '').strip()
        city_name = request.form.get('city', city).strip()
        latitude  = request.form.get('latitude', '') or None
        longitude = request.form.get('longitude', '') or None

        if not all([name, phone, ward_id, complaint]):
            flash('Please fill all required fields.', 'error')
            return redirect(url_for('user.user_form'))

        try:
            from app import get_db
            conn = get_db()
            cur  = conn.cursor()

            # Insert complaint
            cur.execute(
                """INSERT INTO complaints
                   (name, phone, ward_id, city, complaint, latitude, longitude, created_at, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending')""",
                (name, phone, ward_id, city_name, complaint,
                 latitude, longitude, datetime.now())
            )
            conn.commit()
            complaint_id = cur.lastrowid

            # Save uploaded images
            images = request.files.getlist('images')
            images = [img for img in images if img and img.filename]
            if images:
                saved_files = save_images(images)
                for filename in saved_files:
                    cur.execute(
                        "INSERT INTO complaint_images (complaint_id, filename) VALUES (%s, %s)",
                        (complaint_id, filename)
                    )
                conn.commit()

            cur.close()
            conn.close()
            flash(f'Complaint #{complaint_id} registered successfully!', 'success')
            return redirect(url_for('user.user_form'))

        except Exception as e:
            flash(f'Database error: {e}', 'error')

    return render_template('user/user_form.html', city=city, wards=wards, coverage=coverage)


@user_bp.route('/get-wards', methods=['GET'])
def get_wards_ajax():
    city_name = request.args.get('city', '').strip()
    if not city_name:
        city_name = session.get('detected_city', '')
    if not city_name:
        return jsonify({"found": False, "error": "City not specified"}), 400
    return jsonify(get_ward_data(city_name))
