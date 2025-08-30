@echo off
setlocal enabledelayedexpansion

echo 🚀 Time Tracker Public Image Deployment
echo =======================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first:
    echo    https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

REM Get GitHub repository from git remote or prompt user
for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul ^| sed "s/.*github\.com[:/]\([^/]*\/[^/]*\)\.git/\1/"') do set GITHUB_REPO=%%i

if "%GITHUB_REPO%"=="" (
    echo ⚠️  Could not detect GitHub repository from git remote
    set /p GITHUB_REPO="Enter your GitHub repository (e.g., username/timetracker): "
)

REM Export for docker-compose
set GITHUB_REPOSITORY=%GITHUB_REPO%

echo 📦 Using public image: ghcr.io/%GITHUB_REPOSITORY%

REM Create necessary directories
echo 📁 Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your configuration before starting
    echo    Key settings to review:
    echo    - SECRET_KEY: Change this to a secure random string
    echo    - ADMIN_USERNAMES: Set your admin usernames
    echo    - TZ: Set your timezone
    echo    - CURRENCY: Set your currency
) else (
    echo ✅ .env file already exists
)

REM Pull the latest image
echo 📥 Pulling latest Time Tracker image...
docker pull ghcr.io/%GITHUB_REPOSITORY%:latest

REM Start the application using public image
echo 🚀 Starting Time Tracker with public image...
docker-compose -f docker-compose.public.yml up -d

REM Wait for application to start
echo ⏳ Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check if application is running
curl -f http://localhost:8080/_health >nul 2>&1
if errorlevel 1 (
    echo ❌ Application failed to start. Check logs with:
    echo    docker-compose -f docker-compose.public.yml logs
    pause
    exit /b 1
) else (
    echo ✅ Time Tracker is running successfully!
    echo.
    echo 🌐 Access the application at:
    echo    http://localhost:8080
    echo.
    echo 📋 Next steps:
    echo    1. Open the application in your browser
    echo    2. Log in with your admin username
    echo    3. Create your first project
    echo    4. Start tracking time!
    echo.
    echo 🔧 Useful commands:
    echo    View logs: docker-compose -f docker-compose.public.yml logs -f
    echo    Stop app:  docker-compose -f docker-compose.public.yml down
    echo    Restart:   docker-compose -f docker-compose.public.yml restart
    echo    Update:    docker pull ghcr.io/%GITHUB_REPOSITORY%:latest ^&^& docker-compose -f docker-compose.public.yml up -d
)

REM Optional: Enable TLS with reverse proxy
set /p ENABLE_TLS="🔒 Enable HTTPS with reverse proxy? (y/N): "
if /i "%ENABLE_TLS%"=="y" (
    echo 🔒 Starting with TLS support...
    docker-compose -f docker-compose.public.yml --profile tls up -d
    echo ✅ HTTPS enabled! Access at:
    echo    https://localhost
)

echo.
echo 🎉 Deployment complete!
echo.
echo 💡 Benefits of using the public image:
echo    - Faster deployment (no build time)
echo    - Consistent builds across environments
echo    - Automatic updates when you push to main
echo    - Multi-architecture support (AMD64, ARM64, ARMv7)

pause
