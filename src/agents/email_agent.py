from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from typing import Dict, Any, Optional
from src.core.vector_store import VectorStoreManager
from src.utils.logger import logger
from src.core.config import settings

class EmailProcessingAgent:
    """AI Agent for processing emails and generating responses"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.3,
            model_name="gpt-3.5-turbo",
            openai_api_key=settings.openai_api_key
        )
        self.vector_store = VectorStoreManager()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # System prompt for email processing
        self.system_template = """You are an intelligent email assistant for a company. 
Your role is to:
1. Analyze incoming emails and understand the sender's intent
2. Search the company knowledge base for relevant information
3. Draft professional, helpful responses
4. Flag emails that require human attention

Context from knowledge base:
{context}

Previous conversation history:
{chat_history}

Guidelines:
- Be professional and courteous
- Provide accurate information based on the knowledge base
- If unsure, indicate that the query will be forwarded to a human
- Keep responses concise but complete
"""
        
        self.human_template = """
Email from: {sender}
Subject: {subject}
Content: {content}

Please analyze this email and provide:
1. Intent classification (inquiry, complaint, request, etc.)
2. Relevant information from knowledge base
3. Suggested response
4. Priority level (low, medium, high)
"""
        
        # Create prompt template
        system_message = SystemMessagePromptTemplate.from_template(self.system_template)
        human_message = HumanMessagePromptTemplate.from_template(self.human_template)
        self.prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        
        # Create chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory,
            verbose=True
        )
        
        logger.info("EmailProcessingAgent initialized")
    
    def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an email and generate response"""
        try:
            sender = email_data.get("sender", "Unknown")
            subject = email_data.get("subject", "No subject")
            content = email_data.get("content", "")
            
            # Search knowledge base for relevant context
            search_query = f"{subject} {content[:200]}"
            context_results = self.vector_store.search(search_query, n_results=3)
            
            # Prepare context
            context = "\n\n".join([
                f"[{r['metadata'].get('title', 'Document')}]: {r['content']}"
                for r in context_results
            ])
            
            if not context:
                context = "No relevant information found in knowledge base."
            
            # Run the chain
            response = self.chain.run(
                context=context,
                sender=sender,
                subject=subject,
                content=content
            )
            
            # Parse response (in production, use structured output)
            result = {
                "original_email": email_data,
                "analysis": response,
                "context_used": context_results,
                "suggested_action": self._determine_action(response),
                "priority": self._extract_priority(response)
            }
            
            logger.info(f"Successfully processed email from {sender}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return {
                "error": str(e),
                "original_email": email_data,
                "suggested_action": "escalate_to_human"
            }
    
    def _determine_action(self, response: str) -> str:
        """Determine action based on response analysis"""
        response_lower = response.lower()
        if "human attention" in response_lower or "escalate" in response_lower:
            return "escalate_to_human"
        elif "urgent" in response_lower or "immediate" in response_lower:
            return "urgent_response"
        else:
            return "auto_respond"
    
    def _extract_priority(self, response: str) -> str:
        """Extract priority level from response"""
        response_lower = response.lower()
        if "high" in response_lower and "priority" in response_lower:
            return "high"
        elif "medium" in response_lower and "priority" in response_lower:
            return "medium"
        else:
            return "low"
