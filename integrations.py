"""
Memphora Framework Integrations

Native integrations for popular AI frameworks:
- LangChain: Memory store for LangChain conversations
- LlamaIndex: Memory for LlamaIndex chat engines
- CrewAI: Shared memory for multi-agent crews
- AutoGen: Microsoft AutoGen multi-agent memory

Usage:
    from memphora.integrations import (
        MemphoraLangChain,
        MemphoraLlamaIndex,
        MemphoraCrewAI,
        MemphoraAutoGen
    )
"""

from typing import List, Dict, Optional, Any, Sequence
from memphora_sdk import Memphora
import logging

logger = logging.getLogger("memphora.integrations")


# =============================================================================
# LangChain Integration
# =============================================================================

class MemphoraLangChain:
    """
    LangChain Memory Integration for Memphora.
    
    Provides a LangChain-compatible memory store that persists across sessions.
    Works with any LangChain chain, agent, or chat model.
    
    Usage:
        from memphora.integrations import MemphoraLangChain
        from langchain.chains import ConversationChain
        from langchain.llms import OpenAI
        
        # Create Memphora memory
        memory = MemphoraLangChain(
            user_id="user123",
            api_key="your-api-key"
        )
        
        # Use with LangChain
        chain = ConversationChain(
            llm=OpenAI(),
            memory=memory.as_langchain_memory()
        )
        
        response = chain.predict(input="Hello!")
    """
    
    def __init__(
        self,
        user_id: str,
        api_key: str,
        api_url: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_key: str = "history",
        input_key: str = "input",
        output_key: str = "output",
        return_messages: bool = True,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
    ):
        """
        Initialize Memphora LangChain integration.
        
        Args:
            user_id: User identifier
            api_key: Memphora API key
            api_url: Optional custom API URL
            session_id: Optional session ID for scoped memory
            memory_key: Key name for memory in chain context
            input_key: Key for human input
            output_key: Key for AI output
            return_messages: Return as message objects vs string
            human_prefix: Prefix for human messages
            ai_prefix: Prefix for AI messages
        """
        self.memphora = Memphora(
            user_id=user_id,
            api_key=api_key,
            api_url=api_url
        )
        self.session_id = session_id or user_id
        self.memory_key = memory_key
        self.input_key = input_key
        self.output_key = output_key
        self.return_messages = return_messages
        self.human_prefix = human_prefix
        self.ai_prefix = ai_prefix
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant memories based on input."""
        query = inputs.get(self.input_key, "")
        
        if not query:
            return {self.memory_key: [] if self.return_messages else ""}
        
        # Get relevant context from Memphora
        context = self.memphora.get_context(query, limit=10)
        
        if self.return_messages:
            # Return as message-like objects
            return {self.memory_key: self._format_as_messages(context)}
        else:
            # Return as formatted string
            return {self.memory_key: context}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation to Memphora."""
        human_input = inputs.get(self.input_key, "")
        ai_output = outputs.get(self.output_key, "")
        
        if human_input and ai_output:
            self.memphora.store_conversation(human_input, ai_output)
    
    def clear(self) -> None:
        """Clear all memories."""
        self.memphora.clear()
    
    def _format_as_messages(self, context: str) -> List[Dict[str, str]]:
        """Format context as message objects."""
        if not context:
            return []
        
        return [{"role": "system", "content": f"Relevant context:\n{context}"}]
    
    def as_langchain_memory(self):
        """
        Return a LangChain-compatible memory object.
        
        Returns:
            LangChain BaseChatMemory compatible wrapper
        """
        try:
            from langchain.memory import BaseChatMemory
            from langchain.schema import BaseMemory
        except ImportError:
            logger.warning("LangChain not installed. Install with: pip install langchain")
            return self  # Return self as fallback
        
        # Create a wrapper that implements LangChain's memory interface
        class MemphoraLangChainMemory(BaseMemory):
            """LangChain-compatible memory wrapper."""
            
            memphora_integration: MemphoraLangChain = None
            
            class Config:
                arbitrary_types_allowed = True
            
            def __init__(self, integration: 'MemphoraLangChain'):
                super().__init__()
                object.__setattr__(self, 'memphora_integration', integration)
            
            @property
            def memory_variables(self) -> List[str]:
                return [self.memphora_integration.memory_key]
            
            def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                return self.memphora_integration.load_memory_variables(inputs)
            
            def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
                self.memphora_integration.save_context(inputs, outputs)
            
            def clear(self) -> None:
                self.memphora_integration.clear()
        
        return MemphoraLangChainMemory(self)


# =============================================================================
# LlamaIndex Integration
# =============================================================================

class MemphoraLlamaIndex:
    """
    LlamaIndex Memory Integration for Memphora.
    
    Provides persistent memory for LlamaIndex chat engines and agents.
    
    Usage:
        from memphora.integrations import MemphoraLlamaIndex
        from llama_index import VectorStoreIndex, SimpleDirectoryReader
        from llama_index.memory import ChatMemoryBuffer
        
        # Create Memphora memory
        memphora_memory = MemphoraLlamaIndex(
            user_id="user123",
            api_key="your-api-key"
        )
        
        # Create chat engine with Memphora memory
        index = VectorStoreIndex.from_documents(documents)
        chat_engine = index.as_chat_engine(
            chat_mode="context",
            memory=memphora_memory.as_chat_memory()
        )
        
        response = chat_engine.chat("Hello!")
    """
    
    def __init__(
        self,
        user_id: str,
        api_key: str,
        api_url: Optional[str] = None,
        token_limit: int = 3000,
    ):
        """
        Initialize Memphora LlamaIndex integration.
        
        Args:
            user_id: User identifier
            api_key: Memphora API key
            api_url: Optional custom API URL
            token_limit: Maximum tokens for memory context
        """
        self.memphora = Memphora(
            user_id=user_id,
            api_key=api_key,
            api_url=api_url
        )
        self.token_limit = token_limit
        self._chat_history: List[Dict[str, str]] = []
    
    def get(self, query: str = None, limit: int = 10) -> str:
        """Get relevant context from Memphora."""
        if query:
            return self.memphora.get_context(query, limit=limit)
        return ""
    
    def put(self, user_message: str, assistant_message: str) -> None:
        """Store a conversation turn."""
        self.memphora.store_conversation(user_message, assistant_message)
        self._chat_history.append({"role": "user", "content": user_message})
        self._chat_history.append({"role": "assistant", "content": assistant_message})
    
    def get_all(self) -> List[Dict[str, str]]:
        """Get all chat history."""
        return self._chat_history
    
    def reset(self) -> None:
        """Reset chat history."""
        self._chat_history = []
    
    def set(self, messages: List[Dict[str, str]]) -> None:
        """Set chat history from messages."""
        self._chat_history = messages
        
        # Store each conversation pair in Memphora
        for i in range(0, len(messages) - 1, 2):
            if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                self.memphora.store_conversation(
                    messages[i]["content"],
                    messages[i + 1]["content"]
                )
    
    def as_chat_memory(self):
        """
        Return a LlamaIndex-compatible memory object.
        
        Returns:
            LlamaIndex ChatMemoryBuffer compatible wrapper
        """
        try:
            from llama_index.core.memory import ChatMemoryBuffer
        except ImportError:
            try:
                from llama_index.memory import ChatMemoryBuffer
            except ImportError:
                logger.warning("LlamaIndex not installed. Install with: pip install llama-index")
                return self
        
        # Create wrapper class
        class MemphoraLlamaMemory(ChatMemoryBuffer):
            """LlamaIndex-compatible memory wrapper."""
            
            def __init__(self, memphora_integration: 'MemphoraLlamaIndex'):
                self._memphora = memphora_integration
                super().__init__(token_limit=memphora_integration.token_limit)
            
            def get(self, input: str = None, **kwargs) -> str:
                return self._memphora.get(query=input)
            
            def put(self, message: Any) -> None:
                if hasattr(message, 'content') and hasattr(message, 'role'):
                    if message.role == "assistant":
                        # Find last user message
                        history = self._memphora.get_all()
                        if history and history[-1]["role"] == "user":
                            self._memphora.put(
                                history[-1]["content"],
                                message.content
                            )
            
            def reset(self) -> None:
                self._memphora.reset()
        
        return MemphoraLlamaMemory(self)


# =============================================================================
# CrewAI Integration
# =============================================================================

class MemphoraCrewAI:
    """
    CrewAI Memory Integration for Memphora.
    
    Provides shared memory for multi-agent crews with per-agent namespaces.
    
    Usage:
        from memphora.integrations import MemphoraCrewAI
        from crewai import Agent, Task, Crew
        
        # Create Memphora memory for the crew
        crew_memory = MemphoraCrewAI(
            crew_id="my-crew",
            api_key="your-api-key"
        )
        
        # Create agents with shared memory
        researcher = Agent(
            role="Researcher",
            goal="Research information",
            backstory="Expert researcher",
            memory=crew_memory.for_agent("researcher")
        )
        
        writer = Agent(
            role="Writer",
            goal="Write content",
            backstory="Expert writer",
            memory=crew_memory.for_agent("writer")
        )
    """
    
    def __init__(
        self,
        crew_id: str,
        api_key: str,
        api_url: Optional[str] = None,
    ):
        """
        Initialize Memphora CrewAI integration.
        
        Args:
            crew_id: Unique identifier for the crew
            api_key: Memphora API key
            api_url: Optional custom API URL
        """
        self.memphora = Memphora(
            user_id=crew_id,
            api_key=api_key,
            api_url=api_url
        )
        self.crew_id = crew_id
        self._agent_memories: Dict[str, 'MemphoraAgentMemory'] = {}
    
    def for_agent(self, agent_id: str) -> 'MemphoraAgentMemory':
        """
        Get a memory instance for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Agent-specific memory instance with shared crew access
        """
        if agent_id not in self._agent_memories:
            self._agent_memories[agent_id] = MemphoraAgentMemory(
                memphora=self.memphora,
                agent_id=agent_id,
                crew_id=self.crew_id
            )
        return self._agent_memories[agent_id]
    
    def store_shared(self, content: str, metadata: Optional[Dict] = None) -> Dict:
        """Store a shared memory accessible by all agents."""
        meta = metadata or {}
        meta["shared"] = True
        meta["crew_id"] = self.crew_id
        return self.memphora.store_group_memory(self.crew_id, content, meta)
    
    def search_shared(self, query: str, limit: int = 10) -> Dict:
        """Search shared memories across the crew."""
        return self.memphora.search_group_memories(self.crew_id, query, limit)
    
    def get_crew_context(self, limit: int = 50) -> str:
        """Get context from all shared crew memories."""
        return self.memphora.get_group_context(self.crew_id, limit)


class MemphoraAgentMemory:
    """Individual agent memory within a CrewAI crew."""
    
    def __init__(
        self,
        memphora: Memphora,
        agent_id: str,
        crew_id: str
    ):
        self.memphora = memphora
        self.agent_id = agent_id
        self.crew_id = crew_id
    
    def store(self, content: str, metadata: Optional[Dict] = None) -> Dict:
        """Store a memory for this agent."""
        return self.memphora.store_agent_memory(
            agent_id=self.agent_id,
            content=content,
            metadata=metadata
        )
    
    def search(self, query: str, limit: int = 10) -> Dict:
        """Search this agent's memories."""
        return self.memphora.search_agent_memories(
            agent_id=self.agent_id,
            query=query,
            limit=limit
        )
    
    def get_all(self, limit: int = 100) -> List[Dict]:
        """Get all memories for this agent."""
        return self.memphora.get_agent_memories(self.agent_id, limit)
    
    def search_crew(self, query: str, limit: int = 10) -> Dict:
        """Search shared crew memories."""
        return self.memphora.search_group_memories(self.crew_id, query, limit)


# =============================================================================
# AutoGen Integration
# =============================================================================

class MemphoraAutoGen:
    """
    Microsoft AutoGen Memory Integration for Memphora.
    
    Provides persistent memory for AutoGen multi-agent conversations.
    Supports escalation tracking and cross-agent memory sharing.
    
    Usage:
        from memphora.integrations import MemphoraAutoGen
        import autogen
        
        # Create Memphora memory
        memory = MemphoraAutoGen(
            session_id="session-123",
            api_key="your-api-key"
        )
        
        # Create AutoGen agents with memory callbacks
        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config,
        )
        
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
        )
        
        # Register memory hooks
        memory.register_with_agent(assistant)
        memory.register_with_agent(user_proxy)
        
        # Start conversation
        user_proxy.initiate_chat(assistant, message="Hello!")
    """
    
    def __init__(
        self,
        session_id: str,
        api_key: str,
        api_url: Optional[str] = None,
        track_escalations: bool = True,
    ):
        """
        Initialize Memphora AutoGen integration.
        
        Args:
            session_id: Unique session identifier
            api_key: Memphora API key
            api_url: Optional custom API URL
            track_escalations: Whether to track and store escalation events
        """
        self.memphora = Memphora(
            user_id=session_id,
            api_key=api_key,
            api_url=api_url
        )
        self.session_id = session_id
        self.track_escalations = track_escalations
        self._message_buffer: List[Dict[str, str]] = []
    
    def register_with_agent(self, agent) -> None:
        """
        Register memory hooks with an AutoGen agent.
        
        Args:
            agent: AutoGen agent instance
        """
        agent_name = getattr(agent, 'name', 'unknown')
        
        # Store reference to original receive method
        original_receive = agent.receive
        
        def receive_with_memory(message, sender, request_reply=True, silent=False):
            """Wrapper that stores messages to Memphora."""
            # Store the message
            self._on_message(
                content=message if isinstance(message, str) else message.get("content", ""),
                sender=getattr(sender, 'name', 'unknown'),
                receiver=agent_name
            )
            
            # Call original receive
            return original_receive(message, sender, request_reply, silent)
        
        # Replace receive method
        agent.receive = receive_with_memory
    
    def _on_message(self, content: str, sender: str, receiver: str) -> None:
        """Handle incoming message."""
        if not content:
            return
        
        # Buffer message
        self._message_buffer.append({
            "content": content,
            "sender": sender,
            "receiver": receiver
        })
        
        # Store as agent memory
        self.memphora.store_agent_memory(
            agent_id=sender,
            content=content,
            metadata={
                "receiver": receiver,
                "session_id": self.session_id,
                "type": "message"
            }
        )
        
        # Check for escalation keywords
        if self.track_escalations:
            escalation_keywords = ["escalate", "human", "supervisor", "help needed"]
            if any(kw in content.lower() for kw in escalation_keywords):
                self.memphora.store_agent_memory(
                    agent_id=sender,
                    content=f"ESCALATION: {content}",
                    metadata={
                        "type": "escalation",
                        "session_id": self.session_id,
                        "from_agent": sender,
                        "to_agent": receiver
                    }
                )
    
    def get_context(self, query: str, agent_id: Optional[str] = None, limit: int = 10) -> str:
        """
        Get relevant context for a query.
        
        Args:
            query: Search query
            agent_id: Optional agent ID to scope search
            limit: Maximum results
            
        Returns:
            Formatted context string
        """
        if agent_id:
            result = self.memphora.search_agent_memories(agent_id, query, limit=limit)
            facts = result.get("facts", [])
        else:
            # Search all agents in session
            result = self.memphora.search(query, limit=limit)
            facts = result.get("facts", [])
        
        if not facts:
            return ""
        
        # Format facts
        context_lines = []
        for fact in facts:
            if isinstance(fact, dict):
                context_lines.append(fact.get("text", ""))
            else:
                context_lines.append(str(fact))
        
        return "\n".join(context_lines)
    
    def get_escalations(self, limit: int = 20) -> List[Dict]:
        """Get all escalation events."""
        result = self.memphora.search(
            "ESCALATION",
            limit=limit
        )
        return result.get("facts", [])
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the message buffer for current session."""
        return self._message_buffer.copy()
    
    def clear_session(self) -> None:
        """Clear the current session buffer (not Memphora storage)."""
        self._message_buffer = []


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "MemphoraLangChain",
    "MemphoraLlamaIndex",
    "MemphoraCrewAI",
    "MemphoraAgentMemory",
    "MemphoraAutoGen",
]
