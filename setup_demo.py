"""
Setup script to create demo data and test the system
"""
import os
from dotenv import load_dotenv
from src.models.database import SessionLocal, KnowledgeBase, Base, engine
from src.core.vector_store import VectorStoreManager
from datetime import datetime

load_dotenv()

def setup_demo_knowledge_base():
    """Create sample knowledge base entries"""
    db = SessionLocal()
    vector_store = VectorStoreManager()
    
    # Sample knowledge base documents
    demo_docs = [
        {
            "title": "Company Pricing Guide",
            "content": """
# Pricing Plans

## Starter Plan - $49/month
- Up to 100 emails per day
- Basic AI responses
- Email support
- 1 user account

## Professional Plan - $149/month
- Up to 1000 emails per day
- Advanced AI with custom training
- Priority support
- 5 user accounts
- API access

## Enterprise Plan - Custom Pricing
- Unlimited emails
- Custom AI model training
- Dedicated support team
- Unlimited users
- SLA guarantee
- On-premise deployment option

## Annual Discounts
- 10% off for annual billing
- 15% off for 2-year commitment
            """
        },
        {
            "title": "Product Features Guide",
            "content": """
# Key Features

## Email Automation
- Intelligent email classification
- Automatic response generation
- Multi-language support
- Sentiment analysis

## Knowledge Management
- Notion integration
- Document search
- Auto-updating knowledge base
- Version control

## Security Features
- End-to-end encryption
- GDPR compliant
- SOC 2 certified
- Regular security audits
            """
        },
        {
            "title": "Support Documentation",
            "content": """
# Customer Support Guide

## Support Hours
- Standard: 9 AM - 5 PM EST (Mon-Fri)
- Premium: 24/7 support

## Contact Methods
- Email: support@aiworkflow.com
- Chat: Available on dashboard
- Phone: Premium plans only

## Response Times
- Standard: 24-48 hours
- Premium: 4 hours
- Enterprise: 1 hour

## Common Issues
1. API Integration - Check API keys
2. Email not processing - Verify permissions
3. Slow response - Check rate limits
            """
        }
    ]
    
    print("Setting up demo knowledge base...")
    
    for doc in demo_docs:
        # Add to database
        kb_entry = KnowledgeBase(
            source="manual",
            title=doc["title"],
            content=doc["content"]
        )
        db.add(kb_entry)
        
        # Add to vector store
        metadata = {
            "source": "manual",
            "title": doc["title"],
            "created_at": datetime.utcnow().isoformat()
        }
        vector_store.add_document(doc["content"], metadata)
        print(f"✅ Added: {doc['title']}")
    
    db.commit()
    db.close()
    print("\n✅ Demo knowledge base setup complete!")

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Setup demo data
    setup_demo_knowledge_base()
    
    print("\n🚀 Demo setup complete! You can now run the application.")
