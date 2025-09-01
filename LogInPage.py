from flask import request, redirect, url_for, render_template, session
import requests

import sqlite3
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def login_page():
    if request.method == 'POST':
        barangay = request.form['barangay']
        contact_no = request.form['contact_no']
        password = request.form['password']
        unique_id = f"{barangay}_{contact_no}"
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE barangay = ? AND contact_no = ? AND password = ? AND role = ?',
                                (barangay, contact_no, password, 'barangay')).fetchone()
            if user:
                session['role'] = 'barangay'
                session['unique_id'] = unique_id
                session.permanent = True
                return redirect(url_for('barangay_dashboard'))
            return "Invalid credentials", 401
        finally:
            conn.close()
    
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT barangay, contact_no, password FROM users WHERE role = "barangay"').fetchall()
        credentials = [
            {
                'role': 'barangay',
                'display': user['barangay'] or 'Unknown Barangay',
                'contact_no': user['contact_no'],
                'password': user['password'],
                'barangay': user['barangay']
            } for user in users
        ]
        conn.close()
    except Exception as e:
        print(f"Error fetching credentials: {e}")
        credentials = []
    
    return render_template('LogInPage.html', credentials=credentials)

def choose_login_type():
    return render_template('LoginType.html')
