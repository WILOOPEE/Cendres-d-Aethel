@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo          CENDRES D'AETHEL
echo ========================================
echo 1. Edition Ultra Hard (options ajoutees)
echo 2. Edition Monde ouvert
echo 3. Quitter
echo.
set /p choix=Choisis une edition (1-3) : 
if "%choix%"=="1" goto ultra
if "%choix%"=="2" goto monde
if "%choix%"=="3" goto fin
echo Choix invalide.
pause
goto fin
:prepare
if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement Python local...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" goto erreur
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erreur
goto :eof
:ultra
call :prepare
if errorlevel 1 goto fin
.venv\Scripts\python.exe cendres_d_aethel.py
goto fin
:monde
call :prepare
if errorlevel 1 goto fin
.venv\Scripts\python.exe cendres_d_aethel_monde_ouvert.py
goto fin
:erreur
echo.
echo Installation impossible. Installe Python 3 depuis python.org et coche "Add Python to PATH".
echo Si l'environnement virtuel ne peut pas etre cree, consulte LISEZ_MOI.txt.
pause
goto fin
:fin
