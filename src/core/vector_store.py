import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
import uuid
from src.utils.logger import logger
from src.core.config import settings

class VectorStoreManager:
    """Manages vector embeddings for RAG system"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Company knowledge base"}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        logger.info("VectorStoreManager initialized")
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        """Add document to vector store with metadata"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Generate IDs for chunks
            ids = [str(uuid.uuid4()) for _ in chunks]
            
            # Create embeddings
            embeddings = self.embeddings.embed_documents(chunks)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                ids=ids,
                metadatas=[metadata] * len(chunks)
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search vector store for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
