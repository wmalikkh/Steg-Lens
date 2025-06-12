from flask import Flask, request, jsonify, make_response, send_from_directory
import os
import uuid
import time
import base64
import json
from flask_cors import CORS
from Steganography_tool import hide_message, reveal_message, MAX_SIZES
from Cryptography_tool import encrypt, decrypt, is_encrypted, expand_key_to_length

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def get_max_size(ext):
    ext = ext.lstrip('.').lower()
    return MAX_SIZES.get(ext, 0)


def clean_text_content(content):
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    return content.strip()


def safe_remove(filepath, max_retries=3, delay=0.1):
    for i in range(max_retries):
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            if i == max_retries - 1:
                print(f"Failed to remove {filepath}: {str(e)}")
                return False
            time.sleep(delay)
    return False


def apply_layers(message, layers):
    """Apply base64 encoding layers to message (internal use only)"""
    for _ in range(layers):
        message = base64.b64encode(message.encode('utf-8')).decode('utf-8')
    return message


def remove_layers(message):
    """Remove base64 layers from message (internal use only)"""
    current = message
    for _ in range(3):  # Max 3 layers
        try:
            decoded = base64.b64decode(current.encode('utf-8')).decode('utf-8')
            current = decoded
        except:
            break
    return current


@app.route("/hide", methods=["POST"])
def hide_route():
    if "image" not in request.files:
        return jsonify({"error": "Image file missing"}), 400

    message = request.form.get("message", "")
    text_file = request.files.get("text_file")
    encryption = request.form.get("encryption", "false").lower()
    algorithm = request.form.get("algorithm", "").upper()
    key = request.form.get("key", "")
    layers = int(request.form.get("layers", 1))

    if text_file and text_file.filename:
        try:
            ext = os.path.splitext(request.files["image"].filename)[1].lower()
            max_size = get_max_size(ext)
            file_content = text_file.read()
            message = clean_text_content(file_content)

            if not message:
                return jsonify({"error": "Text file is empty or contains no valid text"}), 400
            if len(message.encode('utf-8')) > max_size:
                return jsonify({"error": f"Message exceeds {max_size // 1024}KB limit"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to read text file: {str(e)}"}), 400

    if not message:
        return jsonify({"error": "No message provided"}), 400

    if layers < 1 or layers > 3:
        return jsonify({"error": "Layers must be between 1 and 3"}), 400

    if encryption in ["true", "yes"]:
        if not algorithm or not key:
            return jsonify({"error": "Algorithm and key required for encryption"}), 400
        try:
            if algorithm == "AES-128":
                key = expand_key_to_length(key, 16)
            elif algorithm == "3DES":
                key = expand_key_to_length(key, 24)
            else:
                return jsonify({"error": "Unsupported algorithm"}), 400

            message = encrypt(key.encode('utf-8'), message, algorithm)
        except Exception as e:
            return jsonify({"error": f"Encryption failed: {str(e)}"}), 400

    # Apply base64 layers after encryption (if any)
    if layers > 1:
        message = apply_layers(message, layers)

    temp_input_path = None
    temp_output_path = None

    try:
        image = request.files["image"]
        ext = os.path.splitext(image.filename)[1].lower()
        temp_input_path = os.path.join(UPLOAD_FOLDER, f"temp_input_{uuid.uuid4().hex}{ext}")
        temp_output_path = os.path.join(UPLOAD_FOLDER, f"temp_output_{uuid.uuid4().hex}{ext}")

        image.save(temp_input_path)
        image.close()

        hide_message(temp_input_path, message, temp_output_path)

        with open(temp_output_path, "rb") as f:
            img_bytes = f.read()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif"
        }
        mime_type = mime_types.get(ext, "application/octet-stream")

        response = make_response(img_bytes)
        response.headers.set("Content-Type", mime_type)
        response.headers.set("X-Image-Extension", ext.lstrip('.'))
        response.headers.set("X-Encrypted", "true" if encryption in ["true", "yes"] else "false")
        return response

    except Exception as e:
        return jsonify({"error": f"Failed to hide message: {str(e)}"}), 500
    finally:
        safe_remove(temp_input_path)
        safe_remove(temp_output_path)


@app.route("/extract", methods=["POST"])
def extract_route():
    if "image" not in request.files:
        return jsonify({"error": "Image file missing"}), 400

    temp_extract_path = None
    try:
        image = request.files["image"]
        ext = os.path.splitext(image.filename)[1].lower()
        temp_extract_path = os.path.join(UPLOAD_FOLDER, f"temp_extract_{uuid.uuid4().hex}{ext}")

        image.save(temp_extract_path)
        image.close()

        message = reveal_message(temp_extract_path)
        if not message:
            return jsonify({"error": "No hidden message found"}), 400

        # Remove base64 layers (internal processing only)
        current_message = remove_layers(message)
        encrypted = is_encrypted(current_message)

        response_data = {
            "result": current_message,
            "is_encrypted": encrypted
        }

        if encrypted and request.form.get("decryption", "false").lower() == "true":
            algorithm = request.form.get("algorithm", "").upper()
            key = request.form.get("key", "")

            if not algorithm or not key:
                return jsonify({
                    "error": "Algorithm and key required for decryption",
                    "is_encrypted": True
                }), 400

            try:
                if algorithm == "AES-128":
                    key = expand_key_to_length(key, 16)
                elif algorithm == "3DES":
                    key = expand_key_to_length(key, 24)
                else:
                    return jsonify({
                        "error": "Unsupported algorithm",
                        "supported_algorithms": ["AES-128", "3DES"]
                    }), 400

                decrypted = decrypt(key.encode('utf-8'), current_message)
                response_data.update({
                    "result": decrypted,
                    "is_encrypted": False,
                    "decryption_status": "success"
                })
            except Exception as e:
                response_data.update({
                    "decryption_status": "failed",
                    "decryption_error": str(e)
                })

        if request.form.get("return_as_file", "false").lower() == "true":
            content = response_data.get("result")
            response = make_response(content)
            response.headers.set("Content-Type", "text/plain")
            response.headers.set("Content-Disposition", "attachment", filename="extracted_message.txt")
            return response

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            "error": "Extraction failed",
            "details": str(e)
        }), 400
    finally:
        safe_remove(temp_extract_path)


@app.route("/decrypt", methods=["POST"])
def decrypt_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    encrypted_message = data.get("message")
    algorithm = data.get("algorithm", "").upper()
    key = data.get("key", "")

    if not encrypted_message:
        return jsonify({"error": "No message provided"}), 400
    if not algorithm or not key:
        return jsonify({"error": "Algorithm and key required"}), 400

    try:
        if algorithm == "AES-128":
            key = expand_key_to_length(key, 16)
        elif algorithm == "3DES":
            key = expand_key_to_length(key, 24)
        else:
            return jsonify({"error": "Unsupported algorithm"}), 400

        decrypted = decrypt(key.encode('utf-8'), encrypted_message)
        return jsonify({
            "result": decrypted,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": "Decryption failed",
            "details": str(e),
            "possible_reasons": [
                "Wrong key",
                "Wrong algorithm",
                "Corrupted message data"
            ]
        }), 400


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
    app.run(debug=True, threaded=True)