@echo off
echo 🚀 Starting Knowledge Graph RAG System
echo ==================================================

echo Activating virtual environment...
call ".\env\Scripts\activate.bat"

echo Starting Streamlit app...
echo The app will open in your default browser
echo Press Ctrl+C to stop the server

streamlit run streamlit_app.py

echo Streamlit app stopped
pause
