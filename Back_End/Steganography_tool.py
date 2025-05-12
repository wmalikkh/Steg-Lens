import os
import base64
from PIL import Image, ImageSequence
from PIL.JpegImagePlugin import get_sampling
import piexif
from stegano import lsb

DELIMITER = b"||END||"
PNG_EXT = (".png",)
JPEG_EXT = (".jpg", ".jpeg")
GIF_EXT = (".gif",)

def validate_image_path(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input file not found: {image_path}")
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in PNG_EXT + JPEG_EXT + GIF_EXT:
        raise ValueError("Unsupported format (PNG/JPEG/GIF only)")
    return ext

def _apply_layers(secret, layers):
    for _ in range(layers - 1):
        secret = base64.b64encode(secret.encode()).decode()
    return secret

def _decode_layers(secret, layers):
    for _ in range(layers - 1):
        secret = base64.b64decode(secret.encode()).decode()
    return secret

def hide_message(image_path, secret, output_path, layers=1):
    if not (1 <= layers <= 3):
        raise ValueError("Layers must be between 1 and 3")
    ext = validate_image_path(image_path)
    secret = _apply_layers(secret, layers)

    if ext in PNG_EXT:
        hidden_img = lsb.hide(image_path, secret)
        hidden_img.save(output_path)
        print(f"✅ Hidden in PNG -> {output_path}")

    elif ext in JPEG_EXT:
        img = Image.open(image_path)
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

        payload = secret.encode() + DELIMITER
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = b"ASCII\0\0\0" + payload

        img.save(
            output_path,
            "jpeg",
            exif=piexif.dump(exif_dict),
            quality=95,
            subsampling=get_sampling(img)
        )
        print(f"✅ Hidden in JPEG -> {output_path}")

    elif ext in GIF_EXT:
        img = Image.open(image_path)
        frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(img)]
        pixels = frames[0].load()
        width, height = frames[0].size

        binary = ''.join(format(ord(c), '08b') for c in secret) + '1111111111111110'
        idx = 0
        for y in range(height):
            for x in range(width):
                if idx >= len(binary):
                    break
                r, g, b = pixels[x, y]
                r = (r & ~1) | int(binary[idx])
                pixels[x, y] = (r, g, b)
                idx += 1
            if idx >= len(binary):
                break

        frames[0].save(output_path, format="GIF", save_all=True, append_images=frames[1:], loop=0)
        print(f"✅ Hidden in GIF -> {output_path}")

def reveal_message(image_path, layers=1):
    if not (1 <= layers <= 3):
        raise ValueError("Layers must be between 1 and 3")
    ext = validate_image_path(image_path)

    if ext in PNG_EXT:
        hidden = lsb.reveal(image_path)
        if not hidden:
            raise ValueError("No hidden message in PNG")

    elif ext in JPEG_EXT:
        img = Image.open(image_path)
        if "exif" not in img.info:
            raise ValueError("No EXIF data found")
        exif_dict = piexif.load(img.info["exif"])
        user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")
        if not user_comment:
            raise ValueError("No message in EXIF")
        if user_comment.startswith(b"ASCII\0\0\0"):
            user_comment = user_comment[8:]
        if DELIMITER not in user_comment:
            raise ValueError("No message delimiter found")
        hidden = user_comment.split(DELIMITER)[0].decode()

    elif ext in GIF_EXT:
        img = Image.open(image_path)
        frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(img)]
        pixels = frames[0].load()
        width, height = frames[0].size
        bits = ''
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                bits += str(r & 1)

        marker = '1111111111111110'
        idx = bits.find(marker)
        if idx == -1:
            raise ValueError("No message marker found")
        bits = bits[:idx]
        chars = [chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8)]
        hidden = ''.join(chars)

    if layers > 1:
        hidden = _decode_layers(hidden, layers)

    return hidden
