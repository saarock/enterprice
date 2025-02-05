import serial
import threading
import time
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import deque

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

# Serial connection settings
SERIAL_PORT = 'COM3'  # Change this to your Arduino's port
BAUD_RATE = 9600
TIMEOUT = 1

# Arduino data storage
arduino_data = {"force": 0.0}
data_lock = threading.Lock()
VALUE_PATTERN = r"[-+]?\d*\.\d+|\d+"  # Pattern for extracting numeric values

# Buffer for recent force readings
force_values = deque(maxlen=10)



def read_serial_data():
    """Continuously read data from the serial port."""
    global arduino_data
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    try:
                        values = re.findall(VALUE_PATTERN, line)
                        if len(values) == 1:
                            force = float(values[0])
                            print(f"Force: {force}")
                            with data_lock:
                                arduino_data["force"] = force

                            # Collect only non-zero force values and maintain the buffer
                            with data_lock:
                                if force > 0:
                                    print(force)
                                    force_values.append(force)

                          
                        

                    except ValueError as e:
                        print(f"Error parsing data: {e} | Data: {line}")
                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Serial error: {e}")

@app.route('/data', methods=['GET'])
def get_data():
    """API endpoint to get the latest Arduino data."""
    with data_lock:
        return jsonify(arduino_data)

@app.route('/reset', methods=['POST'])
def reset_data():
    """Reset the Arduino data force value to 0."""
    with data_lock:
        arduino_data["force"] = 0.0
    return jsonify({"status": "success", "message": "Force value reset."})

if __name__ == '__main__':
    print("Server starting...")
    threading.Thread(target=read_serial_data, daemon=True).start()  # Start serial data reading in a separate thread
    app.run(host='0.0.0.0', port=8000)
