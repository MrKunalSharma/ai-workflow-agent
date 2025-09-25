"""
Background tasks for async processing
"""
from celery import current_task
from src.workers.celery_app import celery_app
from src.agents.email_agent import EmailProcessingAgent
from src.connectors.notification_service import NotificationService
from src.utils.logger import logger
from src.models.database import SessionLocal, EmailTask
from typing import Dict, Any
import time

@celery_app.task(bind=True, name='process_email')
def process_email_task(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process email in background"""
    start_time = time.time()
    
    try:
        # Update task status
        current_task.update_state(state='PROCESSING')
        
        # Initialize processor
        processor = EmailProcessingAgent()
        db = SessionLocal()
        
        # Process email
        result = processor.process_email(email_data)
        
        # Store in database
        email_task = EmailTask(
            email_id=email_data.get('id'),
            sender=email_data['sender'],
            subject=email_data['subject'],
            body=email_data['content'],
            intent=result['intent'],
            priority=result['priority'],
            sentiment_score=result.get('sentiment_score', 0),
            confidence_score=result.get('confidence_score', 0),
            suggested_response=result['suggested_response'],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        db.add(email_task)
        db.commit()
        
        # Send webhook notification
        NotificationService.send_webhook(
            event='email.processed',
            data=result
        )
        
        logger.info(f"Email processed successfully: {email_data.get('id')}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()

@celery_app.task(name='sync_knowledge_base')
def sync_knowledge_base_task():
    """Sync knowledge base from multiple sources"""
    sources = ['notion', 'confluence', 'sharepoint']
    results = []
    
    for source in sources:
        try:
            # Sync logic here
            results.append({
                'source': source,
                'status': 'success',
                'documents': 10  # Example
            })
        except Exception as e:
            results.append({
                'source': source,
                'status': 'failed',
                'error': str(e)
            })
    
    return results
