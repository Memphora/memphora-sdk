"""
Memphora SDK - Standalone version for PyPI (no internal dependencies)
Simple, One-Line Integration for Developers
"""
from typing import List, Dict, Optional, Any, Callable
from memory_client import MemoryClient
import inspect
from functools import wraps
import logging

# Use standard logging instead of internal logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class Memphora:
    """
    Simple, developer-friendly SDK for Memphora.
    
    Quick Start:
        from memphora import Memphora
        
        memory = Memphora(
            user_id="user123",
            api_key="your_api_key"
        )
        
        # Store a memory
        memory.store("I love Python programming")
        
        # Search memories
        results = memory.search("What do I love?")
        
        # Auto-remember conversations
        @memory.remember
        def chat(message):
            return ai_response(message)
    """
    
    def __init__(
        self,
        user_id: str,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        auto_compress: bool = True,
        max_tokens: int = 500
    ):
        """
        Initialize Memphora SDK.
        
        Args:
            user_id: User identifier
            api_key: API key for authentication (get from dashboard)
            api_url: Optional API URL (defaults to cloud API, only needed for custom endpoints)
            auto_compress: Automatically compress context (default: True)
            max_tokens: Maximum tokens for context (default: 500)
        """
        # Default to production API - users only need to provide API key
        if api_url is None:
            api_url = "https://api.memphora.ai/api/v1"
        self.user_id = user_id
        self.api_key = api_key
        self.client = MemoryClient(base_url=api_url, api_key=api_key)
        self.auto_compress = auto_compress
        self.max_tokens = max_tokens
        
        logger.info(f"Memphora SDK initialized for user {user_id}")
    
    def remember(self, func: Callable) -> Callable:
        """
        Decorator to automatically remember conversations.
        
        Usage:
            @memory.remember
            def chat(user_message: str) -> str:
                return ai_response(user_message)
        
        The decorator will:
        1. Search for relevant memories
        2. Add them to your function's context
        3. Store the conversation after response
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user message from args or kwargs
            user_message = self._extract_message(func, args, kwargs)
            
            if user_message:
                # Get relevant context
                context = self.get_context(user_message)
                
                # Add context to kwargs
                kwargs['memory_context'] = context
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Store conversation
            if user_message and result:
                self.store_conversation(user_message, result)
            
            return result
        
        return wrapper
    
    def get_context(self, query: str, limit: int = 5) -> str:
        """Get relevant context for a query."""
        try:
            logger.debug(f"SDK get_context: user_id={self.user_id}, query={query[:50]}, base_url={self.client.base_url}")
            memories = self.client.search_memories(
                user_id=self.user_id,
                query=query,
                limit=limit
            )
            logger.debug(f"SDK get_context: got {len(memories) if memories else 0} memories")
            
            if not memories:
                return ""
            
            # Format context
            context_lines = []
            for mem in memories:
                content = mem.get('content', '')
                context_lines.append(f"- {content}")
            
            context = "Relevant context from past conversations:\n" + "\n".join(context_lines)
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return ""
    
    def store(self, content: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Store a memory. Stores complete content directly (preserves exact content).
        
        With optimized storage, this is fast (~50ms) and maintains data quality.
        
        Args:
            content: Memory content
            metadata: Optional metadata dictionary
        
        Returns:
            Created memory dictionary
        """
        try:
            # Store complete memory directly (preserves exact content)
            # With optimized storage, this is fast (~50ms) and maintains data quality
            return self.client.add_memory(
                user_id=self.user_id,
                content=content,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return {}
    
    def search(
        self,
        query: str,
        limit: int = 10,
        rerank: bool = False,
        rerank_provider: str = "auto",
        cohere_api_key: Optional[str] = None,
        jina_api_key: Optional[str] = None
    ) -> Dict:
        """
        Search memories with optional external reranking.
        
        Args:
            query: Search query
            limit: Maximum number of results
            rerank: Enable external reranking (Cohere/Jina) for better relevance
            rerank_provider: Reranking provider ("cohere", "jina", or "auto")
            cohere_api_key: Optional Cohere API key (if not configured on backend)
            jina_api_key: Optional Jina AI API key (if not configured on backend)
        
        Returns:
            Dict with:
                - facts: List of matching facts with memory_id, text, timestamp, similarity
                - critical_context: Important context for LLM agents (if available)
                - metadata: Extracted metadata like key_entities, counts, dates
        
        Example:
            result = memory.search("user preferences")
            for fact in result["facts"]:
                print(fact["text"], fact["similarity"])
            if result.get("critical_context"):
                print(f"Important: {result['critical_context']}")
        """
        try:
            return self.client.search_memories(
                user_id=self.user_id,
                query=query,
                limit=limit,
                rerank=rerank,
                rerank_provider=rerank_provider,
                cohere_api_key=cohere_api_key,
                jina_api_key=jina_api_key
            )
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return {"facts": [], "critical_context": None, "metadata": {}}
    
    def store_conversation(self, user_message: str, ai_response: str) -> None:
        """Store a conversation for automatic memory extraction."""
        try:
            conversation = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            
            self.client.extract_from_conversation(
                user_id=self.user_id,
                conversation=conversation
            )
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    def clear(self) -> bool:
        """Clear all memories for this user."""
        try:
            result = self.client.delete_all_user_memories(self.user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False
    
    # Basic CRUD Operations
    def get_memory(self, memory_id: str) -> Dict:
        """Get a specific memory by ID."""
        try:
            return self.client.get_memory(memory_id)
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return {}
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Update an existing memory."""
        try:
            return self.client.update_memory(memory_id=memory_id, content=content, metadata=metadata)
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return {}
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        try:
            return self.client.delete_memory(memory_id)
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def list_memories(self, limit: int = 100) -> List[Dict]:
        """List all memories for this user."""
        try:
            return self.client.get_user_memories(self.user_id, limit=limit)
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return []
    
    # Conversation Management
    def store_agent_memory(
        self,
        agent_id: str,
        content: str,
        run_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Store a memory for a specific agent."""
        try:
            response = self.client.session.post(
                f"{self.client.base_url}/agents/memories",
                json={
                    "user_id": self.user_id,
                    "agent_id": agent_id,
                    "content": content,
                    "run_id": run_id,
                    "metadata": metadata or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to store agent memory: {e}")
            return {}
    
    def search_agent_memories(
        self,
        agent_id: str,
        query: str,
        run_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """
        Search memories for a specific agent.
        
        Returns:
            Dict with:
                - facts: List of matching facts with memory_id, text, timestamp, similarity
                - agent_id: The agent ID searched
        """
        try:
            response = self.client.session.post(
                f"{self.client.base_url}/agents/memories/search",
                json={
                    "user_id": self.user_id,
                    "agent_id": agent_id,
                    "query": query,
                    "run_id": run_id,
                    "limit": limit
                }
            )
            response.raise_for_status()
            memories = response.json()
            
            # Convert to structured format matching main search()
            facts = []
            for mem in memories:
                facts.append({
                    "text": mem.get("content", ""),
                    "memory_id": mem.get("id") or mem.get("memory_id"),
                    "timestamp": mem.get("timestamp"),
                    "similarity": mem.get("similarity")
                })
            
            return {
                "facts": facts,
                "agent_id": agent_id,
                "metadata": {"run_id": run_id} if run_id else {}
            }
        except Exception as e:
            logger.error(f"Failed to search agent memories: {e}")
            return {"facts": [], "agent_id": agent_id, "metadata": {}}
    
    def get_agent_memories(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Get all memories for a specific agent."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/agents/{agent_id}/memories",
                params={"user_id": self.user_id, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get agent memories: {e}")
            return []
    
    # Group/Collaborative Features
    def store_group_memory(
        self,
        group_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Store a shared memory for a group."""
        try:
            response = self.client.session.post(
                f"{self.client.base_url}/groups/memories",
                json={
                    "user_id": self.user_id,
                    "group_id": group_id,
                    "content": content,
                    "metadata": metadata or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to store group memory: {e}")
            return {}
    
    def search_group_memories(
        self,
        group_id: str,
        query: str,
        limit: int = 10
    ) -> Dict:
        """
        Search memories for a group.
        
        Returns:
            Dict with:
                - facts: List of matching facts with memory_id, text, timestamp, similarity
                - group_id: The group ID searched
        """
        try:
            response = self.client.session.post(
                f"{self.client.base_url}/groups/memories/search",
                json={
                    "user_id": self.user_id,
                    "group_id": group_id,
                    "query": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            memories = response.json()
            
            # Convert to structured format matching main search()
            facts = []
            for mem in memories:
                facts.append({
                    "text": mem.get("content", ""),
                    "memory_id": mem.get("id") or mem.get("memory_id"),
                    "timestamp": mem.get("timestamp"),
                    "similarity": mem.get("similarity")
                })
            
            return {
                "facts": facts,
                "group_id": group_id,
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Failed to search group memories: {e}")
            return {"facts": [], "group_id": group_id, "metadata": {}}
    
    def get_group_context(self, group_id: str, limit: int = 50) -> Dict:
        """Get context for a group."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/groups/{group_id}/context",
                params={"user_id": self.user_id, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get group context: {e}")
            return {}
    
    # User Analytics
    def batch_store(
        self,
        memories: List[Dict[str, str]],
        link_related: bool = True
    ) -> List[Dict]:
        """Batch create multiple memories."""
        try:
            return self.client.batch_create(
                user_id=self.user_id,
                memories=memories,
                link_related=link_related
            )
        except Exception as e:
            logger.error(f"Failed to batch store: {e}")
            return []
    
    # Memory Operations
    def record_conversation(
        self,
        conversation: List[Dict[str, str]],
        platform: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Record a full conversation."""
        try:
            return self.client.record_conversation(
                user_id=self.user_id,
                conversation=conversation,
                platform=platform or "unknown",
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to record conversation: {e}")
            return {}
    
    def get_conversations(
        self,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get user conversations."""
        try:
            return self.client.get_user_conversations(
                user_id=self.user_id,
                platform=platform,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []
    
    def summarize_conversation(
        self,
        conversation: List[Dict[str, str]],
        summary_type: str = "brief"
    ) -> Dict:
        """Summarize a conversation."""
        try:
            return self.client.summarize_conversation(
                conversation=conversation,
                summary_type=summary_type
            )
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return {}
    
    # Image Operations
    def store_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Store an image memory."""
        try:
            return self.client.store_image(
                user_id=self.user_id,
                image_url=image_url,
                image_base64=image_base64,
                description=description,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to store image: {e}")
            return {}
    
    def search_images(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search image memories."""
        try:
            return self.client.search_images(
                user_id=self.user_id,
                query=query,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to search images: {e}")
            return []
    
    # Document & Visual Processing
    
    def ingest_document(
        self,
        content_type: str,
        url: Optional[str] = None,
        data: Optional[str] = None,
        text: Optional[str] = None,
        metadata: Optional[Dict] = None,
        async_processing: bool = True
    ) -> Dict:
        """
        Ingest any document type into memory.
        
        Supports PDF, images, URLs, and plain text. Automatically extracts
        and stores relevant information as searchable memories.
        
        Args:
            content_type: One of "pdf_url", "pdf_base64", "image_url", 
                         "image_base64", "url", or "text"
            url: URL for pdf_url, image_url, or url types
            data: Base64 data for pdf_base64 or image_base64 types
            text: Plain text for text type
            metadata: Optional metadata for the document
            async_processing: If True, returns immediately with job_id (recommended)
            
        Returns:
            If async: Dict with job_id for tracking
            If sync: Dict with extracted memories
        """
        try:
            content = {"type": content_type}
            if url:
                content["url"] = url
            if data:
                content["data"] = data
            if text:
                content["text"] = text
                
            response = self.client.session.post(
                f"{self.client.base_url}/documents",
                json={
                    "user_id": self.user_id,
                    "content": content,
                    "metadata": metadata or {},
                    "async_processing": async_processing
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to ingest document: {e}")
            return {"status": "error", "error": str(e)}
    
    def upload_document(
        self,
        file_data: bytes,
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload any document type and create memories.
        
        Supports PDF, images, text files, markdown, JSON, CSV, and more.
        Files are processed automatically based on file extension.
        
        Args:
            file_data: Raw file bytes
            filename: Filename with extension (e.g., "report.pdf", "notes.txt")
            metadata: Optional metadata for the document
            
        Returns:
            Dict with job_id for tracking (async processing)
        """
        try:
            files = {"file": (filename, file_data)}
            response = self.client.session.post(
                f"{self.client.base_url}/documents/upload",
                params={"user_id": self.user_id},
                files=files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_image_url(self, memory_id: str) -> Dict:
        """
        Get a fresh signed URL for an image memory.
        
        Signed URLs expire after 7 days. Use this to get a new URL
        when the previous one has expired.
        
        Args:
            memory_id: ID of the image memory
            
        Returns:
            Dict with image_url or error message
        """
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/memories/image/{memory_id}/url"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get image URL: {e}")
            return {"status": "error", "error": str(e)}
    
    # Version Control
    def export(
        self,
        format: str = "json"
    ) -> Dict:
        """Export all memories."""
        try:
            return self.client.export_memories(
                user_id=self.user_id,
                format=format
            )
        except Exception as e:
            logger.error(f"Failed to export: {e}")
            return {}
    
    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Upload an image from bytes data."""
        try:
            return self.client.upload_image(
                user_id=self.user_id,
                image_data=image_data,
                filename=filename,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            return {}
    
    # Text Processing
    def health(self) -> Dict:
        """Check API health."""
        try:
            return self.client.health_check()
        except Exception as e:
            logger.error(f"Failed to check health: {e}")
            return {}
    
    # Webhooks
    def __getattr__(self, name):
        """Delegate unknown methods to client for backward compatibility."""
        if hasattr(self.client, name):
            return getattr(self.client, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _extract_message(self, func: Callable, args: tuple, kwargs: dict) -> Optional[str]:
        """Extract user message from function arguments."""
        if 'message' in kwargs:
            return kwargs['message']
        if 'user_message' in kwargs:
            return kwargs['user_message']
        if 'query' in kwargs:
            return kwargs['query']
        
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        if args and len(params) > 0:
            return str(args[0])
        
        return None


# Convenience functions
def init(user_id: str, api_key: Optional[str] = None, **kwargs) -> Memphora:
    """Initialize Memphora SDK (convenience function)."""
    return Memphora(user_id=user_id, api_key=api_key, **kwargs)


def remember(user_id: str, api_key: Optional[str] = None, api_url: Optional[str] = None):
    """Decorator factory for quick integration."""
    memory = Memphora(user_id=user_id, api_key=api_key, api_url=api_url)
    return memory.remember


# Export main classes
__all__ = ['Memphora', 'init', 'remember']

# Import integrations (optional - only if frameworks are installed)
try:
    from integrations import (
        MemphoraLangChain,
        MemphoraLlamaIndex,
        MemphoraCrewAI,
        MemphoraAgentMemory,
        MemphoraAutoGen,
    )
    __all__.extend([
        'MemphoraLangChain',
        'MemphoraLlamaIndex',
        'MemphoraCrewAI',
        'MemphoraAgentMemory',
        'MemphoraAutoGen',
    ])
except ImportError:
    # Integrations not available - that's OK, core SDK still works
    pass
