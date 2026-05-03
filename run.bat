@echo off
setlocal

cd /d "%~dp0"

echo =====================================
echo   LLM Eval Regression Dashboard
echo =====================================

echo [1] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

echo [2] Creating venv if not exists...
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)

echo [3] Activating venv...
call .venv\Scripts\activate.bat

echo [4] Upgrading pip...
python -m pip install --upgrade pip

echo [5] Installing dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo No requirements.txt found. Standard library project.
)

echo [6] Generating 250 eval cases...
python generate_samples.py

echo [7] Running deterministic + local AI eval...
python app.py --cases samples/cases.json --out report --use-ai

echo [8] Starting web dashboard...
start "Eval Backend" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python server.py"

timeout /t 2 >nul
start http://localhost:8007/

echo.
echo Project is running at http://localhost:8007/
echo.

pause
endlocal

