@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .buildenv
if errorlevel 1 goto fail
call .buildenv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pygame-ce pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --name "Cendres d'Aethel" --add-data "Jeu\cendres_d_aethel.py;." --add-data "Jeu\cendres_d_aethel_monde_ouvert.py;." windows_launcher.py
if errorlevel 1 goto fail
echo.
echo EXE cree dans dist\Cendres d'Aethel.exe
pause
exit /b 0
:fail
echo Echec de la construction. Verifie que Python 3 est installe et accessible avec py -3.
pause
exit /b 1
