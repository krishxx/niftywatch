@echo off

REM Step 1: Navigate to virtual environment Scripts folder
cd /d "D:\niftywatch\niftywatch\p310env\Scripts"

REM Step 2: Activate the virtual environment
call activate.bat

REM Step 3: Navigate to project source folder
cd /d "D:\niftywatch\niftywatch\src"

REM Start server.py in a new background window
echo Starting server.py in background...
start "" /B python server.py

REM Start HTTP server on port 5000 in a new background window
echo Starting HTTP server on port 5000...
start "" /B python -m http.server 5000

:loop
echo [%time%] Running get_idx.py
python get_idx.py

echo [%time%] Running live_fvg_monitor.py
python live_fvg_monitor.py

echo [%time%] Displaying FVG CSV output...
python tail_csv.py

REM Wait for 30 seconds
timeout /t 30 >nul

REM Repeat the loop
goto loop