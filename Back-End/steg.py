from stegano import lsb
import os

def hide_message():
    input_path = input("Enter path to the input image (e.g. image.png): ").strip()
    if not os.path.isfile(input_path):
        print("❌ File not found.")
        return

    message = input("Enter the message to hide: ").strip()
    if not message:
        print("❌ Message cannot be empty.")
        return

    output_path = input("Enter name for the output image (e.g. secret.png): ").strip()
    if not output_path.lower().endswith(".png"):
        output_path += ".png"

    try:
        secret_image = lsb.hide(input_path, message)
        secret_image.save(output_path)
        print(f"✅ Message hidden successfully in '{output_path}'")
    except Exception as e:
        print(f"❌ Error hiding message: {e}")

def reveal_message():
    image_path = input("Enter path to the image with the hidden message: ").strip()
    if not os.path.isfile(image_path):
        print("❌ File not found.")
        return

    try:
        message = lsb.reveal(image_path)
        if message:
            print(f"✅ Hidden message: {message}")
        else:
            print("⚠️ No hidden message found.")
    except Exception as e:
        print(f"❌ Error revealing message: {e}")

def main():
    print("Choose operation:")
    print("1. Hide a message")
    print("2. Reveal a message")
    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == '1':
        hide_message()
    elif choice == '2':
        reveal_message()
    else:
        print("❌ Invalid choice.")

if __name__ == "__main__":
    main()
