@echo off
:: LinkedIn Automation — START script
:: Called by Task Scheduler before each automation window.
:: Starts lean services, then schedules auto-stop after WINDOW_MINUTES.

set PROJECT_DIR=d:\ML\Agentic AI\AGA\LinkedIn-Automation
set COMPOSE_FILE=%PROJECT_DIR%\docker\docker-compose.automation.yml
set LOG_FILE=%PROJECT_DIR%\automation_startup.log

:: How long (minutes) to keep services running after start.
:: Morning: jobs fire ~5-10 min after start, each campaign takes ~15-30 min.
:: 90 min is safe for all regions in a window.
set WINDOW_MINUTES=90

echo [%DATE% %TIME%] === Automation window starting === >> "%LOG_FILE%"

:: Wait for Docker Desktop to be ready (max 90 sec)
set /a WAIT=0
:WAIT_DOCKER
docker info >nul 2>&1
if %ERRORLEVEL% == 0 goto DOCKER_READY
if %WAIT% GEQ 18 goto DOCKER_TIMEOUT
set /a WAIT+=1
timeout /t 5 /nobreak >nul
goto WAIT_DOCKER

:DOCKER_TIMEOUT
echo [%DATE% %TIME%] ERROR: Docker not ready — aborting >> "%LOG_FILE%"
exit /b 1

:DOCKER_READY
echo [%DATE% %TIME%] Docker ready. Starting automation services... >> "%LOG_FILE%"
docker compose -p linkedin -f "%COMPOSE_FILE%" up -d --no-build >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Failed to start containers >> "%LOG_FILE%"
    exit /b 1
)

echo [%DATE% %TIME%] Services up. Auto-stop scheduled in %WINDOW_MINUTES% minutes. >> "%LOG_FILE%"

:: Schedule auto-stop via Task Scheduler (one-shot, runs once then deletes itself)
set STOP_SCRIPT=%PROJECT_DIR%\stop_automation.bat
set STOP_TIME_CMD=powershell -Command "(Get-Date).AddMinutes(%WINDOW_MINUTES%).ToString('HH:mm')"
for /f %%T in ('%STOP_TIME_CMD%') do set STOP_TIME=%%T

schtasks /create /tn "LinkedInAutomation_AutoStop" /tr "\"%STOP_SCRIPT%\"" ^
    /sc once /st %STOP_TIME% /f >nul 2>&1

echo [%DATE% %TIME%] Auto-stop task set for %STOP_TIME% >> "%LOG_FILE%"
