from flask import request, redirect, url_for, render_template
import requests

def login_cdrmo_pnp_bfp():
    if request.method == 'POST':
        municipality = request.form['municipality']
        contact_no = request.form['contact_no']
        password = request.form['password']
        role = request.form['role'].lower()
        payload = {
            'municipality': municipality,
            'contact_no': contact_no,
            'password': password,
            'role': role
        }
        response = requests.post('https://alert-858l.onrender.com/login_cdrrmo_pnp_bfp', json=payload)
        if response.status_code == 200:
            data = response.json()
            role = data.get('role')
            if role == 'cdrrmo':
                return redirect(url_for('cdrrmo_dashboard'))
            elif role == 'pnp':
                return redirect(url_for('pnp_dashboard'))
            elif role == 'bfp':
                return redirect(url_for('bfp_dashboard'))
        return "Invalid credentials", 401
    
    # Fetch credentials for display
    try:
        response = requests.get('https://alert-858l.onrender.com/api/get_credentials')
        if response.status_code == 200:
            credentials = response.json()
        else:
            credentials = []
    except Exception as e:
        credentials = []
        print(f"Error fetching credentials: {e}")
    
    return render_template('CDRRMOPNPBFPIn.html', credentials=credentials)

def choose_login_type():
    return render_template('LoginType.html')

def go_to_cdrrmopnpin():
    return render_template('CDRRMOPNPIn.html')
