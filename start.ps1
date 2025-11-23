# DocaCast - Start Script
# This script starts both the backend and frontend servers

Write-Host "🚀 Starting DocaCast Application..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Start Backend
Write-Host "📡 Starting Backend Server (port 8001)..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location "d:\Project\.Completed\DocaCast\backend"
    & "D:/Project/.Completed/DocaCast/.venv/Scripts/python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
}

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🎨 Starting Frontend Server (port 5173)..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "d:\Project\.Completed\DocaCast\frontend\pdf-reader-ui"
    npm run dev
}

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ Servers are starting!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Access the application at:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   Backend:  http://127.0.0.1:8001" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Gray
Write-Host ""

# Monitor jobs
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host ""
    Write-Host "🛑 Stopping servers..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    Write-Host "✅ Servers stopped" -ForegroundColor Green
}
