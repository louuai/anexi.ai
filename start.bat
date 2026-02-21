@echo off
echo ========================================
echo   Anexi.ai - Quick Start Script
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker n'est pas en cours d'execution!
    echo Demarrez Docker Desktop et reessayez.
    pause
    exit /b 1
)

echo [OK] Docker est en cours d'execution
echo.

echo Demarrage des services...
echo.

docker-compose up -d

echo.
echo [OK] Services demarres!
echo.
echo Services disponibles:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - PostgreSQL: localhost:5433
echo.
echo Commandes utiles:
echo   - Voir les logs: docker-compose logs -f
echo   - Arreter: docker-compose down
echo   - Redemarrer: docker-compose restart
echo.
echo Attendez ~30 secondes que tout demarre...
echo.
echo Ouvrez http://localhost:3000 pour commencer!
echo.
pause
