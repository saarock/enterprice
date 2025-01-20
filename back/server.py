import serial
import threading
import time
import re
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for frontend at localhost:5173
CORS(app, origins=["http://localhost:5173/"])
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173/"])

# Serial connection settings
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
TIMEOUT = 1

# Arduino data storage
arduino_data = {"voltage": 0.0, "resistance": 0.0, "force": 0.0}
data_lock = threading.Lock()
VALUE_PATTERN = r"[-+]?\d*\.\d+|\d+"

# Buffer for recent force readings
force_values = []
BUFFER_SIZE = 10  # Size of the buffer for recent forces
final_data_lock = threading.Lock()

def calculate_average_force():
    """Calculate the average of the recent non-zero force values."""
    with data_lock:
        # Filter out zero force values and calculate the average
        non_zero_forces = [force for force in force_values if force > 0]
        if non_zero_forces:
            avg_force = sum(non_zero_forces) / len(non_zero_forces)
        else:
            avg_force = 0.0  # Default to 0 if no valid force values are available
    return avg_force

def reset_data_after_timeout():
    """Reset the data after a timeout."""
    time.sleep(5)
    with final_data_lock:
        global arduino_data
        arduino_data = {"voltage": 0.0, "resistance": 0.0, "force": 0.0}
    socketio.emit('reset_data', arduino_data)  # Notify frontend of reset

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
                    print(f"Received data: {line}")
                    try:
                        values = re.findall(VALUE_PATTERN, line)
                        if len(values) == 3:
                            voltage, resistance, force = map(float, values)

                            with data_lock:
                                arduino_data["voltage"] = voltage
                                arduino_data["resistance"] = resistance
                                arduino_data["force"] = force

                            # Collect only non-zero force values and maintain the buffer
                            with data_lock:
                                if force > 0:
                                    force_values.append(force)
                                    if len(force_values) > BUFFER_SIZE:
                                        force_values.pop(0)

                            print(f"Force values buffer: {force_values}")

                            # Calculate the average force
                            avg_force = calculate_average_force()
                            print(f"Average force: {avg_force}")

                            # Send data to frontend
                            with final_data_lock:
                                arduino_data["force"] = avg_force

                            socketio.emit('new_data', arduino_data)  # Emit to frontend
                            print(f"Sent data: {arduino_data}")

                            # Clear force values after sending
                            with data_lock:
                                force_values.clear()

                            # Start a thread to reset data after timeout
                            threading.Thread(target=reset_data_after_timeout, daemon=True).start()
                        else:
                            print(f"Invalid data format: {line}")
                    except ValueError as e:
                        print(f"Error parsing data: {e} | Data: {line}")
                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Serial error: {e}")

@app.route('/data', methods=['GET'])
def get_data():
    """API endpoint to get the latest Arduino data."""
    print("Data request received")
    with final_data_lock:
        return jsonify(arduino_data)

if __name__ == '__main__':
    threading.Thread(target=read_serial_data, daemon=True).start()
    socketio.run(app, debug=True, host='0.0.0.0', port=6000)
