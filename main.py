from flask import Flask, jsonify, request
import json
import os
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

# ------------------------
# Config
# ------------------------
KEY_FILE = "keys.json"
KEY_LENGTH = 12
EXPIRE_DAYS = 1  # Optional expiration

# ------------------------
# Load or initialize keys
# ------------------------
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        data = json.load(f)
        issued_keys = set(data.get("issued_keys", []))
        used_keys = data.get("used_keys", {})
else:
    issued_keys = set()
    used_keys = {}

# ------------------------
# Helper functions
# ------------------------
def save_keys():
    with open(KEY_FILE, "w") as f:
        json.dump({
            "issued_keys": list(issued_keys),
            "used_keys": used_keys
        }, f)

def generate_key():
    while True:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=KEY_LENGTH))
        if key not in issued_keys:
            issued_keys.add(key)
            save_keys()
            return key

def is_key_expired(key):
    if key in used_keys:
        expire_time = datetime.fromisoformat(used_keys[key]["timestamp"]) + timedelta(days=EXPIRE_DAYS)
        return datetime.utcnow() > expire_time
    return False

# ------------------------
# Endpoints
# ------------------------
@app.route("/getKey")
def get_key():
    key = generate_key()
    return jsonify({"key": key})

@app.route("/validateKey")
def validate_key():
    key = request.args.get("key")
    if key in issued_keys:
        # Check if key is already used
        if key in used_keys and not is_key_expired(key):
            return jsonify({"valid": False})
        # Mark as used
        used_keys[key] = {"timestamp": datetime.utcnow().isoformat()}
        save_keys()
        return jsonify({"valid": True})
    return jsonify({"valid": False})

# ------------------------
# Run server
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
