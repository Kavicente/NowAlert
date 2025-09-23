from flask import request, redirect, url_for, render_template, session, jsonify
import requests
import sqlite3
import os
import logging  # Added for debugging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def login_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        role = request.form['role'].lower()  # Ensure role is lowercase
        municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE role = ? AND assigned_municipality = ? AND contact_no = ? AND password = ?', (role, municipality, contact_no, password)).fetchone()
        conn.close()
        if user:
            logger.info(f"Login successful for {role} in {municipality} with contact_no {contact_no}")
            if role == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif role == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif role == 'bfp':
                return redirect(url_for('bfp_dashboard'))
        logger.warning(f"Login failed for {role} in {municipality} with contact_no {contact_no}")
        return "Invalid credentials", 401
    conn = get_db_connection()
    cdrrmo_pnp_bfp_users = conn.execute('SELECT role, assigned_municipality, contact_no, password FROM users WHERE role IN (?, ?, ?)', ('cdrrmo', 'pnp', 'bfp')).fetchall()
    logger.debug(f"Retrieved {len(cdrrmo_pnp_bfp_users)} CDRRMO/PNP/BFP users: {[dict(row) for row in cdrrmo_pnp_bfp_users]}")
    conn.close()
    return render_template('CDRRMOPNPBFPIn.html', cdrrmo_pnp_bfp_users=cdrrmo_pnp_bfp_users)

def auto_role():
    data = request.form
    role = data.get('role').lower()  # Ensure role is lowercase
    municipality = data.get('municipality')
    contact_no = data.get('contact_no')
    password = data.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE role = ? AND assigned_municipality = ? AND contact_no = ? AND password = ?', (role, municipality, contact_no, password)).fetchone()
    conn.close()
    if user:
        session['role'] = role
        session['unique_id'] = f"{role}_{municipality}_{contact_no}"
        session.permanent = True
        logger.info(f"Auto login successful for {role} with contact_no: {contact_no}")
        if role == 'cdrrmo':
            return redirect(url_for('cdrrmo_dashboard'))
        elif role == 'pnp':
            return redirect(url_for('pnp_dashboard'))
        elif role == 'bfp':
            return redirect(url_for('bfp_dashboard'))
    logger.warning(f"Auto login failed for {role} with contact_no: {contact_no}")
    return "Invalid credentials", 401

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('CDRRMOPNPIn.html')
