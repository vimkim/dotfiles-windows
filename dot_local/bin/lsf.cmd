@echo off
where.exe py >nul 2>&1
if not errorlevel 1 (
    py -3 -X utf8 "%~dp0listing.py" lsf %*
) else (
    python -X utf8 "%~dp0listing.py" lsf %*
)
