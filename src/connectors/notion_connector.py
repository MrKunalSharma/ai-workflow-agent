from notion_client import Client
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from src.utils.logger import logger
from src.core.config import settings

class NotionConnector:
    """Production-ready Notion connector"""
    
    def __init__(self):
        self.client = Client(auth=settings.notion_api_key)
        self.database_id = settings.notion_database_id
        logger.info("NotionConnector initialized")
    
    def fetch_knowledge_base(self) -> List[Dict[str, Any]]:
        """Fetch all pages from knowledge base database"""
        try:
            results = []
            has_more = True
            next_cursor = None
            
            while has_more:
                response = self.client.databases.query(
                    database_id=self.database_id,
                    start_cursor=next_cursor
                )
                
                for page in response['results']:
                    content = self._extract_page_content(page)
                    if content:
                        results.append(content)
                
                has_more = response['has_more']
                next_cursor = response.get('next_cursor')
            
            logger.info(f"Fetched {len(results)} pages from Notion")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching from Notion: {str(e)}")
            return []
    
    def _extract_page_content(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content from a Notion page"""
        try:
            # Get page properties
            properties = page.get('properties', {})
            
            # Extract title
            title = "Untitled"
            if 'Name' in properties and properties['Name']['type'] == 'title':
                title_list = properties['Name']['title']
                if title_list:
                    title = title_list[0]['plain_text']
            elif 'Title' in properties and properties['Title']['type'] == 'title':
                title_list = properties['Title']['title']
                if title_list:
                    title = title_list[0]['plain_text']
            
            # Get page content
            page_id = page['id']
            blocks = self._get_page_blocks(page_id)
            content = self._blocks_to_text(blocks)
            
            # Extract other properties
            tags = []
            if 'Tags' in properties and properties['Tags']['type'] == 'multi_select':
                tags = [tag['name'] for tag in properties['Tags']['multi_select']]
            
            category = ""
            if 'Category' in properties and properties['Category']['type'] == 'select':
                category = properties['Category']['select']['name'] if properties['Category']['select'] else ""
            
            return {
                'id': page_id,
                'title': title,
                'content': content,
                'tags': tags,
                'category': category,
                'url': page['url'],
                'last_edited': page['last_edited_time'],
                'source': 'notion'
            }
            
        except Exception as e:
            logger.error(f"Error extracting page content: {str(e)}")
            return None
    
    def _get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all blocks from a page"""
        try:
            blocks = []
            has_more = True
            next_cursor = None
            
            while has_more:
                response = self.client.blocks.children.list(
                    block_id=page_id,
                    start_cursor=next_cursor
                )
                blocks.extend(response['results'])
                has_more = response['has_more']
                next_cursor = response.get('next_cursor')
            
            return blocks
            
        except Exception as e:
            logger.error(f"Error getting page blocks: {str(e)}")
            return []
    
    def _blocks_to_text(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert Notion blocks to plain text"""
        text_parts = []
        
        for block in blocks:
            block_type = block['type']
            
            if block_type == 'paragraph':
                text = self._rich_text_to_plain(block['paragraph']['rich_text'])
                if text:
                    text_parts.append(text)
            
            elif block_type == 'heading_1':
                text = self._rich_text_to_plain(block['heading_1']['rich_text'])
                if text:
                    text_parts.append(f"\n# {text}\n")
            
            elif block_type == 'heading_2':
                text = self._rich_text_to_plain(block['heading_2']['rich_text'])
                if text:
                    text_parts.append(f"\n## {text}\n")
            
            elif block_type == 'heading_3':
                text = self._rich_text_to_plain(block['heading_3']['rich_text'])
                if text:
                    text_parts.append(f"\n### {text}\n")
            
            elif block_type == 'bulleted_list_item':
                text = self._rich_text_to_plain(block['bulleted_list_item']['rich_text'])
                if text:
                    text_parts.append(f"• {text}")
            
            elif block_type == 'numbered_list_item':
                text = self._rich_text_to_plain(block['numbered_list_item']['rich_text'])
                if text:
                    text_parts.append(f"- {text}")
            
            elif block_type == 'code':
                text = self._rich_text_to_plain(block['code']['rich_text'])
                if text:
                    text_parts.append(f"```\n{text}\n```")
        
        return "\n".join(text_parts)
    
    def _rich_text_to_plain(self, rich_text: List[Dict[str, Any]]) -> str:
        """Convert Notion rich text to plain text"""
        return "".join([text['plain_text'] for text in rich_text])
    
    def create_email_log(self, email_data: Dict[str, Any], response: str) -> Optional[str]:
        """Log processed email to Notion database"""
        try:
            new_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"Email: {email_data.get('subject', 'No Subject')}"
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": "Processed"
                        }
                    },
                    "Date": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Original Email"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"From: {email_data.get('sender', 'Unknown')}\n"
                                                  f"Subject: {email_data.get('subject', 'No Subject')}\n"
                                                  f"Content: {email_data.get('content', '')[:500]}..."
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "AI Response"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": response}}]
                        }
                    }
                ]
            )
            
            logger.info(f"Created email log in Notion: {new_page['id']}")
            return new_page['id']
            
        except Exception as e:
            logger.error(f"Error creating email log in Notion: {str(e)}")
            return None
