from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session

from src.models.database import SessionLocal, EmailTask, KnowledgeBase
from src.core.task_processor import TaskProcessor
from src.utils.logger import logger
from src.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="AI Workflow Agent",
    description="Enterprise-grade AI agent for email automation and knowledge management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API
class EmailResponse(BaseModel):
    id: int
    email_id: str
    sender: str
    subject: str
    processed: bool
    priority: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

class KnowledgeBaseResponse(BaseModel):
    id: int
    source: str
    title: str
    created_at: datetime
    updated_at: datetime

class StatusResponse(BaseModel):
    status: str
    total_emails_processed: int
    total_kb_documents: int
    last_sync: Optional[datetime]

class TestEmailRequest(BaseModel):
    sender: str
    subject: str
    content: str

# Global task processor instance
task_processor = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global task_processor
    task_processor = TaskProcessor()
    logger.info("Application started")

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Workflow Agent",
        "version": "1.0.0"
    }

@app.get("/api/status", response_model=StatusResponse, tags=["Status"])
async def get_status(db: Session = Depends(get_db)):
    """Get system status and statistics"""
    total_emails = db.query(EmailTask).filter(EmailTask.processed == True).count()
    total_kb = db.query(KnowledgeBase).count()
    
    # Get last sync time
    last_kb = db.query(KnowledgeBase).order_by(
        KnowledgeBase.updated_at.desc()
    ).first()
    
    return StatusResponse(
        status="operational",
        total_emails_processed=total_emails,
        total_kb_documents=total_kb,
        last_sync=last_kb.updated_at if last_kb else None
    )

@app.post("/api/sync-knowledge-base", tags=["Knowledge Base"])
async def sync_knowledge_base(background_tasks: BackgroundTasks):
    """Trigger knowledge base synchronization"""
    background_tasks.add_task(task_processor.sync_knowledge_base)
    return {"message": "Knowledge base sync started"}

@app.post("/api/process-emails", tags=["Email Processing"])
async def process_emails(background_tasks: BackgroundTasks):
    """Trigger email processing"""
    background_tasks.add_task(task_processor.process_emails)
    return {"message": "Email processing started"}

@app.post("/api/run-workflow", tags=["Workflow"])
async def run_workflow(background_tasks: BackgroundTasks):
    """Run complete workflow (sync KB + process emails)"""
    background_tasks.add_task(task_processor.run_workflow)
    return {"message": "Workflow started"}

@app.get("/api/emails", response_model=List[EmailResponse], tags=["Email Processing"])
async def get_processed_emails(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of processed emails"""
    emails = db.query(EmailTask).filter(
        EmailTask.processed == True
    ).offset(skip).limit(limit).all()
    
    return [
        EmailResponse(
            id=e.id,
            email_id=e.email_id,
            sender=e.sender,
            subject=e.subject,
            processed=e.processed,
            priority="normal",  # Extract from response in production
            created_at=e.created_at,
            processed_at=e.processed_at
        )
        for e in emails
    ]

@app.get("/api/knowledge-base", response_model=List[KnowledgeBaseResponse], tags=["Knowledge Base"])
async def get_knowledge_base(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get knowledge base documents"""
    documents = db.query(KnowledgeBase).offset(skip).limit(limit).all()
    
    return [
        KnowledgeBaseResponse(
            id=doc.id,
            source=doc.source,
            title=doc.title,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]

@app.post("/api/test-email", tags=["Testing"])
async def test_email_processing(email: TestEmailRequest):
    """Test email processing without actually sending"""
    try:
        result = task_processor.email_agent.process_email({
            "sender": email.sender,
            "subject": email.subject,
            "content": email.content
        })
        
        return {
            "status": "success",
            "analysis": result.get("analysis", ""),
            "suggested_action": result.get("suggested_action", ""),
            "priority": result.get("priority", "low")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search", tags=["Knowledge Base"])
async def search_knowledge_base(query: str):
    """Search knowledge base"""
    try:
        results = task_processor.vector_store.search(query, n_results=5)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
