@echo off
REM ============================================================
REM  iniciar_app.bat - Arranca la app de certificados
REM  de Academia Horizonte en http://localhost:5000
REM  Doble clic para ejecutar. Cerrar la ventana o Ctrl+C
REM  para detener el servidor.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

REM ---- Comprobar que Python esta instalado ----
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python.
    echo Instalalo desde https://www.python.org y marca la opcion
    echo "Add Python to PATH", luego vuelve a hacer doble clic.
    pause
    exit /b 1
)

REM ---- Instalar dependencias solo si faltan ----
python -c "import flask, openpyxl" 2>nul
if errorlevel 1 (
    echo Instalando dependencias: flask y openpyxl ...
    python -m pip install flask openpyxl
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las librerias.
        pause
        exit /b 1
    )
)

REM ---- Abrir el navegador y arrancar el servidor ----
echo Arrancando Academia Horizonte en http://localhost:5000
start http://localhost:5000
python app.py

pause
