import base64
import json
from Cryptodome.Cipher import DES3, AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import PBKDF2
import string
import random
import time

BLOCK_3DES = DES3.block_size
BLOCK_AES = AES.block_size
SALT = b'salt1234'
ITERATIONS = 10000


def _derive_key(key: bytes, algorithm: str) -> bytes:
    if algorithm == "3DES":
        return PBKDF2(key, SALT, 24, count=ITERATIONS)
    elif algorithm == "AES-128":
        return PBKDF2(key, SALT, 16, count=ITERATIONS)
    else:
        raise ValueError("Unsupported algorithm")


def _validate_key(key: bytes, algorithm: str):
    if algorithm not in ["3DES", "AES-128"]:
        raise ValueError("Unsupported algorithm")


def _new_cipher(key: bytes, alg: str, iv: bytes = None):
    try:
        derived_key = _derive_key(key, alg)
        if alg == "3DES":
            return DES3.new(derived_key, DES3.MODE_CBC, iv)
        elif alg == "AES-128":
            return AES.new(derived_key, AES.MODE_CBC, iv)
    except Exception as e:
        raise ValueError(f"Cipher creation failed: {str(e)}")


def is_encrypted(data: str) -> bool:
    """Check if data is in our encrypted format"""
    try:
        # Try to parse as direct JSON
        try:
            decoded = json.loads(data)
            if all(k in decoded for k in ['iv', 'ct', 'alg', 'version']):
                return True
        except json.JSONDecodeError:
            pass

        # Try base64 decoding then JSON
        try:
            decoded = base64.b64decode(data.encode('utf-8')).decode('utf-8')
            json_data = json.loads(decoded)
            return all(k in json_data for k in ['iv', 'ct', 'alg', 'version'])
        except:
            return False
    except:
        return False


def encrypt(key: bytes, plaintext: str, alg: str) -> str:
    """Encrypt plaintext and return as JSON string"""
    try:
        _validate_key(key, alg)
        iv = get_random_bytes(8 if alg == "3DES" else 16)
        bs = BLOCK_3DES if alg == "3DES" else BLOCK_AES

        cipher = _new_cipher(key, alg, iv)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), bs))

        encrypted_data = {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ct': base64.b64encode(ct_bytes).decode('utf-8'),
            'alg': alg,
            'version': '2.1',
            'timestamp': int(time.time())
        }
        return json.dumps(encrypted_data)
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt(key: bytes, encrypted_str: str) -> str:
    """Decrypt message that was encrypted with our encrypt() function"""
    try:
        # First try to parse as direct JSON
        try:
            data = json.loads(encrypted_str)
        except json.JSONDecodeError:
            # If not JSON, try base64 decoding
            try:
                decoded = base64.b64decode(encrypted_str.encode('utf-8')).decode('utf-8')
                data = json.loads(decoded)
            except:
                raise ValueError("Invalid encrypted data format - not JSON or base64 encoded JSON")

        if not all(k in data for k in ['iv', 'ct', 'alg', 'version']):
            raise ValueError("Invalid encrypted data format - missing required fields")

        iv = base64.b64decode(data['iv'].encode('utf-8'))
        ct = base64.b64decode(data['ct'].encode('utf-8'))
        alg = data['alg']

        _validate_key(key, alg)
        bs = BLOCK_3DES if alg == "3DES" else BLOCK_AES

        cipher = _new_cipher(key, alg, iv)
        pt = unpad(cipher.decrypt(ct), bs)
        return pt.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def generate_key(algorithm: str) -> bytes:
    if algorithm == "3DES":
        return get_random_bytes(24)
    elif algorithm == "AES-128":
        return get_random_bytes(16)
    else:
        raise ValueError("Unsupported algorithm")


def expand_key_to_length(key: str, target_length: int) -> str:
    """Ensure the key is exactly target_length by repeating or truncating"""
    if not key:
        raise ValueError("Key cannot be empty")
    repeated_key = (key * ((target_length // len(key)) + 1))[:target_length]
    return repeated_key


def generate_random_key(length: int) -> str:
    """Generate a random alphanumeric key of desired length"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choices(chars, k=length))