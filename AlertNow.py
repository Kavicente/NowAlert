from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file, make_response
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
from datetime import datetime, timedelta
import pytz
import pandas as pd
import uuid
from models import lr_road, lr_fire
from BarangayDashboard import get_barangay_stats, get_latest_alert
from CDRRMODashboard import get_cdrrmo_stats, get_latest_alert
from PNPDashboard import get_pnp_stats, get_latest_alert
from BFPDashboard import get_bfp_stats, get_latest_alert
from BarangayAnalytics import get_barangay_trends, get_barangay_distribution, get_barangay_causes, generate_mock_data
from CDRRMOAnalytics import get_cdrrmo_trends, get_cdrrmo_distribution, get_cdrrmo_causes
from PNPAnalytics import get_pnp_trends, get_pnp_distribution, get_pnp_causes
from BFPAnalytics import get_bfp_trends, get_bfp_distribution, get_bfp_causes
import random

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
    
fire_accident_predictor = None
try:
    fire_accident_predictor = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Fire Models', 'fire_predictor_lr.pkl'))
    logger.info("fire_predictor_lr.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("fire_predictor_lr.pkl not found.")
except Exception as e:
    logger.error(f"Error loading fire_predictor_lr.pkl: {e}")

road_accident_df = pd.DataFrame()
try:
    road_accident_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'road_accident.csv'))
    logger.info("Successfully loaded road_accident.csv")
except FileNotFoundError:
    logger.error("road_accident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading road_accident.csv: {e}")
    
fire_incident_df = pd.DataFrame()
try:
    fire_incident_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'fire_incident.csv'))
    logger.info("Successfully loaded fire_incident.csv")
except FileNotFoundError:
    logger.error("fire_incident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading fire_incident.csv: {e}")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*", max_http_buffer_size=10000000)

alerts = []
responses = []
today_responses = []

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_android_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'AlertNowLocal.db')
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

@app.route('/api/android_signup', methods=['POST'])
def android_signup():
    data = request.json
    conn = get_android_db_connection()
    try:
        username = data.get('username')
        password = data.get('password')
        role = data.get('role').lower()
        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name = data.get('last_name')
        age = data.get('age')
        contact_no = data.get('contact_no')
        house_no = data.get('house_no')
        street_no = data.get('street_no')
        barangay = data.get('barangay')
        municipality = data.get('municipality')
        province = data.get('province')
        position = data.get('position')
        synced = 1

        conn.execute('''
            INSERT INTO users (username, password, role, first_name, middle_name, last_name, age, contact_no, house_no, street_no, barangay, municipality, province, position, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, first_name, middle_name, last_name, age, contact_no, house_no, street_no, barangay, municipality, province, position, synced))
        conn.commit()
        logger.info(f"User {username} signed up successfully with role {role}")
        return jsonify({'message': 'Signup successful'})
    except Exception as e:
        logger.error(f"Signup failed for {username}: {e}")
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/android_login', methods=['POST'])
def android_login():
    data = request.json
    conn = get_android_db_connection()
    try:
        if 'username' in data:
            username = data['username']
            password = data['password']
            user = conn.execute('SELECT role, barangay, house_no, street_no FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            if user:
                logger.info(f"Login successful for username: {username}, role: {user['role']}")
                return jsonify({'role': user['role'], 'barangay': user['barangay'] or '', 'house_no': user['house_no'] or '', 'street_no': user['street_no'] or ''})
            else:
                logger.warning(f"Invalid credentials for username: {username}")
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            role = data['role'].lower()
            municipality = data['municipality']
            contact_no = data['contact_no']
            password = data['password']
            user = conn.execute('SELECT role, municipality FROM users WHERE role = ? AND municipality = ? AND contact_no = ? AND password = ?', 
                                (role, municipality, contact_no, password)).fetchone()
            if user:
                logger.info(f"Login successful for contact_no: {contact_no}, role: {user['role']}")
                return jsonify({'role': user['role'], 'municipality': user['municipality'] or ''})
            else:
                logger.warning(f"Invalid credentials for contact_no: {contact_no}, role: {role}")
                return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ?',
                             ('admin', username, password)).fetchone()
        conn.close()
        if admin:
            session['role'] = 'admin'
            session['unique_id'] = f"admin_{username}"
            session.permanent = True
            logger.info(f"Admin login successful for {username}")
            return redirect(url_for('admin_dashboard'))
        logger.warning(f"Invalid admin credentials for {username}")
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        logger.warning("Unauthorized access to admin_dashboard")
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE role != "admin"').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if 'role' not in session or session['role'] != 'admin':
        logger.warning("Unauthorized access to admin_create_user")
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    role = data.get('role').lower()
    contact_no = data.get('contact_no')
    password = data.get('password')
    barangay = data.get('barangay') if role == 'barangay' else None
    municipality = data.get('municipality') if role in ['pnp', 'cdrrmo', 'bfp'] else None
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (role, contact_no, password, barangay, assigned_municipality) VALUES (?, ?, ?, ?, ?)',
                    (role, contact_no, password, barangay, municipality))
        conn.commit()
        logger.info(f"User created with contact_no: {contact_no}, role: {role}")
    except sqlite3.IntegrityError:
        conn.close()
        logger.error(f"User creation failed, contact_no {contact_no} already exists")
        return jsonify({'error': 'User already exists'}), 400
    conn.close()
    return jsonify({'message': 'User created successfully'})

@app.route('/admin/delete_user/<contact_no>', methods=['POST'])
def admin_delete_user(contact_no):
    if 'role' not in session or session['role'] != 'admin':
        logger.warning("Unauthorized access to admin_delete_user")
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE contact_no = ?', (contact_no,))
    conn.commit()
    conn.close()
    logger.info(f"User deleted with contact_no: {contact_no}")
    return jsonify({'message': 'User deleted successfully'})

def add_response(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON response: {data}")
            return
    today_responses.append(data)

@socketio.on('response')
def handle_response(data):
    try:
        logger.info(f"Received response: {data}")
        response = data if isinstance(data, dict) else json.loads(data)
        response['timestamp'] = datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        response['responded'] = True
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'AlertNowLocal.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('INSERT INTO responses (data, synced) VALUES (?, 0)', (json.dumps(response),))
        conn.commit()
        conn.close()
        today_responses.append(response)
        emit('response_received', {
            'barangay_data': get_barangay_trends('today', response.get('barangay')),
            'cdrrmo_data': get_cdrrmo_trends('today', response.get('municipality')),
            'pnp_data': get_pnp_trends('today', response.get('municipality')),
            'bfp_data': get_bfp_trends('today', response.get('municipality')),
            'barangay_distribution': get_barangay_distribution('today', response.get('barangay')),
            'cdrrmo_distribution': get_cdrrmo_distribution('today', response.get('municipality')),
            'pnp_distribution': get_pnp_distribution('today', response.get('municipality')),
            'bfp_distribution': get_bfp_distribution('today', response.get('municipality')),
            'barangay_causes': get_barangay_causes('today', response.get('barangay')),
            'cdrrmo_causes': get_cdrrmo_causes('today', response.get('municipality')),
            'pnp_causes': get_pnp_causes('today', response.get('municipality')),
            'bfp_causes': get_bfp_causes('today', response.get('municipality')),
            'accident_type': get_accident_type('today', response.get('barangay'), response.get('municipality')),
            'road_condition': get_road_condition('today', response.get('barangay'), response.get('municipality'))
        }, broadcast=True)
    except Exception as e:
        logger.error(f"Error in handle_response: {e}")
    
def get_accident_type(time_filter, barangay=None, municipality=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            accident_types = Counter()
            from AlertNow import today_responses
            for response in today_responses:
                if isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON response: {response}")
                        continue
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('emergency_type', '') == 'Road Accident':
                    if (barangay is None or response.get('barangay', '').lower() == barangay.lower()) or \
                       (municipality is None or response.get('municipality', '').lower() == municipality.lower()):
                        accident_types[response.get('road_accident_type', 'Unknown')] += 1
            return dict(accident_types)
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            accident_types = Counter()
            for record in mock_data:
                if isinstance(record, str):
                    try:
                        record = json.loads(record)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON record: {record}")
                        continue
                if record.get('emergency_type', '') == 'Road Accident':
                    if (barangay is None or record.get('barangay', '').lower() == barangay.lower()) or \
                       (municipality is None or record.get('municipality', '').lower() == municipality.lower()):
                        accident_types[record.get('road_accident_type', 'Unknown')] += 1
            return dict(accident_types)
    except Exception as e:
        logger.error(f"Error in get_accident_type: {e}")
        return {'Unknown': 0}

# New function get_road_condition
def get_road_condition(time_filter, barangay=None, municipality=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            road_conditions = Counter()
            from AlertNow import today_responses
            for response in today_responses:
                if isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON response: {response}")
                        continue
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('emergency_type', '') == 'Road Accident':
                    if (barangay is None or response.get('barangay', '').lower() == barangay.lower()) or \
                       (municipality is None or response.get('municipality', '').lower() == municipality.lower()):
                        road_conditions[response.get('road_condition', 'Unknown')] += 1
            return dict(road_conditions)
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            road_conditions = Counter()
            for record in mock_data:
                if isinstance(record, str):
                    try:
                        record = json.loads(record)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON record: {record}")
                        continue
                if record.get('emergency_type', '') == 'Road Accident':
                    if (barangay is None or record.get('barangay', '').lower() == barangay.lower()) or \
                       (municipality is None or record.get('municipality', '').lower() == municipality.lower()):
                        road_conditions[record.get('road_condition', 'Unknown')] += 1
            return dict(road_conditions)
    except Exception as e:
        logger.error(f"Error in get_road_condition: {e}")
        return {'Unknown': 0}   

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('register_role')
def handle_register_role(data):
    role = data.get('role')
    if role == 'barangay':
        barangay = data.get('barangay').lower() if data.get('barangay') else None
        if barangay:
            join_room(f"barangay_{barangay}")
            logger.info(f"Client {request.sid} joined room barangay_{barangay}")
    elif role == 'cdrrmo':
        municipality = data.get('municipality').lower() if data.get('municipality') else None
        if municipality:
            join_room(f"cdrrmo_{municipality}")
            logger.info(f"Client {request.sid} joined room cdrrmo_{municipality}")
    elif role == 'pnp':
        municipality = data.get('municipality').lower() if data.get('municipality') else None
        if municipality:
            join_room(f"pnp_{municipality}")
            logger.info(f"Client {request.sid} joined room pnp_{municipality}")
    elif role == 'bfp':
        municipality = data.get('municipality').lower() if data.get('municipality') else None
        if municipality:
            join_room(f"bfp_{municipality}")
            logger.info(f"Client {request.sid} joined room bfp_{municipality}")

@socketio.on('alert')
def handle_new_alert(data):
    logger.info(f"New alert received: {data}")
    alert_id = str(uuid.uuid4())
    data['alert_id'] = alert_id
    data['timestamp'] = datetime.utcnow().isoformat()
    data['resident_barangay'] = data.get('barangay', 'Unknown')
    
    # Classify image if present
    image_classification = 'no_image'
    if 'image' in data:
        try:
            image_classification = classify_image(data['image'])
        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            image_classification = 'classification_error'
    data['image_classification'] = image_classification

    alerts.append(data)

    # Emit to relevant rooms
    barangay_room = f"barangay_{data.get('barangay').lower() if data.get('barangay') else ''}"
    municipality = get_municipality_from_barangay(data.get('barangay'))
    if municipality:
        municipality = municipality.lower()
        cdrrmo_room = f"cdrrmo_{municipality}"
        pnp_room = f"pnp_{municipality}"
        bfp_room = f"bfp_{municipality}"
    else:
        logger.warning(f"Municipality not found for barangay: {data.get('barangay')}")
        cdrrmo_room = None
        pnp_room = None
        bfp_room = None
    
    emit('new_alert', data, room=barangay_room)
    logger.info(f"Alert emitted to room {barangay_room}")
    if cdrrmo_room:
        emit('new_alert', data, room=cdrrmo_room)
        logger.info(f"Alert emitted to room {cdrrmo_room}")
    if pnp_room:
        emit('new_alert', data, room=pnp_room)
        logger.info(f"Alert emitted to room {pnp_room}")
    if bfp_room:
        emit('new_alert', data, room=bfp_room)
        logger.info(f"Alert emitted to room {bfp_room}")

    # Emit update_map to relevant rooms
    map_data = {
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'barangay': data.get('barangay'),
        'emergency_type': data.get('emergency_type')
    }
    emit('update_map', map_data, room=barangay_room)
    if cdrrmo_room:
        emit('update_map', map_data, room=cdrrmo_room)
    if pnp_room:
        emit('update_map', map_data, room=pnp_room)
    if bfp_room:
        emit('update_map', map_data, room=bfp_room)    

@socketio.on('forward_alert')
def handle_forward_alert(data):
    logger.info(f"Forward alert received: {data}")
    municipality = get_municipality_from_barangay(data.get('barangay'))
    if municipality:
        municipality = municipality.lower()
    else:
        logger.warning(f"Municipality not found for barangay in forward: {data.get('barangay')}")
        return  # Skip if no municipality
    
    cdrrmo_room = f"cdrrmo_{municipality}"
    pnp_room = f"pnp_{municipality}"
    bfp_room = f"bfp_{municipality}"
    
    emit('new_alert', data, room=cdrrmo_room)
    logger.info(f"Alert forwarded to room {cdrrmo_room}")
    emit('new_alert', data, room=pnp_room)
    logger.info(f"Alert forwarded to room {pnp_room}")
    emit('new_alert', data, room=bfp_room)
    logger.info(f"Alert forwarded to room {bfp_room}")

    map_data = {
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'barangay': data.get('barangay'),
        'emergency_type': data.get('emergency_type')
    }
    emit('update_map', map_data, room=cdrrmo_room)
    emit('update_map', map_data, room=pnp_room)
    emit('update_map', map_data, room=bfp_room)

@socketio.on('barangay_response')
def handle_barangay_response_submitted(data):
    logger.info(f"Barangay response received: {data}")
    data['timestamp'] = datetime.now(pytz.UTC).isoformat()
    
    # Check if response is today for analytics
    response_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
    today = datetime.now(pytz.timezone('Asia/Manila')).date()
    if response_time.date() == today:
        today_responses.append(data)
    
    # Compute prediction using ML model on form data
    try:
        # Default values for expected model features
        default_values = {
            'Year': datetime.now().year,
            'Barangay': data.get('barangay', 'Unknown'),
            'Road_Accident_Type': 'Overspeeding',
            'Accident_Cause': 'Head-on collision'
        }
        
        # Map input values to dataset categories
        type_mapping = {
            'collision': 'Head-on collision',
            'head-on collision': 'Head-on collision',
            'rear-end collision': 'Rear-end collision',
            'side-impact collision': 'Side-impact collision',
            'single vehicle accident': 'Single vehicle accident',
            'pedestrian accident': 'Pedestrian accident'
        }
        cause_mapping = {
            'speeding': 'Overspeeding',
            'overspeeding': 'Overspeeding',
            'drunk driving': 'Drunk Driving',
            'reckless driving': 'Reckless Driving',
            'overloading': 'Overloading',
            'fatigue': 'Fatigue',
            'distracted driving': 'Distracted Driving',
            'poor maintenance': 'Poor Maintenance',
            'mechanical failure': 'Mechanical Failure',
            'inexperience': 'Inexperience'
        }
        
        # Validate and clean input data
        cleaned_data = {}
        for key in default_values:
            if key == 'Year':
                cleaned_data[key] = default_values[key]
            elif key == 'Barangay':
                cleaned_data[key] = data.get('barangay', default_values[key])
            elif key == 'Road_Accident_Type':
                cleaned_data[key] = cause_mapping.get(data.get('road_accident_type', '').lower(), default_values[key])
            elif key == 'Accident_Cause':
                cleaned_data[key] = type_mapping.get(data.get('cause', '').lower(), default_values[key])
        
        # Prepare DataFrame for prediction
        input_df = pd.DataFrame([cleaned_data])
        
        # Ensure all expected columns are present
        expected_columns = road_accident_df.columns
        for col in expected_columns:
            if col not in input_df.columns:
                input_df[col] = 0
        
        # Reorder columns to match training data
        input_df = input_df[expected_columns]
        
        # Make prediction
        if road_accident_predictor:
            prediction = road_accident_predictor.predict_proba(input_df)[:, 1][0] * 100
            data['prediction'] = f"{prediction:.2f}% chance in year {datetime.now().year}"
            logger.info(f"Prediction for barangay response: {data['prediction']}")
        else:
            data['prediction'] = 'prediction_error'
            logger.error("Road accident predictor not loaded")
    except Exception as e:
        data['prediction'] = 'prediction_error'
        logger.error(f"Error in prediction for barangay response: {e}")
    
    responses.append(data)
    
    # Emit response to barangay room
    barangay_room = f"barangay_{data.get('barangay').lower() if data.get('barangay') else ''}"
    emit('barangay_response', data, room=barangay_room)
    logger.info(f"Barangay response emitted to room {barangay_room}")

@socketio.on('cdrrmo_response')
def handle_cdrrmo_response_submitted(data):
    try:
        logger.info(f"CDRRMO response received: {data}")
        municipality = data.get('municipality', '').lower()
        barangay = data.get('barangay', '').lower()
        response = {
            'alert_id': str(uuid.uuid4()),
            'role': data.get('role', 'cdrrmo'),
            'municipality': municipality,
            'emergency_type': data.get('emergency_type', 'N/A'),
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'responded': data.get('responded', True),
            'weather': data.get('weather', 'N/A'),
            'road_condition': data.get('road_condition', 'N/A'),
            'vehicle_type': data.get('vehicle_type', 'N/A'),
            'driver_age': data.get('driver_age', 'N/A'),
            'driver_gender': data.get('driver_gender', 'N/A'),
            'road_accident_type': data.get('accident_type', 'N/A'),
            'cause': data.get('cause', 'N/A'),
            'lat': data.get('lat', 0.0),
            'lon': data.get('lon', 0.0),
            'barangay': barangay,
            'house_no': data.get('house_no', 'N/A'),
            'street_no': data.get('street_no', 'N/A')
        }
        # Check if response is today for analytics
        response_time = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
        today = datetime.now(pytz.timezone('Asia/Manila')).date()
        if response_time.date() == today:
            today_responses.append(response)
        # Compute prediction using ML model on form data
        try:
            # Default values for expected model features
            default_values = {
                'Year': datetime.now().year,
                'Barangay': response.get('barangay', 'Unknown'),
                'Road_Accident_Type': 'Overspeeding',
                'Accident_Cause': 'Head-on collision'
            }
            # Map input values to dataset categories
            type_mapping = {
                'collision': 'Head-on collision',
                'head-on collision': 'Head-on collision',
                'rear-end collision': 'Rear-end collision',
                'side-impact collision': 'Side-impact collision',
                'single vehicle accident': 'Single vehicle accident',
                'pedestrian accident': 'Pedestrian accident'
            }
            cause_mapping = {
                'speeding': 'Overspeeding',
                'overspeeding': 'Overspeeding',
                'drunk driving': 'Drunk Driving',
                'reckless driving': 'Reckless Driving',
                'overloading': 'Overloading',
                'fatigue': 'Fatigue',
                'distracted driving': 'Distracted Driving',
                'poor maintenance': 'Poor Maintenance',
                'mechanical failure': 'Mechanical Failure',
                'inexperience': 'Inexperience'
            }
            # Validate and clean input data
            cleaned_data = {}
            for key in default_values:
                if key == 'Year':
                    cleaned_data[key] = default_values[key]
                elif key == 'Barangay':
                    cleaned_data[key] = response.get('barangay', default_values[key])
                elif key == 'Road_Accident_Type':
                    cleaned_data[key] = cause_mapping.get(response.get('road_accident_type', '').lower(), default_values[key])
                elif key == 'Accident_Cause':
                    cleaned_data[key] = type_mapping.get(response.get('cause', '').lower(), default_values[key])
            # Prepare DataFrame for prediction
            input_df = pd.DataFrame([cleaned_data])
            # Ensure all expected columns are present
            expected_columns = road_accident_df.columns
            for col in expected_columns:
                if col not in input_df.columns:
                    input_df[col] = 0
            # Reorder columns to match training data
            input_df = input_df[expected_columns]
            # Make prediction
            if road_accident_predictor:
                prediction = road_accident_predictor.predict_proba(input_df)[:, 1][0] * 100
                response['prediction'] = f"{prediction:.2f}% chance in year {datetime.now().year}"
                logger.info(f"Prediction for CDRRMO response: {response['prediction']}")
            else:
                response['prediction'] = 'prediction_error'
                logger.error("Road accident predictor not loaded")
        except Exception as e:
            response['prediction'] = 'prediction_error'
            logger.error(f"Prediction error for CDRRMO response: {e}")
        responses.append(response)
        socketio.emit('cdrrmo_response', response, room=f'cdrrmo_{municipality}')
        socketio.emit('update_analytics', response, room=f'cdrrmo_{municipality}')
        logger.info(f"Analytics update emitted to cdrrmo_{municipality}")
        socketio.emit('stats_update', {
            'total_alerts': len(alerts),
            'today_alerts': len([a for a in alerts if a.get('timestamp', '').startswith(datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d'))]),
            'today_responses': len(today_responses)
        }, room=f'cdrrmo_{municipality}')
        logger.info(f"CDRRMO response processed and emitted to cdrrmo_{municipality}")
    except Exception as e:
        logger.error(f"Error processing CDRRMO response: {e}")

# Updated handle_pnp_response_submitted
@socketio.on('pnp_response')
def handle_pnp_response_submitted(data):
    try:
        logger.info(f"PNP response received: {data}")
        municipality = data.get('municipality', '').lower()
        barangay = data.get('barangay', '').lower()
        response = {
            'alert_id': str(uuid.uuid4()),
            'role': data.get('role', 'pnp'),
            'municipality': municipality,
            'emergency_type': data.get('emergency_type', 'N/A'),
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'responded': data.get('responded', True),
            'weather': data.get('weather', 'N/A'),
            'road_condition': data.get('road_condition', 'N/A'),
            'vehicle_type': data.get('vehicle_type', 'N/A'),
            'driver_age': data.get('driver_age', 'N/A'),
            'driver_gender': data.get('driver_gender', 'N/A'),
            'road_accident_type': data.get('accident_type', 'N/A'),
            'cause': data.get('cause', 'N/A'),
            'lat': data.get('lat', 0.0),
            'lon': data.get('lon', 0.0),
            'barangay': barangay,
            'house_no': data.get('house_no', 'N/A'),
            'street_no': data.get('street_no', 'N/A')
        }
        # Check if response is today for analytics
        response_time = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
        today = datetime.now(pytz.timezone('Asia/Manila')).date()
        if response_time.date() == today:
            today_responses.append(response)
        # Compute prediction using ML model on form data
        try:
            # Default values for expected model features
            default_values = {
                'Year': datetime.now().year,
                'Barangay': response.get('barangay', 'Unknown'),
                'Road_Accident_Type': 'Overspeeding',
                'Accident_Cause': 'Head-on collision'
            }
            # Map input values to dataset categories
            type_mapping = {
                'collision': 'Head-on collision',
                'head-on collision': 'Head-on collision',
                'rear-end collision': 'Rear-end collision',
                'side-impact collision': 'Side-impact collision',
                'single vehicle accident': 'Single vehicle accident',
                'pedestrian accident': 'Pedestrian accident'
            }
            cause_mapping = {
                'speeding': 'Overspeeding',
                'overspeeding': 'Overspeeding',
                'drunk driving': 'Drunk Driving',
                'reckless driving': 'Reckless Driving',
                'overloading': 'Overloading',
                'fatigue': 'Fatigue',
                'distracted driving': 'Distracted Driving',
                'poor maintenance': 'Poor Maintenance',
                'mechanical failure': 'Mechanical Failure',
                'inexperience': 'Inexperience'
            }
            # Validate and clean input data
            cleaned_data = {}
            for key in default_values:
                if key == 'Year':
                    cleaned_data[key] = default_values[key]
                elif key == 'Barangay':
                    cleaned_data[key] = response.get('barangay', default_values[key])
                elif key == 'Road_Accident_Type':
                    cleaned_data[key] = cause_mapping.get(response.get('road_accident_type', '').lower(), default_values[key])
                elif key == 'Accident_Cause':
                    cleaned_data[key] = type_mapping.get(response.get('cause', '').lower(), default_values[key])
            # Prepare DataFrame for prediction
            input_df = pd.DataFrame([cleaned_data])
            # Ensure all expected columns are present
            expected_columns = road_accident_df.columns
            for col in expected_columns:
                if col not in input_df.columns:
                    input_df[col] = 0
            # Reorder columns to match training data
            input_df = input_df[expected_columns]
            # Make prediction
            if road_accident_predictor:
                prediction = road_accident_predictor.predict_proba(input_df)[:, 1][0] * 100
                response['prediction'] = f"{prediction:.2f}% chance in year {datetime.now().year}"
                logger.info(f"Prediction for PNP response: {response['prediction']}")
            else:
                response['prediction'] = 'prediction_error'
                logger.error("Road accident predictor not loaded")
        except Exception as e:
            response['prediction'] = 'prediction_error'
            logger.error(f"Prediction error for PNP response: {e}")
        responses.append(response)
        socketio.emit('pnp_response', response, room=f'pnp_{municipality}')
        socketio.emit('update_analytics', response, room=f'pnp_{municipality}')
        logger.info(f"Analytics update emitted to pnp_{municipality}")
        socketio.emit('stats_update', {
            'total_alerts': len(alerts),
            'today_alerts': len([a for a in alerts if a.get('timestamp', '').startswith(datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d'))]),
            'today_responses': len(today_responses)
        }, room=f'pnp_{municipality}')
        logger.info(f"PNP response processed and emitted to pnp_{municipality}")
    except Exception as e:
        logger.error(f"Error processing PNP response: {e}")

@socketio.on('fire_response_submitted')
def handle_fire_response_submitted(data):
    logger.info(f"Received fire response: {data}")
    logger.debug(f"Processing fire response for alert_id: {data.get('alert_id')}")
    default_values = {}
    ftype_mapping = {
        'Electrical Fire': 1,
        'Grass Fire': 2,
        'Residential Fire': 3,
        'Natural Fire': 4,
        'Other Fire': 5
    }
    fcause_mapping = {
        'Arson': 1,
        'Cooking': 2,
        'Electrical': 3,
        'Natural': 4
    }
    cleaned_data = {
        'alert_id': data.get('alert_id'),  # Ensure alert_id is included
        'fire_type': ftype_mapping.get(data.get('fire_type'), 0),
        'fire_cause': fcause_mapping.get(data.get('fire_cause'), 0),
        'weather': data.get('weather', 'Unknown'),
        'fire_severity': data.get('fire_severity', 'Unknown'),
        'lat': data.get('lat', 0.0),
        'lon': data.get('lon', 0.0),
        'barangay': data.get('barangay', 'Unknown'),
        'emergency_type': data.get('emergency_type', 'Unknown')
    }
    cleaned_data.update(default_values)
    
    try:
        if fire_accident_predictor:
            feature_names = ['Fire_Type', 'Fire_Cause', 'Barangay', 'Year']
            features = pd.DataFrame([[
                cleaned_data['fire_type'],
                cleaned_data['fire_cause'],
                cleaned_data['barangay'],
                datetime.now().year
            ]], columns=feature_names)
            prediction = fire_accident_predictor.predict(features)[0]
            probability = fire_accident_predictor.predict_proba(features)[0][1]
            cleaned_data['prediction'] = f"{probability*100:.2f}% chance in year {datetime.now().year + 1}"
        else:
            cleaned_data['prediction'] = 'prediction_error'
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        cleaned_data['prediction'] = 'prediction_error'
    
    responses.append(cleaned_data)
    today_responses.append(cleaned_data)
    municipality = get_municipality_from_barangay(cleaned_data['barangay'])
    if not municipality:
        logger.error(f"No municipality found for barangay: {cleaned_data['barangay']}")
        municipality = 'unknown'
    bfp_room = f"bfp_{municipality.lower()}"
    emit('fire_response_submitted', cleaned_data, room=bfp_room)
    logger.info(f"Fire response broadcasted to room {bfp_room}: {cleaned_data}")
    
def handle_road_analytics_data(time_filter, municipality, barangays, role='barangay'):
    try:
        weather = {'Sunny': 0, 'Rainy': 0, 'Foggy': 0, 'Cloudy': 0}
        road_conditions = {'Dry': 0, 'Wet': 0, 'Icy': 0, 'Snowy': 0}
        vehicle_types = {'Car': 0, 'Motorcycle': 0, 'Truck': 0, 'Bus': 0}
        driver_age = {'18-25': 0, '26-35': 0, '36-50': 0, '51+': 0}
        driver_gender = {'Male': 0, 'Female': 0}
        accident_type = {'Head-on collision': 0, 'Rear-end collision': 0, 'Side-impact collision': 0, 'Single vehicle accident': 0, 'Pedestrian accident': 0}
        accident_cause = {'Overspeeding': 0, 'Drunk Driving': 0, 'Reckless Driving': 0, 'Overloading': 0, 'Fatigue': 0, 'Distracted Driving': 0, 'Poor Maintenance': 0, 'Mechanical Failure': 0, 'Inexperience': 0}
        injuries = [0] * 24
        fatalities = [0] * 24

        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if (response_time.date() == today and 
                    response.get('role', '').lower() == role.lower() and 
                    response.get('emergency_type', '') == 'Road Accident' and
                    response.get('barangay', '') in barangays and
                    response.get('municipality', '').lower() == municipality.lower()):
                    weather[response.get('weather', 'Unknown')] = weather.get(response.get('weather', 'Unknown'), 0) + 1
                    road_conditions[response.get('road_condition', 'Unknown')] = road_conditions.get(response.get('road_condition', 'Unknown'), 0) + 1
                    vehicle_types[response.get('vehicle_type', 'Unknown')] = vehicle_types.get(response.get('vehicle_type', 'Unknown'), 0) + 1
                    driver_age[response.get('driver_age', 'Unknown')] = driver_age.get(response.get('driver_age', 'Unknown'), 0) + 1
                    driver_gender[response.get('driver_gender', 'Unknown')] = driver_gender.get(response.get('driver_gender', 'Unknown'), 0) + 1
                    accident_type[response.get('road_accident_type', 'Unknown')] = accident_type.get(response.get('road_accident_type', 'Unknown'), 0) + 1
                    accident_cause[response.get('cause', 'Unknown')] = accident_cause.get(response.get('cause', 'Unknown'), 0) + 1
                    hour = response_time.hour
                    injuries[hour] += response.get('injuries', 0)
                    fatalities[hour] += response.get('fatalities', 0)
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            for record in mock_data:
                if (record.get('role', '').lower() == role.lower() and 
                    record.get('emergency_type', '') == 'Road Accident' and
                    record.get('barangay', '') in barangays and
                    record.get('municipality', '').lower() == municipality.lower()):
                    weather[record.get('weather', 'Unknown')] = weather.get(record.get('weather', 'Unknown'), 0) + 1
                    road_conditions[record.get('road_condition', 'Unknown')] = road_conditions.get(record.get('road_condition', 'Unknown'), 0) + 1
                    vehicle_types[record.get('vehicle_type', 'Unknown')] = vehicle_types.get(record.get('vehicle_type', 'Unknown'), 0) + 1
                    driver_age[record.get('driver_age', 'Unknown')] = driver_age.get(record.get('driver_age', 'Unknown'), 0) + 1
                    driver_gender[record.get('driver_gender', 'Unknown')] = driver_gender.get(record.get('driver_gender', 'Unknown'), 0) + 1
                    accident_type[record.get('road_accident_type', 'Unknown')] = accident_type.get(record.get('road_accident_type', 'Unknown'), 0) + 1
                    accident_cause[record.get('cause', 'Unknown')] = accident_cause.get(record.get('cause', 'Unknown'), 0) + 1
                    injuries[0] += record.get('injuries', 0)
                    fatalities[0] += record.get('fatalities', 0)

        return {
            'weather': weather,
            'road_conditions': road_conditions,
            'vehicle_types': vehicle_types,
            'driver_age': driver_age,
            'driver_gender': driver_gender,
            'accident_type': accident_type,
            'accident_cause': accident_cause,
            'injuries': injuries,
            'fatalities': fatalities
        }
    except Exception as e:
        logger.error(f"Error in handle_road_analytics_data: {e}")
        return {
            'weather': {'Sunny': 0, 'Rainy': 0, 'Foggy': 0, 'Cloudy': 0},
            'road_conditions': {'Dry': 0, 'Wet': 0, 'Icy': 0, 'Snowy': 0},
            'vehicle_types': {'Car': 0, 'Motorcycle': 0, 'Truck': 0, 'Bus': 0},
            'driver_age': {'18-25': 0, '26-35': 0, '36-50': 0, '51+': 0},
            'driver_gender': {'Male': 0, 'Female': 0},
            'accident_type': {'Head-on collision': 0, 'Rear-end collision': 0, 'Side-impact collision': 0, 'Single vehicle accident': 0, 'Pedestrian accident': 0},
            'accident_cause': {'Overspeeding': 0, 'Drunk Driving': 0, 'Reckless Driving': 0, 'Overloading': 0, 'Fatigue': 0, 'Distracted Driving': 0, 'Poor Maintenance': 0, 'Mechanical Failure': 0, 'Inexperience': 0},
            'injuries': [0] * 24,
            'fatalities': [0] * 24
        }

# Added handle_fire_analytics_data
def handle_fire_analytics_data(time_filter, municipality, barangays, role='barangay'):
    try:
        weather = {'Sunny': 0, 'Rainy': 0, 'Foggy': 0, 'Cloudy': 0}
        property_types = {'Residential': 0, 'Commercial': 0, 'Industrial': 0, 'Other': 0}

        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if (response_time.date() == today and 
                    response.get('role', '').lower() == role.lower() and 
                    response.get('emergency_type', '') == 'Fire' and
                    response.get('barangay', '') in barangays and
                    response.get('municipality', '').lower() == municipality.lower()):
                    weather[response.get('weather', 'Unknown')] = weather.get(response.get('weather', 'Unknown'), 0) + 1
                    property_types[response.get('property_type', 'Unknown')] = property_types.get(response.get('property_type', 'Unknown'), 0) + 1
        else:
            mock_data = generate_mock_data(time_filter, 'fire')
            for record in mock_data:
                if (record.get('role', '').lower() == role.lower() and 
                    record.get('emergency_type', '') == 'Fire' and
                    record.get('barangay', '') in barangays and
                    record.get('municipality', '').lower() == municipality.lower()):
                    weather[record.get('weather', 'Unknown')] = weather.get(record.get('weather', 'Unknown'), 0) + 1
                    property_types[record.get('property_type', 'Unknown')] = property_types.get(record.get('property_type', 'Unknown'), 0) + 1

        return {
            'weather': weather,
            'property_types': property_types
        }
    except Exception as e:
        logger.error(f"Error in handle_fire_analytics_data: {e}")
        return {
            'weather': {'Sunny': 0, 'Rainy': 0, 'Foggy': 0, 'Cloudy': 0},
            'property_types': {'Residential': 0, 'Commercial': 0, 'Industrial': 0, 'Other': 0}
        }

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyBSXRZPDX1x1d91Ck-pskiwGA8Y2-5gDVs')
barangay_coords = {}
try:
    with open(os.path.join(os.path.dirname(__file__), 'assets', 'coords.txt'), 'r') as f:
        barangay_coords = ast.literal_eval(f.read())
except FileNotFoundError:
    logger.error("coords.txt not found in assets directory. Using empty dict.")
except Exception as e:
    logger.error(f"Error loading coords.txt: {e}. Using empty dict.")

municipality_coords = {
    "San Pablo City": {"lat": 14.0642, "lon": 121.3233},
    "Quezon Province": {"lat": 13.9347, "lon": 121.9473},
}

def get_db_connection():
    db_path = os.path.join('/database', 'users_web.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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
    db_path = os.path.join('/database', 'users_web.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    if not os.path.exists(db_path):
        return "Database file not found", 404
    logger.debug(f"Serving database from: {db_path}")
    return send_file(db_path, as_attachment=True, download_name='users_web.db')

@app.route('/download_android_db', methods=['GET'])
def download_android_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'AlertNowLocal.db')
    if not os.path.exists(db_path):
        return "Database file not found", 404
    logger.debug(f"Serving Android database from: {db_path}")
    return send_file(db_path, as_attachment=True, download_name='AlertNowLocal.db')

def construct_unique_id(role, barangay=None, assigned_municipality=None, contact_no=None):
    if role == 'barangay':
        return f"{barangay}_{contact_no}"
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
        unique_id = construct_unique_id('barangay', barangay=barangay, contact_no=contact_no)
        
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug("Accessing /login with method: %s", request.method)
    if request.method == 'POST':
        barangay = request.form['barangay']
        contact_no = request.form['contact_no']
        password = request.form['password']
        unique_id = construct_unique_id('barangay', barangay=barangay, contact_no=contact_no)
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE barangay = ? AND contact_no = ? AND password = ?
        ''', (barangay, contact_no, password)).fetchone()
        conn.close()
        
        if user:
            session['unique_id'] = unique_id
            session['role'] = user['role']
            logger.debug(f"Web login successful for barangay: {unique_id}")
            return redirect(url_for('barangay_dashboard'))
        logger.warning(f"Web login failed for unique_id: {unique_id}")
        return "Invalid credentials", 401
    return render_template('LogInPage.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    barangay = data.get('barangay')
    contact_no = data.get('contact_no')
    password = data.get('password')
    unique_id = construct_unique_id('barangay', barangay=barangay, contact_no=contact_no)
    
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE barangay = ? AND contact_no = ? AND password = ?
    ''', (barangay, contact_no, password)).fetchone()
    conn.close()
    
    if user:
        logger.debug(f"API login successful for user: {unique_id} with role: {user['role']}")
        return jsonify({'status': 'success', 'role': user['role']})
    logger.warning(f"API login failed for unique_id: {unique_id}")
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/signup_cdrrmo_pnp_bfp', methods=['GET', 'POST'])
def signup_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        role = request.form['role'].lower()
        assigned_municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        unique_id = construct_unique_id(role, assigned_municipality=assigned_municipality, contact_no=contact_no)
        
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

@app.route('/login_cdrrmo_pnp_bfp', methods=['GET', 'POST'])
def login_cdrrmo_pnp_bfp():
    logger.debug("Accessing /login_cdrrmo_pnp_bfp with method: %s", request.method)
    if request.method == 'POST':
        role = request.form['role'].lower()
        if 'role' not in request.form:
            logger.error("Role field is missing in the form data")
            return "Role is required", 400
        assigned_municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        
        if role not in ['cdrrmo', 'pnp', 'bfp']:
            logger.error(f"Invalid role provided: {role}")
            return "Invalid role", 400
        
        logger.debug(f"Login attempt: role={role}, municipality={assigned_municipality}, contact_no={contact_no}")
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ?
        ''', (role, contact_no, password, assigned_municipality)).fetchone()
        conn.close()
        
        if user:
            unique_id = construct_unique_id(user['role'], assigned_municipality=assigned_municipality, contact_no=contact_no)
            session['unique_id'] = unique_id
            session['role'] = user['role']
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

@app.route('/login', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            session['role'] = user['role']
            session['barangay'] = user['barangay']
            if user['role'] == 'official':
                return redirect(url_for('barangay_dashboard'))
            elif user['role'] == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif user['role'] == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif user['role'] == 'bfp':
                return redirect(url_for('bfp_dashboard'))
        return "Invalid credentials", 401
    return render_template('LoginPage.html')

@app.route('/signup', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        barangay = request.form['barangay']
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, barangay, role, password) VALUES (?, ?, ?, ?)',
                         (username, barangay, 'official', password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        finally:
            conn.close()
    return render_template('SignUpPage.html')

@app.route('/go_to_login_page', methods=['GET'])
def go_to_login_page():
    logger.debug("Redirecting to /login")
    return redirect(url_for('login'))

@app.route('/go_to_signup_type', methods=['GET'])
def go_to_signup_type():
    logger.debug("Redirecting to /")
    return redirect(url_for('home'))

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

def load_coords():
    coords_path = os.path.join(app.root_path, 'assets', 'coords.txt')
    alerts_data = []
    try:
        with open(coords_path, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        barangay, municipality, message, timestamp = parts
                        alerts_data.append({
                            "barangay": barangay.strip(),
                            "municipality": municipality.strip(),
                            "message": message.strip(),
                            "timestamp": timestamp.strip()
                        })
    except FileNotFoundError:
        logger.warning("coords.txt not found, using empty alerts.")
    except Exception as e:
        logger.error(f"Error loading coords.txt: {e}")
    return alerts_data

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
            if prediction not in ['road_accident', 'fire_incident']:
                alert['image'] = None

        alerts.append(alert)
        socketio.emit('new_alert', alert)
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
    new_alert = {
        "barangay": data['barangay'],
        "municipality": data['municipality'],
        "message": data['message'],
        "timestamp": data['timestamp']
    }
    alerts.append(new_alert)
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
    try:
        if 'role' not in session or session['role'] != 'barangay':
            return redirect(url_for('login'))
        stats = get_barangay_stats()
        unique_id = session.get('unique_id')
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE barangay = ? AND contact_no = ?
        ''', (unique_id.split('_')[0], unique_id.split('_')[1])).fetchone()
        conn.close()
        
        if not unique_id or not user or user['role'] != 'barangay':
            logger.warning("Unauthorized access to barangay_dashboard. Session: %s, User: %s", session, user)
            return redirect(url_for('login'))
        
        barangay = user['barangay']
        assigned_municipality = user['assigned_municipality'] or 'San Pablo City'
        latest_alert = get_latest_alert()
        stats = get_barangay_stats()
        coords = barangay_coords.get(assigned_municipality, {}).get(barangay, {'lat': 14.5995, 'lon': 120.9842})
        
        try:
            lat_coord = float(coords.get('lat', 14.5995))
            lon_coord = float(coords.get('lon', 120.9842))
        except (ValueError, TypeError):
            logger.error(f"Invalid coordinates for {barangay} in {assigned_municipality}, using defaults")
            lat_coord = 14.5995
            lon_coord = 120.9842

        logger.debug(f"Rendering BarangayDashboard for {barangay} in {assigned_municipality}")
        return render_template('BarangayDashboard.html', 
                            latest_alert=latest_alert, 
                            stats=stats, 
                            barangay=barangay, 
                            lat_coord=lat_coord, 
                            lon_coord=lon_coord, 
                            google_api_key=GOOGLE_API_KEY)

    except Exception as e:
        logger.error(f"Error in barangay_dashboard: {e}")
        return "Internal Server Error", 500


@app.route('/cdrrmo_dashboard')
def cdrrmo_dashboard():
    try:
        if 'role' not in session or session['role'] != 'cdrrmo':
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        stats = get_cdrrmo_stats()
        unique_id = session.get('unique_id')
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
        ''', ('cdrrmo', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
        conn.close()
        
        if not unique_id or not user or user['role'] != 'cdrrmo':
            logger.warning("Unauthorized access to cdrrmo_dashboard. Session: %s, User: %s", session, user)
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        
        assigned_municipality = user['assigned_municipality'] or "San Pablo City"
        stats = get_cdrrmo_stats()
        coords = municipality_coords.get(assigned_municipality, {'lat': 14.5995, 'lon': 120.9842})
        
        try:
            lat_coord = float(coords.get('lat', 14.5995))
            lon_coord = float(coords.get('lon', 120.9842))
        except (ValueError, TypeError):
            logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
            lat_coord = 14.5995
            lon_coord = 120.9842

        logger.debug(f"Rendering CDRRMODashboard for {assigned_municipality}")
        return render_template('CDRRMODashboard.html', 
                               stats=stats, 
                               municipality=assigned_municipality, 
                               lat_coord=lat_coord, 
                               lon_coord=lon_coord, 
                               google_api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Error in cdrrmo_dashboard: {e}")
        return "Internal Server Error", 500

@app.route('/pnp_dashboard')
def pnp_dashboard():
    try:
        if 'role' not in session or session['role'] != 'pnp':
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        stats = get_pnp_stats()
        unique_id = session.get('unique_id')
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
        ''', ('pnp', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
        conn.close()
        
        if not unique_id or not user or user['role'] != 'pnp':
            logger.warning("Unauthorized access to pnp_dashboard. Session: %s, User: %s", session, user)
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        
        assigned_municipality = user['assigned_municipality'] or "San Pablo City"
        stats = get_pnp_stats()
        coords = municipality_coords.get(assigned_municipality, {'lat': 14.5995, 'lon': 120.9842})
        
        try:
            lat_coord = float(coords.get('lat', 14.5995))
            lon_coord = float(coords.get('lon', 120.9842))
        except (ValueError, TypeError):
            logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
            lat_coord = 14.5995
            lon_coord = 120.9842

        logger.debug(f"Rendering PNPDashboard for {assigned_municipality}")
        return render_template('PNPDashboard.html', 
                               stats=stats, 
                               municipality=assigned_municipality, 
                               lat_coord=lat_coord, 
                               lon_coord=lon_coord, 
                               google_api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Error in pnp_dashboard: {e}")
        return "Internal Server Error", 500

@app.route('/bfp_dashboard')
def bfp_dashboard():
    try:
        if 'role' not in session or session['role'] != 'bfp':
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        stats = get_bfp_stats()
        unique_id = session.get('unique_id')
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?
        ''', ('bfp', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
        conn.close()
        
        if not unique_id or not user or user['role'] != 'bfp':
            logger.warning("Unauthorized access to bfp_dashboard. Session: %s, User: %s", session, user)
            return redirect(url_for('login_cdrrmo_pnp_bfp'))
        
        assigned_municipality = user['assigned_municipality'] or "San Pablo City"
        stats = get_bfp_stats()
        coords = municipality_coords.get(assigned_municipality, {'lat': 14.5995, 'lon': 120.9842})
        
        try:
            lat_coord = float(coords.get('lat', 14.5995))
            lon_coord = float(coords.get('lon', 120.9842))
        except (ValueError, TypeError):
            logger.error(f"Invalid coordinates for {assigned_municipality}, using defaults")
            lat_coord = 14.5995
            lon_coord = 120.9842

        logger.debug(f"Rendering BFPDashboard for {assigned_municipality}")
        return render_template('BFPDashboard.html', 
                               stats=stats, 
                               municipality=assigned_municipality, 
                               lat_coord=lat_coord,
                               lon_coord=lon_coord,
                               google_api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Error in bfp_dashboard: {e}")
        return "Internal Server Error", 500


@app.route('/barangay/analytics')
def barangay_analytics():
    if 'role' not in session or session['role'] != 'barangay':
        logger.warning("Unauthorized access to barangay_analytics")
        return redirect(url_for('login'))
    unique_id = session.get('unique_id')
    conn = get_db_connection()
    user = conn.execute('SELECT barangay FROM users WHERE barangay = ? AND contact_no = ?',
                        (unique_id.split('_')[0], unique_id.split('_')[1])).fetchone()
    conn.close()
    barangay = user['barangay'] if user else "Unknown"
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    return render_template('BarangayAnalytics.html', barangay=barangay, current_datetime=current_datetime)

@app.route('/api/barangay_analytics_data')
def barangay_analytics_data():
    try:
        time_filter = request.args.get('time', 'today')
        barangay = request.args.get('barangay')
        trends = get_barangay_trends(time_filter, barangay)
        distribution = get_barangay_distribution(time_filter, barangay)
        causes_data = get_barangay_causes(time_filter, barangay)
        accident_type = get_accident_type(time_filter, barangay)
        road_condition = get_road_condition(time_filter, barangay)
        road_data = road_accident_df('road_accident.csv', time_filter) if time_filter != 'today' else today_responses
        fire_data = fire_incident_df('fire_accident.csv', time_filter) if time_filter != 'today' else today_responses
        analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'road_conditions': Counter(d.get('road_condition', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'vehicle_types': Counter(d.get('vehicle_type', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_age': Counter(d.get('driver_age', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_gender': Counter(d.get('driver_gender', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'accident_type': accident_type,
            'accident_cause': causes_data.get('road', {}),
            'injuries': [0] * 24,
            'fatalities': [0] * 24
        }
        fire_analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire'),
            'property_types': Counter(d.get('property_type', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire')
        }
        for data in road_data:
            if isinstance(data, dict) and data.get('emergency_type', '') == 'Road Accident':
                hour = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila')).hour
                analytics_data['injuries'][hour] += data.get('injuries', 0)
                analytics_data['fatalities'][hour] += data.get('fatalities', 0)
        logger.debug(f"Barangay trends type: {type(trends)}, value: {trends}")
        logger.debug(f"Barangay distribution type: {type(distribution)}, value: {distribution}")
        logger.debug(f"Barangay causes_data type: {type(causes_data)}, value: {causes_data}")
        logger.debug(f"Barangay analytics_data type: {type(analytics_data)}, value: {analytics_data}")
        logger.debug(f"Barangay fire_analytics_data type: {type(fire_analytics_data)}, value: {fire_analytics_data}")
        return jsonify({
            'trends': trends,
            'distribution': distribution,
            'causes': causes_data,
            'analytics_data': analytics_data,
            'fire_analytics_data': fire_analytics_data
        })
    except Exception as e:
        logger.error(f"Error in barangay_analytics_data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cdrrmo/analytics')
def cdrrmo_analytics():
    if 'role' not in session or session['role'] != 'cdrrmo':
        logger.warning("Unauthorized access to cdrrmo_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('cdrrmo', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
    conn.close()
    municipality = user['assigned_municipality'] if user else "Unknown"
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = ["Barangay 1", "Barangay 2", "Barangay 3"]
    return render_template('CDRRMOAnalytics.html', municipality=municipality, current_datetime=current_datetime, barangays=barangays)



@app.route('/pnp/analytics')
def pnp_analytics():
    if 'role' not in session or session['role'] != 'pnp':
        logger.warning("Unauthorized access to pnp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('pnp', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
    conn.close()
    municipality = user['assigned_municipality'] if user else "Unknown"
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = ["Barangay 1", "Barangay 2", "Barangay 3"]
    return render_template('PNPAnalytics.html', municipality=municipality, current_datetime=current_datetime, barangays=barangays)

@app.route('/api/cdrrmo_analytics_data')
def cdrrmo_analytics_data():
    try:
        time_filter = request.args.get('time', 'today')
        municipality = request.args.get('municipality')
        trends = get_cdrrmo_trends(time_filter, municipality)
        distribution = get_cdrrmo_distribution(time_filter, municipality)
        causes_data = get_cdrrmo_causes(time_filter, municipality)
        accident_type = get_accident_type(time_filter, None, municipality)
        road_condition = get_road_condition(time_filter, None, municipality)
        road_data = road_accident_df('road_accident.csv', time_filter) if time_filter != 'today' else today_responses
        fire_data = fire_incident_df('fire_accident.csv', time_filter) if time_filter != 'today' else today_responses
        analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'road_conditions': Counter(d.get('road_condition', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'vehicle_types': Counter(d.get('vehicle_type', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_age': Counter(d.get('driver_age', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_gender': Counter(d.get('driver_gender', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'accident_type': accident_type,
            'accident_cause': causes_data.get('road', {}),
            'injuries': [0] * 24,
            'fatalities': [0] * 24
        }
        fire_analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire'),
            'property_types': Counter(d.get('property_type', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire')
        }
        for data in road_data:
            if isinstance(data, dict) and data.get('emergency_type', '') == 'Road Accident':
                hour = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila')).hour
                analytics_data['injuries'][hour] += data.get('injuries', 0)
                analytics_data['fatalities'][hour] += data.get('fatalities', 0)
        logger.debug(f"CDRRMO trends type: {type(trends)}, value: {trends}")
        logger.debug(f"CDRRMO distribution type: {type(distribution)}, value: {distribution}")
        logger.debug(f"CDRRMO causes_data type: {type(causes_data)}, value: {causes_data}")
        logger.debug(f"CDRRMO analytics_data type: {type(analytics_data)}, value: {analytics_data}")
        logger.debug(f"CDRRMO fire_analytics_data type: {type(fire_analytics_data)}, value: {fire_analytics_data}")
        return jsonify({
            'trends': trends,
            'distribution': distribution,
            'causes': causes_data,
            'analytics_data': analytics_data,
            'fire_analytics_data': fire_analytics_data
        })
    except Exception as e:
        logger.error(f"Error in cdrrmo_analytics_data: {e}")
        return jsonify({'error': str(e)}), 500

# Updated /api/pnp_analytics_data
@app.route('/api/pnp_analytics_data')
def pnp_analytics_data():
    try:
        time_filter = request.args.get('time', 'today')
        municipality = request.args.get('municipality')
        trends = get_pnp_trends(time_filter, municipality)
        distribution = get_pnp_distribution(time_filter, municipality)
        causes_data = get_pnp_causes(time_filter, municipality)
        accident_type = get_accident_type(time_filter, None, municipality)
        road_condition = get_road_condition(time_filter, None, municipality)
        road_data = road_accident_df('road_accident.csv', time_filter) if time_filter != 'today' else today_responses
        fire_data = fire_incident_df('fire_accident.csv', time_filter) if time_filter != 'today' else today_responses
        analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'road_conditions': Counter(d.get('road_condition', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'vehicle_types': Counter(d.get('vehicle_type', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_age': Counter(d.get('driver_age', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'driver_gender': Counter(d.get('driver_gender', 'Unknown') for d in road_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Road Accident'),
            'accident_type': accident_type,
            'accident_cause': causes_data.get('road', {}),
            'injuries': [0] * 24,
            'fatalities': [0] * 24
        }
        fire_analytics_data = {
            'weather': Counter(d.get('weather', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire'),
            'property_types': Counter(d.get('property_type', 'Unknown') for d in fire_data if isinstance(d, dict) and d.get('emergency_type', '') == 'Fire')
        }
        for data in road_data:
            if isinstance(data, dict) and data.get('emergency_type', '') == 'Road Accident':
                hour = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila')).hour
                analytics_data['injuries'][hour] += data.get('injuries', 0)
                analytics_data['fatalities'][hour] += data.get('fatalities', 0)
        logger.debug(f"PNP trends type: {type(trends)}, value: {trends}")
        logger.debug(f"PNP distribution type: {type(distribution)}, value: {distribution}")
        logger.debug(f"PNP causes_data type: {type(causes_data)}, value: {causes_data}")
        logger.debug(f"PNP analytics_data type: {type(analytics_data)}, value: {analytics_data}")
        logger.debug(f"PNP fire_analytics_data type: {type(fire_analytics_data)}, value: {fire_analytics_data}")
        return jsonify({
            'trends': trends,
            'distribution': distribution,
            'causes': causes_data,
            'analytics_data': analytics_data,
            'fire_analytics_data': fire_analytics_data
        })
    except Exception as e:
        logger.error(f"Error in pnp_analytics_data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/bfp/analytics')
def bfp_analytics():
    if 'role' not in session or session['role'] != 'bfp':
        logger.warning("Unauthorized access to bfp_analytics")
        return redirect(url_for('login_cdrrmo_pnp_bfp'))
    unique_id = session.get('unique_id')
    conn = get_db_connection()
    user = conn.execute('SELECT assigned_municipality FROM users WHERE role = ? AND contact_no = ? AND assigned_municipality = ?',
                        ('bfp', unique_id.split('_')[2], unique_id.split('_')[1])).fetchone()
    conn.close()
    municipality = user['assigned_municipality'] if user else "Unknown"
    current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%a/%m/%d/%y %H:%M:%S')
    barangays = ["Barangay 1", "Barangay 2", "Barangay 3"]
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




def get_latest_alert():
    try:
        if alerts:
            return alerts[-1]
        return None
    except Exception as e:
        logger.error(f"Error in get_latest_alert: {e}")
        return None

def get_barangay_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'barangay' or a.get('barangay')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_barangay_stats: {e}")
        return Counter()

def get_cdrrmo_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'cdrrmo' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_stats: {e}")
        return Counter()

def get_pnp_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'pnp' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_pnp_stats: {e}")
        return Counter()

def get_bfp_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'bfp' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_bfp_stats: {e}")
        return Counter()

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
        conn.commit()
        conn.close()
        logger.info("Database 'users_web.db' initialized successfully or already exists.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    db_path = os.path.join(os.path.dirname(__file__), 'database', 'AlertNowLocal.db')
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                users TEXT,
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                age INTEGER,
                contact_no TEXT,
                house_no TEXT,
                street_no TEXT,
                barangay TEXT,
                municipality TEXT,
                province TEXT,
                position TEXT,
                synced INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Android database 'AlertNowLocal.db' initialized successfully or already exists.")
    except Exception as e:
        logger.error(f"Failed to initialize Android database: {e}")

    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)