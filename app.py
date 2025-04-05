import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
google_api_key = "AIzaSyC5TNTnmnxJ7Mkhx48--XOCSg7WX9NndHU"

def json_for_Google_API(wifi_str):
    access_points = []
    for line in wifi_str.strip().split('\n'): #separate each rows
        parts = line.split('|')
        ssid = mac = rssi = None
        for part in parts:
            part = part.strip()
            if (part.startswith("SSID")):
                ssid = part.split("SSID:")[1].strip()
            if (part.startswith("MAC")):
                mac = part.split("MAC:")[1].strip()
            if (part.startswith("RSSI")):
                rssi = part.split("RSSI:")[1].strip()
        if mac and rssi:
            access_points.append({
                "macAddress": mac,
                "signalStrength": rssi
            })

    # Final payload for Google
    google_payload = {
        "wifiAccessPoints": access_points
    }

    print(json.dumps(google_payload, indent=2))

    return google_payload

@app.route('/')
def index():
    # Serve the HTML page directly from the backend
    return render_template('index.html')  # This renders the HTML page when visiting "/"

@app.route('/ttn-data', methods=['POST'])
def ttn_data():
    try:
        # Get JSON payload from the request
        if request.is_json:
            ttn_payload = request.get_json()  # Parse JSON data
            #print('Received TTN Data:', ttn_payload)

            # Check if the necessary fields exist in the data
            if 'uplink_message' not in ttn_payload :
                return jsonify({"error": "Missing required fields"}), 400

            # Process data (you can add more functionality here as needed)
            wifi_props = ttn_payload['uplink_message']['decoded_payload']['bytes']
            wifi_str = bytes(wifi_props).decode('utf-8')

            google_payload = json_for_Google_API(wifi_str)

            url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={google_api_key}"
            response = requests.post(url, json=google_payload)
            if response.status_code == 200:
                # Process the JSON response
                data = response.json()
                
                # Extract and print relevant details
                if 'location' in data:
                    location = data['location']
                    latitude = location.get('lat')
                    longitude = location.get('lng')
                    accuracy = data.get('accuracy')

                    print(f"Latitude: {latitude}")
                    print(f"Longitude: {longitude}")
                    print(f"Accuracy: {accuracy} meters")
                    # Emit the data to all connected clients using the correct 'socketio.emit' method
                    socketio.emit('new_data', data)
                else:
                    print("Location data not found in the response.")
            else:
                print(f"Error: {response.status_code} - {response.text}")

            # Return a success response
            return jsonify({"message": "Data received successfully", "data": ttn_payload}), 200
        else:
            return jsonify({"error": "Invalid data format. Expected JSON."}), 400

    except Exception as e:
        # Log the error
        print(f"Error processing data: {e}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)