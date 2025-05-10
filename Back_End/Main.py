import os
from Steganography_tool import hide_message, reveal_message
from Cryptography_tool import encrypt, decrypt

def main():
    print("\n🔐 Steg-Lens CLI")
    print("1) Hide a message")
    print("2) Reveal a message")
    choice = input("> ").strip()

    if choice == "1":
        src = input("Enter image path (PNG/JPEG/GIF): ").strip()
        if not os.path.exists(src):
            print("❌ Error: File not found")
            return

        secret = input("Enter your message: ").strip()
        output = input("Output filename: ").strip()

        enc_choice = input("Encrypt message? (y/n): ").lower()
        if enc_choice == "y":
            algo = input("Algorithm (AES-128 or 3DES): ").strip().upper()
            key = input("Enter key: ").strip()
            try:
                if algo == "AES-128" and len(key) == 16:
                    secret = encrypt(key.encode(), secret, "AES-128")
                elif algo == "3DES" and len(key) == 21:
                    key_bytes = key.encode() + key[:3].encode()
                    secret = encrypt(key_bytes, secret, "3DES")
                else:
                    print("❌ Invalid key length")
                    return
            except Exception as e:
                print(f"❌ Encryption failed: {e}")
                return

        try:
            layers = int(input("Number of steganography layers (1–3): "))
            hide_message(src, secret, output, layers=layers)
            print("✅ Message hidden successfully!")
        except Exception as e:
            print(f"❌ Error: {e}")

    elif choice == "2":
        src = input("Enter image path to extract from: ").strip()
        if not os.path.exists(src):
            print("❌ Error: File not found")
            return

        try:
            layers = int(input("Number of steganography layers used (1–3): "))
            message = reveal_message(src, layers=layers)
            print(f"📩 Hidden Message: {message}")
        except Exception as e:
            print(f"❌ Error: {e}")
            return

        dec_choice = input("Decrypt message? (y/n): ").lower()
        if dec_choice == "y":
            algo = input("Algorithm (AES-128 or 3DES): ").strip().upper()
            key = input("Enter key: ").strip()
            try:
                if algo == "AES-128" and len(key) == 16:
                    message = decrypt(key.encode(), message)
                elif algo == "3DES" and len(key) == 21:
                    key_bytes = key.encode() + key[:3].encode()
                    message = decrypt(key_bytes, message)
                else:
                    print("❌ Invalid key length")
                    return
                print(f"🔓 Decrypted Message: {message}")
            except Exception as e:
                print(f"❌ Decryption failed: {e}")

    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()
