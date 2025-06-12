import os
import json
import base64
from Steganography_tool import hide_message, reveal_message, MAX_SIZES
from Cryptography_tool import encrypt, decrypt, is_encrypted, expand_key_to_length, generate_random_key

def read_text_file(file_path, max_size):
    try:
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            print(f"❌ File too large (max {max_size // 1024}KB)")
            return None
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def write_text_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"✅ Saved to {file_path}")
    except Exception as e:
        print(f"❌ Error writing file: {e}")

def get_max_size(ext):
    ext = ext.lstrip('.').lower()
    return MAX_SIZES.get(ext, 0)

def main():
    print("\n🔐 Steg-Lens CLI")
    print("1) Hide a message")
    print("2) Reveal a message")
    choice = input("> ").strip()

    if choice == "1":
        img_path = input("Enter path to image file: ").strip()
        if not os.path.exists(img_path):
            print("❌ Error: Image file not found")
            return

        ext = os.path.splitext(img_path)[1].lower()
        max_size = get_max_size(ext)
        if max_size == 0:
            print("❌ Unsupported image format")
            return

        print("\nInput Message:")
        print("1) Type message")
        print("2) Load from .txt file")
        method = input("Choose (1/2): ").strip()
        if method == "1":
            message = input("Enter your message: ").strip()
        elif method == "2":
            text_path = input("Enter path to .txt file: ").strip()
            if not os.path.exists(text_path):
                print("❌ Text file not found")
                return
            message = read_text_file(text_path, max_size)
            if message is None:
                return
        else:
            print("❌ Invalid method")
            return

        encrypt_choice = input("Encrypt the message? (y/n): ").lower()
        if encrypt_choice == "y":
            print("\nEncryption Algorithms:")
            print("1) AES-128")
            print("2) 3DES")
            algo_choice = input("Choose algorithm used (1/2): ").strip()
            if algo_choice == "1":
                algo = "AES-128"
                key_len = 16
            elif algo_choice == "2":
                algo = "3DES"
                key_len = 24
            else:
                print("❌ Invalid algorithm choice")
                return

            key_input = input("Enter key or type 'random' to generate one: ").strip()
            if key_input.lower() == "random":
                key = generate_random_key(key_len)
                print(f"🔑 Generated Key: {key}")
            else:
                key = expand_key_to_length(key_input, key_len)

            try:
                message = encrypt(key.encode('utf-8'), message, algo)
            except Exception as e:
                print(f"❌ Encryption failed: {e}")
                return

        try:
            layers = int(input("How many base64 layers? (1–3): ").strip())
            if not (1 <= layers <= 3):
                raise ValueError
        except:
            print("❌ Invalid layer count")
            return

        out_path = input("Enter path to save output image: ").strip()
        try:
            hide_message(img_path, message, out_path, layers=layers)
            print(f"✅ Message hidden successfully in {out_path}")
        except Exception as e:
            print(f"❌ Failed to hide message: {e}")

    elif choice == "2":
        src = input("Enter image path to extract from: ").strip()
        if not os.path.exists(src):
            print("❌ Error: Image file not found")
            return

        try:
            print("\n🔍 Extracting message...")
            message = reveal_message(src)

            # Auto-decode base64 until it's a JSON blob
            decoded = message
            encrypted = False
            for _ in range(3):
                try:
                    test_decode = base64.b64decode(decoded.encode('utf-8')).decode('utf-8')
                    if is_encrypted(test_decode):
                        message = test_decode
                        encrypted = True
                        break
                    decoded = test_decode
                except:
                    break

            if encrypted:
                print("\n⚠️  Encrypted message detected!")
                dec_choice = input("Decrypt message? (y/n): ").lower()
                if dec_choice != "y":
                    print("\n📄 Encrypted content preview:")
                    print(message[:200] + ("..." if len(message) > 200 else ""))
                    return

                print("\nEncryption Algorithms:")
                print("1) AES-128")
                print("2) 3DES")
                algo_choice = input("Choose algorithm used (1/2): ").strip()

                if algo_choice == "1":
                    algo = "AES-128"
                    key = input("Enter decryption key: ").strip()
                    key = expand_key_to_length(key, 16)
                elif algo_choice == "2":
                    algo = "3DES"
                    key = input("Enter decryption key: ").strip()
                    key = expand_key_to_length(key, 24)
                else:
                    print("❌ Invalid algorithm choice")
                    return

                try:
                    print("🔓 Decrypting message...")
                    decrypted = decrypt(key.encode('utf-8'), message)
                    print("\n🔓 Decrypted Message:")
                    print(decrypted[:200] + ("..." if len(decrypted) > 200 else ""))
                    message = decrypted
                except Exception as e:
                    print(f"\n❌ Decryption failed: {e}")
                    print("Possible reasons:")
                    print("- Wrong key")
                    print("- Wrong algorithm")
                    return
            else:
                print("\n📩 Extracted Message:")
                print(message[:200] + ("..." if len(message) > 200 else ""))

            save_choice = input("\nSave to file? (y/n): ").lower()
            if save_choice == "y":
                file_path = input("Enter output file path: ").strip()
                write_text_file(file_path, message)
        except Exception as e:
            print(f"❌ Error: {e}")

    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()
