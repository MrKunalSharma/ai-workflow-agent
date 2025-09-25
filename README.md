┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Gmail API │────▶│ Task Queue │────▶│ AI Agent │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────┐ ┌─────────────────┐
│ Database │ │ Vector Store │
└─────────────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────┐ ┌─────────────────┐
│ Notion API │ │ FastAPI │
└─────────────────┘ └─────────────────┘




## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key
- Google Cloud Project with Gmail API enabled
- Notion API Key and Database ID

## 🔧 Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements-basic.txt`

## ⚙️ Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `NOTION_API_KEY`: Your Notion integration key
   - `NOTION_DATABASE_ID`: Your Notion database ID

## 🚀 Running the Application

```bash
python run.py


          
Access the API at: http://localhost:8000
API Documentation: http://localhost:8000/docs

📡 API Endpoints
GET /: Health check
GET /api/status: System status
POST /api/sync-knowledge-base: Sync Notion knowledge base
POST /api/process-emails: Process unread emails
GET /api/emails: List processed emails
POST /api/test-email: Test email processing
🧪 Testing

          

bash


# Run tests
pytest tests/

# Test email processing
curl -X POST http://localhost:8000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"sender":"test@example.com","subject":"Test","content":"Hello"}'


                
📈 Performance Considerations
Implements connection pooling for database
Uses async processing for scalability
Vector store for efficient similarity search
Caching for frequently accessed data
🔒 Security
Environment variables for sensitive data
OAuth2 for Gmail authentication
API key authentication for Notion
Input validation and sanitization
