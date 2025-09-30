#!/bin/bash

echo "🚀 Setting up Affiliate Scraper Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. Please update it with your MongoDB Atlas credentials."
    echo "📋 Edit .env file with your MongoDB Atlas connection string and other settings."
    exit 1
fi

echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🧪 Testing API..."
curl -f http://localhost:8000 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ API is running at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "❌ API is not responding. Check the logs with: docker-compose logs"
fi

echo "🎉 Setup complete!"
