import os
from PIL import Image, ImageSequence
from PIL.JpegImagePlugin import get_sampling
import piexif
from stegano import lsb
import io

DELIMITER = b"||END||"
PNG_EXT = (".png",)
JPEG_EXT = (".jpg", ".jpeg")
GIF_EXT = (".gif",)

# Hide a message into an image (auto detect format)
def hide_message(image_path, secret, output_path):
    ext = os.path.splitext(image_path)[1].lower()

    if ext in PNG_EXT:
        hidden_img = lsb.hide(image_path, secret)
        hidden_img.save(output_path)
        print(f"✅ Hidden in PNG -> {output_path}")

    elif ext in JPEG_EXT:
        img = Image.open(image_path)
        exif = piexif.load(img.info.get("exif", b""))
        payload = secret.encode() + DELIMITER
        exif["Exif"][piexif.ExifIFD.UserComment] = b"ASCII\0\0\0" + payload
        img.save(output_path, "jpeg", exif=piexif.dump(exif), quality=95, subsampling=get_sampling(img))
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

        # Save the GIF in its original format
        frames[0].save(output_path, format="GIF", save_all=True, append_images=frames[1:], loop=0)
        print(f"✅ Hidden in GIF -> {output_path}")

    else:
        raise ValueError("Unsupported image format (PNG, JPEG, GIF only).")

# Reveal a message from an image (auto detect format)
def reveal_message(image_path):
    ext = os.path.splitext(image_path)[1].lower()

    if ext in PNG_EXT:
        hidden = lsb.reveal(image_path)
        if not hidden:
            raise ValueError("No hidden message found in PNG.")
        return hidden

    elif ext in JPEG_EXT:
        img = Image.open(image_path)
        exif = piexif.load(img.info.get("exif", b""))
        data = exif["Exif"].get(piexif.ExifIFD.UserComment, b"")
        if data.startswith(b"ASCII\0\0\0"):
            data = data[8:]
        if DELIMITER not in data:
            raise ValueError("No hidden message marker found in JPEG.")
        return data.split(DELIMITER)[0].decode()

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
            raise ValueError("No hidden message found in GIF.")

        bits = bits[:idx]
        chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
        return ''.join(chars)

    else:
        raise ValueError("Unsupported image format (PNG, JPEG, GIF only).")
