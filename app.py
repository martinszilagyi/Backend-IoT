import os
import sys
import json
import requests
import base64
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta

app = Flask(__name__)
socketio = SocketIO(app)
google_api_key = os.environ.get("API_KEY")
last_data = {}

#Function decodes incoming data and 'jsonify' it to be compatible with Google Geolocation API.
def json_for_Google_API(wifi_bytes):
    print(wifi_bytes)

    #status of the device
    status = wifi_bytes[0]

    status_str = "Status Unknown"

    if status == 0:
        status_str = "Active Mode"
    elif status == 1:
        status_str == "Park Mode"
    elif status == 2:
        status_str == "Storage Mode"
    elif status == 3:
        status_str == "ALARM ACTIVATED"

    #percentage of the device
    percentage = wifi_bytes[1]

    #empty WiFi nodes 'array'
    access_points = []

    #Scan through all WiFi nodes
    for j in range(2, len(wifi_bytes), 7):
        #Extract MAC address of WiFi node
        mac = format((wifi_bytes[j] & 0xF0) >> 4, 'x') + format(wifi_bytes[j] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 1] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 1] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 2] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 2] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 3] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 3] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 4] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 4] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 5] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 5] & 0x0F, 'x')
        #Extract signal strength (minus sign not included in the message but always negative)
        rssi = -wifi_bytes[j + 6]

        #If there's valid MAC address and RSSI
        if mac and rssi:
            print(f"MAC: {mac}, RSSI: {rssi}")
            #append found MAC address properties
            access_points.append({
                "macAddress": mac,
                "signalStrength": rssi
            })

    #Final payload for Google
    google_payload = {
        "considerIp": "false",
        "wifiAccessPoints": access_points
    }

    #Debug
    print(json.dumps(google_payload, indent=2))

    #Returns with all extracted data
    return status_str, percentage, google_payload

#Rendering index.html
@app.route('/')
def index():
    #If there's a json file containing last available data, render the page with last data...
    try:
        with open("last_data.json", "r") as json_file:
            last_data = json.load(json_file)
            return render_template('index.html',
                                   data_exists=True,
                                   last_status = last_data['status'],
                                   last_percentage = last_data['percentage'],
                                   last_timestamp = last_data['timestamp'],
                                   last_latitude = last_data['location']['latitude'],
                                   last_longitude = last_data['location']['longitude'],
                                   last_accuracy = last_data['location']['accuracy'])
    except FileNotFoundError:
        print("last_data.json not found. No data to display.")
    #Otherwise render page with default appearance
    return render_template('index.html', data_exists=False,)

#upon triggering ttn-data
@app.route('/ttn-data', methods=['POST'])
def ttn_data():
    try:
        #Get json payload from the request
        if request.is_json:
            #Parse JSON data
            ttn_payload = request.get_json()

            #Check if the necessary fields exist in the data
            if 'uplink_message' not in ttn_payload or 'frm_payload' not in ttn_payload['uplink_message']:
                return jsonify({"error": "Missing required fields"}), 400

            #Process base64 encoded data
            wifi_props_64 = ttn_payload['uplink_message']['frm_payload']
            #Decode base64 data
            decoded_bytes = base64.b64decode(wifi_props_64)
            #Arrange properties into a list
            wifi_props = list(decoded_bytes)

            #Create appropriate json structure for using Google geolocation API
            status_str, percentage, google_payload = json_for_Google_API(wifi_props)

            #Get date and time (Server where the app is deployed is in other timezone)
            now = datetime.now() + timedelta(hours=2)

            #Trigger status script with new data
            socketio.emit('status', [status_str, percentage, now.strftime("%Y-%m-%d %H:%M:%S")])  # Emit status and percentage to all connected clients

            #Formulate to be stored data
            stored_data = {
                "status": status_str,
                "percentage": percentage,
                "location": {
                    "latitude": 0,
                    "longitude": 0,
                    "accuracy": 0,
                },
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            #Invoke API with the json structure created
            url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={google_api_key}"
            response = requests.post(url, json=google_payload)

            #If valid data has been received
            if response.status_code == 200:
                #Process the json response
                data = response.json()
                
                #Extract and print(debug) relevant details
                if 'location' in data:
                    location = data['location']
                    latitude = location.get('lat')
                    longitude = location.get('lng')
                    accuracy = data.get('accuracy')

                    stored_data['location']['latitude'] = latitude
                    stored_data['location']['longitude'] = longitude
                    stored_data['location']['accuracy'] = accuracy

                    #Debug
                    print(f"Latitude: {latitude}")
                    print(f"Longitude: {longitude}")
                    print(f"Accuracy: {accuracy} meters")

                    #Emit the data to all connected clients using the correct 'socketio.emit' method
                    socketio.emit('location', data)
                else:
                    #Location cannot be determined
                    print("Location data not found in the response.")
            else:
                #debug
                print(f"Error: {response.status_code} - {response.text}")

            #Save data into a json file that would be loaded in on page refresh
            with open("last_data.json", "w") as json_file:
                json.dump(stored_data, json_file, indent=4)

            #Return a success response
            return jsonify({"message": "Data received successfully", "data": ttn_payload}), 200
        else:
            #Return error response
            return jsonify({"error": "Invalid data format. Expected JSON."}), 400

    except Exception as e:
        #Log the error
        print(f"Error processing data: {e}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500

@app.route('/set_opMode', methods=['POST'])
def set_opMode():
    data = request.get_json()
    mode = data.get('mode')
    print(f"Set opmode to: {mode}")
    
    #CALL TTN API TO SEND DOWNLINK MSG





    return jsonify({'mode': mode}), 200

#Start the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)