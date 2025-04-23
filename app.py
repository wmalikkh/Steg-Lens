from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from Crypto.Cipher import DES3, AES
import base64
import tempfile
import io
from PIL import Image
from stegano import lsb

app = Flask(__name__)
CORS(app)

def pad(data, block_size):
    while len(data) % block_size != 0:
        data += ' '
    return data

@app.route('/encrypt', methods=['POST'])
def encrypt_text():
    data = request.json
    text = data.get('text')
    key = data.get('key')
    algorithm = data.get('algorithm')

    if algorithm == '3DES':
        if len(key) != 21:
            return jsonify({'error': '3DES key must be 21 bytes'}), 400
        key = key.encode('utf-8') + key[:3].encode('utf-8')
        cipher = DES3.new(key, DES3.MODE_ECB)
        block_size = DES3.block_size
    elif algorithm == 'AES-128':
        if len(key) != 16:
            return jsonify({'error': 'AES-128 key must be 16 bytes'}), 400
        key = key.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)
        block_size = AES.block_size
    else:
        return jsonify({'error': 'Unsupported algorithm'}), 400

    padded_data = pad(text, block_size)
    encrypted_bytes = cipher.encrypt(padded_data.encode('utf-8'))
    encrypted_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    return jsonify({'result': encrypted_base64})

@app.route('/decrypt', methods=['POST'])
def decrypt_text():
    data = request.json
    encrypted_data = data.get('text')
    key = data.get('key')
    algorithm = data.get('algorithm')

    if algorithm == '3DES':
        if len(key) != 21:
            return jsonify({'error': '3DES key must be 21 bytes'}), 400
        key = key.encode('utf-8') + key[:3].encode('utf-8')
        cipher = DES3.new(key, DES3.MODE_ECB)
    elif algorithm == 'AES-128':
        if len(key) != 16:
            return jsonify({'error': 'AES-128 key must be 16 bytes'}), 400
        key = key.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)
    else:
        return jsonify({'error': 'Unsupported algorithm'}), 400

    try:
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = cipher.decrypt(encrypted_bytes).decode('utf-8').strip()
        return jsonify({'result': decrypted})
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500

@app.route('/hide', methods=['POST'])
def hide_text_in_image():
    if 'image' not in request.files or 'message' not in request.form:
        return jsonify({'error': 'Missing image or message'}), 400

    image_file = request.files['image']
    message = request.form['message']
    image_bytes = image_file.read()

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_format = img.format.lower()
        print(f"[DEBUG] Image format: {img_format}")

        if img_format in ['jpeg', 'jpg']:
            if img.mode != "RGB":
                img = img.convert("RGB")
            pixels = img.load()
            width, height = img.size
            binary = ''.join(format(ord(c), '08b') for c in message) + '1111111111111110'
            data_index = 0

            for y in range(height):
                for x in range(width):
                    if data_index >= len(binary):
                        break
                    r, g, b = pixels[x, y]
                    r = (r & ~1) | int(binary[data_index])
                    pixels[x, y] = (r, g, b)
                    data_index += 1
                if data_index >= len(binary):
                    break

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=90)
            output.seek(0)
            response = make_response(send_file(output, mimetype='image/jpeg', as_attachment=True, download_name='steg-image.jpg'))
            response.headers['X-Image-Extension'] = 'jpg'
            return response

        elif img_format == 'png':
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                temp.write(image_bytes)
                temp.flush()
                hidden_img = lsb.hide(temp.name, message)
                output_path = temp.name.replace(".png", "_secret.png")
                hidden_img.save(output_path)
                response = make_response(send_file(output_path, mimetype='image/png', as_attachment=True, download_name='steg-image.png'))
                response.headers['X-Image-Extension'] = 'png'
                return response
        else:
            return jsonify({'error': 'Unsupported image format. Only PNG and JPEG allowed.'}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to hide text: {str(e)}'}), 500

@app.route('/extract', methods=['POST'])
def extract_text_from_image():
    if 'image' not in request.files:
        return jsonify({'error': 'Missing image file'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_format = img.format.lower()
        print(f"[DEBUG] Extract format: {img_format}")

        if img_format in ['jpeg', 'jpg']:
            if img.mode != "RGB":
                img = img.convert("RGB")

            pixels = img.load()
            width, height = img.size
            binary_message = ''

            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    binary_message += str(r & 1)

            end_marker = '1111111111111110'
            end_index = binary_message.find(end_marker)
            if end_index != -1:
                binary_message = binary_message[:end_index]
            else:
                return jsonify({'error': 'No hidden message found in the image'}), 404

            message = ''
            for i in range(0, len(binary_message), 8):
                byte = binary_message[i:i+8]
                if len(byte) == 8:
                    message += chr(int(byte, 2))

        elif img_format == 'png':
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                temp.write(image_bytes)
                temp.flush()
                message = lsb.reveal(temp.name)
        else:
            return jsonify({'error': 'Unsupported image format for extraction.'}), 400

        if not message:
            return jsonify({'error': 'No hidden message found in the image'}), 404

        return jsonify({'result': message})

    except Exception as e:
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)