import os
import pickle
import base64
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from src.utils.logger import logger
from src.core.config import settings

class GmailConnector:
    """Production-ready Gmail connector with OAuth2"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
        logger.info("GmailConnector initialized")
    
    def _authenticate(self):
        """Handle OAuth2 authentication"""
        # Token file stores the user's access and refresh tokens
        if os.path.exists(settings.gmail_token_path):
            with open(settings.gmail_token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(settings.gmail_credentials_path):
                    logger.error("Gmail credentials file not found. Please set up OAuth2 credentials.")
                    raise FileNotFoundError(
                        "Gmail credentials not found. Download from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.gmail_credentials_path, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            os.makedirs(os.path.dirname(settings.gmail_token_path), exist_ok=True)
            with open(settings.gmail_token_path, 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def get_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch unread emails from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread category:primary',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Fetched {len(emails)} unread emails")
            return emails
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            return []
    
    def _get_email_details(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'content': body,
                'snippet': message.get('snippet', ''),
                'thread_id': message.get('threadId'),
                'label_ids': message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting email details: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return body
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except HttpError as error:
            logger.error(f'An error occurred sending email: {error}')
            return False
    
    def mark_as_read(self, msg_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Marked email {msg_id} as read")
            return True
            
        except HttpError as error:
            logger.error(f'Error marking email as read: {error}')
            return False
