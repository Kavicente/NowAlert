import sqlite3
import logging
import uuid
from datetime import datetime
import pytz
from flask_socketio import emit

# Initialize logger
logger = logging.getLogger(__name__)

def setup_responses(app, socketio, alerts, accepted_roles, get_db_connection, get_municipality_from_barangay):
    @socketio.on('alert')
    def handle_new_alert(data):
        try:
            logger.info(f"New alert received: {data}")
            alert_id = str(uuid.uuid4())
            data['alert_id'] = alert_id
            data['timestamp'] = datetime.utcnow().isoformat()
            data['resident_barangay'] = data.get('barangay', 'Unknown')

            alerts.append(data)

            barangay_room = f"barangay_{data.get('barangay').lower() if data.get('barangay') else ''}"
            emit('new_alert', data, room=barangay_room)
            logger.info(f"Alert emitted to room {barangay_room}")

            map_data = {
                'lat': data.get('lat'),
                'lon': data.get('lon'),
                'barangay': data.get('barangay'),
                'emergency_type': data.get('emergency_type')
            }
            emit('update_map', map_data, room=barangay_room)
        except Exception as e:
            logger.error(f"Error handling alert: {e}")

    @socketio.on('forward_alert')
    def handle_forward_alert(data):
        logger.info(f"Forward alert received: {data}")
        try:
            target_role = data.get('target_role').lower()
            municipality = get_municipality_from_barangay(data.get('barangay', 'Unknown'))
            alert_id = data.get('alert_id')
            alert_data = next((alert for alert in alerts if alert['alert_id'] == alert_id), None)
            if alert_data:
                if target_role == 'cdrrmo':
                    emit('redirected_alert', alert_data, room=f"cdrrmo_{municipality.lower()}")
                    emit('redirected_alert', alert_data, room=f"pnp_{municipality.lower()}")
                    logger.info(f"Alert {alert_id} forwarded to cdrrmo_{municipality.lower()} and pnp_{municipality.lower()}")
                elif target_role == 'bfp':
                    emit('redirected_alert', alert_data, room=f"bfp_{municipality.lower()}")
                    emit('redirected_alert', alert_data, room=f"pnp_{municipality.lower()}")
                    logger.info(f"Alert {alert_id} forwarded to bfp_{municipality.lower()} and pnp_{municipality.lower()}")
                elif target_role == 'pnp':
                    emit('redirected_alert', alert_data, room=f"pnp_{municipality.lower()}")
                    logger.info(f"Alert {alert_id} forwarded to pnp_{municipality.lower()}")
                elif target_role in ['health', 'hospital']:
                    emit('redirected_alert', alert_data, room=f"{target_role}_{municipality.lower()}")
                    logger.info(f"Alert {alert_id} forwarded to {target_role}_{municipality.lower()}")
                else:
                    logger.error(f"Invalid target role: {target_role}")
        except Exception as e:
            logger.error(f"Error forwarding alert: {e}")

    @socketio.on('response_update')
    def handle_response(data):
        conn = get_db_connection()
        c = conn.cursor()
        try:
            manila = pytz.timezone('Asia/Manila')
            base_time = datetime.now(manila)
            
            if data.get('emergency_type') == 'Road Accident':
                c.execute('''
                    INSERT INTO barangay_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'),
                    data.get('road_accident_cause'),
                    data.get('road_accident_type'),
                    data.get('weather'),
                    data.get('road_condition'),
                    data.get('vehicle_type'),
                    data.get('driver_age'),
                    data.get('driver_gender'),
                    data.get('lat'),
                    data.get('lon'),
                    data.get('barangay'),
                    data.get('emergency_type'),
                    base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            elif data.get('emergency_type') == 'Fire Incident':
                c.execute('''
                    INSERT INTO barangay_fire_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'), data.get('fire_type'), data.get('fire_cause'),
                    data.get('weather'), data.get('fire_severity'), data.get('lat'), data.get('lon'),
                    data.get('barangay'), data.get('emergency_type'), base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            elif data.get('emergency_type') == 'Crime Incident':
                c.execute('''
                    INSERT INTO barangay_crime_response (alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender, suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'), data.get('crime_type'), data.get('crime_cause'), data.get('level'),
                    data.get('suspect_gender'), data.get('victim_gender'), data.get('suspect_age'),
                    data.get('victim_age'), data.get('lat'), data.get('lon'), data.get('barangay'),
                    data.get('emergency_type'), base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            elif data.get('emergency_type') == 'Health Emergency':
                c.execute('''
                    INSERT INTO barangay_health_response (alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'), data.get('health_type'), data.get('health_cause'),
                    data.get('weather'), data.get('patient_age'), data.get('patient_gender'),
                    data.get('lat'), data.get('lon'), data.get('barangay'), data.get('emergency_type'),
                    base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            c.execute('''
                INSERT INTO bfp_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('alert_id'),
                data.get('fire_type'),
                data.get('fire_cause'),
                data.get('weather'),
                data.get('fire_severity'),
                data.get('lat'),
                data.get('lon'),
                data.get('barangay'),
                data.get('emergency_type'),
                base_time.strftime('%Y-%m-%d %H:%M:%S'),
                data.get('responded', True)
            ))
            c.execute('''
                INSERT INTO cdrrmo_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('alert_id'),
                data.get('road_accident_cause'),
                data.get('road_accident_type'),
                data.get('weather'),
                data.get('road_condition'),
                data.get('vehicle_type'),
                data.get('driver_age'),
                data.get('driver_gender'),
                data.get('lat'),
                data.get('lon'),
                data.get('barangay'),
                data.get('emergency_type'),
                base_time.strftime('%Y-%m-%d %H:%M:%S'),
                data.get('responded', True)
            ))
            if data.get('emergency_type') == 'Road Accident':
                c.execute('''
                    INSERT INTO pnp_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'),
                    data.get('road_accident_cause'),
                    data.get('road_accident_type'),
                    data.get('weather'),
                    data.get('road_condition'),
                    data.get('vehicle_type'),
                    data.get('driver_age'),
                    data.get('driver_gender'),
                    data.get('lat'),
                    data.get('lon'),
                    data.get('barangay'),
                    data.get('emergency_type'),
                    base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            elif data.get('emergency_type') == 'Fire Incident':
                c.execute('''
                    INSERT INTO pnp_fire_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'), data.get('fire_type'), data.get('fire_cause'),
                    data.get('weather'), data.get('fire_severity'), data.get('lat'), data.get('lon'),
                    data.get('barangay'), data.get('emergency_type'), base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            elif data.get('emergency_type') == 'Crime Incident':
                c.execute('''
                    INSERT INTO pnp_crime_response (alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender, suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('alert_id'), data.get('crime_type'), data.get('crime_cause'), data.get('level'),
                    data.get('suspect_gender'), data.get('victim_gender'), data.get('suspect_age'),
                    data.get('victim_age'), data.get('lat'), data.get('lon'), data.get('barangay'),
                    data.get('emergency_type'), base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('responded', True)
                ))
            c.execute('''
                INSERT INTO health_response (
                    alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('alert_id'),
                data.get('health_type'),
                data.get('health_cause'),
                data.get('weather'),
                data.get('patient_age'),
                data.get('patient_gender'),
                data.get('lat'),
                data.get('lon'),
                data.get('barangay'),
                data.get('emergency_type'),
                base_time.strftime('%Y-%m-%d %H:%M:%S'),
                data.get('responded', True)
            ))
            c.execute('''
                INSERT INTO hospital_response (
                    alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('alert_id'),
                data.get('health_type'),
                data.get('health_cause'),
                data.get('weather'),
                data.get('patient_age'),
                data.get('patient_gender'),
                data.get('lat'),
                data.get('lon'),
                data.get('barangay'),
                data.get('emergency_type'),
                base_time.strftime('%Y-%m-%d %H:%M:%S'),
                data.get('responded', True)
            ))
            conn.commit()
            logger.info(f"Response data inserted for alert_id: {data.get('alert_id')}")
            # Emit updates to respective chart pages
            from BarangayCharts import handle_barangay_response
            from BFPCharts import handle_bfp_response
            from CDRRMOCharts import handle_cdrrmo_response
            from PNPCharts import handle_pnp_response
            from HealthCharts import handle_health_response
            from HospitalCharts import handle_hospital_response
            handle_barangay_response(data)
            handle_bfp_response(data)
            handle_cdrrmo_response(data)
            handle_pnp_response(data)
            handle_health_response(data)
            handle_hospital_response(data)
        except Exception as e:
            logger.error(f"Error inserting response data: {e}")
            conn.rollback()
        finally:
            conn.close()

    @socketio.on('submit_response')
    def handle_submit_response(data):
        try:
            alert_id = data.get('alert_id', str(uuid.uuid4()))
            role = data.get('role', '').lower()
            barangay = data.get('barangay', '')
            municipality = get_municipality_from_barangay(barangay) or data.get('municipality', '')
            emergency_type = data.get('emergency_type', '')
            road_accident_cause = data.get('road_accident_cause', '')
            road_accident_type = data.get('road_accident_type', '')
            weather = data.get('weather', '')
            road_condition = data.get('road_condition', '')
            vehicle_type = data.get('vehicle_type', '')
            driver_age = data.get('driver_age', '')
            driver_gender = data.get('driver_gender', '')
            fire_type = data.get('fire_type', '')
            fire_cause = data.get('fire_cause', '')
            fire_severity = data.get('fire_severity', '')
            crime_type = data.get('crime_type', '')
            crime_cause = data.get('crime_cause', '')
            level = data.get('level', '')
            suspect_gender = data.get('suspect_gender', '')
            victim_gender = data.get('victim_gender', '')
            suspect_age = data.get('suspect_age', '')
            victim_age = data.get('victim_age', '')
            health_type = data.get('health_type', '')
            health_cause = data.get('health_cause', '')
            patient_age = data.get('patient_age', '')
            patient_gender = data.get('patient_gender', '')
            lat = data.get('lat', 0.0)
            lon = data.get('lon', 0.0)
            timestamp = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
            responded = True

            conn = get_db_connection()
            c = conn.cursor()
            if role == 'barangay':
                if emergency_type == 'Road Accident':
                    c.execute('''
                        INSERT INTO barangay_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, road_accident_cause, road_accident_type, weather, road_condition,
                        vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type,
                        timestamp, responded
                    ))
                elif emergency_type == 'Fire Incident':
                    c.execute('''
                        INSERT INTO barangay_fire_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon,
                        barangay, emergency_type, timestamp, responded
                    ))
                elif emergency_type == 'Crime Incident':
                    c.execute('''
                        INSERT INTO barangay_crime_response (alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender, suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender,
                        suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded
                    ))
                elif emergency_type == 'Health Emergency':
                    c.execute('''
                        INSERT INTO barangay_health_response (alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, health_type, health_cause, weather, patient_age, patient_gender,
                        lat, lon, barangay, emergency_type, timestamp, responded
                    ))
            elif role == 'cdrrmo':
                c.execute('''
                    INSERT INTO cdrrmo_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id, road_accident_cause, road_accident_type, weather, road_condition,
                    vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type,
                    timestamp, responded
                ))
            elif role == 'pnp':
                if emergency_type == 'Crime Incident':
                    c.execute('''
                        INSERT INTO pnp_crime_response (alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender, suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, crime_type, crime_cause, level, suspect_gender, victim_gender,
                        suspect_age, victim_age, lat, lon, barangay, emergency_type, timestamp, responded
                    ))
                elif emergency_type == 'Fire Incident':
                    c.execute('''
                        INSERT INTO pnp_fire_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon,
                        barangay, emergency_type, timestamp, responded
                    ))
                else:
                    c.execute('''
                        INSERT INTO pnp_response (alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, timestamp, responded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id, road_accident_cause, road_accident_type, weather, road_condition,
                        vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type,
                        timestamp, responded
                    ))
            elif role == 'bfp':
                c.execute('''
                    INSERT INTO bfp_response (alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon, barangay, emergency_type, timestamp, responded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id, fire_type, fire_cause, weather, fire_severity, lat, lon,
                    barangay, emergency_type, timestamp, responded
                ))
            elif role == 'health':
                c.execute('''
                    INSERT INTO health_response (
                        alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id, health_type, health_cause, weather, patient_age, patient_gender,
                    lat, lon, barangay, emergency_type, timestamp, responded
                ))
            elif role == 'hospital':
                c.execute('''
                    INSERT INTO hospital_response (
                        alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, timestamp, responded, assigned_hospital
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id, health_type, health_cause, weather, patient_age, patient_gender,
                    lat, lon, barangay, emergency_type, timestamp, responded, data.get('assigned_hospital', '')
                ))
            conn.commit()
            conn.close()

            # Emit response without prediction
            response_data = {
                'alert_id': alert_id,
                'role': role,
                'barangay': barangay,
                'municipality': municipality,
                'emergency_type': emergency_type,
                'timestamp': timestamp
            }
            emit(f'{role}_response', response_data)
            logger.info(f"Response submitted for alert {alert_id} by {role}")
        except Exception as e:
            logger.error(f"Error in handle_submit_response: {e}")
            conn.rollback()
            conn.close()

    @socketio.on('role_accepted')
    def role_accepted(data):
        logger.info(f"Role {data['role']} accepted for alert {data['alert_id']}")
        try:
            alert_id = data['alert_id']
            role = data['role'].lower()
            if alert_id not in accepted_roles:
                accepted_roles[alert_id] = []
            if role not in accepted_roles[alert_id]:
                accepted_roles[alert_id].append(role)
                alert_data = next((alert for alert in alerts if alert['alert_id'] == alert_id), None)
                if alert_data:
                    namespace = f'/{role}'
                    emit('new_alert', alert_data, namespace=namespace)
                    logger.info(f"Forwarded alert {alert_id} to {namespace}")
        except Exception as e:
            logger.error(f"Error in role_accepted: {e}")

    @socketio.on('role_declined')
    def role_declined(data):
        logger.info(f"Role {data['role']} declined for alert {data['alert_id']}")
        try:
            alert_id = data['alert_id']
            role = data['role'].lower()
            if alert_id in accepted_roles and role in accepted_roles[alert_id]:
                accepted_roles[alert_id].remove(role)
                logger.info(f"Removed {role} from accepted roles for alert {alert_id}")
        except Exception as e:
            logger.error(f"Error in role_declined: {e}")

    @socketio.on('redirect_alert')
    def handle_redirect_alert(data):
        logger.debug(f"Redirected alert received: {data}")
        try:
            target_role = data.get('target_role').lower()
            municipality = data.get('municipality', '').lower()
            if target_role in ['bfp', 'cdrrmo', 'health', 'hospital', 'pnp']:
                emit('redirected_alert', data, room=f"{target_role}_{municipality}")
            else:
                logger.error(f"Invalid target role: {target_role}")
        except Exception as e:
            logger.error(f"Error in handle_redirect_alert: {e}")