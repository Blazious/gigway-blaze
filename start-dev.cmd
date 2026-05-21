@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%escrow_platform"
set "FRONTEND_DIR=%ROOT%frontend"
set "BACKEND_URL=http://127.0.0.1:8000/api/health/"
set "FRONTEND_URL=http://127.0.0.1:5173/"

echo Starting GigWay fullstack dev environment...
echo.

if not exist "%BACKEND_DIR%\manage.py" (
  echo Backend not found at "%BACKEND_DIR%".
  exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo Frontend not found at "%FRONTEND_DIR%".
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH.
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found on PATH.
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo Installing frontend dependencies...
  pushd "%FRONTEND_DIR%" >nul
  call npm.cmd install
  if errorlevel 1 (
    popd >nul
    echo Frontend dependency install failed.
    exit /b 1
  )
  popd >nul
)

netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  echo Port 8000 is already in use. Run stop-dev.cmd first, then try again.
  exit /b 1
)

netstat -ano | findstr /r /c:":5173 .*LISTENING" >nul
if not errorlevel 1 (
  echo Port 5173 is already in use. Run stop-dev.cmd first, then try again.
  exit /b 1
)

echo Starting backend at http://127.0.0.1:8000/
start "GigWay Backend" /D "%BACKEND_DIR%" cmd /k python manage.py runserver 127.0.0.1:8000 --noreload

echo Starting frontend at http://127.0.0.1:5173/
start "GigWay Frontend" /D "%FRONTEND_DIR%" cmd /k npm.cmd run dev -- --host 127.0.0.1

echo.
echo Give both windows a few seconds to finish starting.
echo Frontend: %FRONTEND_URL%
echo Backend health: %BACKEND_URL%
echo.
echo Close the two server windows to stop the dev environment.

endlocal
