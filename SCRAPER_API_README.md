# Scraper Allocator API

A FastAPI-based scraper task allocation system that manages scraping jobs across industries and queries with progress tracking.

## 🚀 Features

- **Intelligent Task Allocation**: Automatically assigns the next scraping task based on progress
- **Progress Tracking**: Tracks completion status and pagination for each task
- **MongoDB Integration**: Uses Motor async client for high-performance database operations
- **RESTful API**: Clean, well-documented endpoints with proper error handling
- **Type Safety**: Full Pydantic model validation for requests and responses

## 📋 API Endpoints

### 1. POST `/api/scraper/run`
Assigns the next scraping task based on current progress.

**Response:**
```json
{
  "industry_name": "Technology",
  "query": "best SaaS tools for startups",
  "start_param": 1,
  "progress_id": "64f8a1b2c3d4e5f678901234"
}
```

**Logic:**
- If `scraped_progress` is empty → first industry + first query
- If last task not done → return same task
- If last task done → move to next industry/query combination

### 2. PATCH `/api/scraper/update-progress/{id}`
Updates an existing progress record.

**Request Body:**
```json
{
  "done": true,
  "start_param": 15,
  "se_id": "session_abc123"
}
```

**Response:**
```json
{
  "id": "64f8a1b2c3d4e5f678901234",
  "i_id": "64f8a1b2c3d4e5f678901235",
  "q_id": "64f8a1b2c3d4e5f678901236",
  "done": true,
  "start_param": 15,
  "se_id": "session_abc123",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. GET `/api/scraper/status`
Get current scraper status and statistics.

**Response:**
```json
{
  "industries_count": 4,
  "queries_count": 4,
  "total_progress": 8,
  "completed_progress": 3,
  "last_progress": { ... }
}
```

## 🗄️ Database Schema

### Collections

#### `industries`
```json
{
  "_id": ObjectId,
  "industry_name": "Technology"
}
```

#### `queries`
```json
{
  "_id": ObjectId,
  "query": "best SaaS tools for startups"
}
```

#### `scraped_progress`
```json
{
  "_id": ObjectId,
  "i_id": "industry_id",
  "q_id": "query_id",
  "done": false,
  "start_param": 1,
  "se_id": "session_id",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- FastAPI
- Motor (async MongoDB driver)

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export MONGODB_URL="mongodb://localhost:27017"
```

3. **Start MongoDB:**
```bash
mongod
```

4. **Run the API:**
```bash
uvicorn app.main:app --reload
```

5. **Access API documentation:**
```
http://localhost:8000/docs
```

## 📊 Usage Examples

### 1. Create Sample Data

```javascript
// MongoDB shell
db.industries.insertMany([
  { "industry_name": "Technology" },
  { "industry_name": "Finance" },
  { "industry_name": "Healthcare" }
]);

db.queries.insertMany([
  { "query": "best SaaS tools" },
  { "query": "crypto trends" },
  { "query": "AI healthcare solutions" }
]);
```

### 2. Get Next Task

```bash
curl -X POST "http://localhost:8000/api/scraper/run"
```

### 3. Update Progress

```bash
curl -X PATCH "http://localhost:8000/api/scraper/update-progress/64f8a1b2c3d4e5f678901234" \
  -H "Content-Type: application/json" \
  -d '{
    "done": true,
    "start_param": 10,
    "se_id": "session_123"
  }'
```

### 4. Check Status

```bash
curl -X GET "http://localhost:8000/api/scraper/status"
```

## 🔄 Task Allocation Logic

The API implements a sophisticated task allocation system:

1. **First Run**: Assigns first industry + first query
2. **Incomplete Task**: Returns the same task if not done
3. **Complete Task**: Moves to next industry for same query
4. **Query Complete**: Moves to next query + first industry
5. **All Complete**: Restarts from beginning

## 🚨 Error Handling

- **400 Bad Request**: Invalid data or missing collections
- **404 Not Found**: Progress record not found
- **500 Internal Server Error**: Database or server issues

## 🧪 Testing

Run the test script:
```bash
python test_scraper_api.py
```

## 📈 Performance Features

- **Async Operations**: All database operations are asynchronous
- **Connection Pooling**: Efficient MongoDB connection management
- **Index Optimization**: Proper indexing for fast queries
- **Error Recovery**: Graceful handling of edge cases

## 🔧 Configuration

Environment variables:
- `MONGODB_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name (default: scraper_db)

## 📝 API Documentation

Full interactive documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
