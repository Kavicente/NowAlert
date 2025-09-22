from flask import request, jsonify, render_template
import sqlite3
import pytz
from datetime import datetime, timedelta
import os 


def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_bfp_chart_data(time_filter, barangay=None):
    from AlertNow import app  # Moved inside function
    conn = get_db_connection()  # Using the defined get_db_connection function
    c = conn.cursor()
    query = "SELECT fire_cause, fire_type, weather, fire_severity, timestamp FROM bfp_response"
    manila = pytz.timezone('Asia/Manila')
    base_time = datetime.now(pytz.timezone('Asia/Manila'))
    
    if barangay:
        query += " WHERE barangay = ?"
        if time_filter == 'today':
            c.execute(query + " AND date(timestamp) = date(?)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'daily':
            c.execute(query + " AND date(timestamp) = date(?)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'weekly':
            one_week_ago = base_time - timedelta(days=7)
            c.execute(query + " AND date(timestamp) BETWEEN date(?) AND date(?)", (barangay, one_week_ago.strftime('%Y-%m-%d'), base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'monthly':
            c.execute(query + " AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?)", (barangay, base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'yearly':
            c.execute(query + " AND strftime('%Y', timestamp) = strftime('%Y', ?)", (barangay, base_time.strftime('%Y-%m-%d')))
    else:
        if time_filter == 'today':
            c.execute(query + " WHERE date(timestamp) = date(?)", (base_time.strftime('%Y-%m-%d'),))
        elif time_filter == 'daily':
            c.execute(query + " WHERE date(timestamp) = date(?)", (base_time.strftime('%Y-%m-%d'),))
        elif time_filter == 'weekly':
            one_week_ago = base_time - timedelta(days=7)
            c.execute(query + " WHERE date(timestamp) BETWEEN date(?) AND date(?)", (one_week_ago.strftime('%Y-%m-%d'), base_time.strftime('%Y-%m-%d')))
        elif time_filter == 'monthly':
            c.execute(query + " WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', ?)", (base_time.strftime('%Y-%m-%d'),))
        elif time_filter == 'yearly':
            c.execute(query + " WHERE strftime('%Y', timestamp) = strftime('%Y', ?)", (base_time.strftime('%Y-%m-%d'),))
    rows = c.fetchall()
    conn.close()

    causes = {}; types = {}; weathers = {}; severities = {}
    for row in rows:
        causes[row[0]] = causes.get(row[0], 0) + 1
        types[row[1]] = types.get(row[1], 0) + 1
        weathers[row[2]] = weathers.get(row[2], 0) + 1
        severities[row[3]] = severities.get(row[3], 0) + 1

    return {
        'cause': {'labels': list(causes.keys()) if causes else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(causes.values()) if causes else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']}]},
        'type': {'labels': list(types.keys()) if types else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(types.values()) if types else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']}]},
        'weather': {'labels': list(weathers.keys()) if weathers else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(weathers.values()) if weathers else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']}]},
        'severity': {'labels': list(severities.keys()) if severities else ['No Data'], 'datasets': [{'label': 'Count', 'data': list(severities.values()) if severities else [0], 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']}]}
    }

def bfp_charts():
    from AlertNow import app  # Moved inside function
    conn = get_db_connection()  # Using the defined get_db_connection function
    c = conn.cursor()
    c.execute("SELECT DISTINCT barangay FROM bfp_response")
    barangays = [row['barangay'] for row in c.fetchall() if row['barangay']]
    conn.close()
    return render_template('BFPCharts.html', barangays=barangays, current_datetime=datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S'))

def bfp_charts_data():
    from AlertNow import app  # Moved inside function
    time_filter = request.args.get('time_filter', 'today')
    barangay = request.args.get('barangay')
    data = get_bfp_chart_data(time_filter, barangay)
    return jsonify(data)

def handle_bfp_response(data):
    from AlertNow import socketio, app  # Moved inside function
    chart_data = get_bfp_chart_data('today', data.get('barangay'))
    socketio.emit('bfp_response_update', chart_data, broadcast=True)