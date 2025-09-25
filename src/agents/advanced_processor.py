"""
Advanced AI processing with multiple models and techniques
"""
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline
import torch
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from src.utils.logger import logger

class AdvancedEmailProcessor:
    """Production-grade email processor with advanced AI"""
    
    def __init__(self):
        # Initialize models
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        self.zero_shot_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )
        
        # Intent categories
        self.intent_categories = [
            "pricing inquiry",
            "technical support",
            "complaint",
            "feature request",
            "billing issue",
            "sales opportunity",
            "partnership inquiry",
            "general question"
        ]
        
        # Initialize TF-IDF for similarity
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000)
        
        logger.info("Advanced Email Processor initialized")
    
    def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive email analysis"""
        content = email_data['content']
        
        # 1. Sentiment Analysis
        sentiment = self._analyze_sentiment(content)
        
        # 2. Intent Classification
        intent, confidence = self._classify_intent(content)
        
        # 3. Entity Extraction
        entities = self._extract_entities(content)
        
        # 4. Urgency Detection
        urgency_score = self._calculate_urgency(content, sentiment)
        
        # 5. Generate Summary
        summary = self._generate_summary(content) if len(content) > 500 else None
        
        # 6. Suggest Response
        response = self._generate_response(
            intent=intent,
            sentiment=sentiment,
            entities=entities,
            email_data=email_data
        )
        
        return {
            'intent': intent,
            'confidence_score': confidence,
            'sentiment': sentiment['label'],
            'sentiment_score': sentiment['score'],
            'urgency_score': urgency_score,
            'entities': entities,
            'summary': summary,
            'suggested_response': response,
            'requires_human': self._requires_human_review(
                confidence, urgency_score, sentiment
            )
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze email sentiment"""
        result = self.sentiment_analyzer(text[:512])[0]
        
        # Convert to -1 to 1 scale
        if result['label'] == 'NEGATIVE':
            score = -result['score']
        else:
            score = result['score']
        
        return {
            'label': result['label'].lower(),
            'score': score
        }
    
    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """Zero-shot intent classification"""
        result = self.zero_shot_classifier(
            text[:512],
            candidate_labels=self.intent_categories
        )
        
        # Get top intent
        intent = result['labels'][0].replace(' ', '_').upper()
        confidence = result['scores'][0]
        
        return intent, confidence
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from email"""
        entities = {
            'money': self._extract_money_mentions(text),
            'dates': self._extract_dates(text),
            'products': self._extract_product_mentions(text),
            'companies': self._extract_company_names(text)
        }
        return entities
    
    def _calculate_urgency(self, text: str, sentiment: Dict[str, Any]) -> float:
        """Calculate urgency score (0-1)"""
        urgency_keywords = [
            'urgent', 'asap', 'immediately', 'critical',
            'emergency', 'now', 'today', 'deadline'
        ]
        
        text_lower = text.lower()
        keyword_score = sum(1 for kw in urgency_keywords if kw in text_lower) / len(urgency_keywords)
        
        # Factor in sentiment
        sentiment_factor = 0.3 if sentiment['label'] == 'negative' else 0
        
        # Factor in exclamation marks
        exclamation_factor = min(text.count('!') / 10, 0.2)
        
        urgency_score = min(keyword_score + sentiment_factor + exclamation_factor, 1.0)
        
        return urgency_score
    
    def _requires_human_review(
        self,
        confidence: float,
        urgency: float,
        sentiment: Dict[str, Any]
    ) -> bool:
        """Determine if human review is needed"""
        if confidence < 0.7:
            return True
        if urgency > 0.7:
            return True
        if sentiment['label'] == 'negative' and sentiment['score'] < -0.8:
            return True
        return False
    
    def _generate_summary(self, content: str) -> str:
        """Generate email summary"""
        if len(content) < 100:
            return content
        
        summary = self.summarizer(
            content[:1024],
            max_length=130,
            min_length=30,
            do_sample=False
        )
        
        return summary[0]['summary_text']
    
    def _extract_money_mentions(self, text: str) -> List[str]:
        """Extract monetary amounts"""
        import re
        pattern = r'\$[\d,]+\.?\d*|\d+\s*(?:dollars|usd|euros|eur)'
        return re.findall(pattern, text.lower())
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract date mentions"""
        # Simplified - in production use dateutil or similar
        import re
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}'
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text.lower()))
        return dates
    
    def _extract_product_mentions(self, text: str) -> List[str]:
        """Extract product mentions"""
        # In production, use NER model or product catalog
        product_keywords = ['enterprise', 'starter', 'professional', 'api', 'integration']
        return [kw for kw in product_keywords if kw in text.lower()]
    
    def _extract_company_names(self, text: str) -> List[str]:
        """Extract company names"""
        # Simplified - in production use NER
        import re
        pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Ltd|Corp|Company))?'
        return re.findall(pattern, text)
    
    def _generate_response(
        self,
        intent: str,
        sentiment: Dict[str, Any],
        entities: Dict[str, Any],
        email_data: Dict[str, Any]
    ) -> str:
        """Generate contextual response"""
        # This would integrate with your template system
        # and LLM for dynamic response generation
        
        response_templates = {
            'PRICING_INQUIRY': self._pricing_response,
            'TECHNICAL_SUPPORT': self._support_response,
            'COMPLAINT': self._complaint_response,
        }
        
        template_func = response_templates.get(
            intent,
            self._default_response
        )
        
        return template_func(email_data, entities, sentiment)
    
    def _pricing_response(self, email_data, entities, sentiment):
        """Generate pricing inquiry response"""
        money_mentions = entities.get('money', [])
        
        response = f"Dear {email_data['sender'].split('@')[0]},\n\n"
        response += "Thank you for your interest in our pricing plans.\n\n"
        
        if money_mentions:
            response += f"I noticed you mentioned {', '.join(money_mentions)}. "
        
        response += "Here's our current pricing structure:\n"
        response += "- Starter: $49/month (up to 1,000 emails)\n"
        response += "- Professional: $149/month (up to 10,000 emails)\n"
        response += "- Enterprise: Custom pricing for unlimited usage\n\n"
        
        if sentiment['label'] == 'positive':
            response += "I'd be happy to schedule a demo to show you how our solution can benefit your team.\n"
        
        response += "\nBest regards,\nAI Workflow Team"
        
        return response
    
    def _support_response(self, email_data, entities, sentiment):
        """Generate support response"""
        return "Support response template"
    
    def _complaint_response(self, email_data, entities, sentiment):
        """Generate complaint response"""
        return "Complaint response template"
    
    def _default_response(self, email_data, entities, sentiment):
        """Default response template"""
        return "Default response template"
