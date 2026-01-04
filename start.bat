@echo off
REM Script de démarrage pour le Laboratoire Scientifique IA Pac-Man
REM Version Windows - Lance le backend et le frontend

echo ========================================
echo Laboratoire Scientifique IA Pac-Man
echo ========================================

REM Vérifier si Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Activer l'environnement virtuel si present
if exist "venv311\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel venv311...
    call "venv311\Scripts\activate.bat"
) else (
    echo Environnement virtuel non trouve, utilisation de Python systeme
)

REM Lancer le backend FastAPI
echo Lancement du backend FastAPI sur http://localhost:8000...
start "Backend Pac-Man" cmd /k "cd backend && python -m app_simple"

REM Attendre que le backend demarre
timeout /t 3 /nobreak >nul

REM Lancer le frontend React
echo Lancement du frontend React sur http://localhost:3000...
start "Frontend Pac-Man" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Applications lancees avec succes !
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Appuyez sur une touche pour fermer ce script...
