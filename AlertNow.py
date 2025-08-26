from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
from flask_socketio import SocketIO, emit, join_room
import logging
import ast
import os
import json
import sqlite3
import joblib
import cv2
import numpy as np
from collections import Counter
from datetime import datetime
import pytz
import pandas as pd
import uuid
from models import lr_road, lr_fire
from BarangayDashboard import get_barangay_stats, get_latest_alert as get_barangay_latest_alert
from CDRRMODashboard import get_cdrrmo_stats, get_latest_alert as get_cdrrmo_latest_alert
from PNPDashboard import get_pnp_stats, get_latest_alert as get_pnp_latest_alert
from BFPDashboard import get_bfp_stats, get_latest_alert as get_bfp_latest_alert
from BarangayAnalytics import get_barangay_trends, get_barangay_distribution, get_barangay_causes
from CDRRMOAnalytics import get_cdrrmo_trends, get_cdrrmo_distribution, get_cdrrmo_causes
from PNPAnalytics import get_pnp_trends, get_pnp_distribution, get_pnp_causes
from BFPAnalytics import get_bfp_trends, get_bfp_distribution, get_bfp_causes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

road_accident_predictor = None
try:
    road_accident_predictor = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 'road_predictor_lr.pkl'))
    logger.info("road_accident_predictor_lr.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("road_accident_predictor_lr.pkl not found.")
except Exception as e:
    logger.error(f"Error loading road_accident_predictor_lr.pkl: {e}")

road_accident_df = pd.DataFrame()
try:
    road_accident_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'road_accident.csv'))
    logger.info("Successfully loaded road_accident.csv")
except FileNotFoundError:
    logger.error("road_accident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading road_accident.csv: {e}")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*", max_http_buffer_size=10000000)

alerts = []

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyBSXRZPDX1x1d91Ck-pskiwGA8Y2-5gDVs')

barangay_coords = {}
try:
    with open(os.path.join(os.path.dirname(__file__), 'assets', 'coords.txt'), 'r') as f:
        barangay_coords = ast.literal_eval(f.read())
except FileNotFoundError:
    logger.error("coords.txt not found in assets directory. Using fallback.")
    barangay_coords = {
        "San Pablo City": ["Barangay 1", "Barangay 2", "Barangay 3"],
        "Quezon Province": ["Barangay A", "Barangay B", "Barangay C"]
    }
except Exception as e:
    logger.error(f"Error loading coords.txt: {e}. Using fallback.")
    barangay_coords = {
        "San Pablo City": ["Barangay 1", "Barangay 2", "Barangay 3"],
        "Quezon Province": ["Barangay A", "Barangay B", "Barangay C"]
    }

municipality_coords = {
    "San Pablo City": {"lat": 14.0642, "lon": 121.3233},
    "Quezon Province": {"lat": 13.9347, "lon": 121.9473},
}

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_municipality_from_barangay(barangay):
    for municipality, barangays in barangay_coords.items():
        if barangay in barangays:
            return municipality
    return None

def classify_image(base64_image):
    try:
        import base64
        img_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.error("Failed to decode image")
            return 'unknown'
        img = cv2.resize(img, (64, 64))
        features = img.flatten().reshape(1, -1)
        if road_accident_predictor:
            prediction = road_accident_predictor.predict(features)[0]
            logger.debug(f"Image classified as: {prediction}")
            return prediction
        return 'unknown'
    except Exception as e:
        logger.error(f"Image classification failed: {e}")
        return 'unknown'

def construct_unique_id(role, barangay=None, assigned_municipality=None, contact_no=None):
    if role == 'barangay':
        if not barangay or not contact_no:
            raise ValueError("barangay and contact_no are required for barangay role")
        # Replace underscores in barangay and contact_no to prevent splitting issues
        barangay = barangay.replace('_', '-')
        contact_no = contact_no.replace('_', '-')
        return f"barangay_{barangay}_{contact_no}"
    if not assigned_municipality or not contact_no:
        raise ValueError("assigned_municipality and contact_no are required for non-barangay role")
    assigned_municipality = assigned_municipality.replace('_', '-')
    contact_no = contact_no.replace('_', '-')
    return f"{role}_{assigned_municipality}_{contact_no}"

@app.route('/')
def home():
    logger.debug("Rendering SignUpType.html")
    return render_template('SignUpType.html')

@app.route('/signup_barangay', methods=['GET', 'POST'])
def signup_barangay():
    if request.method == 'POST':
        barangay = request.form['barangay']
        assigned_municipality = request.form['municipality']
        province = request.form['province']
        contact_no = request.form['contact_no']
        password = request.form['password']
        # Validate inputs to prevent underscores
        if '_' in barangay or '_' in contact_no:
            logger.error("Underscores are not allowed in barangay or contact_no")
            return "Underscores are not allowed in barangay or contact number", 400
        try:
            unique_id = construct_unique_id('barangay', barangay=barangay, contact_no=contact_no)
        except ValueError as e:
            logger.error(f"Signup failed: {e}")
            return str(e), 400
        
        conn = get_db_connection()
        try:
            existing_user = conn.execute('SELECT * FROM users WHERE contact_no = ?', (contact_no,)).fetchone()
            if existing_user:
                logger.error("Signup failed: Contact number %s already exists", contact_no)
                return "Contact number already exists", 400
            
            conn.execute('''
                INSERT INTO users (barangay, role, contact_no, assigned_municipality, province, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (barangay, 'barangay', contact_no, assigned_municipality, province, password))
            conn.commit()
            logger.debug("User signed up successfully: %s", unique_id)
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            logger.error("IntegrityError during signup: %s", e)
            return "User already exists", 400
        except Exception as e:
            logger.error(f"Signup failed for {unique_id}: {e}")
            return f"Signup failed: {e}", 500
        finally:
            conn.close()
    return render_template('SignUpPage.html')

@app.route('/signup_cdrrmo_pnp_bfp', methods=['GET', 'POST'])
def signup_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        role = request.form['role'].lower()
        assigned_municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        # Validate inputs to prevent underscores
        if '_' in assigned_municipality or '_' in contact_no:
            logger.error("Underscores are not allowed in municipality or contact_no")
            return "Underscores are not allowed in municipality or contact number", 400
        try:
            unique_id = construct_unique_id(role, assigned_municipality=assigned_municipality, contact_no=contact_no)
        except ValueError as e:
            logger.error(f"Signup failed: {e}")
            return str(e), 400
        
        conn = get_db_connection()
        try:
            existing_user = conn.execute('SELECT * FROM users WHERE contact_no = ?', (contact_no,)).fetchone()
            if existing_user:
                logger.error("Signup failed: Contact number %s already exists", contact_no)
                return "Contact number already exists", 400
            
            conn.execute('''
                INSERT INTO users (role, contact_no, assigned_municipality, password)
                VALUES (?, ?, ?, ?)
            ''', (role, contact_no, assigned_municipality, password))
            conn.commit()
            logger.debug("User signed up successfully: %s", unique_id)
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        except sqlite3.IntegrityError as e:
            logger.error("IntegrityError during signup: %s", e)
            return "User already exists", 400
        except Exception as e:
            logger.error(f"Signup failed for {unique_id}: {e}")
            return f"Signup failed: {e}", 500
        finally:
            conn.close()
    return render_template('CDRRMOPNPBFPUp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug("Accessing /login with method: %s", request.method)
    if request.method == 'POST':
        barangay = request.form['barangay']
        contact_no = request.form['contact_no']
        password = request.form['password']
        # Validate inputs to prevent underscores
        if '_' in barangay or '_' in contact_no:
            logger.error("Underscores are not allowed in barangay or contact_no")
            return "Underscores are not allowed in barangay or contact number", 400
        try:
            unique_id = construct_unique_id('barangay', barangay=barangay, contact_no=contact_no)
        except ValueError as e:
            logger.error(f"Login failed: {e}")
            return str(e), 400
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE barangay = ? AND contact_no = ? AND password = ?
        ''', (barangay, contact_no, password)).fetchone()
        conn.close()
        
        if user:
            session['unique_id'] = unique_id
            session['role'] = user['role']
            session['barangay'] = user['barangay']
            logger.debug(f"Web login successful for barangay: {unique_id}")
            return redirect(url_for('barangay_dashboard'))
        logger.warning(f"Web login failed for unique_id: {unique_id}")
        return "Invalid credentials", 401
    return render_template('LogInPage.html')

@app.route('/login_cdrrmo_pnp_bfp', methods=['GET', 'POST'])
def login_cdrrmo_pnp_bfp():
    logger.debug("Accessing /login_cdrrmo_pnp_bfp with method: %s", request.method)
    if request.method == 'POST':
        role = request.form.get('role', '').lower()
        if not role:
            logger.error("Role field is missing in the form data")
            return "Role is required", 400
        assigned_municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        
        if role not in ['cdrrmo', 'pnp', 'bfp']:
            logger.error(f"Invalid role provided: {role}")
            return "Invalid role", 400
        
        # Validate inputs to prevent underscores
        if '_' in assigned_municipality or '_' in contact_no:
            logger.error("Underscores are not allowed in municipality or contact_no")
            return "Underscores are not allowed in municipality or contact number", 400
        
        logger.debug(f"Login attempt: role={role}, municipality={assigned_municipality}, contact_no={contact_no}")
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ?
        ''', (role, contact_no, password, assigned_municipality)).fetchone()
        conn.close()
        
        if user:
            try:
                unique_id = construct_unique_id(user['role'], assigned_municipality=assigned_municipality, contact_no=contact_no)
            except ValueError as e:
                logger.error(f"Login failed: {e}")
                return str(e), 400
            session['unique_id'] = unique_id
            session['role'] = user['role']
            session['municipality'] = user['assigned_municipality']
            logger.debug(f"Web login successful for user: {unique_id} ({user['role']})")
            if user['role'] == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif user['role'] == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif user['role'] == 'bfp':
                return redirect(url_for('bfp_dashboard'))
        logger.warning(f"Web login failed for assigned_municipality: {assigned_municipality}, contact: {contact_no}, role: {role}")
        return "Invalid credentials", 401
    return render_template('CDRRMOPNPBFPIn.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Validate username to prevent underscores
        if '_' in username:
            logger.error("Underscores are not allowed in username")
            return "Underscores are not allowed in username", 400
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ?',
                            ('admin', username, password)).fetchone()
        conn.close()
        if admin:
            session['role'] = 'admin'
            session['unique_id'] = f"admin_{username}"
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE role != "admin"').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    role = data.get('role')
    contact_no = data.get('contact_no')
    password = data.get('password')
    barangay = data.get('barangay') if role == 'barangay' else None
    municipality = data.get('municipality') if role in ['pnp', 'cdrrmo', 'bfp'] else None
    # Validate inputs to prevent underscores
    if (barangay and '_' in barangay) or '_' in contact_no or (municipality and '_' in municipality):
        logger.error("Underscores are not allowed in barangay, contact_no, or municipality")
        return jsonify({'error': 'Underscores are not allowed in barangay, contact number, or municipality'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (role, contact_no, password, barangay, assigned_municipality) VALUES (?, ?, ?, ?, ?)',
                    (role, contact_no, password, barangay, municipality))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'User already exists'}), 400
    conn.close()
    return jsonify({'message': 'User created successfully'})

@app.route('/admin/delete_user/<contact_no>', methods=['POST'])
def admin_delete_user(contact_no):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE contact_no = ?', (contact_no,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted successfully'})

@app.route('/export_users', methods=['GET'])
def export_users():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/download_db', methods=['GET'])
def download_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    if not os.path.exists(db_path):
        return "Database file not found", 404
    logger.debug(f"Serving database from: {db_path}")
    return send_file(db_path, as_attachment=True, download_name='users_web.db')

@app.route('/choose_login_type', methods=['GET'])
def choose_login_type():
    logger.debug("Rendering LoginType.html")
    return render_template('LoginType.html')

@app.route('/go_to_cdrrmopnpbfpin', methods=['GET'])
def go_to_cdrrmopnpbfpin():
    logger.debug("Redirecting to /login_cdrrmo_pnp_bfp")
    return redirect(url_for('login_cdrrmo_pnp_bfp'))

@app.route('/signup_muna', methods=['GET'])
def signup_muna():
    logger.debug("Redirecting to /signup_cdrrmo_pnp_bfp")
    return redirect(url_for('signup_cdrrmo_pnp_bfp'))

@app.route('/signup_na', methods=['GET'])
def signup_na():
    logger.debug("Redirecting to /signup_barangay")
    return redirect(url_for('signup_barangay'))

@app.route('/logout')
def logout():
    role = session.pop('role', None)
    session.clear()
    logger.debug(f"User logged out. Redirecting from role: {role}")
    if role == 'barangay':
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login_cdrrmo_pnp_bfp'))

@socketio.on('connect')
def handle_connect():
    logger.debug(f"Client connected: {request.sid}")
    if 'role' in session and 'unique_id' in session:
        role = session['role']
        unique_id = session['unique_id']
        join_room(unique_id)
        logger.debug(f"Client {request.sid} joined room {unique_id}")
        if role == 'barangay':
            barangay = session.get('barangay')
            if barangay:
                join_room(f"barangay_{barangay}")
                logger.debug(f"Client {request.sid} joined room barangay_{barangay}")
        elif role in ['cdrrmo', 'pnp', 'bfp']:
            municipality = session.get('municipality')
            if municipality:
                join_room(f"{role}_{municipality}")
                logger.debug(f"Client {request.sid} joined room {role}_{municipality}")

@socketio.on('register_role')
def handle_register_role(data):
    logger.debug(f"Register role received: {data}")
    role = data.get('role')
    if role == 'barangay':
        barangay = data.get('barangay')
        if barangay:
            join_room(f"barangay_{barangay}")
            logger.debug(f"Client {request.sid} joined room barangay_{barangay}")
    elif role in ['cdrrmo', 'pnp', 'bfp']:
        municipality = data.get('municipality')
        if municipality:
            join_room(f"{role}_{municipality}")
            logger.debug(f"Client {request.sid} joined room {role}_{municipality}")

@socketio.on('new_alert')
def handle_new_alert(data):
    try:
        logger.debug(f"New alert received: {data}")
        alert_id = str(uuid.uuid4())
        data['alert_id'] = alert_id
        data['timestamp'] = datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        barangay = data.get('barangay')
        emergency_type = data.get('emergency_type', 'unknown')
        
        if 'image' in data and data['image']:
            data['image_classification'] = classify_image(data['image'])
        else:
            data['image_classification'] = 'no_image'

        alerts.append(data)
        logger.debug(f"Alert stored: {alert_id}")

        conn = get_db_connection()
        conn.execute('INSERT INTO alerts (alert_id, barangay, emergency_type, lat, lon, house_no, street_no, image_classification, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (alert_id, barangay, emergency_type, data.get('lat'), data.get('lon'), data.get('house_no'), data.get('street_no'), data.get('image_classification'), data['timestamp']))
        conn.commit()
        conn.close()

        if barangay:
            socketio.emit('new_alert', data, room=f"barangay_{barangay}")
            logger.debug(f"Emitted new_alert to barangay_{barangay}")
    except Exception as e:
        logger.error(f"Error handling new alert: {e}")

@socketio.on('forward_alert')
def handle_forward_alert(data):
    try:
        logger.debug(f"Forward alert received: {data}")
        alert_id = data.get('alert_id')
        barangay = data.get('barangay')
        municipality = get_municipality_from_barangay(barangay)
        if not municipality:
            logger.error(f"No municipality found for barangay: {barangay}")
            return

        data['timestamp'] = datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        conn = get_db_connection()
        conn.execute('UPDATE alerts SET forwarded_to = ? WHERE alert_id = ?', ('cdrrmo,pnp,bfp', alert_id))
        conn.commit()
        conn.close()

        for role in ['cdrrmo', 'pnp', 'bfp']:
            socketio.emit('forward_alert', data, room=f"{role}_{municipality}")
            socketio.emit('update_map', {'lat': data.get('lat'), 'lon': data.get('lon'), 'emergency_type': data.get('emergency_type'), 'barangay': barangay}, room=f"{role}_{municipality}")
            logger.debug(f"Emitted forward_alert and update_map to {role}_{municipality}")
    except Exception as e:
        logger.error(f"Error forwarding alert: {e}")

@socketio.on('response_submitted')
def handle_response(data):
    try:
        logger.debug(f"Response submitted: {data}")
        alert_id = data.get('alert_id')
        barangay = data.get('barangay')
        municipality = get_municipality_from_barangay(barangay)
        if not municipality:
            logger.error(f"No municipality found for barangay: {barangay}")
            return

        response_data = {
            'alert_id': alert_id,
            'barangay': barangay,
            'road_accident_cause': data.get('road_accident_cause'),
            'road_accident_type': data.get('road_accident_type'),
            'weather': data.get('weather'),
            'road_condition': data.get('road_condition'),
            'vehicle_type': data.get('vehicle_type'),
            'driver_age': data.get('driver_age'),
            'driver_gender': data.get('driver_gender'),
            'lat': data.get('lat'),
            'lon': data.get('lon'),
            'timestamp': datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        }

        conn = get_db_connection()
        conn.execute('INSERT INTO responses (alert_id, barangay, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (alert_id, barangay, response_data['road_accident_cause'], response_data['road_accident_type'],
                     response_data['weather'], response_data['road_condition'], response_data['vehicle_type'],
                     response_data['driver_age'], response_data['driver_gender'], response_data['lat'], response_data['lon'], response_data['timestamp']))
        conn.commit()
        conn.close()

        if road_accident_predictor:
            try:
                features = {
                    'road_accident_cause': [response_data['road_accident_cause']],
                    'road_accident_type': [response_data['road_accident_type']],
                    'weather': [response_data['weather']],
                    'road_condition': [response_data['road_condition']],
                    'vehicle_type': [response_data['vehicle_type']],
                    'driver_age': [response_data['driver_age']],
                    'driver_gender': [response_data['driver_gender']]
                }
                features_df = pd.DataFrame(features)
                for column in features_df.columns:
                    if features_df[column].dtype == 'object':
                        features_df[column] = features_df[column].astype('category').cat.codes
                prediction = road_accident_predictor.predict(features_df)[0]
                response_data['prediction'] = str(prediction)
                logger.debug(f"Prediction made: {prediction}")
            except Exception as e:
                logger.error(f"Error making prediction: {e}")
                response_data['prediction'] = 'Error in prediction'
        else:
            response_data['prediction'] = 'Predictor not loaded'

        if barangay:
            socketio.emit('response_submitted', response_data, room=f"barangay_{barangay}")
        for role in ['cdrrmo', 'pnp', 'bfp']:
            socketio.emit('response_submitted', response_data, room=f"{role}_{municipality}")
            logger.debug(f"Emitted response_submitted to {role}_{municipality}")
    except Exception as e:
        logger.error(f"Error handling response: {e}")

@app.route('/send_alert', methods=['POST'])
def send_alert():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        lat = data.get('lat')
        lon = data.get('lon')
        emergency_type = data.get('emergency_type', 'General')
        image = data.get('image')
        user_role = data.get('user_role', 'unknown')
        image_upload_time = data.get('imageUploadTime', datetime.now().isoformat())
        barangay = data.get('barangay', 'N/A')
        municipality = get_municipality_from_barangay(barangay)
        if not municipality:
            logger.error(f"Could not find municipality for barangay: {barangay}")
            return jsonify({'error': 'Invalid barangay'}), 400

        if image:
            upload_time = datetime.fromisoformat(image_upload_time)
            if (datetime.now() - upload_time).total_seconds() > 30 * 60:
                image = None
                emergency_type = 'Not Specified'

        alert = {
            'lat': lat,
            'lon': lon,
            'emergency_type': emergency_type,
            'image': image,
            'role': user_role,
            'house_no': data.get('house_no', 'N/A'),
            'street_no': data.get('street_no', 'N/A'),
            'barangay': barangay,
            'municipality': municipality,
            'timestamp': datetime.now(pytz.timezone('Asia/Manila')).isoformat(),
            'imageUploadTime': image_upload_time,
            'alert_id': str(uuid.uuid4()),
            'user_barangay': barangay
        }
        
        if alert['image']:
            prediction = classify_image(alert['image'])
            alert['image_classification'] = prediction if prediction in ['road_accident', 'fire_incident'] else 'unknown'

        alerts.append(alert)
        conn = get_db_connection()
        conn.execute('INSERT INTO alerts (alert_id, barangay, emergency_type, lat, lon, house_no, street_no, image_classification, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (alert['alert_id'], barangay, emergency_type, alert['lat'], alert['lon'], alert['house_no'], alert['street_no'], alert['image_classification'], alert['timestamp']))
        conn.commit()
        conn.close()

        if barangay and barangay != 'N/A':
            socketio.emit('new_alert', alert, room=f"barangay_{barangay}")
        return jsonify({'status': 'success', 'message': 'Alert sent'}), 200
    except Exception as e:
        logger.error(f"Error processing send_alert: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats')
def get_stats():
    try:
        total = len(alerts)
        critical = len([a for a in alerts if a.get('emergency_type', '').lower() == 'critical'])
        return jsonify({'total': total, 'critical': critical})
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return jsonify({'error': 'Failed to retrieve stats'}), 500

@app.route('/api/distribution')
def get_distribution():
    try:
        role = request.args.get('role', 'all')
        if role == 'barangay':
            filtered_alerts = [a for a in alerts if a.get('role') == 'barangay' or a.get('barangay')]
        elif role == 'cdrrmo':
            filtered_alerts = [a for a in alerts if a.get('role') == 'cdrrmo' or a.get('assigned_municipality')]
        elif role == 'pnp':
            filtered_alerts = [a for a in alerts if a.get('role') == 'pnp' or a.get('assigned_municipality')]
        elif role == 'bfp':
            filtered_alerts = [a for a in alerts if a.get('role') == 'bfp' or a.get('assigned_municipality')]
        else:
            filtered_alerts = alerts
        types = [a.get('emergency_type', 'unknown') for a in filtered_alerts]
        return jsonify(dict(Counter(types)))
    except Exception as e:
        logger.error(f"Error in get_distribution: {e}")
        return jsonify({'error': 'Failed to retrieve distribution'}), 500

@app.route('/add_alert', methods=['POST'])
def add_alert():
    data = request.form
    barangay = data.get('barangay')
    municipality = data.get('municipality')
    # Validate inputs to prevent underscores
    if (barangay and '_' in barangay) or (municipality and '_' in municipality):
        logger.error("Underscores are not allowed in barangay or municipality")
        return jsonify({'error': 'Underscores are not allowed in barangay or municipality'}), 400
    new_alert = {
        "barangay": barangay,
        "municipality": municipality,
        "message": data.get('message'),
        "timestamp": data.get('timestamp'),
        "alert_id": str(uuid.uuid4())
    }
    alerts.append(new_alert)
    conn = get_db_connection()
    conn.execute('INSERT INTO alerts (alert_id, barangay, emergency_type, timestamp) VALUES (?, ?, ?, ?)',
                (new_alert['alert_id'], new_alert['barangay'], 'General', new_alert['timestamp']))
    conn.commit()
    conn.close()
    if new_alert['barangay']:
        socketio.emit('new_alert', new_alert, room=f"barangay_{new_alert['barangay']}")
    return jsonify({"status": "success", "alert": new_alert})

@app.route('/export_alerts')
def export_alerts():
    with open('alerts.json', 'w') as f:
        json.dump(alerts, f, indent=4)
    return jsonify({"status": "success", "file": "alerts.json"})

@app.route('/api/analytics')
def get_analytics():
    try:
        role = request.args.get('role', 'all')
        if role == 'barangay':
            trends = get_barangay_trends()
            distribution = get_barangay_distribution()
            causes = get_barangay_causes()
        elif role == 'cdrrmo':
            trends = get_cdrrmo_trends()
            distribution = get_cdrrmo_distribution()
            causes = get_cdrrmo_causes()
        elif role == 'pnp':
            trends = get_pnp_trends()
            distribution = get_pnp_distribution()
            causes = get_pnp_causes()
        elif role == 'bfp':
            trends = get_bfp_trends()
            distribution = get_bfp_distribution()
            causes = get_bfp_causes()
        else:
            return jsonify({'error': 'Invalid role'}), 400
        return jsonify({'trends': trends, 'distribution': distribution, 'causes': causes})
    except Exception as e:
        logger.error(f"Error in get_analytics: {e}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500

@app.route('/barangay_dashboard')
def barangay_dashboard():
    if 'role' not in session or session['role'] != 'barangay':
        logger.warning("Unauthorized access to barangay_dashboard")
        return redirect(url_for('login'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for barangay_dashboard")
        return redirect(url_for('login'))
    
    # Validate unique_id format
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'barangay':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login'))
    
    barangay = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE barangay = ? AND contact_no = ?
    ''', (barangay, contact_no)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'barangay':
        logger.warning("Unauthorized access to barangay_dashboard. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login'))
    
    assigned_municipality = user['assigned_municipality'] or 'San Pablo City'
    latest_alert = get_barangay_latest_alert()
    stats = get_barangay_stats()
    coords = municipality_coords.get(assigned_municipality, {'lat': 14.0642, 'lon': 121.3233})
    
    try:
        lat_coord = float(latest_alert.get('lat', coords['lat']) if latest_alert else coords['lat'])
        lon_coord = float(latest_alert.get('lon', coords['lon']) if latest_alert else coords['lon'])
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates for {barangay} in {assigned_municipality}, using defaults")
        lat_coord = 14.0642
        lon_coord = 121.3233

    logger.debug(f"Rendering BarangayDashboard for {barangay} in {assigned_municipality}")
    return render_template('BarangayDashboard.html', 
                           latest_alert=latest_alert, 
                           stats=stats, 
                           barangay=barangay, 
                           lat_coord=lat_coord, 
                           lon_coord=lon_coord, 
                           google_api_key=GOOGLE_API_KEY)

@app.route('/cdrrmo_dashboard')
def cdrrmo_dashboard():
    if 'role' not in session or session['role'] != 'cdrrmo':
        logger.warning("Unauthorized access to cdrrmo_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for cdrrmo_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'cdrrmo':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    assigned_municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
    ''', ('cdrrmo', contact_no, assigned_municipality)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'cdrrmo':
        logger.warning("Unauthorized access to cdrrmo_dashboard. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    latest_alert = get_cdrrmo_latest_alert()
    stats = get_cdrrmo_stats()
    coords = municipality_coords.get(assigned_municipality, {'lat': 14.0642, 'lon': 121.3233})
    
    try:
        lat_coord = float(latest_alert.get('lat', coords['lat']) if latest_alert else coords['lat'])
        lon_coord = float(latest_alert.get('lon', coords['lon']) if latest_alert else coords['lon'])
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
        lat_coord = 14.0642
        lon_coord = 121.3233

    logger.debug(f"Rendering CDRRMODashboard for {assigned_municipality}")
    return render_template('CDRRMODashboard.html', 
                           latest_alert=latest_alert,
                           stats=stats, 
                           municipality=assigned_municipality, 
                           lat_coord=lat_coord, 
                           lon_coord=lon_coord, 
                           google_api_key=GOOGLE_API_KEY)

@app.route('/pnp_dashboard')
def pnp_dashboard():
    if 'role' not in session or session['role'] != 'pnp':
        logger.warning("Unauthorized access to pnp_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for pnp_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'pnp':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    assigned_municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
    ''', ('pnp', contact_no, assigned_municipality)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'pnp':
        logger.warning("Unauthorized access to pnp_dashboard. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    latest_alert = get_pnp_latest_alert()
    stats = get_pnp_stats()
    coords = municipality_coords.get(assigned_municipality, {'lat': 14.0642, 'lon': 121.3233})
    
    try:
        lat_coord = float(latest_alert.get('lat', coords['lat']) if latest_alert else coords['lat'])
        lon_coord = float(latest_alert.get('lon', coords['lon']) if latest_alert else coords['lon'])
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
        lat_coord = 14.0642
        lon_coord = 121.3233

    logger.debug(f"Rendering PNPDashboard for {assigned_municipality}")
    return render_template('PNPDashboard.html', 
                           latest_alert=latest_alert,
                           stats=stats, 
                           municipality=assigned_municipality, 
                           lat_coord=lat_coord, 
                           lon_coord=lon_coord, 
                           google_api_key=GOOGLE_API_KEY)

@app.route('/bfp_dashboard')
def bfp_dashboard():
    if 'role' not in session or session['role'] != 'bfp':
        logger.warning("Unauthorized access to bfp_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for bfp_dashboard")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'bfp':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    assigned_municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
    ''', ('bfp', contact_no, assigned_municipality)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'bfp':
        logger.warning("Unauthorized access to bfp_dashboard. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    latest_alert = get_bfp_latest_alert()
    stats = get_bfp_stats()
    coords = municipality_coords.get(assigned_municipality, {'lat': 14.0642, 'lon': 121.3233})
    
    try:
        lat_coord = float(latest_alert.get('lat', coords['lat']) if latest_alert else coords['lat'])
        lon_coord = float(latest_alert.get('lon', coords['lon']) if latest_alert else coords['lon'])
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
        lat_coord = 14.0642
        lon_coord = 121.3233

    logger.debug(f"Rendering BFPDashboard for {assigned_municipality}")
    return render_template('BFPDashboard.html', 
                           latest_alert=latest_alert,
                           stats=stats, 
                           municipality=assigned_municipality, 
                           lat_coord=lat_coord, 
                           lon_coord=lon_coord, 
                           google_api_key=GOOGLE_API_KEY)

@app.route('/barangay/analytics')
def barangay_analytics():
    if 'role' not in session or session['role'] != 'barangay':
        logger.warning("Unauthorized access to barangay_analytics")
        return redirect(url_for('login'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for barangay_analytics")
        return redirect(url_for('login'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'barangay':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login'))
    
    barangay = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('SELECT barangay, assigned_municipality FROM users WHERE barangay = ? AND contact_no = ?',
                        (barangay, contact_no)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'barangay':
        logger.warning("Unauthorized access to barangay_analytics. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login'))
    
    municipality = user['assigned_municipality'] if user else "San Pablo City"
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = barangay_coords.get(municipality, [])
    return render_template('BarangayAnalytics.html', barangay=barangay, current_datetime=current_datetime, barangays=barangays)

@app.route('/api/barangay_analytics_data', methods=['GET'])
def barangay_analytics_data():
    time_filter = request.args.get('time', 'weekly')
    trends = get_barangay_trends(time_filter)
    distribution = get_barangay_distribution(time_filter)
    causes_data = get_barangay_causes(time_filter)
    weather = {'Sunny': 10, 'Rainy': 5, 'Foggy': 2}
    road_conditions = {'Dry': 12, 'Wet': 4, 'Icy': 1}
    vehicle_types = {'Car': 8, 'Motorcycle': 6, 'Truck': 3}
    driver_age = {'18-25': 5, '26-35': 7, '36-50': 3, '51+': 2}
    driver_gender = {'Male': 12, 'Female': 5}
    accident_type = {'Collision': 10, 'Rollover': 4, 'Pedestrian': 3}
    injuries = [5, 3, 2, 1] * (len(trends['labels']) // 4 + 1)
    fatalities = [1, 0, 1, 0] * (len(trends['labels']) // 4 + 1)
    return jsonify({
        'trends': trends,
        'distribution': distribution,
        'causes': causes_data['road'],
        'weather': weather,
        'road_conditions': road_conditions,
        'vehicle_types': vehicle_types,
        'driver_age': driver_age,
        'driver_gender': driver_gender,
        'accident_type': accident_type,
        'injuries': injuries[:len(trends['labels'])],
        'fatalities': fatalities[:len(trends['labels'])]
    })

@app.route('/cdrrmo/analytics')
def cdrrmo_analytics():
    if 'role' not in session or session['role'] != 'cdrrmo':
        logger.warning("Unauthorized access to cdrrmo_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for cdrrmo_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'cdrrmo':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('cdrrmo', contact_no, municipality)).fetchone()
    conn.close()
    
    if not user:
        logger.warning("Unauthorized access to cdrrmo_analytics. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = barangay_coords.get(municipality, [])
    return render_template('CDRRMOAnalytics.html', municipality=municipality, current_datetime=current_datetime, barangays=barangays)

@app.route('/api/cdrrmo_analytics_data', methods=['GET'])
def get_cdrrmo_analytics_data():
    time_filter = request.args.get('time', 'weekly')
    trends = get_cdrrmo_trends(time_filter)
    distribution = get_cdrrmo_distribution(time_filter)
    causes_data = get_cdrrmo_causes(time_filter)
    weather = {'Sunny': 10, 'Rainy': 5, 'Foggy': 2}
    road_conditions = {'Dry': 12, 'Wet': 4, 'Icy': 1}
    vehicle_types = {'Car': 8, 'Motorcycle': 6, 'Truck': 3}
    driver_age = {'18-25': 5, '26-35': 7, '36-50': 3, '51+': 2}
    driver_gender = {'Male': 12, 'Female': 5}
    accident_type = {'Collision': 10, 'Rollover': 4, 'Pedestrian': 3}
    injuries = [5, 3, 2, 1] * (len(trends['labels']) // 4 + 1)
    fatalities = [1, 0, 1, 0] * (len(trends['labels']) // 4 + 1)
    return jsonify({
        'trends': trends,
        'distribution': distribution,
        'causes': causes_data['road'],
        'weather': weather,
        'road_conditions': road_conditions,
        'vehicle_types': vehicle_types,
        'driver_age': driver_age,
        'driver_gender': driver_gender,
        'accident_type': accident_type,
        'injuries': injuries[:len(trends['labels'])],
        'fatalities': fatalities[:len(trends['labels'])]
    })

@app.route('/pnp/analytics')
def pnp_analytics():
    if 'role' not in session or session['role'] != 'pnp':
        logger.warning("Unauthorized access to pnp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for pnp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'pnp':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('pnp', contact_no, municipality)).fetchone()
    conn.close()
    
    if not user:
        logger.warning("Unauthorized access to pnp_analytics. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = barangay_coords.get(municipality, [])
    return render_template('PNPAnalytics.html', municipality=municipality, current_datetime=current_datetime, barangays=barangays)

@app.route('/api/pnp_analytics_data', methods=['GET'])
def get_pnp_analytics_data():
    time_filter = request.args.get('time', 'weekly')
    trends = get_pnp_trends(time_filter)
    distribution = get_pnp_distribution(time_filter)
    causes_data = get_pnp_causes(time_filter)
    weather = {'Sunny': 10, 'Rainy': 5, 'Foggy': 2}
    road_conditions = {'Dry': 12, 'Wet': 4, 'Icy': 1}
    vehicle_types = {'Car': 8, 'Motorcycle': 6, 'Truck': 3}
    driver_age = {'18-25': 5, '26-35': 7, '36-50': 3, '51+': 2}
    driver_gender = {'Male': 12, 'Female': 5}
    accident_type = {'Collision': 10, 'Rollover': 4, 'Pedestrian': 3}
    injuries = [5, 3, 2, 1] * (len(trends['labels']) // 4 + 1)
    fatalities = [1, 0, 1, 0] * (len(trends['labels']) // 4 + 1)
    return jsonify({
        'trends': trends,
        'distribution': distribution,
        'causes': causes_data['road'],
        'weather': weather,
        'road_conditions': road_conditions,
        'vehicle_types': vehicle_types,
        'driver_age': driver_age,
        'driver_gender': driver_gender,
        'accident_type': accident_type,
        'injuries': injuries[:len(trends['labels'])],
        'fatalities': fatalities[:len(trends['labels'])]
    })

@app.route('/bfp/analytics')
def bfp_analytics():
    if 'role' not in session or session['role'] != 'bfp':
        logger.warning("Unauthorized access to bfp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    if not unique_id:
        logger.warning("No unique_id in session for bfp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    unique_id_parts = unique_id.split('_')
    logger.debug(f"unique_id: {unique_id}, parts: {unique_id_parts}")
    if len(unique_id_parts) != 3 or unique_id_parts[0] != 'bfp':
        logger.warning(f"Invalid unique_id format: {unique_id}")
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    municipality = unique_id_parts[1]
    contact_no = unique_id_parts[2]
    
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('bfp', contact_no, municipality)).fetchone()
    conn.close()
    
    if not user:
        logger.warning("Unauthorized access to bfp_analytics. Session: %s, User: %s", session, user)
        session.clear()
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = barangay_coords.get(municipality, [])
    return render_template('BFPAnalytics.html', municipality=municipality, current_datetime=current_datetime, barangays=barangays)

@app.route('/api/bfp_analytics_data', methods=['GET'])
def get_bfp_analytics_data():
    try:
        time_filter = request.args.get('time', 'weekly')
        barangay = request.args.get('barangay', '')
        trends = get_bfp_trends(time_filter, barangay)
        distribution = get_bfp_distribution(time_filter, barangay)
        causes = get_bfp_causes(time_filter, barangay)
        
        return jsonify({
            'trends': trends,
            'distribution': distribution,
            'causes': causes
        })
    except Exception as e:
        logger.error(f"Error in get_bfp_analytics_data: {e}")
        return jsonify({'error': 'Failed to retrieve analytics data'}), 500

if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                barangay TEXT,
                role TEXT NOT NULL,
                contact_no TEXT UNIQUE NOT NULL,
                assigned_municipality TEXT,
                province TEXT,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                barangay TEXT,
                emergency_type TEXT,
                lat REAL,
                lon REAL,
                house_no TEXT,
                street_no TEXT,
                image_classification TEXT,
                timestamp TEXT,
                forwarded_to TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                alert_id TEXT,
                barangay TEXT,
                road_accident_cause TEXT,
                road_accident_type TEXT,
                weather TEXT,
                road_condition TEXT,
                vehicle_type TEXT,
                driver_age TEXT,
                driver_gender TEXT,
                lat REAL,
                lon REAL,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database 'users_web.db' initialized successfully or already exists.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)