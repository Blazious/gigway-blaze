@echo off
setlocal

echo Stopping GigWay dev servers on ports 5173 and 8000...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173 .*LISTENING"') do (
  taskkill /PID %%p /T /F >nul 2>nul
)

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 .*LISTENING"') do (
  taskkill /PID %%p /T /F >nul 2>nul
)

echo Done.
endlocal
