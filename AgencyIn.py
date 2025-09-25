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


def login_agency():
    logger.debug("Accessing /login_agency with method: %s", request.method)
    if request.method == 'POST':
        role = request.form['role'].lower()
        if 'role' not in request.form:
            logger.error("Role field is missing in the form data")
            return "Role is required", 400
        assigned_municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        assigned_hospital = request.form.get('assigned_hospital', '').lower() if role == 'hospital' else None
        
        if role not in ['cdrrmo', 'pnp', 'bfp', 'city health', 'hospital']:
            logger.error(f"Invalid role provided: {role}")
            return "Invalid role", 400
        
        logger.debug(f"Login attempt: role={role}, municipality={assigned_municipality}, contact_no={contact_no}")
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ? AND (assigned_hospital = ? OR assigned_hospital IS NULL)
        ''', (role, contact_no, password, assigned_municipality, assigned_hospital)).fetchone()
        conn.close()
        
        if user:
            unique_id = f"{role}_{assigned_municipality}_{contact_no}"
            session['unique_id'] = unique_id
            session['role'] = user['role']
            session['municipality'] = user['assigned_municipality']
            session['assigned_hospital'] = user['assigned_hospital'] if role == 'hospital' else None
            logger.debug(f"Web login successful for user: {unique_id} ({user['role']})")
            if user['role'] == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif user['role'] == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif user['role'] == 'bfp':
                return redirect(url_for('bfp_dashboard'))
            elif user['role'] == 'city health':
                return redirect(url_for('health_dashboard'))
            elif user['role'] == 'hospital':
                return redirect(url_for('hospital_dashboard'))
        logger.warning(f"Web login failed for assigned_municipality: {assigned_municipality}, contact: {contact_no}, role: {role}")
        return render_template('AgencyIn.html', error="Invalid credentials or hospital assignment", cdrrmo_pnp_bfp_users=[])
    
    conn = get_db_connection()
    cdrrmo_pnp_bfp_users = conn.execute('SELECT role, assigned_municipality, contact_no, password, assigned_hospital FROM users WHERE role IN (?, ?, ?, ?, ?)', 
                                        ('cdrrmo', 'pnp', 'bfp', 'city health', 'hospital')).fetchall()
    logger.debug(f"Retrieved {len(cdrrmo_pnp_bfp_users)} CDRRMO/PNP/BFP/City Health/Hospital users: {[dict(row) for row in cdrrmo_pnp_bfp_users]}")
    conn.close()
    return render_template('AgencyIn.html', cdrrmo_pnp_bfp_users=cdrrmo_pnp_bfp_users)



def auto_role():
    data = request.form
    role = data.get('role').lower()
    municipality = data.get('municipality')
    contact_no = data.get('contact_no')
    password = data.get('password')
    assigned_hospital = data.get('assigned_hospital', '').lower() if role == 'hospital' else None
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE role = ? AND assigned_municipality = ? AND contact_no = ? AND password = ? AND (assigned_hospital = ? OR assigned_hospital IS NULL)', 
                        (role, municipality, contact_no, password, assigned_hospital)).fetchone()
    conn.close()
    if user:
        session['role'] = role
        session['unique_id'] = f"{role}_{municipality}_{contact_no}"
        session['municipality'] = municipality
        session['assigned_hospital'] = user['assigned_hospital'] if role == 'hospital' else None
        session.permanent = True
        logger.info(f"Auto login successful for {role} with contact_no: {contact_no}")
        if role == 'cdrrmo':
            return redirect(url_for('cdrrmo_dashboard'))
        elif role == 'pnp':
            return redirect(url_for('pnp_dashboard'))
        elif role == 'bfp':
            return redirect(url_for('bfp_dashboard'))
        elif role == 'city health':
            return redirect(url_for('health_dashboard'))
        elif role == 'hospital':
            return redirect(url_for('hospital_dashboard'))
    logger.warning(f"Auto login failed for {role} with contact_no: {contact_no}")
    return "Invalid credentials"

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('AgencyIn.html')
