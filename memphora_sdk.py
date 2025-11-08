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
            memories = self.client.search_memories(
                user_id=self.user_id,
                query=query,
                limit=limit
            )
            
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
        Store a memory. Automatically processes and optimizes the content for better retrieval.
        
        Args:
            content: Memory content
            metadata: Optional metadata dictionary
        
        Returns:
            Created memory dictionary
        """
        try:
            # Automatically extract and store memories (ensures clean, standardized format)
            extracted_memories = self.client.extract_from_content(
                user_id=self.user_id,
                content=content,
                metadata=metadata or {}
            )
            
            # Return the first extracted memory (or fallback to direct storage if extraction failed)
            if extracted_memories and len(extracted_memories) > 0:
                return extracted_memories[0]
            else:
                # Fallback to direct storage if extraction returned nothing
                return self.client.add_memory(
                    user_id=self.user_id,
                    content=content,
                    metadata=metadata or {}
                )
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            # Fallback to direct storage on error
            try:
                return self.client.add_memory(
                    user_id=self.user_id,
                    content=content,
                    metadata=metadata or {}
                )
            except:
                return {}
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search memories."""
        try:
            return self.client.search_memories(
                user_id=self.user_id,
                query=query,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
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
    def get_conversation(self, conversation_id: str) -> Dict:
        """Get a specific conversation by ID."""
        try:
            return self.client.get_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return {}
    
    def get_summary(self) -> Dict:
        """Get rolling summary of conversations."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/memory/summary/{self.user_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return {}
    
    # Multi-Agent Support
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
    ) -> List[Dict]:
        """Search memories for a specific agent."""
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
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search agent memories: {e}")
            return []
    
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
    ) -> List[Dict]:
        """Search memories for a group."""
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
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search group memories: {e}")
            return []
    
    def get_group_context(self, group_id: str, limit: int = 50) -> Dict:
        """Get context for a group."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/groups/{group_id}/context",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get group context: {e}")
            return {}
    
    # User Analytics
    def get_user_analytics(self) -> Dict:
        """Get user's memory statistics and insights."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/analytics/user-stats/{self.user_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}
    
    def get_memory_growth(self, days: int = 30) -> Dict:
        """Track memory growth over time."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/analytics/memory-growth",
                params={"days": days, "user_id": self.user_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get memory growth: {e}")
            return {}
    
    # Memory Relationships
    def get_related_memories(self, memory_id: str, limit: int = 10) -> List[Dict]:
        """Get memories related to a specific memory."""
        try:
            context = self.client.get_memory_context(memory_id=memory_id, depth=1)
            return context.get("related_memories", [])[:limit]
        except Exception as e:
            logger.error(f"Failed to get related memories: {e}")
            return []
    
    # Delegate all other methods to client
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



