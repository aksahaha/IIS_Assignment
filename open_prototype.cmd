@echo off
setlocal
cd /d "%~dp0"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
  python serve_prototype.py %*
  goto done
)
set "PROTOTYPE_PYTHON="
for /d %%D in ("%ProgramFiles%\WindowsApps\OpenAI.CodexPrimaryRuntime.*") do (
  if exist "%%~fD\dependencies\python\python.exe" set "PROTOTYPE_PYTHON=%%~fD\dependencies\python\python.exe"
)
if defined PROTOTYPE_PYTHON (
  "%PROTOTYPE_PYTHON%" serve_prototype.py %*
  goto done
)
py -3 serve_prototype.py %*
:done
if errorlevel 1 (
  echo.
  echo The prototype needs Python 3.10 or newer. Keep this window open while using it.
  echo You can also run: python serve_prototype.py
  pause
)
