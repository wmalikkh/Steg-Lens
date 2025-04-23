from PIL import Image
import io

# ✅ إخفاء نص داخل صورة JPEG
def hide_in_jpeg(image_bytes, message):
    image = Image.open(io.BytesIO(image_bytes))

    # 🔄 تأكد من أن الصورة بصيغة RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    pixels = image.load()
    width, height = image.size

    # 🧬 تحويل الرسالة إلى ثنائية مع نهاية مميزة
    binary_message = ''.join(format(ord(c), '08b') for c in message) + '1111111111111110'
    data_index = 0

    # 🔁 كتابة كل بت داخل قيمة الأحمر (R) في البكسلات
    for y in range(height):
        for x in range(width):
            if data_index >= len(binary_message):
                break
            r, g, b = pixels[x, y]
            r = (r & ~1) | int(binary_message[data_index])  # أدخل البت في أقل بت للرّقم
            pixels[x, y] = (r, g, b)
            data_index += 1
        if data_index >= len(binary_message):
            break

    # 📤 حفظ النتيجة في BytesIO
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)  # ✅ استخدم جودة جيدة
    output.seek(0)
    return output.getvalue()

# ✅ استخراج نص من صورة JPEG
def extract_from_jpeg(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))

    # 🔄 تأكد من أن الصورة بصيغة RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    pixels = image.load()
    width, height = image.size

    # 🧪 قراءة أقل بت من كل R (قناة الأحمر)
    binary_message = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary_message += str(r & 1)

    # 🧷 علامة نهاية الرسالة
    end_marker = '1111111111111110'
    end_index = binary_message.find(end_marker)
    if end_index == -1:
        return None  # ⛔ لم يتم العثور على نهاية الرسالة

    binary_message = binary_message[:end_index]

    # 🔄 تحويل ثنائي إلى نص
    message = ''
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if len(byte) == 8:
            message += chr(int(byte, 2))

    return message