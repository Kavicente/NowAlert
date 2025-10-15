import qrcode
import os

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data('http://alertnow-cgre.onrender.com/static/AlertNow,zip')  # Use local URL for testing
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save(os.path.join(os.path.dirname(__file__), 'static', 'qrcode.png'))