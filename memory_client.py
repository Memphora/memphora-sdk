"""Python SDK client for Memphora."""
import requests
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MemoryClient:
    """Client for interacting with the Memphora API."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", api_key: Optional[str] = None):
        """
        Initialize the memory client.
        
        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication (Bearer token)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
        # Set up session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers with API key if provided
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    def _get_headers(self, additional_headers: Optional[Dict] = None) -> Dict:
        """Get request headers with API key."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if additional_headers:
            headers.update(additional_headers)
        return headers
    
    def add_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a new memory.
        
        Args:
            user_id: ID of the user
            content: Memory content
            metadata: Optional metadata dictionary
        
        Returns:
            Created memory dictionary
        """
        response = self.session.post(
            f"{self.base_url}/memories",
            json={
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_memory(self, memory_id: str) -> Dict:
        """
        Get a memory by ID.
        
        Args:
            memory_id: ID of the memory
        
        Returns:
            Memory dictionary
        """
        response = self.session.get(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return response.json()
    
    def get_user_memories(self, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get all memories for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of memories to return
        
        Returns:
            List of memory dictionaries
        """
        response = self.session.get(
            f"{self.base_url}/memories/user/{user_id}",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        rerank: bool = False,
        rerank_provider: str = "auto",
        cohere_api_key: Optional[str] = None,
        jina_api_key: Optional[str] = None
    ) -> List[Dict]:
        """
        Search memories semantically with optional external reranking.
        
        Args:
            user_id: ID of the user
            query: Search query
            limit: Maximum number of results
            rerank: Enable external reranking (Cohere/Jina) for better relevance
            rerank_provider: Reranking provider ("cohere", "jina", or "auto")
            cohere_api_key: Optional Cohere API key (if not configured on backend)
            jina_api_key: Optional Jina AI API key (if not configured on backend)
        
        Returns:
            List of matching memory dictionaries
        """
        payload = {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "rerank": rerank,
            "rerank_provider": rerank_provider
        }
        
        if cohere_api_key:
            payload["cohere_api_key"] = cohere_api_key
        if jina_api_key:
            payload["jina_api_key"] = jina_api_key
        
        response = self.session.post(
            f"{self.base_url}/memories/search",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Update a memory.
        
        Args:
            memory_id: ID of the memory
            content: New content (optional)
            metadata: New metadata (optional)
        
        Returns:
            Updated memory dictionary
        """
        update_data = {}
        if content is not None:
            update_data["content"] = content
        if metadata is not None:
            update_data["metadata"] = metadata
        
        response = self.session.put(
            f"{self.base_url}/memories/{memory_id}",
            json=update_data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: ID of the memory
        
        Returns:
            True if successful
        """
        response = self.session.delete(f"{self.base_url}/memories/{memory_id}")
        response.raise_for_status()
        return True
    
    def extract_from_conversation(
        self,
        user_id: str,
        conversation: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Extract and store memories from a conversation.
        Automatically processes conversation to extract key information.
        
        Args:
            user_id: ID of the user
            conversation: List of messages with 'role' and 'content' keys
        
        Returns:
            List of extracted and stored memory dictionaries
        """
        response = self.session.post(
            f"{self.base_url}/conversations/extract",
            json={
                "user_id": user_id,
                "conversation": conversation
            }
        )
        response.raise_for_status()
        return response.json()
    
    def extract_from_content(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Extract and store memories from a single content string.
        Automatically processes content to ensure clean, standardized format for better retrieval.
        
        Args:
            user_id: ID of the user
            content: Content string to extract memories from
            metadata: Optional metadata dictionary
        
        Returns:
            List of extracted and stored memory dictionaries
        """
        response = self.session.post(
            f"{self.base_url}/memories/extract",
            json={
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    # Advanced Memory Operations
    def create_advanced_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None,
        link_to: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a memory with graph linking.
        
        Args:
            user_id: ID of the user
            content: Memory content
            metadata: Optional metadata dictionary
            link_to: Optional list of memory IDs to link to
        
        Returns:
            Created memory dictionary
        """
        response = self.session.post(
            f"{self.base_url}/memories/advanced",
            json={
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {},
                "link_to": link_to or []
            }
        )
        response.raise_for_status()
        return response.json()
    
    def search_advanced(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        filters: Optional[Dict] = None,
        include_related: bool = False,
        min_score: float = 0.0,
        sort_by: str = "relevance"
    ) -> List[Dict]:
        """
        Advanced memory search with filtering and scoring.
        
        Args:
            user_id: ID of the user
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            include_related: Include related memories via graph
            min_score: Minimum relevance score (0.0 to 1.0)
            sort_by: Sort by "relevance", "recency", or "importance"
        
        Returns:
            List of matching memory dictionaries
        """
        response = self.session.post(
            f"{self.base_url}/memories/search/advanced",
            json={
                "user_id": user_id,
                "query": query,
                "limit": limit,
                "filters": filters or {},
                "include_related": include_related,
                "min_score": min_score,
                "sort_by": sort_by
            }
        )
        response.raise_for_status()
        return response.json()
    
    def batch_create(
        self,
        user_id: str,
        memories: List[Dict[str, str]],
        link_related: bool = True
    ) -> List[Dict]:
        """
        Create multiple memories in batch.
        
        Args:
            user_id: ID of the user
            memories: List of memory dictionaries with 'content' and optional 'metadata'
            link_related: Automatically link related memories
        
        Returns:
            List of created memory dictionaries
        """
        response = self.session.post(
            f"{self.base_url}/memories/batch",
            json={
                "user_id": user_id,
                "memories": memories,
                "link_related": link_related
            }
        )
        response.raise_for_status()
        return response.json()
    
    def merge_memories(
        self,
        memory_ids: List[str],
        merge_strategy: str = "combine"
    ) -> Dict:
        """
        Merge multiple memories.
        
        Args:
            memory_ids: List of memory IDs to merge
            merge_strategy: "combine", "keep_latest", or "keep_most_relevant"
        
        Returns:
            Merged memory dictionary
        """
        response = self.session.post(
            f"{self.base_url}/memories/merge",
            json={
                "memory_ids": memory_ids,
                "merge_strategy": merge_strategy
            }
        )
        response.raise_for_status()
        return response.json()
    
    def find_contradictions(
        self,
        memory_id: str,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Find potentially contradictory memories.
        
        Args:
            memory_id: ID of the memory to check
            similarity_threshold: Similarity threshold for contradiction detection
        
        Returns:
            List of potentially contradictory memories
        """
        response = self.session.get(
            f"{self.base_url}/memories/{memory_id}/contradictions",
            params={"similarity_threshold": similarity_threshold}
        )
        response.raise_for_status()
        return response.json()
    
    def link_memories(
        self,
        memory_id: str,
        target_id: str,
        relationship_type: str = "related"
    ) -> Dict:
        """
        Link two memories in the graph.
        
        Args:
            memory_id: Source memory ID
            target_id: Target memory ID
            relationship_type: "related", "contradicts", "supports", or "extends"
        
        Returns:
            Relationship information
        """
        response = self.session.post(
            f"{self.base_url}/memories/{memory_id}/link",
            params={
                "target_id": target_id,
                "relationship_type": relationship_type
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_memory_context(
        self,
        memory_id: str,
        depth: int = 2
    ) -> Dict:
        """
        Get full context around a memory.
        
        Args:
            memory_id: ID of the memory
            depth: Depth of related memories to retrieve
        
        Returns:
            Context dictionary with related memories
        """
        response = self.session.get(
            f"{self.base_url}/memories/{memory_id}/context",
            params={"depth": depth}
        )
        response.raise_for_status()
        return response.json()
    
    def find_memory_path(
        self,
        source_id: str,
        target_id: str
    ) -> Dict:
        """
        Find shortest path between two memories in the graph.
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
        
        Returns:
            Path information with memory details
        """
        response = self.session.get(
            f"{self.base_url}/memories/{source_id}/path/{target_id}"
        )
        response.raise_for_status()
        return response.json()
    
    # Export/Import
    def export_memories(
        self,
        user_id: str,
        format: str = "json"
    ) -> Dict:
        """
        Export all memories for a user.
        
        Args:
            user_id: ID of the user
            format: Export format ("json" or "csv")
        
        Returns:
            Export data with format information
        """
        response = self.session.get(
            f"{self.base_url}/users/{user_id}/export",
            params={"format": format}
        )
        response.raise_for_status()
        return response.json()
    
    def import_memories(
        self,
        user_id: str,
        data: str,
        format: str = "json"
    ) -> Dict:
        """
        Import memories for a user.
        
        Args:
            user_id: ID of the user
            data: Import data (JSON or CSV string)
            format: Import format ("json" or "csv")
        
        Returns:
            Import result with count and memories
        """
        response = self.session.post(
            f"{self.base_url}/users/{user_id}/import",
            params={"format": format},
            json={"data": data}
        )
        response.raise_for_status()
        return response.json()
    
    # Statistics
    def get_user_statistics(self, user_id: str) -> Dict:
        """
        Get statistics about user memories.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Statistics dictionary
        """
        response = self.session.get(
            f"{self.base_url}/users/{user_id}/statistics"
        )
        response.raise_for_status()
        return response.json()
    
    def get_global_statistics(self) -> Dict:
        """
        Get global statistics.
        
        Returns:
            Global statistics dictionary
        """
        response = self.session.get(f"{self.base_url}/statistics")
        response.raise_for_status()
        return response.json()
    
    def delete_all_user_memories(self, user_id: str) -> Dict:
        """
        Delete all memories for a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Deletion result with count
        """
        response = self.session.delete(
            f"{self.base_url}/users/{user_id}/memories"
        )
        response.raise_for_status()
        return response.json()
    
    def set_retention_policy(
        self,
        data_type: str,
        retention_days: int,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_delete: bool = False
    ) -> Dict:
        """
        Set a data retention policy (organization-level or user-level).
        
        Args:
            data_type: Type of data (memory, log, metric)
            retention_days: Number of days to retain data
            organization_id: Organization ID (optional, for org-level policies)
            user_id: User ID (optional, for user-level policies)
            auto_delete: Whether to automatically delete old data
        
        Returns:
            Created policy dictionary
        """
        response = self.session.post(
            f"{self.base_url}/security/retention-policies",
            json={
                "data_type": data_type,
                "retention_days": retention_days,
                "organization_id": organization_id,
                "user_id": user_id,
                "auto_delete": auto_delete
            }
        )
        response.raise_for_status()
        return response.json()
    
    def apply_retention_policies(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Apply retention policies and delete old data.
        
        Args:
            organization_id: Apply policies for specific organization (optional)
            user_id: Apply policies for specific user (optional)
        
        Returns:
            Result with deleted_count and policies_applied
        """
        params = {}
        if organization_id:
            params["organization_id"] = organization_id
        if user_id:
            params["user_id"] = user_id
        
        response = self.session.post(
            f"{self.base_url}/security/apply-retention",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    # Memory Versioning
    def get_memory_versions(self, memory_id: str, limit: int = 50) -> List[Dict]:
        """
        Get all versions for a memory.
        
        Args:
            memory_id: ID of the memory
            limit: Maximum number of versions to return
        
        Returns:
            List of version dictionaries
        """
        response = self.session.get(
            f"{self.base_url}/memories/{memory_id}/versions",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def get_version(self, version_id: str) -> Dict:
        """
        Get a specific version.
        
        Args:
            version_id: ID of the version
        
        Returns:
            Version dictionary
        """
        response = self.session.get(f"{self.base_url}/versions/{version_id}")
        response.raise_for_status()
        return response.json()
    
    def get_version_history(
        self,
        memory_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[Dict]:
        """
        Get version history for a memory.
        
        Args:
            memory_id: ID of the memory
            from_version: Start version number (optional)
            to_version: End version number (optional)
        
        Returns:
            List of version history entries
        """
        params = {}
        if from_version is not None:
            params["from_version"] = from_version
        if to_version is not None:
            params["to_version"] = to_version
        
        response = self.session.get(
            f"{self.base_url}/memories/{memory_id}/history",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def rollback_memory(
        self,
        memory_id: str,
        target_version: int,
        user_id: str
    ) -> Dict:
        """
        Rollback a memory to a specific version.
        
        Args:
            memory_id: ID of the memory
            target_version: Version number to rollback to
            user_id: ID of the user performing rollback
        
        Returns:
            Rollback result
        """
        response = self.session.post(
            f"{self.base_url}/memories/{memory_id}/rollback",
            params={"user_id": user_id},
            json={"target_version": target_version}
        )
        response.raise_for_status()
        return response.json()
    
    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict:
        """
        Compare two versions of a memory.
        
        Args:
            version_id_1: First version ID
            version_id_2: Second version ID
        
        Returns:
            Comparison result
        """
        response = self.session.get(
            f"{self.base_url}/versions/compare",
            params={
                "version_id_1": version_id_1,
                "version_id_2": version_id_2
            }
        )
        response.raise_for_status()
        return response.json()
    
    # Conversation Features
    def record_conversation(
        self,
        user_id: str,
        conversation: List[Dict[str, str]],
        platform: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record a full conversation.
        
        Args:
            user_id: ID of the user
            conversation: List of messages with 'role' and 'content'
            platform: Optional platform identifier
            metadata: Optional conversation metadata
        
        Returns:
            Recorded conversation dictionary
        """
        response = self.session.post(
            f"{self.base_url}/conversations/record",
            json={
                "user_id": user_id,
                "conversation": conversation,
                "platform": platform or "unknown",
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_conversation(self, conversation_id: str) -> Dict:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
        
        Returns:
            Conversation dictionary
        """
        response = self.session.get(
            f"{self.base_url}/conversations/{conversation_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_conversations(
        self,
        user_id: str,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: ID of the user
            platform: Optional platform filter
            limit: Maximum number of conversations
        
        Returns:
            List of conversation dictionaries
        """
        params = {"limit": limit}
        if platform:
            params["platform"] = platform
        
        response = self.session.get(
            f"{self.base_url}/conversations/user/{user_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def summarize_conversation(
        self,
        conversation: List[Dict[str, str]],
        summary_type: str = "brief"
    ) -> Dict:
        """
        Summarize a conversation.
        
        Args:
            conversation: List of messages with 'role' and 'content'
            summary_type: "brief", "detailed", "topics", or "action_items"
        
        Returns:
            Summary dictionary
        """
        response = self.session.post(
            f"{self.base_url}/conversations/summarize",
            json={
                "conversation": conversation,
                "summary_type": summary_type
            }
        )
        response.raise_for_status()
        return response.json()
    
    # Performance Features
    def search_optimized(
        self,
        user_id: str,
        query: str,
        max_tokens: int = 2000,
        max_memories: int = 20,
        use_compression: bool = True,
        use_cache: bool = True
    ) -> Dict:
        """
        Optimized memory search (26% better accuracy, 91% faster).
        
        Args:
            user_id: ID of the user
            query: Search query
            max_tokens: Maximum token budget
            max_memories: Maximum number of memories
            use_compression: Enable context compression
            use_cache: Use cached results
        
        Returns:
            Optimized context with performance metrics
        """
        response = self.session.post(
            f"{self.base_url}/memories/search/optimized",
            json={
                "user_id": user_id,
                "query": query,
                "max_tokens": max_tokens,
                "max_memories": max_memories,
                "use_compression": use_compression,
                "use_cache": use_cache
            }
        )
        response.raise_for_status()
        return response.json()
    
    def search_enhanced(
        self,
        user_id: str,
        query: str,
        max_tokens: int = 2000,
        max_memories: int = 20,
        use_compression: bool = True
    ) -> Dict:
        """
        Enhanced search with maximum performance (>35% accuracy improvement).
        
        Args:
            user_id: ID of the user
            query: Search query
            max_tokens: Maximum token budget
            max_memories: Maximum number of memories
            use_compression: Enable context compression
        
        Returns:
            Enhanced context with performance metrics
        """
        response = self.session.post(
            f"{self.base_url}/memories/search/enhanced",
            json={
                "user_id": user_id,
                "query": query,
                "max_tokens": max_tokens,
                "max_memories": max_memories,
                "use_compression": use_compression
            }
        )
        response.raise_for_status()
        return response.json()
    
    # Text Features
    def concise_text(self, text: str) -> Dict:
        """
        Make text more concise.
        
        Args:
            text: Text to make concise
        
        Returns:
            Concise text result
        """
        response = self.session.post(
            f"{self.base_url}/text/conciser",
            json={"text": text}
        )
        response.raise_for_status()
        return response.json()
    
    # Multimodal Features
    def store_image(
        self,
        user_id: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Store an image memory.
        
        Args:
            user_id: ID of the user
            image_url: URL of the image (optional)
            image_base64: Base64 encoded image (optional)
            description: Optional image description
            metadata: Optional metadata dictionary
        
        Returns:
            Created image memory dictionary
        """
        response = self.session.post(
            f"{self.base_url}/memories/image",
            json={
                "user_id": user_id,
                "image_url": image_url,
                "image_base64": image_base64,
                "description": description,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def upload_image(
        self,
        user_id: str,
        image_data: bytes,
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload and process an image.
        
        Args:
            user_id: ID of the user
            image_data: Image file data (bytes)
            filename: Image filename
            metadata: Optional metadata dictionary
        
        Returns:
            Uploaded image memory dictionary
        """
        files = {"file": (filename, image_data)}
        # user_id is sent as query parameter, not form data
        # metadata can be sent as form data if needed, but backend doesn't use it from form
        response = self.session.post(
            f"{self.base_url}/memories/image/upload",
            params={"user_id": user_id},
            files=files
        )
        response.raise_for_status()
        return response.json()
    
    def search_images(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search memories using image descriptions.
        
        Args:
            user_id: ID of the user
            query: Text query describing the image
            limit: Maximum number of results
        
        Returns:
            List of matching image memories
        """
        # user_id, query, and limit are sent as query parameters, not JSON body
        response = self.session.post(
            f"{self.base_url}/memories/image/search",
            params={"user_id": user_id, "query": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    # Security & Compliance
    def export_gdpr(self, user_id: str) -> Dict:
        """
        Export all user data for GDPR compliance.
        
        Args:
            user_id: ID of the user
        
        Returns:
            GDPR export data
        """
        response = self.session.get(
            f"{self.base_url}/security/compliance/gdpr/export/{user_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def delete_gdpr(self, user_id: str) -> Dict:
        """
        Delete all user data for GDPR compliance.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Deletion confirmation
        """
        response = self.session.delete(
            f"{self.base_url}/security/compliance/gdpr/delete/{user_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def record_compliance_event(
        self,
        compliance_type: str,
        event_type: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        data_subject_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict:
        """
        Record a compliance event.
        
        Args:
            compliance_type: Type of compliance (GDPR, SOC2, HIPAA)
            event_type: Type of event (data_access, deletion, export, etc.)
            user_id: Optional user ID
            organization_id: Optional organization ID
            data_subject_id: Optional data subject ID (for GDPR)
            details: Optional additional details
        
        Returns:
            Event recording confirmation
        """
        response = self.session.post(
            f"{self.base_url}/security/compliance-events",
            json={
                "compliance_type": compliance_type,
                "event_type": event_type,
                "user_id": user_id,
                "organization_id": organization_id,
                "data_subject_id": data_subject_id,
                "details": details or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def encrypt_data(self, data: str) -> Dict:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data string to encrypt
        
        Returns:
            Dictionary with encrypted data
        """
        response = self.session.post(
            f"{self.base_url}/security/encrypt",
            json={"data": data}
        )
        response.raise_for_status()
        return response.json()
    
    def decrypt_data(self, encrypted_data: str) -> Dict:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data string
        
        Returns:
            Dictionary with decrypted data
        """
        response = self.session.post(
            f"{self.base_url}/security/decrypt",
            json={"encrypted_data": encrypted_data}
        )
        response.raise_for_status()
        return response.json()
    
    def get_compliance_report(
        self,
        organization_id: str,
        compliance_type: Optional[str] = None
    ) -> Dict:
        """
        Get compliance report for an organization.
        
        Args:
            organization_id: ID of the organization
            compliance_type: Optional compliance type filter
        
        Returns:
            Compliance report dictionary
        """
        params = {}
        if compliance_type:
            params["compliance_type"] = compliance_type
        
        response = self.session.get(
            f"{self.base_url}/security/compliance/report/{organization_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    # Health Check
    def health_check(self) -> Dict:
        """
        Check API health status.
        
        Returns:
            Health status dictionary
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    # Webhooks
    def create_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict:
        """
        Create a new webhook.
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Optional webhook secret for signing
        
        Returns:
            Created webhook dictionary
        """
        response = self.session.post(
            f"{self.base_url}/webhooks",
            json={
                "url": url,
                "events": events,
                "secret": secret
            }
        )
        response.raise_for_status()
        return response.json()
    
    def list_webhooks(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all webhooks.
        
        Args:
            user_id: Optional user ID filter
        
        Returns:
            List of webhook dictionaries
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        
        response = self.session.get(
            f"{self.base_url}/webhooks",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_webhook(self, webhook_id: str) -> Dict:
        """
        Get a webhook by ID.
        
        Args:
            webhook_id: ID of the webhook
        
        Returns:
            Webhook dictionary
        """
        response = self.session.get(f"{self.base_url}/webhooks/{webhook_id}")
        response.raise_for_status()
        return response.json()
    
    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Dict:
        """
        Update a webhook.
        
        Args:
            webhook_id: ID of the webhook
            url: New webhook URL (optional)
            events: New event list (optional)
            secret: New webhook secret (optional)
            active: Active status (optional)
        
        Returns:
            Updated webhook dictionary
        """
        update_data = {}
        if url is not None:
            update_data["url"] = url
        if events is not None:
            update_data["events"] = events
        if secret is not None:
            update_data["secret"] = secret
        if active is not None:
            update_data["active"] = active
        
        response = self.session.put(
            f"{self.base_url}/webhooks/{webhook_id}",
            json=update_data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_webhook(self, webhook_id: str) -> Dict:
        """
        Delete a webhook.
        
        Args:
            webhook_id: ID of the webhook
        
        Returns:
            Deletion confirmation
        """
        response = self.session.delete(f"{self.base_url}/webhooks/{webhook_id}")
        response.raise_for_status()
        return response.json()
    
    def test_webhook(self, webhook_id: str) -> Dict:
        """
        Test a webhook with a sample event.
        
        Args:
            webhook_id: ID of the webhook
        
        Returns:
            Test result
        """
        response = self.session.post(
            f"{self.base_url}/webhooks/{webhook_id}/test"
        )
        response.raise_for_status()
        return response.json()
    
    # Observability
    def get_metrics(self) -> Dict:
        """
        Get system metrics.
        
        Returns:
            Metrics dictionary
        """
        response = self.session.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()
    
    def get_metrics_summary(self) -> Dict:
        """
        Get metrics summary.
        
        Returns:
            Metrics summary dictionary
        """
        response = self.session.get(f"{self.base_url}/metrics/summary")
        response.raise_for_status()
        return response.json()
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get audit logs.
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of logs
        
        Returns:
            List of audit log entries
        """
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id
        
        response = self.session.get(
            f"{self.base_url}/audit-logs",
            params=params
        )
        response.raise_for_status()
        result = response.json()
        # Backend returns {"logs": [...]}, extract the list
        if isinstance(result, dict) and "logs" in result:
            return result["logs"]
        return result if isinstance(result, list) else []

