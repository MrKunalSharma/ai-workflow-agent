from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Workflow Agent (Simplified)",
    description="Simplified version for testing",
    version="1.0.0"
)

# Simple in-memory storage
knowledge_base = []
processed_emails = []

class TestEmailRequest(BaseModel):
    sender: str
    subject: str
    content: str

class EmailProcessor:
    """Simplified email processor"""
    
    def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simple processing logic
        content_lower = email_data['content'].lower()
        
        # Determine intent
        if 'pricing' in content_lower:
            intent = 'pricing_inquiry'
            response = "Thank you for your interest in our pricing. Our plans start at $49/month for the Starter plan, $149/month for Professional, and custom pricing for Enterprise. We offer 10% discount for annual billing."
        elif 'support' in content_lower or 'help' in content_lower:
            intent = 'support_request'
            response = "Thank you for contacting support. Our team is available Mon-Fri 9AM-5PM EST. For immediate assistance, please check our documentation."
        else:
            intent = 'general_inquiry'
            response = "Thank you for your email. We've received your message and will respond within 24-48 hours."
        
        # Determine priority
        priority = 'high' if 'urgent' in content_lower else 'normal'
        
        return {
            'intent': intent,
            'priority': priority,
            'suggested_response': response,
            'original_email': email_data
        }

# Create processor instance
email_processor = EmailProcessor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Workflow Agent (Simplified)",
        "version": "1.0.0"
    }

@app.post("/api/test-email")
async def test_email_processing(email: TestEmailRequest):
    """Test email processing"""
    try:
        result = email_processor.process_email({
            "sender": email.sender,
            "subject": email.subject,
            "content": email.content
        })
        
        # Store for demo
        processed_emails.append(result)
        
        return {
            "status": "success",
            "intent": result['intent'],
            "priority": result['priority'],
            "suggested_response": result['suggested_response']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processed-emails")
async def get_processed_emails():
    """Get list of processed emails"""
    return {
        "total": len(processed_emails),
        "emails": processed_emails[-10:]  # Last 10 emails
    }

@app.post("/api/knowledge-base/add")
async def add_to_knowledge_base(title: str, content: str):
    """Add document to knowledge base"""
    doc = {
        "id": len(knowledge_base) + 1,
        "title": title,
        "content": content
    }
    knowledge_base.append(doc)
    return {"message": "Document added", "id": doc['id']}

@app.get("/api/knowledge-base")
async def get_knowledge_base():
    """Get knowledge base documents"""
    return {"total": len(knowledge_base), "documents": knowledge_base}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
