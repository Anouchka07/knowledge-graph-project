# GraphRAG Streamlit App Runner
# This script activates the virtual environment and runs the Streamlit app

Write-Host "🚀 Starting Knowledge Graph RAG System" -ForegroundColor Green
Write-Host "=" * 50

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\env\Scripts\Activate.ps1"

# Run the Streamlit app
Write-Host "Starting Streamlit app..." -ForegroundColor Yellow
Write-Host "The app will open in your default browser" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or Ctrl+Break to stop the server" -ForegroundColor Red
Write-Host "If Ctrl+C doesn't work, try Ctrl+Break or close this terminal" -ForegroundColor Magenta

try {
    streamlit run streamlit_app.py
}
finally {
    Write-Host "Streamlit app stopped" -ForegroundColor Green
}
