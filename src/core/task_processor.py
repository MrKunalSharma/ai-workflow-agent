import asyncio
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.database import SessionLocal, EmailTask, KnowledgeBase
from src.agents.email_agent import EmailProcessingAgent
from src.connectors.gmail_connector import GmailConnector
from src.connectors.notion_connector import NotionConnector
from src.core.vector_store import VectorStoreManager
from src.utils.logger import logger

class TaskProcessor:
    """Main task processor that orchestrates the workflow"""
    
    def __init__(self):
        self.email_agent = EmailProcessingAgent()
        self.gmail = GmailConnector()
        self.notion = NotionConnector()
        self.vector_store = VectorStoreManager()
        self.db = SessionLocal()
        logger.info("TaskProcessor initialized")
    
    async def sync_knowledge_base(self):
        """Sync knowledge base from Notion to vector store"""
        try:
            logger.info("Starting knowledge base sync...")
            
            # Fetch all pages from Notion
            pages = self.notion.fetch_knowledge_base()
            
            for page in pages:
                # Check if already in database
                existing = self.db.query(KnowledgeBase).filter(
                    KnowledgeBase.source == "notion",
                    KnowledgeBase.title == page['title']
                ).first()
                
                # Update or create
                if existing:
                    existing.content = page['content']
                    existing.updated_at = datetime.utcnow()
                else:
                    kb_entry = KnowledgeBase(
                        source="notion",
                        title=page['title'],
                        content=page['content']
                    )
                    self.db.add(kb_entry)
                
                # Add to vector store
                metadata = {
                    "source": "notion",
                    "title": page['title'],
                    "tags": page.get('tags', []),
                    "category": page.get('category', ''),
                    "url": page.get('url', '')
                }
                
                self.vector_store.add_document(page['content'], metadata)
            
            self.db.commit()
            logger.info(f"Knowledge base sync completed. Processed {len(pages)} pages.")
            
        except Exception as e:
            logger.error(f"Error syncing knowledge base: {str(e)}")
            self.db.rollback()
    
    async def process_emails(self):
        """Process unread emails"""
        try:
            logger.info("Starting email processing...")
            
            # Fetch unread emails
            emails = self.gmail.get_unread_emails(max_results=20)
            
            for email in emails:
                # Check if already processed
                existing = self.db.query(EmailTask).filter(
                    EmailTask.email_id == email['id']
                ).first()
                
                if existing and existing.processed:
                    continue
                
                # Create or update email task
                if not existing:
                    email_task = EmailTask(
                        email_id=email['id'],
                        sender=email['sender'],
                        subject=email['subject'],
                        body=email['content']
                    )
                    self.db.add(email_task)
                else:
                    email_task = existing
                
                # Process email with AI agent
                result = self.email_agent.process_email({
                    "sender": email['sender'],
                    "subject": email['subject'],
                    "content": email['content']
                })
                
                # Handle result based on suggested action
                action = result.get('suggested_action', 'auto_respond')
                
                if action == 'auto_respond':
                    # Send automated response
                    response_text = self._extract_response_text(result['analysis'])
                    
                    # For demo, we'll just log the response
                    logger.info(f"Would send response to {email['sender']}: {response_text[:100]}...")
                    
                    # In production, uncomment this:
                    # self.gmail.send_email(
                    #     to=email['sender'],
                    #     subject=f"Re: {email['subject']}",
                    #     body=response_text
                    # )
                    
                    # Mark as read
                    self.gmail.mark_as_read(email['id'])
                    
                elif action == 'escalate_to_human':
                    logger.info(f"Email from {email['sender']} requires human attention")
                    # In production, send notification to team
                
                # Update database
                email_task.processed = True
                email_task.processed_at = datetime.utcnow()
                email_task.response = result.get('analysis', '')
                
                # Log to Notion
                self.notion.create_email_log(email, result.get('analysis', ''))
                
                self.db.commit()
                
                # Small delay to avoid rate limits
                await asyncio.sleep(2)
            
            logger.info(f"Email processing completed. Processed {len(emails)} emails.")
            
        except Exception as e:
            logger.error(f"Error processing emails: {str(e)}")
            self.db.rollback()
    
    def _extract_response_text(self, analysis: str) -> str:
        """Extract the suggested response from agent analysis"""
        # Simple extraction - in production, use structured output
        if "Suggested response:" in analysis:
            parts = analysis.split("Suggested response:")
            if len(parts) > 1:
                return parts[1].strip()
        
        # Fallback
        return "Thank you for your email. We have received your message and will respond shortly."
    
    async def run_workflow(self):
        """Run the complete workflow"""
        try:
            # First sync knowledge base
            await self.sync_knowledge_base()
            
            # Then process emails
            await self.process_emails()
            
            logger.info("Workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
        finally:
            self.db.close()
