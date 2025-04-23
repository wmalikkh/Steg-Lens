from Crypto.Cipher import DES3, AES
import base64

def pad(data, block_size):
    """Pads the data to ensure it's a multiple of the block size"""
    while len(data) % block_size != 0:
        data += ' '
    return data

def encrypt(key, data, algorithm):
    """Encrypts the message based on the selected algorithm"""
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
    """Decrypts the message based on the selected algorithm"""
    if algorithm == '3DES':
        cipher = DES3.new(key, DES3.MODE_ECB)
    elif algorithm == 'AES-128':
        cipher = AES.new(key, AES.MODE_ECB)
    else:
        raise ValueError("Unsupported algorithm. Choose '3DES' or 'AES-128'.")

    encrypted_bytes = base64.b64decode(encrypted_data)
    decrypted_data = cipher.decrypt(encrypted_bytes).decode('utf-8')
    return decrypted_data.strip()

# Example Usage
if __name__ == "__main__":
    print("Choose encryption algorithm:")
    print("1. 3DES (21-byte key)")
    print("2. AES-128 (16-byte key)")
    algorithm_choice = input("Enter the number corresponding to your choice: ")

    if algorithm_choice == '1':
        algorithm = '3DES'
        key = input("Enter a 21-byte key: ").encode('utf-8')
        if len(key) != 21:
            raise ValueError("Invalid key length. 3DES requires a 21-byte key.")
        key += key[:3]  # Extend the 21-byte key to 24 bytes
    elif algorithm_choice == '2':
        algorithm = 'AES-128'
        key = input("Enter a 16-byte key: ").encode('utf-8')
        if len(key) != 16:
            raise ValueError("Invalid key length. AES-128 requires a 16-byte key.")
    else:
        raise ValueError("Invalid choice. Choose '1' for 3DES or '2' for AES-128.")

    print("Choose operation:")
    print("1. Encrypt")
    print("2. Decrypt")
    operation_choice = input("Enter the number corresponding to your choice: ")

    if operation_choice == '1':
        data = input("Enter the text to encrypt: ")
        encrypted_data = encrypt(key, data, algorithm)
        print(f"Encrypted: {encrypted_data}")
    elif operation_choice == '2':
        encrypted_data = input("Enter the text to decrypt: ")
        decrypted_data = decrypt(key, encrypted_data, algorithm)
        print(f"Decrypted: {decrypted_data}")
    else:
        raise ValueError("Invalid choice. Choose '1' to encrypt or '2' to decrypt.")
