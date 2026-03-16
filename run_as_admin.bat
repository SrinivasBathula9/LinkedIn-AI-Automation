@echo off
:: Launches register_schedule_tasks.ps1 as Administrator with execution policy bypass.
:: Double-click THIS file to register the scheduler tasks.

set SCRIPT=%~dp0register_schedule_tasks.ps1

powershell -Command "Start-Process powershell -ArgumentList '-NoExit -ExecutionPolicy Bypass -File \"%SCRIPT%\"' -Verb RunAs"
