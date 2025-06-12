# StegLens

StegLens is a graduation project that allows secure steganography by hiding encrypted text messages inside images (PNG, JPEG, GIF). It uses a Python Flask backend and a modern HTML/CSS/JS frontend.

## 🌐 Live Demo
[https://steglens.online](https://steglens.online)

## 🎯 Features
- Hide secret messages inside images
- AES-128 and 3DES optional encryption
- Multi-layer steganography (1-3 layers)
- Type message manually OR upload a text file
- Drag & drop image selection
- Clean modern responsive interface
- Works securely online from any device

## 🖥️ How to Run Locally
1. Clone the repo:
```
git clone https://github.com/your-username/StegLens.git
cd StegLens
```
2. Create virtual environment (optional):
```
python -m venv venv
source venv/bin/activate  # (Linux/macOS)
venv\Scripts\activate   # (Windows)
```
3. Install requirements:
```
pip install -r requirements.txt
```
4. Run Flask app:
```
cd Back-End
python App.py
```
5. Visit `http://127.0.0.1:5000` and test image + text file upload.

## 🚀 Deployment
Recommended: [https://render.com](https://render.com)
- Add your GitHub repo
- Set `build command: pip install -r requirements.txt`
- Set `start command: gunicorn App:app`
- Connect your domain `steglens.online`

## 📋 License

This project is licensed under the **GNU General Public License v3.0**.

You are free to use, modify, and redistribute this software under the terms of the [GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.html).
