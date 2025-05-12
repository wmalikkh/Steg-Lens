from flask import Flask, request, jsonify, make_response, send_from_directory
import os
import uuid
from flask_cors import CORS
from Steganography_tool import hide_message, reveal_message
from Cryptography_tool import encrypt, decrypt

app = Flask(__name__)
CORS(app)

@app.route("/hide", methods=["POST"])
def hide_route():
    if "image" not in request.files or "message" not in request.form:
        return jsonify({"error": "Image or message missing."})

    image = request.files["image"]
    message = request.form["message"]

    try:
        filename = image.filename
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ['.jpeg', '.jpg', '.png', '.gif']:
            ext = '.png'

        temp_input_path = f"temp_input_{uuid.uuid4().hex}{ext}"
        temp_output_path = f"temp_output_{uuid.uuid4().hex}{ext}"

        image.save(temp_input_path)

        layers = int(request.form.get("layers", 1))
        hide_message(temp_input_path, message, temp_output_path, layers=layers)

        with open(temp_output_path, "rb") as f:
            img_bytes = f.read()

        os.remove(temp_input_path)
        os.remove(temp_output_path)

        if ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif ext == ".png":
            mime_type = "image/png"
        elif ext == ".gif":
            mime_type = "image/gif"
        else:
            mime_type = "application/octet-stream"

        response = make_response(img_bytes)
        response.headers.set("Content-Type", mime_type)
        response.headers.set("X-Image-Extension", ext.lstrip('.'))

        return response

    except Exception as e:
        return jsonify({"error": f"Failed to hide: {e}"})


@app.route("/extract", methods=["POST"])
def extract_route():
    if "image" not in request.files:
        return jsonify({"error": "Image missing."})

    image = request.files["image"]

    try:
        filename = image.filename
        ext = os.path.splitext(filename)[1].lower()
        temp_extract_path = f"temp_extract_{uuid.uuid4().hex}{ext}"
        image.save(temp_extract_path)

        # ✅ Add debug prints
        print("⚙️ /extract hit")
        print("📂 Files:", request.files)
        print("🧾 Form:", request.form)

        # Ensure layers exists and is valid
        layers = request.form.get("layers")
        if not layers:
            return jsonify({"error": "Layers field missing."})

        layers = int(layers)
        message = reveal_message(temp_extract_path, layers=layers)

        os.remove(temp_extract_path)

        return jsonify({"result": message})

    except Exception as e:
        print("❌ Error in /extract:", e)
        return jsonify({"error": f"Failed to extract: {e}"})


@app.route("/encrypt", methods=["POST"])
def encrypt_route():
    try:
        data = request.get_json()
        text = data["text"]
        key = data["key"].encode()
        algorithm = data["algorithm"]

        encrypted = encrypt(key, text, algorithm)
        return jsonify({"result": encrypted})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/decrypt", methods=["POST"])
def decrypt_route():
    try:
        data = request.get_json()
        text = data["text"]
        key = data["key"].encode()
        algorithm = data["algorithm"]  # Optional

        decrypted = decrypt(key, text)
        return jsonify({"result": decrypted})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/")
def serve_frontend():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(base_dir, "..", "Front-End")
    return send_from_directory(frontend_dir, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(base_dir, "..", "Front-End")
    return send_from_directory(frontend_dir, path)

if __name__ == "__main__":
    app.run(debug=True)
