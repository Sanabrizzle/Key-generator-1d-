from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ------------------------
# Config
# ------------------------
KEY_FILE = "keys.json"
EXPIRE_DAYS = 1  # optional expiration for keys

# ------------------------
# Load keys from file
# ------------------------
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        data = json.load(f)
        unused_keys = data.get("unused_keys", [])
        used_keys = data.get("used_keys", {})
else:
    unused_keys = []
    used_keys = {}

def save_keys():
    with open(KEY_FILE, "w") as f:
        json.dump({"unused_keys": unused_keys, "used_keys": used_keys}, f)

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
    if not unused_keys:
        return jsonify({"error": "No keys available"}), 404

    key = unused_keys.pop(0)  # take the first unused key
    used_keys[key] = {"timestamp": datetime.utcnow().isoformat()}
    save_keys()
    return jsonify({"key": key})

@app.route("/validateKey")
def validate_key():
    key = request.args.get("key")
    if key in used_keys and not is_key_expired(key):
        return jsonify({"valid": True})
    return jsonify({"valid": False})

# ------------------------
# Run server
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
