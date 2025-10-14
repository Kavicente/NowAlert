from flask import render_template, send_file, url_for
import os

def signup_type():
    return render_template('SignUpType.html')

def login_type():
    return render_template('LoginType.html')

def choose_login_type():
    return render_template('LoginType.html')

def download_apk_folder():
    zip_path = os.path.join(os.path.dirname(__file__), 'static', 'AlertNow.zip')
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, download_name='AlertNow.zip')
    else:
        return "File not found", 404