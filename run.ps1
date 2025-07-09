# Knowledge Graph Generator Runner
# This script activates the virtual environment and runs the project

Write-Host "🚀 Knowledge Graph Generator" -ForegroundColor Green
Write-Host "=" * 50

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\env\Scripts\Activate.ps1"

# Set API key
Write-Host "Setting API key..." -ForegroundColor Yellow
$env:GEMINI_API_KEY = "AIzaSyBBpVvZ8laKUDr0xFPcJPy5Ts7sQsy7kBQ"

# Run the project
Write-Host "Running knowledge graph generator..." -ForegroundColor Yellow
python main.py

Write-Host "✅ Done! Check knowledge_graph.html in your browser" -ForegroundColor Green
