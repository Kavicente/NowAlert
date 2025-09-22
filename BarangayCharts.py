from flask import request, jsonify, render_template
import sqlite3
import pytz
from datetime import datetime
import os 


def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_barangay_chart_data(time_filter):
    from AlertNow import app  # Moved inside function
    conn = get_db_connection()
    conn = conn.cursor()
    query = "SELECT road_accident_cause, road_accident_type, driver_gender, vehicle_type, driver_age, road_condition, timestamp FROM barangay_response"
    manila = pytz.timezone('Asia/Manila')
    base_time = datetime.now(pytz.timezone('Asia/Manila'))
    if time_filter == 'today':
        conn.execute(query + " WHERE date(timestamp) = date(?)", (base_time.strftime('%Y-%m-%d'),))
    elif time_filter == 'daily':
        conn.execute(query + " GROUP BY date(timestamp)")
    elif time_filter == 'weekly':
        conn.execute(query + " GROUP BY strftime('%Y-%W', timestamp)")
    elif time_filter == 'monthly':
        conn.execute(query + " GROUP BY strftime('%Y-%m', timestamp)")
    elif time_filter == 'yearly':
        conn.execute(query + " GROUP BY strftime('%Y', timestamp)")
    rows = conn.fetchall()
    conn.close()

    causes = {}
    types = {}
    genders = {}
    vehicles = {}
    ages = {}
    conditions = {}
    for row in rows:
        causes[row[0]] = causes.get(row[0], 0) + 1
        types[row[1]] = types.get(row[1], 0) + 1
        genders[row[2]] = genders.get(row[2], 0) + 1
        vehicles[row[3]] = vehicles.get(row[3], 0) + 1
        ages[row[4]] = ages.get(row[4], 0) + 1
        conditions[row[5]] = conditions.get(row[5], 0) + 1

    return {
        'cause': {'labels': list(causes.keys()), 'datasets': [{'label': 'Count', 'data': list(causes.values()), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']}]},
        'type': {'labels': list(types.keys()), 'datasets': [{'label': 'Count', 'data': list(types.values()), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']}]},
        'gender': {'labels': list(genders.keys()), 'datasets': [{'label': 'Count', 'data': list(genders.values()), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']}]},
        'vehicle': {'labels': list(vehicles.keys()), 'datasets': [{'label': 'Count', 'data': list(vehicles.values()), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']}]},
        'age': {'labels': list(ages.keys()), 'datasets': [{'label': 'Count', 'data': list(ages.values()), 'backgroundColor': '#36A2EB', 'borderColor': '#FF6384', 'fill': False}]},
        'condition': {'labels': list(conditions.keys()), 'datasets': [{'label': 'Count', 'data': list(conditions.values()), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']}]}
    }

def barangay_charts():
    from AlertNow import app  # Moved inside function
    return render_template('BarangayCharts.html', barangay='SampleBarangay', current_datetime=datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S'))

def barangay_charts_data():
    from AlertNow import app  # Moved inside function
    time_filter = request.args.get('time_filter', 'today')
    data = get_barangay_chart_data(time_filter)
    return jsonify(data)

def handle_barangay_response(data):
    from AlertNow import socketio, app  # Moved inside function
    # Simulate database update and emit update
    chart_data = get_barangay_chart_data('today')
    socketio.emit('barangay_response_update', chart_data, broadcast=True)