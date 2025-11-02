@echo off
echo 🚀 MediSage AI Deployment Script
echo ==================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Please create it first.
    pause
    exit /b 1
)

echo ✅ Environment file found

REM Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose down

REM Build images
echo 🔨 Building Docker images...
docker-compose build --no-cache

REM Start containers
echo 🚀 Starting containers...
docker-compose up -d

REM Wait for services
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak

REM Check status
docker-compose ps

echo.
echo ✅ Deployment complete!
echo.
echo 🌐 Access your application at:
echo    Frontend: http://localhost:8501
echo    Backend API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
pause