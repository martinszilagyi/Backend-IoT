from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ttn-data', methods=['POST'])
def ttn_data():
    try:
        # Get JSON payload from TTN
        ttn_payload = request.json
        
        # Log or process the data
        print('Received TTN Data:', ttn_payload)

        # You can store it in a database or process it as needed
        # For example, you could use SQLite, PostgreSQL, etc.

        # Respond with success message
        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Failed to process data"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)