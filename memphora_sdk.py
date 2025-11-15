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
    
    def search(
        self,
        query: str,
        limit: int = 10,
        rerank: bool = False,
        rerank_provider: str = "auto",
        cohere_api_key: Optional[str] = None,
        jina_api_key: Optional[str] = None
    ) -> List[Dict]:
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
            List of matching memory dictionaries
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
                params={"user_id": self.user_id, "limit": limit}
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
    
    # Advanced Search Methods
    def search_advanced(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict] = None,
        include_related: bool = False,
        min_score: float = 0.0,
        sort_by: str = "relevance"
    ) -> List[Dict]:
        """Advanced search with filtering and scoring."""
        try:
            return self.client.search_advanced(
                user_id=self.user_id,
                query=query,
                limit=limit,
                filters=filters or {},
                include_related=include_related,
                min_score=min_score,
                sort_by=sort_by
            )
        except Exception as e:
            logger.error(f"Failed to search advanced: {e}")
            return []
    
    def search_optimized(
        self,
        query: str,
        max_tokens: int = 2000,
        max_memories: int = 20,
        use_compression: bool = True,
        use_cache: bool = True
    ) -> Dict:
        """Optimized search for better performance."""
        try:
            return self.client.search_optimized(
                user_id=self.user_id,
                query=query,
                max_tokens=max_tokens,
                max_memories=max_memories,
                use_compression=use_compression,
                use_cache=use_cache
            )
        except Exception as e:
            logger.error(f"Failed to search optimized: {e}")
            return {}
    
    def search_enhanced(
        self,
        query: str,
        max_tokens: int = 1500,
        max_memories: int = 15,
        use_compression: bool = True
    ) -> Dict:
        """Enhanced search with maximum performance."""
        try:
            return self.client.search_enhanced(
                user_id=self.user_id,
                query=query,
                max_tokens=max_tokens,
                max_memories=max_memories,
                use_compression=use_compression
            )
        except Exception as e:
            logger.error(f"Failed to search enhanced: {e}")
            return {}
    
    # Batch Operations
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
    def merge(
        self,
        memory_ids: List[str],
        strategy: str = "combine"
    ) -> Dict:
        """Merge multiple memories."""
        try:
            return self.client.merge_memories(
                memory_ids=memory_ids,
                merge_strategy=strategy
            )
        except Exception as e:
            logger.error(f"Failed to merge memories: {e}")
            return {}
    
    def find_contradictions(
        self,
        memory_id: str,
        threshold: float = 0.7
    ) -> List[Dict]:
        """Find potentially contradictory memories."""
        try:
            return self.client.find_contradictions(
                memory_id=memory_id,
                similarity_threshold=threshold
            )
        except Exception as e:
            logger.error(f"Failed to find contradictions: {e}")
            return []
    
    def get_context_for_memory(
        self,
        memory_id: str,
        depth: int = 2
    ) -> Dict:
        """Get full context around a memory."""
        try:
            return self.client.get_memory_context(
                memory_id=memory_id,
                depth=depth
            )
        except Exception as e:
            logger.error(f"Failed to get context for memory: {e}")
            return {}
    
    # Statistics
    def get_statistics(self) -> Dict:
        """Get user's memory statistics and insights."""
        try:
            return self.client.get_user_statistics(self.user_id)
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    # Conversation Management
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
    
    # Version Control
    def get_versions(
        self,
        memory_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get memory versions."""
        try:
            return self.client.get_memory_versions(
                memory_id=memory_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get versions: {e}")
            return []
    
    def rollback(
        self,
        memory_id: str,
        target_version: int
    ) -> Dict:
        """Rollback memory to a version."""
        try:
            return self.client.rollback_memory(
                memory_id=memory_id,
                target_version=target_version,
                user_id=self.user_id
            )
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return {}
    
    # Advanced Memory Operations (continued)
    def link(
        self,
        memory_id: str,
        target_id: str,
        relationship_type: str = "related"
    ) -> Dict:
        """Link two memories in the graph."""
        try:
            return self.client.link_memories(
                memory_id=memory_id,
                target_id=target_id,
                relationship_type=relationship_type
            )
        except Exception as e:
            logger.error(f"Failed to link memories: {e}")
            return {}
    
    def find_path(
        self,
        source_id: str,
        target_id: str
    ) -> Dict:
        """Find shortest path between two memories in the graph."""
        try:
            return self.client.find_memory_path(
                source_id=source_id,
                target_id=target_id
            )
        except Exception as e:
            logger.error(f"Failed to find path: {e}")
            return {}
    
    # Advanced Search Context Methods
    def get_optimized_context(
        self,
        query: str,
        max_tokens: int = 2000,
        max_memories: int = 20,
        use_compression: bool = True,
        use_cache: bool = True
    ) -> str:
        """Get optimized context for a query (returns formatted string)."""
        try:
            result = self.search_optimized(
                query=query,
                max_tokens=max_tokens,
                max_memories=max_memories,
                use_compression=use_compression,
                use_cache=use_cache
            )
            return result.get('context', '')
        except Exception as e:
            logger.error(f"Failed to get optimized context: {e}")
            return ''
    
    def get_enhanced_context(
        self,
        query: str,
        max_tokens: int = 1500,
        max_memories: int = 15,
        use_compression: bool = True
    ) -> str:
        """Get enhanced context for a query (returns formatted string)."""
        try:
            result = self.search_enhanced(
                query=query,
                max_tokens=max_tokens,
                max_memories=max_memories,
                use_compression=use_compression
            )
            return result.get('context', '')
        except Exception as e:
            logger.error(f"Failed to get enhanced context: {e}")
            return ''
    
    # Version Control (continued)
    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict:
        """Compare two versions of a memory."""
        try:
            return self.client.compare_versions(
                version_id_1=version_id_1,
                version_id_2=version_id_2
            )
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            return {}
    
    # Export/Import
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
    
    def import_memories(
        self,
        data: str,
        format: str = "json"
    ) -> Dict:
        """Import memories."""
        try:
            return self.client.import_memories(
                user_id=self.user_id,
                data=data,
                format=format
            )
        except Exception as e:
            logger.error(f"Failed to import: {e}")
            return {}
    
    # Image Operations (continued)
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
    def concise(
        self,
        text: str
    ) -> Dict:
        """Make text more concise."""
        try:
            return self.client.concise_text(text=text)
        except Exception as e:
            logger.error(f"Failed to concise text: {e}")
            return {}
    
    # Health Check
    def health(self) -> Dict:
        """Check API health."""
        try:
            return self.client.health_check()
        except Exception as e:
            logger.error(f"Failed to check health: {e}")
            return {}
    
    # Webhooks
    def create_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict:
        """Create a webhook."""
        try:
            return self.client.create_webhook(
                url=url,
                events=events,
                secret=secret
            )
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            return {}
    
    def list_webhooks(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all webhooks."""
        try:
            return self.client.list_webhooks(user_id=user_id or self.user_id)
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            return []
    
    def get_webhook(self, webhook_id: str) -> Dict:
        """Get a specific webhook."""
        try:
            return self.client.get_webhook(webhook_id)
        except Exception as e:
            logger.error(f"Failed to get webhook: {e}")
            return {}
    
    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Dict:
        """Update a webhook."""
        try:
            options = {}
            if url is not None:
                options["url"] = url
            if events is not None:
                options["events"] = events
            if secret is not None:
                options["secret"] = secret
            if active is not None:
                options["active"] = active
            
            return self.client.update_webhook(webhook_id, **options)
        except Exception as e:
            logger.error(f"Failed to update webhook: {e}")
            return {}
    
    def delete_webhook(self, webhook_id: str) -> Dict:
        """Delete a webhook."""
        try:
            return self.client.delete_webhook(webhook_id)
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return {}
    
    def test_webhook(self, webhook_id: str) -> Dict:
        """Test a webhook."""
        try:
            return self.client.test_webhook(webhook_id)
        except Exception as e:
            logger.error(f"Failed to test webhook: {e}")
            return {}
    
    # Security & Compliance
    def export_gdpr(self) -> Dict:
        """Export GDPR data for this user."""
        try:
            return self.client.export_gdpr(self.user_id)
        except Exception as e:
            logger.error(f"Failed to export GDPR data: {e}")
            return {}
    
    def delete_gdpr(self) -> Dict:
        """Delete GDPR data for this user."""
        try:
            return self.client.delete_gdpr(self.user_id)
        except Exception as e:
            logger.error(f"Failed to delete GDPR data: {e}")
            return {}
    
    def set_retention_policy(
        self,
        data_type: str,
        retention_days: int,
        organization_id: Optional[str] = None,
        auto_delete: bool = False
    ) -> Dict:
        """Set a data retention policy."""
        try:
            return self.client.set_retention_policy(
                data_type=data_type,
                retention_days=retention_days,
                organization_id=organization_id,
                user_id=self.user_id,
                auto_delete=auto_delete
            )
        except Exception as e:
            logger.error(f"Failed to set retention policy: {e}")
            return {}
    
    def apply_retention_policies(
        self,
        organization_id: Optional[str] = None
    ) -> Dict:
        """Apply retention policies."""
        try:
            return self.client.apply_retention_policies(
                organization_id=organization_id,
                user_id=self.user_id
            )
        except Exception as e:
            logger.error(f"Failed to apply retention policies: {e}")
            return {}
    
    def get_compliance_report(
        self,
        organization_id: str,
        compliance_type: Optional[str] = None
    ) -> Dict:
        """Get compliance report."""
        try:
            return self.client.get_compliance_report(
                organization_id=organization_id,
                compliance_type=compliance_type
            )
        except Exception as e:
            logger.error(f"Failed to get compliance report: {e}")
            return {}
    
    def record_compliance_event(
        self,
        compliance_type: str,
        event_type: str,
        organization_id: Optional[str] = None,
        data_subject_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict:
        """Record a compliance event."""
        try:
            return self.client.record_compliance_event(
                compliance_type=compliance_type,
                event_type=event_type,
                user_id=self.user_id,
                organization_id=organization_id,
                data_subject_id=data_subject_id,
                details=details or {}
            )
        except Exception as e:
            logger.error(f"Failed to record compliance event: {e}")
            return {}
    
    def encrypt_data(self, data: str) -> Dict:
        """Encrypt sensitive data."""
        try:
            return self.client.encrypt_data(data)
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return {}
    
    def decrypt_data(self, encrypted_data: str) -> Dict:
        """Decrypt sensitive data."""
        try:
            return self.client.decrypt_data(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return {}
    
    # Observability
    def get_metrics(self) -> Dict:
        """Get system metrics."""
        try:
            return self.client.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics summary."""
        try:
            return self.client.get_metrics_summary()
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    def get_audit_logs(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit logs for this user."""
        try:
            return self.client.get_audit_logs(
                user_id=self.user_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
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



