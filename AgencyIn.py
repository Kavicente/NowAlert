from flask import request, redirect, url_for, render_template, session, jsonify, flash
import requests
import sqlite3
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def send_dilg_password(password):
    sender = "castillovinceb@gmail.com"
    receiver = "vncbcstll@gmail.com"
    subject = "Your DILG Login Password"
    body = f"""
    <h2>DILG Login Access</h2>
    <p>Your temporary login password is:</p>
    <h3 style="color:#224380; font-family:monospace;">{password}</h3>
    <p>Use this with your assigned municipality to log in.</p>
    <p><em>This is an automated message.</em></p>
    """

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        app_pass = os.getenv('EMAIL_PASS')
        if not app_pass:
            logger.error("EMAIL_PASS not set")
            return
        server.login(sender, app_pass.replace(" ", ""))
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        logger.info(f"DILG password email sent: {password}")
    except Exception as e:
        logger.error(f"Failed to send DILG email: {e}")

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
        
        if role not in ['cdrrmo', 'pnp', 'bfp', 'city health', 'hospital', 'dilg']:
            logger.error(f"Invalid role provided: {role}")
            return "Invalid role", 400
        
        logger.debug(f"Login attempt: role={role}, municipality={assigned_municipality}, contact_no={contact_no}")
        
        conn = get_db_connection()
        if role == 'dilg':
            # Allow login if password ends with 'DILG!' (generated)
            if password.endswith('DILG!'):
                session['role'] = 'dilg'
                session['municipality'] = assigned_municipality
                session['contact_no'] = 'DILG_ADMIN'
                conn.close()
                return redirect('/dilg_dashboard')
        elif role == 'hospital':
            user = conn.execute('''
                SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ? AND assigned_hospital = ?
            ''', (role, contact_no, password, assigned_municipality, assigned_hospital)).fetchone()
        else:
            user = conn.execute('''
                SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ?
            ''', (role, contact_no, password, assigned_municipality)).fetchone()
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
        return render_template('AgencyIn.html', error="Invalid credentials", cdrrmo_pnp_bfp_users=[])
    
    conn = get_db_connection()
    cdrrmo_pnp_bfp_users = conn.execute('SELECT role, assigned_municipality, contact_no, password, assigned_hospital FROM users WHERE role IN (?, ?, ?, ?, ?)', 
                                        ('cdrrmo', 'pnp', 'bfp', 'city health', 'hospital')).fetchall()
    logger.debug(f"Retrieved {len(cdrrmo_pnp_bfp_users)} users")
    conn.close()
    return render_template('AgencyIn.html', cdrrmo_pnp_bfp_users=cdrrmo_pnp_bfp_users)

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('AgencyIn.html')