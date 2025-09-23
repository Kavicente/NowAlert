from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file, make_response
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import pytz
from datetime import datetime
import os 


def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

import sqlite3
import pytz
from datetime import datetime

def get_pnp_chart_data(time_filter, barangay=None):
    from AlertNow import app  # Moved inside function
    conn = get_db_connection()  # Using the defined get_db_connection()
    c = conn.cursor()
    query = "SELECT road_accident_cause, road_accident_type, driver_gender, vehicle_type, driver_age, road_condition, barangay, timestamp FROM pnp_response"
    manila = pytz.timezone('Asia/Manila')
    base_time = datetime.now(pytz.timezone('Asia/Manila'))
    if barangay:
        query += " WHERE barangay = ?"
        if time_filter == 'today':
            c.execute(query + " AND date(timestamp) = date(?)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'daily':
            c.execute(query + " AND date(timestamp) = date(?) GROUP BY date(timestamp)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'weekly':
            c.execute(query + " AND strftime('%Y-%W', timestamp) = strftime('%Y-%W', ?) GROUP BY strftime('%Y-%W', timestamp)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'monthly':
            c.execute(query + " AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?) GROUP BY strftime('%Y-%m', timestamp)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'yearly':
            c.execute(query + " AND strftime('%Y', timestamp) = strftime('%Y', ?) GROUP BY strftime('%Y', timestamp)", (barangay, base_time.strftime('%Y-%m-%d')))
    else:
        if time_filter == 'today':
            c.execute(query + " WHERE date(timestamp) = date(?)", (base_time.strftime('%Y-%m-%d'),))
        elif time_filter == 'daily':
            c.execute(query + " GROUP BY date(timestamp)")
        elif time_filter == 'weekly':
            c.execute(query + " GROUP BY strftime('%Y-%W', timestamp)")
        elif time_filter == 'monthly':
            c.execute(query + " GROUP BY strftime('%Y-%m', timestamp)")
        elif time_filter == 'yearly':
            c.execute(query + " GROUP BY strftime('%Y', timestamp)")
    rows = c.fetchall()
    conn.close()

    causes = {}; types = {}; genders = {}; vehicles = {}; ages = {}; conditions = {}; barangays = {}
    for row in rows:
        causes[row[0]] = causes.get(row[0], 0) + 1
        types[row[1]] = types.get(row[1], 0) + 1
        genders[row[2]] = genders.get(row[2], 0) + 1
        vehicles[row[3]] = vehicles.get(row[3], 0) + 1
        ages[row[4]] = ages.get(row[4], 0) + 1
        conditions[row[5]] = conditions.get(row[5], 0) + 1
        barangays[row[6]] = barangays.get(row[6], 0) + 1

    return {
        'barangay': {'labels': list(barangays.keys()) if barangays else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(barangays.values()) if barangays else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']}]},
        'cause': {'labels': list(causes.keys()) if causes else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(causes.values()) if causes else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']}]},
        'type': {'labels': list(types.keys()) if types else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(types.values()) if types else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']}]},
        'gender': {'labels': list(genders.keys()) if genders else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(genders.values()) if genders else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']}]},
        'vehicle': {'labels': list(vehicles.keys()) if vehicles else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(vehicles.values()) if vehicles else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']}]},
        'age': {'labels': list(ages.keys()) if ages else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(ages.values()) if ages else [0], 'backgroundColor': '#36A2EB', 'borderColor': '#FF6384', 'fill': False}]},
        'condition': {'labels': list(conditions.keys()) if conditions else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(conditions.values()) if conditions else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']}]}
    }

def pnp_charts():
    from AlertNow import app  # Moved inside function
    return render_template('PNPCharts.html', current_datetime=datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S'))

def pnp_charts_data():
    from AlertNow import app  # Moved inside function
    time_filter = request.args.get('time_filter', 'today')
    barangay = request.args.get('barangay')
    data = get_pnp_chart_data(time_filter, barangay)
    return jsonify(data)

def handle_pnp_response(data):
    from AlertNow import socketio, app  # Moved inside function
    chart_data = get_pnp_chart_data('today', data.get('barangay'))
    socketio.emit('pnp_response_update', chart_data, broadcast=True)