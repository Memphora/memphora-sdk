# Memphora SDK

[![PyPI version](https://badge.fury.io/py/memphora.svg)](https://badge.fury.io/py/memphora)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Memphora SDK** - A simple, powerful Python SDK for adding persistent memory to your AI applications. Give your AI agents the ability to remember past conversations, learn from interactions, and provide context-aware responses.

## 🚀 Quick Start

### Installation

```bash
pip install memphora
```

### Basic Usage

```python
from memphora_sdk import Memphora

# Initialize with your user ID and API key
memory = Memphora(
    user_id="user123",
    api_key="your_api_key_here"  # Get from https://memphora.ai/dashboard
)

# Store a memory
memory.store("I love Python programming and machine learning")

# Search memories
results = memory.search("What do I love?")
for mem in results:
    print(f"- {mem['content']}")
```

## 📚 Documentation

**Full documentation:** [https://memphora.ai/docs](https://memphora.ai/docs)

For detailed API reference, examples, and integration guides, visit our [documentation site](https://memphora.ai/docs).

## ✨ Features

- **🔍 Semantic Search** - Find relevant memories using natural language queries
- **💾 Automatic Memory Extraction** - Automatically extract and store important information from conversations
- **🎯 Context-Aware Responses** - Get relevant context for any query
- **🔗 Easy Integration** - Works with OpenAI, Anthropic, LangChain, LlamaIndex, and more
- **⚡ Simple API** - Clean, intuitive interface that's easy to use
- **🚀 Production Ready** - Built for scale with automatic compression and optimization

## 📖 Examples

### Example 1: Simple Memory Storage

```python
from memphora_sdk import Memphora

memory = Memphora(user_id="user123", api_key="your_api_key")

# Store memories
memory.store("I work as a software engineer at Google")
memory.store("I have 5 years of Python experience")
memory.store("I'm learning machine learning")

# Search for relevant memories
results = memory.search("What's my job?")
# Returns: [{"content": "I work as a software engineer at Google", ...}]
```

### Example 2: Auto-Remember Decorator

```python
from memphora_sdk import Memphora

memory = Memphora(user_id="user123", api_key="your_api_key")

@memory.remember
def chat(user_message: str, memory_context: str = "") -> str:
    """
    Chat function with automatic memory integration.
    The decorator automatically:
    1. Searches for relevant memories
    2. Passes them as memory_context
    3. Stores the conversation after response
    """
    # Use memory_context in your prompt
    prompt = f"""Context from past conversations:
{memory_context}

User: {user_message}
Assistant:"""
    
    # Your AI logic here
    response = your_ai_model(prompt)
    return response

# Just call it normally - memory handling is automatic!
response = chat("What are my interests?")
```

### Example 3: OpenAI Integration

```python
from memphora_sdk import Memphora
from openai import OpenAI

memory = Memphora(user_id="user123", api_key="your_api_key")
openai_client = OpenAI()

def chat_with_memory(user_message: str) -> str:
    # Get relevant context automatically
    context = memory.get_context(user_message, limit=5)
    
    # Add context to your prompt
    messages = [
        {"role": "system", "content": f"Relevant context: {context}"},
        {"role": "user", "content": user_message}
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    ai_response = response.choices[0].message.content
    
    # Store conversation automatically
    memory.store_conversation(user_message, ai_response)
    
    return ai_response
```

### Example 4: LangChain Integration

```python
from memphora_sdk import Memphora
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Create Memphora memory adapter for LangChain
memory = Memphora(user_id="user123", api_key="your_api_key")

# Use with LangChain
llm = ChatOpenAI(model="gpt-4")

def get_langchain_memory():
    """Convert Memphora memory to LangChain format."""
    from langchain.memory import ConversationBufferMemory
    
    class MemphoraMemory(ConversationBufferMemory):
        def load_memory_variables(self, inputs):
            query = inputs.get("input", "")
            context = memory.get_context(query)
            return {"history": context}
        
        def save_context(self, inputs, outputs):
            user_msg = inputs.get("input", "")
            ai_msg = outputs.get("output", "")
            memory.store_conversation(user_msg, ai_msg)
    
    return MemphoraMemory()

chain = ConversationChain(llm=llm, memory=get_langchain_memory())
response = chain.run("What are my interests?")
```

## 🔑 Getting Your API Key

1. **Sign up** at [https://memphora.ai/signup](https://memphora.ai/signup)
2. **Get your API key** from the dashboard: [https://memphora.ai/dashboard/api](https://memphora.ai/dashboard/api)
3. **Start using** the SDK!

## 📋 API Reference

### Memphora Class

#### Initialization

```python
Memphora(
    user_id: str,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    auto_compress: bool = True,
    max_tokens: int = 500
)
```

**Parameters:**
- `user_id` (str): Your unique user identifier
- `api_key` (str, optional): Your API key from the dashboard
- `api_url` (str, optional): Custom API URL (defaults to production API)
- `auto_compress` (bool): Automatically compress context (default: True)
- `max_tokens` (int): Maximum tokens for context (default: 500)

#### Methods

##### `store(content: str, metadata: Optional[Dict] = None) -> Dict`

Store a memory. Automatically processes and optimizes content for better retrieval.

```python
memory.store("I love Python", metadata={"category": "preference"})
```

##### `search(query: str, limit: int = 10) -> List[Dict]`

Search for relevant memories using semantic search.

```python
results = memory.search("What do I love?", limit=5)
```

##### `get_context(query: str, limit: int = 5) -> str`

Get formatted context string for a query.

```python
context = memory.get_context("What are my interests?")
```

##### `store_conversation(user_message: str, ai_response: str) -> None`

Store a conversation for automatic memory extraction.

```python
memory.store_conversation("Hello", "Hi! How can I help?")
```

##### `@remember` Decorator

Automatically handle memory for function calls.

```python
@memory.remember
def my_function(user_input: str, memory_context: str = "") -> str:
    # memory_context is automatically populated
    return process(user_input, memory_context)
```

##### `clear() -> bool`

Clear all memories for this user.

```python
memory.clear()
```

##### `get_memory(memory_id: str) -> Dict`

Get a specific memory by ID.

##### `update_memory(memory_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict`

Update an existing memory.

##### `delete_memory(memory_id: str) -> bool`

Delete a specific memory.

##### `list_memories(limit: int = 100) -> List[Dict]`

List all memories for this user.

## 🔧 Configuration

### Environment Variables

You can set these environment variables instead of passing parameters:

```bash
export MEMPHORA_USER_ID="user123"
export MEMPHORA_API_KEY="your_api_key"
export MEMPHORA_API_URL="https://api.memphora.ai/api/v1"  # Optional
```

Then initialize without parameters:

```python
from memphora_sdk import Memphora
import os

memory = Memphora(
    user_id=os.getenv("MEMPHORA_USER_ID"),
    api_key=os.getenv("MEMPHORA_API_KEY")
)
```

## 🎯 Use Cases

- **AI Chatbots** - Give your chatbot persistent memory across conversations
- **Virtual Assistants** - Remember user preferences and past interactions
- **Customer Support** - Maintain context across support sessions
- **Educational Platforms** - Track learning progress and preferences
- **Enterprise AI** - Build context-aware AI applications
- **Developer Tools** - Remember IDE settings and workflow patterns

## 🔗 Integrations

Memphora works seamlessly with:

- **OpenAI** - GPT-4, GPT-3.5, and other OpenAI models
- **Anthropic** - Claude models
- **LangChain** - Full LangChain compatibility
- **LlamaIndex** - LlamaIndex memory integration
- **Custom LLMs** - Works with any AI model

## 📦 Requirements

- Python 3.8+
- `requests>=2.31.0`
- `urllib3>=2.1.0`

## 🚀 Installation Options

### From PyPI (Recommended)

```bash
pip install memphora
```

### From Source

```bash
git clone https://github.com/memphora/memphora.git
cd memphora/sdk
pip install -e .
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- **Documentation:** [https://memphora.ai/docs](https://memphora.ai/docs)
- **Issues:** [GitHub Issues](https://github.com/memphora/memphora/issues)

## 🌟 Features in Detail

### Semantic Search
Find relevant memories using natural language. No need for exact keyword matches.

### Automatic Memory Extraction
Memphora automatically extracts important information from conversations, so you don't have to manually identify what to remember.

### Context Compression
Automatically compresses and optimizes context to stay within token limits while preserving important information.

### Metadata Filtering
Store and filter memories using custom metadata for advanced use cases.

### Production Ready
Built for scale with automatic retries, connection pooling, and error handling.

## 📊 Example Output

```python
# Store a memory
memory.store("I work at Google as a software engineer")

# Search
results = memory.search("Where do I work?")
# Output:
# [
#   {
#     "id": "mem_123",
#     "content": "I work at Google as a software engineer",
#     "metadata": {},
#     "created_at": "2025-11-08T01:00:00Z",
#     "relevance_score": 0.95
#   }
# ]

# Get context
context = memory.get_context("Tell me about my job")
# Output:
# "Relevant context from past conversations:
# - I work at Google as a software engineer"
```

## 🔄 Migration Guide

If you're upgrading from an older version, see our [Migration Guide](https://memphora.ai/docs/migration) in the documentation.

## 🎓 Learn More

- **Quick Start Guide:** [https://memphora.ai/docs/quickstart](https://memphora.ai/docs/quickstart)
- **API Reference:** [https://memphora.ai/docs/api](https://memphora.ai/docs/api)
- **Examples:** [https://memphora.ai/docs/examples](https://memphora.ai/docs/examples)
- **Best Practices:** [https://memphora.ai/docs/best-practices](https://memphora.ai/docs/best-practices)

---

**Made with ❤️ by the Memphora team**

For more information, visit [https://memphora.ai](https://memphora.ai)

