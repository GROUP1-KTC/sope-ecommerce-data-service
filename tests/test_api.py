import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "SOPE E-commerce Data Service"

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_sentiment_analyze_endpoint():
    """Test sentiment analysis endpoint"""
    response = client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "This is a great product!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "confidence" in data
    assert "score" in data

def test_sentiment_batch_analyze_endpoint():
    """Test batch sentiment analysis endpoint"""
    response = client.post(
        "/api/v1/sentiment/analyze-batch",
        json={"texts": ["Great product!", "Terrible quality"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2

def test_sentiment_health_endpoint():
    """Test sentiment service health check"""
    response = client.get("/api/v1/sentiment/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentiment_analysis"