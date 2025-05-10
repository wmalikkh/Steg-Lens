import os
import base64
import json
from Crypto.Cipher import DES3, AES
from Crypto.Util.Padding import pad, unpad

BLOCK_3DES = DES3.block_size
BLOCK_AES = AES.block_size

def _new_cipher(key: bytes, alg: str, iv: bytes = None):
    if alg == "3DES":
        return DES3.new(key, DES3.MODE_CBC, iv)
    elif alg == "AES-128":
        return AES.new(key, AES.MODE_CBC, iv)
    else:
        raise ValueError("Unsupported algorithm")

def encrypt(key: bytes, plaintext: str, alg: str) -> str:
    iv = os.urandom(8 if alg == "3DES" else 16)
    bs = BLOCK_3DES if alg == "3DES" else BLOCK_AES
    ct = _new_cipher(key, alg, iv).encrypt(pad(plaintext.encode(), bs))
    blob = {"alg": alg, "iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()}
    return base64.b64encode(json.dumps(blob).encode()).decode()

def decrypt(key: bytes, b64_blob: str) -> str:
    try:
        blob = json.loads(base64.b64decode(b64_blob.encode()).decode())
        alg = blob["alg"]
        iv = base64.b64decode(blob["iv"])
        ct = base64.b64decode(blob["ct"])
        bs = BLOCK_3DES if alg == "3DES" else BLOCK_AES
        pt = unpad(_new_cipher(key, alg, iv).decrypt(ct), bs)
        return pt.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
