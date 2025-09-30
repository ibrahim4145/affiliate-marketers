# Affiliate Scraper Backend

FastAPI backend for the Affiliate Scraper application with MongoDB Atlas integration.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- MongoDB Atlas account and cluster

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd affiliate-scraper-project/backend
   ```

2. **Create environment file**
   ```bash
   cp env.example .env
   ```

3. **Configure your environment variables in `.env`**
   ```env
   # MongoDB Atlas Configuration
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name
   MONGO_DB=affiliate_marketers

   # JWT Configuration
   SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440

   # CORS Configuration
   ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

5. **Test the API**
   ```bash
   curl http://localhost:8000
   ```

## 📋 API Endpoints

- **API Base**: `http://localhost:3000`
- **Documentation**: `http://localhost:3000/docs`
- **Registration**: `http://localhost:3000/api/auth/register`
- **Login**: `http://localhost:3000/api/auth/login`

## 🛑 Stop the Application

```bash
docker-compose down
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB Atlas connection string | Required |
| `MONGO_DB` | Database name | `affiliate_marketers` |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `1440` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

## 🚀 Production Deployment

For production deployment on Koyeb:

1. Set the environment variables in your Koyeb service settings
2. Deploy using the Dockerfile
3. Your API will be available at your Koyeb URL
