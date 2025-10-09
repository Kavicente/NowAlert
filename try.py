@socketio.on('barangay_health_response')
def handle_barangay_health_response(data):
    logger.info(f"Received health response from barangay: {data}")
    data['timestamp'] = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    try:
        conn.execute('''
                INSERT INTO barangay_response (
                    alert_id, health_cause, health_type, patient_age, patient_gender, 
                    lat, lon, barangay, emergency_type, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('alert_id'), data.get('health_cause'), data.get('health_type'),
                data.get('patient_age', '0'), data.get('patient_gender', ''), data.get('lat'), data.get('lon'),
                data.get('barangay'), data.get('emergency_type'), data['timestamp']
            ))
        conn.commit()
        logger.info(f"Stored barangay response for alert_id: {data.get('alert_id')}")
    except Exception as e:
        logger.error(f"Error storing barangay response: {e}")
    finally:
        conn.close()
         
    try:
        default_values - {
            'Year': datetime.now().year
            'Barangay': data.get('barangay', 'Unknown'),
            'Health_Type' 'Heart Attack',
        }