# webhook.py
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# Benutzerdefinierte Validierungslogik
def validate_pod_labels(labels):
    # Hier kannst du deine benutzerdefinierte Validierungslogik implementieren
    # Überprüfe, ob bestimmte Labels gesetzt sind oder nicht
    # ...
    return True  # Rückgabe von True oder False je nach Validierungsergebnis

# Webhook-Endpunkt
@app.route('/validate/', methods=['POST'])
def validate_pod_webhook():
    try:
        # Lese die eingehende Anfrage
        request_data = request.get_json()
        pod_metadata = request_data['request']['object']['metadata']
        pod_labels = pod_metadata.get('labels', {})
        print(pod_labels, request_data)
        # Führe die Validierungslogik aus
        if not validate_pod_labels(pod_labels):
            return jsonify({'allowed': False, 'status': 'Pod validation failed'}), 403

        # Antworte mit einem erfolgreichen Ergebnis
        return jsonify({'allowed': True, 'status': 'Pod validation passed'}), 200

    except Exception as e:
        logging.error(f'Error processing webhook request: {e}')
        return jsonify({'allowed': False, 'status': 'Error processing webhook request'}), 500

if __name__ == '__main__':
    # Konfiguration des Loggings
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    # Starte den Webhook-Server
    app.run(host='0.0.0.0', port=8085)
