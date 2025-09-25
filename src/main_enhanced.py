from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import openai
from dotenv import load_dotenv
import json

load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Create FastAPI app
app = FastAPI(
    title="AI Workflow Agent - Enhanced",
    description="Production-ready AI agent with OpenAI integration",
    version="2.0.0"
)

# In-memory storage (in production, use a real database)
knowledge_base = []
processed_emails = []
email_templates = {}

class TestEmailRequest(BaseModel):
    sender: str
    subject: str
    content: str

class KnowledgeBaseEntry(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"

class EmailTemplate(BaseModel):
    name: str
    template: str
    variables: List[str]

class AIEmailProcessor:
    """Enhanced email processor with OpenAI"""
    
    def __init__(self):
        self.setup_system_prompt()
    
    def setup_system_prompt(self):
        self.system_prompt = """You are an AI assistant for a company that helps process customer emails. 
        Your tasks are to:
        1. Analyze the email intent (pricing_inquiry, support_request, complaint, general_inquiry)
        2. Determine priority (low, normal, high, urgent)
        3. Generate a professional response
        4. Extract key information
        
        Available knowledge base context will be provided when relevant.
        
        Respond in JSON format with the following structure:
        {
            "intent": "category of email",
            "priority": "priority level",
            "key_points": ["list of key points from email"],
            "suggested_response": "your suggested response",
            "requires_human": boolean,
            "sentiment": "positive/neutral/negative"
        }
        """
    
    def find_relevant_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Find relevant knowledge base entries"""
        relevant = []
        query_lower = query.lower()
        
        for kb in knowledge_base:
            if any(word in kb['content'].lower() for word in query_lower.split()):
                relevant.append(kb)
        
        return relevant[:3]  # Return top 3 most relevant
    
    def process_email_with_ai(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email using OpenAI"""
        try:
            # Find relevant knowledge
            relevant_kb = self.find_relevant_knowledge(
                f"{email_data['subject']} {email_data['content']}"
            )
            
            # Prepare context
            context = ""
            if relevant_kb:
                context = "\n\nRelevant knowledge base entries:\n"
                for kb in relevant_kb:
                    context += f"- {kb['title']}: {kb['content'][:200]}...\n"
            
            # Create the prompt
            user_prompt = f"""
            Process this email:
            From: {email_data['sender']}
            Subject: {email_data['subject']}
            Content: {email_data['content']}
            
            {context}
            """
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            result['original_email'] = email_data
            result['knowledge_used'] = [kb['title'] for kb in relevant_kb]
            result['processed_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            # Fallback to rule-based processing
            return self.process_email_with_rules(email_data)
    
    def process_email_with_rules(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback rule-based processing"""
        content_lower = email_data['content'].lower()
        subject_lower = email_data['subject'].lower()
        
        # Enhanced intent detection with priority order
        intent = 'general_inquiry'
        priority = 'normal'
        
        # Check for crisis/complaint indicators FIRST (highest priority)
        crisis_keywords = [
            'unacceptable', 'lawsuit', 'legal action', 'sue', 'breach of contract',
            'system down', 'system failure', 'lost revenue', 'losing money',
            'disaster', 'incompetence', 'terminate contract', 'failed', 'broken'
        ]
        
        complaint_keywords = [
            'complaint', 'unhappy', 'disappointed', 'frustrated', 'angry',
            'terrible', 'awful', 'worst', 'disgusted', 'unacceptable'
        ]
        
        # Check for high-value sales opportunities
        sales_keywords = [
            'evaluation', 'evaluating', 'requirement', 'deployment', 'enterprise',
            'budget', 'proposal', 'rfp', 'vendor', 'implementation', 'pilot',
            'trial', 'demo', 'users', 'employees', 'global', 'scale'
        ]
        
        # Technical/support keywords
        support_keywords = [
            'error', 'bug', 'issue', 'problem', 'not working', 'broken',
            'help', 'support', 'technical', 'troubleshoot', 'fix', 'resolve',
            'integration', 'stopped working', 'failing', 'timeout', 'can\'t',  # Added
            'unable', 'failure', 'not functioning'  # Added
        ]
        
        # Pricing keywords
        pricing_keywords = [
            'pricing', 'cost', 'price', 'plan', 'quote', 'discount',
            'billing', 'payment', 'subscription', 'fee', 'charge'
        ]
        
        # Count keyword matches for each category
        crisis_count = sum(1 for kw in crisis_keywords if kw in content_lower)
        complaint_count = sum(1 for kw in complaint_keywords if kw in content_lower)
        sales_count = sum(1 for kw in sales_keywords if kw in content_lower)
        support_count = sum(1 for kw in support_keywords if kw in content_lower)
        pricing_count = sum(1 for kw in pricing_keywords if kw in content_lower)
        
        # Determine intent based on highest match count and context
        if crisis_count >= 2 or ('urgent' in subject_lower and complaint_count >= 1):
            intent = 'complaint'
            priority = 'urgent'
        elif complaint_count >= 2:
            intent = 'complaint'
            priority = 'high'
        # Updated sales opportunity detection - MORE FLEXIBLE
        elif (sales_count >= 2 and any(indicator in content_lower for indicator in ['deployment', 'enterprise', 'evaluation', 'requirements'])) or \
            (pricing_count >= 1 and any(indicator in content_lower for indicator in ['enterprise', 'custom', 'deployment'])) or \
            (sales_count >= 3 and any(indicator in content_lower for indicator in ['budget', '000', 'million', 'employees'])):
            intent = 'sales_opportunity'
            priority = 'high'
        # Updated urgent support detection - CHECKS SUBJECT TOO
        elif support_count >= 1 and ('urgent' in subject_lower or 'broken' in subject_lower):
            intent = 'support_request'
            priority = 'urgent'
        elif support_count >= 2:
            intent = 'support_request'
            priority = 'normal' if not any(word in content_lower for word in ['urgent', 'asap', 'critical']) else 'high'
        elif pricing_count >= 1:
            intent = 'pricing_inquiry'
            priority = 'normal'
        else:
            intent = 'general_inquiry'
            priority = 'normal'

        
        # Priority override checks
        urgent_indicators = [
            'urgent', 'asap', 'immediately', 'critical', 'emergency',
            'right now', 'immediate', 'time sensitive', '!!!'
        ]
        
        high_value_indicators = [
            '$', 'million', 'thousand', 'budget', 'enterprise',
            '10,000', '50,000', '100,000', '1m+', 'global deployment'
        ]
        
        # Check for urgency override
        if any(indicator in content_lower for indicator in urgent_indicators):
            priority = 'urgent' if priority != 'urgent' else priority
        
        # Check for high-value override
        if any(indicator in content_lower for indicator in high_value_indicators):
            priority = 'high' if priority == 'normal' else priority
        
        # Enhanced sentiment analysis
        negative_indicators = [
            'unacceptable', 'terrible', 'awful', 'horrible', 'worst',
            'angry', 'furious', 'frustrated', 'disappointed', 'upset',
            'disaster', 'failure', 'incompetent', 'pathetic'
        ]
        
        positive_indicators = [
            'thank', 'thanks', 'appreciate', 'great', 'excellent',
            'wonderful', 'fantastic', 'amazing', 'pleased', 'happy',
            'excited', 'looking forward', 'interested'
        ]
        
        # Calculate sentiment scores
        negative_score = sum(1 for word in negative_indicators if word in content_lower)
        positive_score = sum(1 for word in positive_indicators if word in content_lower)
        
        # Check for CAPS LOCK (anger indicator)
        caps_words = len([word for word in email_data['content'].split() if word.isupper() and len(word) > 3])
        exclamation_count = email_data['content'].count('!')
        
        # Determine sentiment
        if negative_score > positive_score or caps_words > 5 or exclamation_count > 10:
            sentiment = 'negative'
        elif positive_score > negative_score:
            sentiment = 'positive'
        else:
            sentiment = 'neutral'
        
        # Extract key points (smarter extraction)
        key_points = self.extract_key_points_smart(email_data['content'])
        
        # Generate appropriate response
        response = self.get_smart_response(intent, email_data, priority, sentiment)
        
        # Determine if human review is needed
        requires_human = (
            priority in ['high', 'urgent'] or
            intent == 'complaint' or
            'legal' in content_lower or
            'lawsuit' in content_lower or
            sales_count >= 5 or  # Complex sales inquiry
            '$' in email_data['content'] and any(amt in email_data['content'] for amt in ['000', 'million', 'M'])
        )
        
        return {
            'intent': intent,
            'priority': priority,
            'key_points': key_points,
            'suggested_response': response,
            'requires_human': requires_human,
            'sentiment': sentiment,
            'original_email': email_data,
            'knowledge_used': [],
            'processed_at': datetime.now().isoformat()
        }

    def extract_key_points_smart(self, content: str) -> List[str]:
        """Smarter key point extraction"""
        # Split into sentences more intelligently
        import re
        sentences = re.split(r'[.!?]+', content)
        
        key_points = []
        important_sentences = []
        
        # Keywords that indicate important information
        important_keywords = [
            'demand', 'require', 'must', 'need', 'want', 'expect',
            'budget', 'deadline', 'urgent', 'million', 'thousand',
            'employees', 'users', 'issue', 'problem', 'error'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                # Check if sentence contains important information
                sentence_lower = sentence.lower()
                importance_score = sum(1 for kw in important_keywords if kw in sentence_lower)
                
                if importance_score > 0 or '?' in sentence or '!' in sentence:
                    important_sentences.append((importance_score, sentence))
        
        # Sort by importance and take top 5
        important_sentences.sort(key=lambda x: x[0], reverse=True)
        key_points = [sent[1] for sent in important_sentences[:5]]
        
        # If no important sentences found, take first 3 sentences
        if not key_points:
            key_points = [s.strip() for s in sentences[:3] if len(s.strip()) > 10]
        
        return key_points

    def get_smart_response(self, intent: str, email_data: Dict[str, Any], priority: str, sentiment: str) -> str:
        """Generate smarter responses based on context"""
        sender_name = email_data['sender'].split('@')[0].replace('.', ' ').title()
        
        if intent == 'complaint' and priority == 'urgent':
            return f"""Dear {sender_name},

I sincerely apologize for the critical situation you're experiencing. This is absolutely not the level of service we strive to provide.

I've immediately escalated your case to our executive team and technical emergency response unit. You can expect:

1. A call from our VP of Customer Success within 30 minutes
2. Our senior engineering team is investigating the issue with highest priority
3. A detailed incident report and resolution plan within 2 hours
4. Full review of your account and compensation discussion

Your direct escalation contact:
- Emergency Hotline: 1-800-URGENT-1 (ext. 911)
- Executive Email: executive.escalation@aiworkflow.com
- Ticket #: CRITICAL-{datetime.now().strftime('%Y%m%d-%H%M')}

We understand the severity of this situation and are mobilizing all resources to resolve it immediately.

Sincerely,
AI Workflow Emergency Response Team"""
        
        elif intent == 'sales_opportunity' and priority == 'high':
            return f"""Dear {sender_name},

Thank you for considering AI Workflow for your enterprise deployment. Based on your requirements, you're exactly the type of organization we love to partner with.

I've shared your detailed requirements with our Enterprise Solutions team. Given the scale and complexity of your needs, I'd like to arrange:

1. Technical Architecture Review - Our solutions architects will design a custom deployment plan
2. Security & Compliance Documentation - All certifications and audit reports
3. Executive Briefing - With our CTO to discuss your specific technical requirements
4. Proof of Concept - We can set up a pilot program for your team

For immediate assistance:
- Enterprise Sales Direct: +1-555-ENTERPRISE
- Schedule a call: https://calendly.com/aiworkflow-enterprise/technical-review

We typically respond to RFPs within 48 hours. Given your timeline, we'll prioritize your proposal.

Looking forward to partnering with you!

Best regards,
Enterprise Solutions Team
AI Workflow"""
        
        else:
            # Use existing templates for other cases
            return self.get_template_response(f"{intent}_response", email_data)

    
    def extract_key_points(self, content: str) -> List[str]:
        """Extract key points from email content"""
        sentences = content.split('.')
        key_points = []
        
        for sentence in sentences[:3]:  # First 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 10:
                key_points.append(sentence)
        
        return key_points
    
    def get_template_response(self, template_name: str, email_data: Dict[str, Any]) -> str:
        """Get response from template"""
        templates = {
            'pricing_response': """Dear {sender},

Thank you for your interest in our pricing plans. We offer three tiers:
- Starter: $49/month - Perfect for small teams
- Professional: $149/month - Ideal for growing businesses  
- Enterprise: Custom pricing - For large organizations

We also offer a 10% discount for annual billing and a 14-day free trial.

Would you like to schedule a call to discuss which plan best fits your needs?

Best regards,
AI Workflow Team""",
            
            'support_response': """Dear {sender},

Thank you for reaching out to our support team. We understand you're experiencing an issue and we're here to help.

Your request has been logged and our support team will respond within 24 hours. For urgent matters, you can also:
- Check our documentation at docs.aiworkflow.com
- Join our community forum
- Call our support line at 1-800-AI-HELP (Premium plans)

We appreciate your patience.

Best regards,
AI Workflow Support Team""",
            
            'complaint_response': """Dear {sender},

We sincerely apologize for any inconvenience you've experienced. Your satisfaction is our top priority, and we take your feedback very seriously.

Your concern has been escalated to our senior support team who will contact you within 4 hours to resolve this issue.

In the meantime, please don't hesitate to call our priority support line at 1-800-AI-HELP.

We value your business and are committed to making this right.

Best regards,
AI Workflow Customer Success Team""",
            
            'general_response': """Dear {sender},

Thank you for contacting AI Workflow. We've received your message regarding "{subject}" and appreciate you reaching out.

Our team will review your inquiry and respond within 24-48 hours with the information you need.

If you have any urgent matters, please don't hesitate to call us at 1-800-AI-HELP.

Best regards,
AI Workflow Team"""
        }
        
        template = templates.get(template_name, templates['general_response'])
        return template.format(
            sender=email_data['sender'].split('@')[0].title(),
            subject=email_data['subject']
        )

# Create processor instance
processor = AIEmailProcessor()

# Initialize with sample knowledge base
def init_knowledge_base():
    default_kb = [
        {
            "title": "Product Overview",
            "content": "AI Workflow Agent is an enterprise email automation platform that uses advanced AI to process and respond to customer emails. Features include smart categorization, automated responses, and integration with popular tools.",
            "category": "product"
        },
        {
            "title": "Security & Compliance",
            "content": "We are SOC 2 Type II certified, GDPR compliant, and use end-to-end encryption for all data. Our infrastructure is hosted on AWS with 99.9% uptime SLA. All data is encrypted at rest and in transit.",
            "category": "security"
        },
        {
            "title": "Integration Guide",
            "content": "AI Workflow integrates with Gmail, Outlook, Slack, Notion, Salesforce, and 50+ other tools. Setup takes less than 5 minutes with our OAuth2 integration. API access is available for custom integrations.",
            "category": "technical"
        }
    ]
    
    for kb in default_kb:
        knowledge_base.append(kb)

# Initialize on startup
init_knowledge_base()

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Workflow Agent - Enhanced",
        "version": "2.0.0",
        "ai_enabled": bool(openai.api_key),
        "knowledge_base_size": len(knowledge_base)
    }

@app.post("/api/test-email")
async def test_email_processing(email: TestEmailRequest):
    """Test email processing with AI"""
    try:
        # Use AI if available, otherwise use rules
        if openai.api_key:
            result = processor.process_email_with_ai(email.dict())
        else:
            result = processor.process_email_with_rules(email.dict())
        
        # Store result
        processed_emails.append(result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """Get processing statistics"""
    if not processed_emails:
        return {"message": "No emails processed yet"}
    
    intents = {}
    priorities = {}
    sentiments = {}
    
    for email in processed_emails:
        intents[email['intent']] = intents.get(email['intent'], 0) + 1
        priorities[email['priority']] = priorities.get(email['priority'], 0) + 1
        sentiments[email['sentiment']] = sentiments.get(email['sentiment'], 0) + 1
    
    return {
        "total_processed": len(processed_emails),
        "intents": intents,
        "priorities": priorities,
        "sentiments": sentiments,
        "requires_human_review": sum(1 for e in processed_emails if e.get('requires_human', False)),
        "ai_enabled": bool(openai.api_key)
    }

@app.post("/api/knowledge-base")
async def add_knowledge_base(entry: KnowledgeBaseEntry):
    """Add to knowledge base"""
    kb_entry = entry.dict()
    kb_entry['id'] = len(knowledge_base) + 1
    kb_entry['created_at'] = datetime.now().isoformat()
    knowledge_base.append(kb_entry)
    
    return {"message": "Knowledge base entry added", "id": kb_entry['id']}

@app.get("/api/knowledge-base")
async def get_knowledge_base():
    """Get all knowledge base entries"""
    return {
        "total": len(knowledge_base),
        "entries": knowledge_base
    }

@app.get("/api/emails/recent")
async def get_recent_emails(limit: int = 10):
    """Get recently processed emails"""
    return {
        "total": len(processed_emails),
        "recent": processed_emails[-limit:]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
