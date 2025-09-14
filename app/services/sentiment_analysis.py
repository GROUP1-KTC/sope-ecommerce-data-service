import re
from typing import List, Tuple, Dict
from app.models.schemas import SentimentResponse

class SentimentAnalysisService:
    def __init__(self):
        self.sentiment_keywords = {
            'positive': [
                'excellent', 'amazing', 'great', 'good', 'fantastic', 'wonderful',
                'perfect', 'love', 'best', 'awesome', 'outstanding', 'superb',
                'brilliant', 'satisfied', 'happy', 'pleased', 'impressed',
                'recommend', 'quality', 'fast', 'beautiful', 'comfortable'
            ],
            'negative': [
                'terrible', 'awful', 'bad', 'horrible', 'worst', 'hate',
                'disappointing', 'poor', 'cheap', 'broken', 'defective',
                'slow', 'uncomfortable', 'expensive', 'useless', 'waste',
                'regret', 'problem', 'issue', 'complaint', 'refund'
            ]
        }
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def analyze_sentiment(self, text: str) -> SentimentResponse:
        """Analyze sentiment of a single text"""
        if not text or not text.strip():
            return SentimentResponse(
                text=text,
                sentiment="neutral",
                confidence=0.0,
                score=0.0
            )
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Simple keyword-based sentiment analysis
        keyword_score = self._keyword_sentiment_score(processed_text)
        
        # Use keyword score as the final score
        final_score = keyword_score
        
        # Determine sentiment label
        if final_score > 0.1:
            sentiment = "positive"
        elif final_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate confidence based on score magnitude
        confidence = min(abs(final_score), 1.0)
        
        return SentimentResponse(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            score=final_score
        )
    
    def analyze_batch_sentiment(self, texts: List[str]) -> List[SentimentResponse]:
        """Analyze sentiment for a batch of texts"""
        return [self.analyze_sentiment(text) for text in texts]
    
    def _keyword_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score based on keyword presence"""
        words = text.split()
        positive_count = sum(1 for word in words if word in self.sentiment_keywords['positive'])
        negative_count = sum(1 for word in words if word in self.sentiment_keywords['negative'])
        
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_keywords
    
    def get_sentiment_distribution(self, texts: List[str]) -> Dict[str, float]:
        """Get distribution of sentiments in a collection of texts"""
        if not texts:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        
        results = self.analyze_batch_sentiment(texts)
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for result in results:
            sentiment_counts[result.sentiment] += 1
        
        total = len(results)
        return {
            sentiment: count / total 
            for sentiment, count in sentiment_counts.items()
        }

# Global instance
sentiment_service = SentimentAnalysisService()