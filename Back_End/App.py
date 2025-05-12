from flask import Flask, request, jsonify, make_response, send_from_directory
import os
import uuid
from flask_cors import CORS
from Steganography_tool import hide_message, reveal_message, MAX_SIZES
from Cryptography_tool import encrypt, decrypt

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_max_size(ext):
    ext = ext.lstrip('.').lower()
    return MAX_SIZES.get(ext, 0)

@app.route("/hide", methods=["POST"])
def hide_route():
    if "image" not in request.files:
        return jsonify({"error": "Image file missing"}), 400

    message = request.form.get("message", "")
    text_file = request.files.get("text_file")

    if text_file and not message:
        try:
            ext = os.path.splitext(request.files["image"].filename)[1]
            max_size = get_max_size(ext)
            if text_file.content_length > max_size:
                return jsonify({"error": f"File exceeds {max_size // 1024}KB limit for {ext.upper()}"}), 400
            message = text_file.read(max_size).decode('utf-8')
        except Exception as e:
            return jsonify({"error": f"Failed to read text file: {str(e)}"}), 400

    if not message:
        return jsonify({"error": "No message provided"}), 400

    layers = int(request.form.get("layers", 1))
    encryption = request.form.get("encryption", "false").lower()
    algorithm = request.form.get("algorithm", "").upper()
    key = request.form.get("key", "")

    try:
        if layers < 1 or layers > 3:
            return jsonify({"error": "Layers must be between 1 and 3"}), 400

        if encryption in ["true", "yes"]:
            if not algorithm or not key:
                return jsonify({"error": "Algorithm and key required for encryption"}), 400
            if algorithm == "AES-128" and len(key) != 16:
                return jsonify({"error": "AES-128 requires 16 character key"}), 400
            if algorithm == "3DES" and len(key) != 24:
                return jsonify({"error": "3DES requires 24 character key"}), 400

            message = encrypt(key.encode(), message, algorithm)

        image = request.files["image"]
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in ['.jpeg', '.jpg', '.png', '.gif']:
            ext = '.png'

        temp_input_path = os.path.join(UPLOAD_FOLDER, f"temp_input_{uuid.uuid4().hex}{ext}")
        temp_output_path = os.path.join(UPLOAD_FOLDER, f"temp_output_{uuid.uuid4().hex}{ext}")
        image.save(temp_input_path)

        hide_message(temp_input_path, message, temp_output_path, layers=layers)

        with open(temp_output_path, "rb") as f:
            img_bytes = f.read()

        os.remove(temp_input_path)
        os.remove(temp_output_path)

        mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}
        mime_type = mime_types.get(ext, "application/octet-stream")

        response = make_response(img_bytes)
        response.headers.set("Content-Type", mime_type)
        response.headers.set("X-Image-Extension", ext.lstrip('.'))
        return response

    except Exception as e:
        return jsonify({"error": f"Failed to hide message: {str(e)}"}), 500

@app.route("/extract", methods=["POST"])
def extract_route():
    if "image" not in request.files:
        return jsonify({"error": "Image file missing"}), 400

    try:
        image = request.files["image"]
        ext = os.path.splitext(image.filename)[1].lower()
        temp_extract_path = os.path.join(UPLOAD_FOLDER, f"temp_extract_{uuid.uuid4().hex}{ext}")
        image.save(temp_extract_path)

        message = reveal_message(temp_extract_path)
        os.remove(temp_extract_path)

        return jsonify({"result": message})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 400

@app.route("/decrypt", methods=["POST"])
def decrypt_route():
    data = request.get_json()
    text = data.get("text", "")
    key = data.get("key", "")
    algorithm = data.get("algorithm", "").upper()

    if not text or not key or not algorithm:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        result = decrypt(key.encode(), text)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 400

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
