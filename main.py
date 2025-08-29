from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

KEYS_FILE = "keys.json"

# Ensure keys.json exists
if not os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "w") as f:
        json.dump({"used_keys": {}, "claimed_ips": {}}, f, indent=4)

def load_data():
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_key(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route("/getKey")
def get_key():
    data = load_data()
    user_ip = request.remote_addr

    # Check if IP already claimed within 24 hours
    claimed_ips = data.get("claimed_ips", {})
    if user_ip in claimed_ips:
        last_claim = datetime.fromisoformat(claimed_ips[user_ip])
        if datetime.utcnow() - last_claim < timedelta(days=1):
            return jsonify({"error": "You have already claimed a key today"}), 403

    # Generate a new key
    key = generate_key()
    data["used_keys"][key] = {"claimed_by": user_ip, "timestamp": datetime.utcnow().isoformat()}
    data["claimed_ips"][user_ip] = datetime.utcnow().isoformat()

    save_data(data)
    return jsonify({"key": key})

@app.route("/validateKey")
def validate_key():
    key = request.args.get("key")
    if not key:
        return jsonify({"valid": False})
    data = load_data()
    if key in data["used_keys"]:
        return jsonify({"valid": True})
    return jsonify({"valid": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
