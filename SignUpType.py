from flask import render_template, send_file, url_for
import os
import qrcode

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

def generate_qr():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data('http://alertnow-cgre.onrender.com/static/AlertNow.zip')  # Use local URL for testing
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(os.path.dirname(__file__), 'static', 'qrcode.png'))
    return "QR code generated", 200