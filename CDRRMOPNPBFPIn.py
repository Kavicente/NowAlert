from flask import request, redirect, url_for, render_template,session
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

def login_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        role = request.form['role'].lower()
        unique_id = f"{role}_{municipality}_{contact_no}"
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE role = ? AND assigned_municipality = ? AND contact_no = ? AND password = ?',
                                (role, municipality, contact_no, password)).fetchone()
            if user:
                session['role'] = role
                session['unique_id'] = unique_id
                session.permanent = True
                if role == 'cdrrmo':
                    return redirect(url_for('cdrrmo_dashboard'))
                elif role == 'pnp':
                    return redirect(url_for('pnp_dashboard'))
                elif role == 'bfp':
                    return redirect(url_for('bfp_dashboard'))
            return "Invalid credentials", 401
        finally:
            conn.close()
    
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT role, assigned_municipality, contact_no, password FROM users WHERE role IN ("cdrrmo", "pnp", "bfp")').fetchall()
        credentials = [
            {
                'role': user['role'],
                'display': f"{user['role'].upper()} {user['assigned_municipality'] or 'Unknown Municipality'}",
                'contact_no': user['contact_no'],
                'password': user['password'],
                'municipality': user['assigned_municipality']
            } for user in users
        ]
        conn.close()
    except Exception as e:
        print(f"Error fetching credentials: {e}")
        credentials = []
    
    return render_template('CDRRMOPNPBFPIn.html', credentials=credentials)

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('CDRRMOPNPIn.html')
