from flask import request, redirect, url_for, render_template, session
import requests
from AlertNow import app, get_db_connection
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def login_page():
    if request.method == 'POST':
        contact_no = request.form.get('contact_no')
        password = request.form.get('password')
        barangay = request.form.get('barangay')
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND barangay = ?',
                               ('barangay', contact_no, password, barangay)).fetchone()
            if user:
                session['role'] = 'barangay'
                session['unique_id'] = f"{barangay}_{contact_no}"
                session.permanent = True
                logger.info(f"Login successful for barangay {barangay}")
                return redirect(url_for('barangay_dashboard'))
            else:
                logger.warning(f"Invalid credentials for contact_no: {contact_no}, barangay: {barangay}")
                return render_template('LogInPage.html', error="Invalid credentials", credentials=[])
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return render_template('LogInPage.html', error=str(e), credentials=[])
        finally:
            conn.close()
    
    # Fetch credentials for display
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT role, barangay, assigned_municipality, contact_no, password FROM users WHERE role != "admin"').fetchall()
        credentials = []
        for user in users:
            if user['role'] == 'barangay':
                credentials.append({
                    'role': user['role'],
                    'display': user['barangay'] or 'Unknown Barangay',
                    'contact_no': user['contact_no'],
                    'password': user['password'],
                    'barangay': user['barangay'] or ''
                })
        conn.close()
        return render_template('LogInPage.html', credentials=credentials)
    except Exception as e:
        logger.error(f"Error fetching credentials: {e}")
        return render_template('LogInPage.html', error=str(e), credentials=[])

def choose_login_type():
    return render_template('LoginType.html')
