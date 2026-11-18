@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo   OpenPin - Local Offline Sync for Plaud NotePin ^& Note
echo   Seu hardware, seus audios - 100%% local e sem nuvem
echo ============================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        set "PY_CMD=py -3"
    ) else (
        echo [!] Python 3 nao encontrado neste computador / Python 3 not found.
        echo.
        echo Deseja instalar o Python 3.12 automaticamente pelo Windows ^(winget^)?
        echo Install Python 3.12 automatically via Windows winget? [S/Y = Sim/Yes, N = Nao/No]
        set /p INSTALL_PY="> "
        if /i "!INSTALL_PY!"=="S" goto :install_py
        if /i "!INSTALL_PY!"=="Y" goto :install_py
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    set "PY_CMD=python"
)
goto :setup_venv

:install_py
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
echo.
echo [OK] Python instalado! Feche esta janela e clique duas vezes em Start-Windows.bat novamente.
echo [OK] Python installed! Close this window and double-click Start-Windows.bat again.
pause
exit /b 0

:setup_venv
if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Criando ambiente isolado pela primeira vez / Creating local environment...
    %PY_CMD% -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERRO] Falha ao criar .venv. Verifique se o Python 3.10+ esta instalado.
        pause
        exit /b 1
    )
    echo [2/2] Instalando dependencias locais / Installing local dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        echo [!] Tentando instalacao basica sem pacotes opcionais WinRT...
        ".venv\Scripts\python.exe" -m pip install fastapi uvicorn python-multipart bleak websockets av
    )
)

echo.
echo [OK] Abrindo painel no navegador em http://127.0.0.1:8765 ...
echo [OK] Opening control panel in browser at http://127.0.0.1:8765 ...
echo      ^(Mantenha esta janela aberta enquanto usa o aplicativo / Keep this window open^)
echo.

".venv\Scripts\python.exe" -m openpin
pause
