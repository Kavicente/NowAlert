from flask import render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_municipality_from_barangay(barangay):
    from AlertNow import get_municipality_from_barangay
    return get_municipality_from_barangay(barangay)

def get_default_barangay(municipality):
    from AlertNow import barangay_coords
    return next(iter(barangay_coords.get(municipality, {})), 'Unknown')


def get_barangays():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT barangay FROM health_response WHERE barangay IS NOT NULL')
        barangays = [row['barangay'] for row in cursor.fetchall()]
        conn.close()
        return sorted(barangays)
    except Exception as e:
        logger.error(f"Error fetching barangays: {e}")
        return []

def health_charts():
    try:
        barangay = session.get('barangay', None)
        municipality = session.get('municipality', 'Unknown')
        if not barangay or barangay == 'Unknown':
            barangay = get_default_barangay(municipality)
            session['barangay'] = barangay
            logger.info(f"Set default barangay to {barangay} for municipality {municipality}")
        if 'role' not in session or session['role'] != 'health':
            logger.warning("Unauthorized access to health charts")
            return redirect(url_for('admin_login'))
        current_datetime = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Rendering health charts for barangay: {barangay}")
        return render_template('HealthCharts.html', barangay=barangay, current_datetime=current_datetime)
    except Exception as e:
        logger.error(f"Error in health_charts: {e}")
        return "Internal Server Error", 500

def health_charts_data():
    try:
        time_filter = request.args.get('time', 'today')
        barangay = request.args.get('barangay', 'Unknown')
        hospital = request.args.get('hospital', '')
        municipality = get_municipality_from_barangay(barangay)
        session_municipality = session.get('municipality', 'Unknown')
        if barangay == 'Unknown' or not municipality:
            barangay = get_default_barangay(session_municipality)
            logger.warning(f"Invalid barangay {request.args.get('barangay', 'Unknown')}, using default {barangay} for municipality {session_municipality}")
        if municipality != session_municipality:
            logger.warning(f"Barangay {barangay} does not belong to municipality {session_municipality}")
            return jsonify({}), 400
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now(pytz.timezone('Asia/Manila'))
        if time_filter == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif time_filter == 'daily':
            start_time = now - timedelta(days=1)
            end_time = now
        elif time_filter == 'weekly':
            start_time = now - timedelta(days=7)
            end_time = now
        elif time_filter == 'monthly':
            start_time = now - timedelta(days=30)
            end_time = now
        elif time_filter == 'yearly':
            start_time = now - timedelta(days=365)
            end_time = now
        else:
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now

        query = '''
            SELECT barangay, health_type, health_cause, weather, patient_age, patient_gender
            FROM health_response
            WHERE timestamp BETWEEN ? AND ? AND barangay = ?
        '''
        cursor.execute(query, (start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), barangay))
        rows = cursor.fetchall()
        hospital_query = '''
            SELECT assigned_hospital
            FROM hospital_response
            WHERE timestamp BETWEEN ? AND ? AND barangay = ?
        '''
        if hospital:
            hospital_query += " AND assigned_hospital = ?"
            cursor.execute(hospital_query, (start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), barangay, hospital))
        else:
            cursor.execute(hospital_query, (start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), barangay))
        hospital_rows = cursor.fetchall()
        conn.close()

        barangay_data = {}
        health_type_data = {}
        health_cause_data = {}
        weather_data = {}
        patient_age_data = {}
        patient_gender_data = {}
        responder_data = {}

        for row in rows:
            barangay_val = row['barangay'] or 'Unknown'
            health_type = row['health_type'] or 'Unknown'
            health_cause = row['health_cause'] or 'Unknown'
            weather = row['weather'] or 'Unknown'
            patient_age = row['patient_age'] or 'Unknown'
            patient_gender = row['patient_gender'] or 'Unknown'

            barangay_data[barangay_val] = barangay_data.get(barangay_val, 0) + 1
            health_type_data[health_type] = health_type_data.get(health_type, 0) + 1
            health_cause_data[health_cause] = health_cause_data.get(health_cause, 0) + 1
            weather_data[weather] = weather_data.get(weather, 0) + 1
            patient_age_data[patient_age] = patient_age_data.get(patient_age, 0) + 1
            patient_gender_data[patient_gender] = patient_gender_data.get(patient_gender, 0) + 1
            
        for row in hospital_rows:
            responder = row['assigned_hospital'] or 'Unknown'
            responder_data[responder] = responder_data.get(responder, 0) + 1

        logger.info(f"Health chart data - Barangay: {barangay_data}, Health Type: {health_type_data}, Health Cause: {health_cause_data}, Weather: {weather_data}, Patient Age: {patient_age_data}, Patient Gender: {patient_gender_data}, Responder: {responder_data}")

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB']

        chart_data = {
            'barangay': {
                'labels': list(barangay_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Barangay Incidents',
                    'data': list(barangay_data.values()) or [0],
                    'backgroundColor': colors[:len(barangay_data)] or ['#999999'],
                    'borderColor': colors[:len(barangay_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'health_type': {
                'labels': list(health_type_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Health Emergency Type',
                    'data': list(health_type_data.values()) or [0],
                    'backgroundColor': colors[:len(health_type_data)] or ['#999999'],
                    'borderColor': colors[:len(health_type_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'health_cause': {
                'labels': list(health_cause_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Health Emergency Cause',
                    'data': list(health_cause_data.values()) or [0],
                    'backgroundColor': colors[:len(health_cause_data)] or ['#999999'],
                    'borderColor': colors[:len(health_cause_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'weather': {
                'labels': list(weather_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Weather Conditions',
                    'data': list(weather_data.values()) or [0],
                    'backgroundColor': colors[:len(weather_data)] or ['#999999'],
                    'borderColor': colors[:len(weather_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'patient_age': {
                'labels': list(patient_age_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Patient Age',
                    'data': list(patient_age_data.values()) or [0],
                    'backgroundColor': colors[:len(patient_age_data)] or ['#999999'],
                    'borderColor': colors[:len(patient_age_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'patient_gender': {
                'labels': list(patient_gender_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Patient Gender',
                    'data': list(patient_gender_data.values()) or [0],
                    'backgroundColor': colors[:len(patient_gender_data)] or ['#999999'],
                    'borderColor': colors[:len(patient_gender_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            },
            'responder': {
                'labels': list(responder_data.keys()) or ['No Data'],
                'datasets': [{
                    'label': 'Health Responder',
                    'data': list(responder_data.values()) or [0],
                    'backgroundColor': colors[:len(responder_data)] or ['#999999'],
                    'borderColor': colors[:len(responder_data)] or ['#999999'],
                    'borderWidth': 1
                }]
            }
        }
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error in health_charts_data: {e}")
        return jsonify({}), 500