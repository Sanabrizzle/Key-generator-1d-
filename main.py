from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

KEYS_FILE = "keys.json"

# Ensure keys.json exists and has proper structure
def ensure_keys_file():
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            json.dump({"used_keys": {}, "claimed_ips": {}}, f, indent=4)
    else:
        try:
            with open(KEYS_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
        if "used_keys" not in data:
            data["used_keys"] = {}
        if "claimed_ips" not in data:
            data["claimed_ips"] = {}
        with open(KEYS_FILE, "w") as f:
            json.dump(data, f, indent=4)

def load_data():
    ensure_keys_file()
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_key(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route("/getKey")
def get_key():
    try:
        data = load_data()
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"

        claimed_ips = data.get("claimed_ips", {})
        last_claim_str = claimed_ips.get(user_ip)
        if last_claim_str:
            try:
                last_claim = datetime.fromisoformat(last_claim_str)
                if datetime.utcnow() - last_claim < timedelta(days=1):
                    return jsonify({"error": "You have already claimed a key today"}), 403
            except:
                pass

        # Generate new key
        key = generate_key()
        data["used_keys"][key] = {
            "claimed_by": user_ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        data["claimed_ips"][user_ip] = datetime.utcnow().isoformat()

        save_data(data)
        return jsonify({"key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/validateKey")
def validate_key():
    try:
        key = request.args.get("key")
        if not key:
            return jsonify({"valid": False})

        data = load_data()
        key_info = data["used_keys"].get(key)
        if not key_info:
            return jsonify({"valid": False})

        key_time = datetime.fromisoformat(key_info["timestamp"])
        if datetime.utcnow() - key_time > timedelta(days=1):
            return jsonify({"valid": False, "error": "Key expired"})

        return jsonify({"valid": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
