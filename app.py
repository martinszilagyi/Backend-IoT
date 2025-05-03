import os
import sys
from decouple import config
import json
import requests
import base64
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
google_api_key = os.environ.get("API_KEY")

#This function decodes incoming data and 'jsonify' it to be compatible with Google Geolocation API.
def json_for_Google_API(wifi_bytes):
    print(wifi_bytes)

    status = wifi_bytes[0]                                              #status of the device
    percentage = wifi_bytes[1]                                          #percentage of the device

    access_points = []

    for j in range(2, len(wifi_bytes), 7):
        mac = format((wifi_bytes[j] & 0xF0) >> 4, 'x') + format(wifi_bytes[j] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 1] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 1] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 2] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 2] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 3] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 3] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 4] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 4] & 0x0F, 'x') + ':' + format((wifi_bytes[j + 5] & 0xF0) >> 4, 'x') + format(wifi_bytes[j + 5] & 0x0F, 'x')
        rssi = -wifi_bytes[j + 6]

        if mac and rssi:
            print(f"MAC: {mac}, RSSI: {rssi}")
            access_points.append({                                              #temporary access point properites in json format
                "macAddress": mac,
                "signalStrength": rssi
            })

    #Final payload for Google
    google_payload = {
        "considerIp": "false",
        "wifiAccessPoints": access_points
    }

    #debug
    print(json.dumps(google_payload, indent=2))

    return status, percentage, google_payload

#Rendering index.html
@app.route('/')
def index():
    return render_template('index.html')

#upon triggering ttn-data
@app.route('/ttn-data', methods=['POST'])
def ttn_data():
    try:
        #Get json payload from the request
        if request.is_json:
            ttn_payload = request.get_json()  # Parse JSON data
            #print('Received TTN Data:', ttn_payload)

            #Check if the necessary fields exist in the data (Can be deleted...)
            if 'uplink_message' not in ttn_payload :
                return jsonify({"error": "Missing required fields"}), 400

            #Process data
            wifi_props_64 = ttn_payload['uplink_message']['frm_payload'] #base64 encoded data
            #print(f"Received data: {wifi_props}")
            decoded_bytes = base64.b64decode(wifi_props_64)
            wifi_props = list(decoded_bytes)

            #Create appropriate json structure for using Google geolocation API
            status, percentage, google_payload = json_for_Google_API(wifi_props)

            socketio.emit('status', [status, percentage])

            #Invoke API with the json structure created
            url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={google_api_key}"
            response = requests.post(url, json=google_payload)
            if response.status_code == 200:
                #Process the json response
                data = response.json()
                
                #Extract and print relevant details
                if 'location' in data:
                    location = data['location']
                    latitude = location.get('lat')
                    longitude = location.get('lng')
                    accuracy = data.get('accuracy')

                    #Debug
                    print(f"Latitude: {latitude}")
                    print(f"Longitude: {longitude}")
                    print(f"Accuracy: {accuracy} meters")

                    # Emit the data to all connected clients using the correct 'socketio.emit' method
                    socketio.emit('new_data', data)
                else:
                    print("Location data not found in the response.")
            else:
                print(f"Error: {response.status_code} - {response.text}")

            #Return a success response
            return jsonify({"message": "Data received successfully", "data": ttn_payload}), 200
        else:
            return jsonify({"error": "Invalid data format. Expected JSON."}), 400

    except Exception as e:
        #Log the error
        print(f"Error processing data: {e}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500

#Start the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)