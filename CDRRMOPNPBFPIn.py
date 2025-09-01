from flask import request, redirect, url_for, render_template, session
import requests
from AlertNow import app, get_db_connection
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def login_cdrrmo_pnp_bfp():
    if request.method == 'POST':
        role = request.form.get('role').lower()
        municipality = request.form.get('municipality')
        contact_no = request.form.get('contact_no')
        password = request.form.get('password')
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE role = ? AND contact_no = ? AND password = ? AND assigned_municipality = ?',
                               (role, contact_no, password, municipality)).fetchone()
            if user:
                session['role'] = role
                session['unique_id'] = f"{role}_{contact_no}_{municipality}"
                session.permanent = True
                logger.info(f"Login successful for {role} in {municipality}")
                if role == 'cdrrmo':
                    return redirect(url_for('cdrrmo_dashboard'))
                elif role == 'pnp':
                    return redirect(url_for('pnp_dashboard'))
                elif role == 'bfp':
                    return redirect(url_for('bfp_dashboard'))
                else:
                    logger.warning(f"Invalid role for login: {role}")
                    return render_template('CDRRMOPNPBFPIn.html', error="Invalid role", credentials=[])
            else:
                logger.warning(f"Invalid credentials for contact_no: {contact_no}, role: {role}")
                return render_template('CDRRMOPNPBFPIn.html', error="Invalid credentials", credentials=[])
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return render_template('CDRRMOPNPBFPIn.html', error=str(e), credentials=[])
        finally:
            conn.close()
    
    # Fetch credentials for display
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT role, barangay, assigned_municipality, contact_no, password FROM users WHERE role != "admin"').fetchall()
        credentials = []
        for user in users:
            if user['role'] in ['cdrrmo', 'pnp', 'bfp']:
                credentials.append({
                    'role': user['role'],
                    'display': f"{user['role'].upper()} {user['assigned_municipality'] or 'Unknown Municipality'}",
                    'contact_no': user['contact_no'],
                    'password': user['password'],
                    'municipality': user['assigned_municipality'] or ''
                })
        conn.close()
        return render_template('CDRRMOPNPBFPIn.html', credentials=credentials)
    except Exception as e:
        logger.error(f"Error fetching credentials: {e}")
        return render_template('CDRRMOPNPBFPIn.html', error=str(e), credentials=[])

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('CDRRMOPNPIn.html')
