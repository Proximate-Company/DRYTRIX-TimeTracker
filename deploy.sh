#!/bin/bash

# Time Tracker Deployment Script for Raspberry Pi
# This script sets up the Time Tracker application on a Raspberry Pi

set -e

echo "🚀 Time Tracker Deployment Script"
echo "=================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "   It may work on other systems but is not tested"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker $USER"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install docker-compose-plugin"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs backups

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration before starting"
    echo "   Key settings to review:"
    echo "   - SECRET_KEY: Change this to a secure random string"
    echo "   - ADMIN_USERNAMES: Set your admin usernames"
    echo "   - TZ: Set your timezone"
    echo "   - CURRENCY: Set your currency"
else
    echo "✅ .env file already exists"
fi

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting Time Tracker..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if curl -f http://localhost:8080/_health > /dev/null 2>&1; then
    echo "✅ Time Tracker is running successfully!"
    echo ""
    echo "🌐 Access the application at:"
    echo "   http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Open the application in your browser"
    echo "   2. Log in with your admin username"
    echo "   3. Create your first project"
    echo "   4. Start tracking time!"
    echo ""
    echo "🔧 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop app:  docker-compose down"
    echo "   Restart:   docker-compose restart"
    echo "   Update:    git pull && docker-compose up -d --build"
else
    echo "❌ Application failed to start. Check logs with:"
    echo "   docker-compose logs"
    exit 1
fi

# Optional: Enable TLS with reverse proxy
read -p "🔒 Enable HTTPS with reverse proxy? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔒 Starting with TLS support..."
    docker-compose --profile tls up -d
    echo "✅ HTTPS enabled! Access at:"
    echo "   https://$(hostname -I | awk '{print $1}')"
fi

echo ""
echo "🎉 Deployment complete!"
