#!/bin/bash

# Time Tracker Public Image Deployment Script
# This script deploys Time Tracker using the pre-built public Docker image

set -e

echo "🚀 Time Tracker Public Image Deployment"
echo "======================================="

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

# Get GitHub repository from git remote or prompt user
GITHUB_REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github\.com[:/]\([^/]*\/[^/]*\)\.git/\1/' || echo "")

if [ -z "$GITHUB_REPO" ]; then
    echo "⚠️  Could not detect GitHub repository from git remote"
    read -p "Enter your GitHub repository (e.g., username/timetracker): " GITHUB_REPO
fi

# Export for docker-compose
export GITHUB_REPOSITORY="$GITHUB_REPO"

echo "📦 Using public image: ghcr.io/$GITHUB_REPOSITORY"

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

# Pull the latest image
echo "📥 Pulling latest Time Tracker image..."
docker pull "ghcr.io/$GITHUB_REPOSITORY:latest"

# Start the application using public image
echo "🚀 Starting Time Tracker with public image..."
docker-compose -f docker-compose.public.yml up -d

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
    echo "   View logs: docker-compose -f docker-compose.public.yml logs -f"
    echo "   Stop app:  docker-compose -f docker-compose.public.yml down"
    echo "   Restart:   docker-compose -f docker-compose.public.yml restart"
    echo "   Update:    docker pull ghcr.io/$GITHUB_REPOSITORY:latest && docker-compose -f docker-compose.public.yml up -d"
else
    echo "❌ Application failed to start. Check logs with:"
    echo "   docker-compose -f docker-compose.public.yml logs"
    exit 1
fi

# Optional: Enable TLS with reverse proxy
read -p "🔒 Enable HTTPS with reverse proxy? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔒 Starting with TLS support..."
    docker-compose -f docker-compose.public.yml --profile tls up -d
    echo "✅ HTTPS enabled! Access at:"
    echo "   https://$(hostname -I | awk '{print $1}')"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "💡 Benefits of using the public image:"
echo "   - Faster deployment (no build time)"
echo "   - Consistent builds across environments"
echo "   - Automatic updates when you push to main"
echo "   - Multi-architecture support (AMD64, ARM64, ARMv7)"
