@echo off
where.exe py >nul 2>&1
if not errorlevel 1 (
    py -3 -X utf8 "%~dp0herdr_attention.py" %*
) else (
    python -X utf8 "%~dp0herdr_attention.py" %*
)
