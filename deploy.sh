#!/bin/bash

# 🚀 Bumuk Library CRM - Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🏛️ Bumuk Library CRM - Deployment Script"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# Bumuk Library CRM Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
CRM_NAME=Bumuk Library CRM
CRM_VERSION=1.0.0

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF
    echo "📝 Please edit .env file with your actual API keys before continuing"
    echo "🔑 Add your OpenAI API key to OPENAI_API_KEY variable"
    read -p "Press Enter after updating .env file..."
fi

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting the application..."
docker-compose up -d

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access your CRM at: http://localhost:8501"
    echo "📱 Remote teams can access at: http://your-server-ip:8501"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs -f"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop app:  docker-compose down"
echo "  Restart:   docker-compose restart"
echo "  Update:    git pull && docker-compose up -d --build"
echo ""
echo "🔒 Security Note: Make sure to configure your firewall to only allow access from trusted IP addresses"
