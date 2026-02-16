@echo off
echo Starting FlixVibe...
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.ps1
pip install -r requirements.txt
streamlit run app.py
pause
