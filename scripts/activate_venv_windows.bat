@echo off
REM Script d'activation de l'environnement virtuel pour le projet lab-ia-pacman
REM Version recommandée : Python 3.11 (compatibilité optimale avec ONNX Runtime et SQLAlchemy)

REM Vérifier la version de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur : Python n'est pas installé ou n'est pas dans le PATH.
    echo Installez Python 3.11 depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Extraire la version (format: Python X.Y.Z)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do set PYTHON_MAJOR=%%a& set PYTHON_MINOR=%%b

REM Vérifier la compatibilité
if %PYTHON_MAJOR% LSS 3 (
    echo Attention : Python %PYTHON_VERSION% est trop ancien. Version minimale requise : 3.9
    echo Le projet peut ne pas fonctionner correctement.
    pause
) else if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 9 (
        echo Attention : Python %PYTHON_VERSION% est trop ancien. Version minimale requise : 3.9
        echo Le projet peut ne pas fonctionner correctement.
        pause
    ) else if %PYTHON_MINOR% GTR 13 (
        echo Attention : Python %PYTHON_VERSION% est plus recent que 3.13.
        echo Certaines dependances (ONNX Runtime, SQLAlchemy) peuvent ne pas etre compatibles.
        echo Recommande : downgrader vers Python 3.11.
        pause
    )
)

echo Version Python detectee : %PYTHON_VERSION%
echo Creation de l'environnement virtuel .venv...
python -m venv .venv
if errorlevel 1 (
    echo Erreur lors de la creation de l'environnement virtuel.
    pause
    exit /b 1
)

echo Activation de l'environnement...
.\.venv\Scripts\activate
if errorlevel 1 (
    echo Erreur lors de l'activation de l'environnement.
    pause
    exit /b 1
)

echo Virtual environment .venv cree et active.
echo Pour installer les dependances, executez : pip install -r requirements.txt
pause
