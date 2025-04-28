@echo off
title StegLens Builder
color 0A

echo Cleaning old builds...
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
del /q *.spec

echo Building new StegLens EXE...
python -m PyInstaller --onefile --noconsole ^
--add-data "Back-End;Back-End" ^
--add-data "Front-End;Front-End" ^
--hidden-import flask ^
--hidden-import flask_cors ^
--hidden-import PIL ^
--hidden-import stegano ^
--hidden-import piexif ^
--hidden-import Cryptodome ^
--hidden-import Crypto.Cipher.DES3 ^
--hidden-import Crypto.Cipher.AES ^
--hidden-import Crypto.Util.Padding ^
--icon=stegicon.ico ^
--name=StegLens ^
Launcher.py

echo Moving EXE out of dist folder...
move /Y dist\StegLens.exe StegLens.exe

echo.
echo ✅ Build and Move completed successfully!
echo Your EXE is now here: %cd%\StegLens.exe
pause
