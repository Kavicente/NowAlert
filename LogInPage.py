from flask import request, redirect, url_for, render_template
import requests

def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        barangay = request.form['barangay']
        payload = {'username': username, 'password': password, 'barangay': barangay}
        response = requests.post('https://alert-858l.onrender.com/login', json=payload)
        if response.status_code == 200:
            data = response.json()
            role = data.get('role')
            if role == 'barangay':
                return redirect(url_for('barangay_dashboard'))
            elif role == 'cdrrmo':
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
    
    return render_template('LogInPage.html', credentials=credentials)

def choose_login_type():
    return render_template('LoginType.html')
