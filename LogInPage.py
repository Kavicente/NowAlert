from flask import request, redirect, url_for, render_template, session
import requests
import sqlite3
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def login_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        role = request.form['role']
        municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE role IN (?, ?, ?) AND assigned_municipality = ? AND contact_no = ? AND password = ?', (role, 'pnp', 'bfp', municipality, contact_no, password)).fetchone()
        conn.close()
        if user:
            if role == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif role == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif role == 'bfp':
                return redirect(url_for('bfp_dashboard'))
        return "Invalid credentials", 401
    conn = get_db_connection()
    cdrrmo_pnp_bfp_users = conn.execute('SELECT role, assigned_municipality, contact_no, password FROM users WHERE role IN (?, ?, ?)', ('cdrrmo', 'pnp', 'bfp')).fetchall()
    conn.close()
    return render_template('CDRRMOPNPBFPIn.html', cdrrmo_pnp_bfp_users=cdrrmo_pnp_bfp_users)

def choose_login_type():
    return render_template('LoginType.html')
