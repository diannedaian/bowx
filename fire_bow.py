import time
import csv
import serial
import serial.tools.list_ports
from pynput.mouse import Controller, Button

arduino = True  # Set to True to use Arduino, False to use keyboard
mouse = Controller()

# === PARAMETERS ===
SERIAL_PORT = '/dev/cu.usbserial-110'  # Update this if necessary
BAUD_RATE = 115200
TRIGGER_THRESHOLD = 4000  # You can adjust this
DEBOUNCE_TIME = 0.5       # Minimum time between fires, in seconds

last_trigger_time = 0

if arduino:
    # List available ports (optional)
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print("Found port:", port.device)

    # Create CSV file for logging (optional)
    f = open("data.csv", "w", newline='')
    writer = csv.writer(f)

    # Open serial connection
    serialCom = serial.Serial(SERIAL_PORT, BAUD_RATE)
    serialCom.dtr = False
    time.sleep(1)
    serialCom.reset_input_buffer()
    serialCom.dtr = True

    print("Waiting for data from ESP32...")

    while True:
        try:
            line = serialCom.readline().decode('utf-8').strip()
            if line == "":
                continue

            parts = line.split(',')
            values = [float(p) for p in parts]

            # Write to CSV
            writer.writerow(values)
            f.flush()

            # Fire bow if a specific value crosses threshold
            if len(values) >= 3:
                val = max(values[0], values[1], values[2])  # Read from ports 1–3 only
                current_time = time.time()

                if val > TRIGGER_THRESHOLD and current_time - last_trigger_time > DEBOUNCE_TIME:
                    print(f"Firing bow! value={val}")
                    mouse.press(Button.left)
                    time.sleep(0.1)
                    mouse.release(Button.left)
                    last_trigger_time = current_time

            current_time = time.time()

            if val > TRIGGER_THRESHOLD and current_time - last_trigger_time > DEBOUNCE_TIME:
                print(f"Firing bow! value={val}")
                mouse.press(Button.left)
                time.sleep(0.1)  # Hold for short time to simulate bow draw
                mouse.release(Button.left)
                last_trigger_time = current_time

        except Exception as e:
            print("Error:", e)
