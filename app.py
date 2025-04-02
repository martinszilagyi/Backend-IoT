from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

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
            print('Received TTN Data:', ttn_payload)

            # Check if the necessary fields exist in the data
            if 'dev_eui' not in ttn_payload or 'payload_fields' not in ttn_payload:
                return jsonify({"error": "Missing required fields"}), 400

            # Process data (you can add more functionality here as needed)
            temperature = ttn_payload['payload_fields'].get('temperature')
            humidity = ttn_payload['payload_fields'].get('humidity')

            print(f"Temperature: {temperature}, Humidity: {humidity}")

            # Emit the data to all connected clients using the correct 'socketio.emit' method
            socketio.emit('new_data', {
                "dev_eui": ttn_payload['dev_eui'],
                "temperature": temperature,
                "humidity": humidity
            })

            # Return a success response
            return jsonify({"message": "Data received successfully", "data": ttn_payload}), 200
        else:
            return jsonify({"error": "Invalid data format. Expected JSON."}), 400

    except Exception as e:
        # Log the error
        print(f"Error processing data: {e}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500

if __name__ == '__main__':
    # Start the server and use Socket.IO to handle real-time connections
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)