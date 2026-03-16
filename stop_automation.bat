@echo off
:: LinkedIn Automation — STOP script
:: Gracefully stops all automation containers.
:: Called automatically by start_automation.bat after WINDOW_MINUTES.
:: Can also be run manually anytime to kill the stack.

set PROJECT_DIR=d:\ML\Agentic AI\AGA\LinkedIn-Automation
set COMPOSE_FILE=%PROJECT_DIR%\docker\docker-compose.automation.yml
set LOG_FILE=%PROJECT_DIR%\automation_startup.log

echo [%DATE% %TIME%] === Automation window ending — stopping services === >> "%LOG_FILE%"

docker compose -p linkedin -f "%COMPOSE_FILE%" stop >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% == 0 (
    echo [%DATE% %TIME%] All services stopped cleanly >> "%LOG_FILE%"
) else (
    echo [%DATE% %TIME%] WARNING: Some services may not have stopped cleanly >> "%LOG_FILE%"
)

:: Remove the one-shot auto-stop task (cleans up after itself)
schtasks /delete /tn "LinkedInAutomation_AutoStop" /f >nul 2>&1

echo [%DATE% %TIME%] === Done === >> "%LOG_FILE%"
