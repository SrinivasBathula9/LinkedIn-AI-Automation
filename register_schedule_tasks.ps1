# LinkedIn Automation - Task Scheduler Registration
# Run ONCE as Administrator.
# DO NOT double-click - use the run_as_admin.bat launcher instead.
#
# This registers TWO daily start tasks (morning + evening).
# The start script auto-schedules its own stop after WINDOW_MINUTES=90.

# Keep window open on any error
$ErrorActionPreference = "Stop"
trap {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
    exit 1
}

# Check running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator." -ForegroundColor Red
    Write-Host "Close this window and use run_as_admin.bat instead." -ForegroundColor Yellow
    Read-Host
    exit 1
}

$ProjectDir = "d:\ML\Agentic AI\AGA\LinkedIn-Automation"
$StartScript = "$ProjectDir\start_automation.bat"
$StopScript  = "$ProjectDir\stop_automation.bat"

# --- Configure your local schedule here ---
# Set these to YOUR local time (the laptop's timezone).
# APScheduler fires region jobs relative to each region's timezone internally.
# You just need Docker running during these two daily windows.

$MorningStart = "08:55"   # 5 min before 9 AM window
$EveningStart = "23:15"   # 5 min before evening window
# ------------------------------------------

$Action_Start = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$StartScript`""

$Action_Stop = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$StopScript`""

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -DontStopOnIdleEnd

$currentUser = (& whoami).Trim()
$Principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Highest

# Morning start task
$TriggerMorning = New-ScheduledTaskTrigger -Daily -At $MorningStart
Unregister-ScheduledTask -TaskName "LinkedInAutomation_Morning" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName    "LinkedInAutomation_Morning" `
    -Action      $Action_Start `
    -Trigger     $TriggerMorning `
    -Settings    $Settings `
    -Principal   $Principal `
    -Description "Start LinkedIn automation for morning window ($MorningStart)" `
    -Force | Out-Null
Write-Host "Morning start task registered: $MorningStart daily" -ForegroundColor Green

# Evening start task
$TriggerEvening = New-ScheduledTaskTrigger -Daily -At $EveningStart
Unregister-ScheduledTask -TaskName "LinkedInAutomation_Evening" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName    "LinkedInAutomation_Evening" `
    -Action      $Action_Start `
    -Trigger     $TriggerEvening `
    -Settings    $Settings `
    -Principal   $Principal `
    -Description "Start LinkedIn automation for evening window ($EveningStart)" `
    -Force | Out-Null
Write-Host "Evening start task registered: $EveningStart daily" -ForegroundColor Green

# Emergency stop task (run on-demand only, no schedule)
Unregister-ScheduledTask -TaskName "LinkedInAutomation_EmergencyStop" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName    "LinkedInAutomation_EmergencyStop" `
    -Action      $Action_Stop `
    -Settings    $Settings `
    -Principal   $Principal `
    -Description "Emergency stop - run manually from Task Scheduler" `
    -Force | Out-Null
Write-Host "Emergency stop task registered (run manually from Task Scheduler)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Morning : starts at $MorningStart -> auto-stops after 90 min"
Write-Host "  Evening : starts at $EveningStart -> auto-stops after 90 min"
Write-Host "  RAM/CPU : idle rest of the day"
Write-Host ""
Write-Host "To change times: edit MorningStart/EveningStart in this script and re-run."
Write-Host "To emergency stop now: run stop_automation.bat"
Write-Host ""
Read-Host "Press Enter to exit"
