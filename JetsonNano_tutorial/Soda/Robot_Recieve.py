from flask import Flask, request, jsonify
from pop import Pilot
import threading
import time

app = Flask(__name__)
bot = Pilot.SerBot()
bot.setSpeed(99)

# Shared state for watchdog
last_command_time = time.time()
WATCHDOG_TIMEOUT = 1.0  # seconds

# --- Define command handler functions ---
def move_forward():
    bot.forward()
    bot.steering = 0

def move_backward():
    bot.backward(99)
    bot.steering = 0

def turn_left():
    bot.forward()
    bot.steering = -0.5

def turn_right():
    bot.forward()
    bot.steering = 0.5

def stop_bot():
    bot.stop()

# --- Command dispatch table ---
command_table = {
    "forward": move_forward,
    "backward": move_backward,
    "left": turn_left,
    "right": turn_right,
    "stop": stop_bot
}

# --- Watchdog thread ---
def watchdog():
    global last_command_time
    while True:
        time.sleep(0.1)
        if time.time() - last_command_time > WATCHDOG_TIMEOUT:
            stop_bot()

# Start watchdog in background
threading.Thread(target=watchdog, daemon=True).start()

# --- Flask route ---
@app.route('/control', methods=['POST'])
def control():
    global last_command_time
    data = request.get_json()
    if not data or 'cmd' not in data:
        return jsonify({"error": "Missing 'cmd'"}), 400

    cmd = data['cmd']
    print(f"📥 Received command: {cmd}")
    last_command_time = time.time()  # Reset watchdog

    handler = command_table.get(cmd)
    if handler:
        handler()
        return jsonify({"status": "ok", "executed": cmd})
    else:
        return jsonify({"error": "Unknown command"}), 400

# --- Run server ---
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("🛑 Dừng lại bởi người dùng")
        stop_bot()
