# SOPE E-commerce Data Service

A comprehensive data processing service for e-commerce applications providing sentiment analysis, product filtering, recommendations, similarity matching, and high-benefit analytics.

## Features

### 🎭 Sentiment Analysis (Phân loại cảm xúc)
- Analyze sentiment of product reviews and comments
- Batch processing for multiple texts
- Support for Vietnamese and English text
- Real-time sentiment scoring (-1 to 1 scale)
- Confidence metrics for predictions

### 🔍 Product Filtering (Lọc sản phẩm)
- Advanced product search and filtering
- Category-based filtering
- Price range filtering
- Brand and rating-based filtering
- Full-text search across product descriptions
- Feature-based product matching

### 🎯 Product Recommendations (Sản phẩm gợi ý)
- Collaborative filtering based on user behavior
- Content-based filtering using product features
- Hybrid recommendation system
- Personalized recommendations for users
- Trending and popular product suggestions

### 🔗 Product Similarity (Sản phẩm tương tự)
- Content-based similarity matching
- Behavior-based similarity using user interactions
- Feature-based similarity comparison
- Pre-computed similarity matrices for performance
- Multiple similarity algorithms

### 📊 High-Benefit Analytics (Tập lợi ích cao)
- Multi-factor benefit scoring system
- User preference analysis
- Category performance analytics
- Trend analysis and predictions
- ROI and value optimization recommendations

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **ML Libraries**: scikit-learn, NLTK, TextBlob
- **API Documentation**: Auto-generated with Swagger/OpenAPI
- **Containerization**: Docker & Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/GROUP1-KTC/sope-ecommerce-data-service.git
cd sope-ecommerce-data-service
```

2. Start all services:
```bash
docker-compose up -d
```

3. The API will be available at `http://localhost:8000`
4. API documentation at `http://localhost:8000/docs`

### Manual Installation

1. Install Python 3.11+ and PostgreSQL
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

5. Initialize the database:
```bash
python -c "from app.utils.database_setup import create_tables; create_tables()"
```

6. Run the application:
```bash
python main.py
```

## API Endpoints

### Sentiment Analysis
- `POST /api/v1/sentiment/analyze` - Analyze single text sentiment
- `POST /api/v1/sentiment/analyze-batch` - Batch sentiment analysis
- `POST /api/v1/sentiment/distribution` - Get sentiment distribution

### Products
- `POST /api/v1/products/search` - Search and filter products
- `GET /api/v1/products/{product_id}` - Get product by ID
- `GET /api/v1/products/category/{category}` - Get products by category
- `GET /api/v1/products/trending/` - Get trending products
- `GET /api/v1/products/top-rated/` - Get top-rated products

### Recommendations
- `POST /api/v1/recommendations/` - Get product recommendations
- `GET /api/v1/recommendations/user/{user_id}` - Get user recommendations

### Similarity
- `POST /api/v1/similarity/` - Get similar products
- `GET /api/v1/similarity/product/{product_id}` - Get product similarities
- `POST /api/v1/similarity/compute-similarities` - Pre-compute similarities

### Analytics
- `POST /api/v1/analytics/high-benefit` - Analyze high-benefit products
- `GET /api/v1/analytics/high-benefit/` - Get high-benefit products
- `GET /api/v1/analytics/category/{category}` - Get category analytics
- `POST /api/v1/analytics/user-interaction` - Record user interaction

## Usage Examples

### Sentiment Analysis
```python
import requests

# Analyze sentiment
response = requests.post(
    "http://localhost:8000/api/v1/sentiment/analyze",
    json={"text": "This product is amazing!"}
)
print(response.json())
# Output: {"text": "This product is amazing!", "sentiment": "positive", "confidence": 0.8, "score": 0.7}
```

### Product Search
```python
# Search products
response = requests.post(
    "http://localhost:8000/api/v1/products/search",
    json={
        "category": "Electronics",
        "min_price": 100,
        "max_price": 1000,
        "search_query": "iPhone"
    }
)
```

### Get Recommendations
```python
# Get recommendations for a user
response = requests.get(
    "http://localhost:8000/api/v1/recommendations/user/user123?limit=5"
)
```

## Configuration

Environment variables can be set in `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce_data
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
pytest tests/test_sentiment.py -v
pytest tests/test_api.py -v
```

## Development

### Project Structure
```
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Configuration and settings
│   ├── database/      # Database connection and setup
│   ├── models/        # Database and Pydantic models
│   ├── services/      # Business logic services
│   └── utils/         # Utility functions
├── tests/             # Test cases
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker configuration
└── docker-compose.yml # Docker Compose setup
```

### Adding New Features

1. Create new service in `app/services/`
2. Add database models if needed in `app/models/database.py`
3. Create API endpoints in `app/api/`
4. Add tests in `tests/`
5. Update documentation

## Performance Optimization

- **Caching**: Redis is used for caching frequent queries
- **Database Indexing**: Key fields are indexed for fast queries
- **Batch Processing**: Support for batch operations to reduce API calls
- **Pre-computed Similarities**: Similarity matrices can be pre-computed
- **Async Operations**: FastAPI provides async support for I/O operations

## Monitoring and Logging

- Health check endpoints for all services
- Structured logging for debugging
- Performance metrics collection
- Error tracking and reporting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the API documentation at `/docs` endpoint