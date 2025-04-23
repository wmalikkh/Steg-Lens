from Crypto.Cipher import DES3, AES
import base64
from stegano import lsb
import os
from PIL import Image

def pad(data, block_size):
    while len(data) % block_size != 0:
        data += ' '
    return data

def encrypt(key, data, algorithm):
    if algorithm == '3DES':
        cipher = DES3.new(key, DES3.MODE_ECB)
        block_size = DES3.block_size
    elif algorithm == 'AES-128':
        cipher = AES.new(key, AES.MODE_ECB)
        block_size = AES.block_size
    else:
        raise ValueError("Unsupported algorithm. Choose '3DES' or 'AES-128'.")

    padded_data = pad(data, block_size)
    encrypted_bytes = cipher.encrypt(padded_data.encode('utf-8'))
    encrypted_data = base64.b64encode(encrypted_bytes).decode('utf-8')
    return encrypted_data

def decrypt(key, encrypted_data, algorithm):
    if algorithm == '3DES':
        cipher = DES3.new(key, DES3.MODE_ECB)
    elif algorithm == 'AES-128':
        cipher = AES.new(key, AES.MODE_ECB)
    else:
        raise ValueError("Unsupported algorithm. Choose '3DES' or 'AES-128'.")

    encrypted_bytes = base64.b64decode(encrypted_data)
    decrypted_data = cipher.decrypt(encrypted_bytes).decode('utf-8')
    return decrypted_data.strip()

def encode_with_pil(image_path, secret_message, output_image_path):
    image = Image.open(image_path)
    if image.mode != 'RGB':
        raise ValueError("Image must be in RGB format")

    encoded_image = image.copy()
    width, height = encoded_image.size
    pixels = encoded_image.load()

    binary_message = ''.join(format(ord(char), '08b') for char in secret_message)
    binary_message += '1111111111111110'  # delimiter
    message_index = 0

    for y in range(height):
        for x in range(width):
            if message_index < len(binary_message):
                r, g, b = pixels[x, y]
                r = (r & ~1) | int(binary_message[message_index])
                message_index += 1
                if message_index < len(binary_message):
                    g = (g & ~1) | int(binary_message[message_index])
                    message_index += 1
                if message_index < len(binary_message):
                    b = (b & ~1) | int(binary_message[message_index])
                    message_index += 1
                pixels[x, y] = (r, g, b)
            else:
                break

    encoded_image.save(output_image_path)
    print(f"✅ Message encoded and saved to {output_image_path}")

def decode_with_pil(image_path):
    image = Image.open(image_path)
    if image.mode != 'RGB':
        raise ValueError("Image must be in RGB format")

    binary_message = ""
    width, height = image.size
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary_message += str(r & 1)
            binary_message += str(g & 1)
            binary_message += str(b & 1)

    binary_message = binary_message.split('1111111111111110')[0]
    decoded_message = "".join(chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8))
    return decoded_message

def main():
    print("🔐 Steganography Tool")
    print("Choose operation:")
    print("1. Hide a message in an image")
    print("2. Reveal a message from an image")
    operation_choice = input("Enter the number corresponding to your choice: ").strip()

    if operation_choice == '1':
        image_path = input("Enter the path to your input image (RGB, PNG/JPEG): ").strip()
        if not os.path.isfile(image_path):
            print("❌ File not found.")
            return

        message = input("Enter the secret message to encode: ").strip()
        if not message:
            print("❌ Message cannot be empty.")
            return

        format_choice = input("Enter output image format (PNG or JPEG): ").strip().upper()
        if format_choice not in ["PNG", "JPEG"]:
            print("❌ Invalid format. Please choose PNG or JPEG.")
            return

        encrypt_choice = input("Do you want to encrypt the message before encoding? (y/n): ").strip().lower()
        if encrypt_choice == 'y':
            algorithm_choice = input("Choose encryption algorithm:\n1. 3DES\n2. AES-128\nEnter your choice: ").strip()
            if algorithm_choice == '1':
                key = input("Enter a 21-byte key: ").encode('utf-8')
                if len(key) != 21:
                    print("❌ Invalid key length. 3DES requires a 21-byte key.")
                    return
                key += key[:3]  # Extend to 24 bytes
                message = encrypt(key, message, '3DES')
            elif algorithm_choice == '2':
                key = input("Enter a 16-byte key: ").encode('utf-8')
                if len(key) != 16:
                    print("❌ Invalid key length. AES-128 requires a 16-byte key.")
                    return
                message = encrypt(key, message, 'AES-128')
            else:
                print("❌ Invalid algorithm choice.")
                return

        output_path = input("Enter path for the output image (without extension): ").strip()
        output_image_path = f"{output_path}.{format_choice.lower()}"

        try:
            encode_with_pil(image_path, message, output_image_path)
        except Exception as e:
            print(f"❌ Error encoding message: {e}")

    elif operation_choice == '2':
        image_path = input("Enter the path to the image (PNG/JPEG): ").strip()
        if not os.path.isfile(image_path):
            print("❌ File not found.")
            return
        try:
            message = decode_with_pil(image_path)
            print(f"✅ Hidden message: {message}")
            decrypt_choice = input("Do you want to decrypt the message? (y/n): ").strip().lower()
            if decrypt_choice == 'y':
                algorithm_choice = input("Choose encryption algorithm:\n1. 3DES\n2. AES-128\nEnter your choice: ").strip()
                if algorithm_choice == '1':
                    key = input("Enter a 21-byte key: ").encode('utf-8')
                    if len(key) != 21:
                        print("❌ Invalid key length. 3DES requires a 21-byte key.")
                        return
                    key += key[:3]
                    message = decrypt(key, message, '3DES')
                elif algorithm_choice == '2':
                    key = input("Enter a 16-byte key: ").encode('utf-8')
                    if len(key) != 16:
                        print("❌ Invalid key length. AES-128 requires a 16-byte key.")
                        return
                    message = decrypt(key, message, 'AES-128')
                else:
                    print("❌ Invalid algorithm choice.")
                    return
                print(f"✅ Decrypted message: {message}")
        except Exception as e:
            print(f"❌ Error decoding message: {e}")
    else:
        print("❌ Invalid operation selection. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
