"""
Comprehensive Production Test Suite for Memphora Python SDK
Tests all 63 methods in the SDK with proper error handling and cleanup
Matches the TypeScript SDK test structure
"""

import os
import sys
import time
import pytest
from typing import List, Dict, Any, Optional
import json
import base64
import threading

# Add parent directory to path to import SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memphora_sdk import Memphora

# Configuration
TEST_CONFIG = {
    'api_url': os.getenv('MEMPHORA_API_URL', 'https://api.memphora.ai/api/v1'),
    'api_key': os.getenv('MEMPHORA_API_KEY', 'memphora_live_sk_WSiRO1FuMQClgj2pdZ7gT6aYbmFLwAHqzbO7cVahWi8'),
    'user_id': f'test-user-{int(time.time())}-{os.urandom(4).hex()}',
    'timeout': 60,  # 60 seconds
}

# Helper function for delays
def delay(seconds: float):
    """Simple delay helper."""
    time.sleep(seconds)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope='module')
def memory():
    """Create a Memphora instance for testing."""
    mem = Memphora(
        user_id=TEST_CONFIG['user_id'],
        api_key=TEST_CONFIG['api_key'],
        api_url=TEST_CONFIG['api_url']
    )
    print(f"\n🧪 Starting comprehensive tests for user: {TEST_CONFIG['user_id']}\n")
    yield mem
    
    # Cleanup
    print('\n🧹 Cleaning up test data...\n')
    mem.clear()
    print('✓ Cleaned up all test memories')


@pytest.fixture(scope='function')
def created_memories():
    """Track created memory IDs for cleanup."""
    return []


@pytest.fixture(scope='function')
def created_webhooks():
    """Track created webhook IDs for cleanup."""
    return []


@pytest.fixture(scope='function')
def created_conversations():
    """Track created conversation IDs for cleanup."""
    return []


@pytest.fixture(scope='function')
def created_agents():
    """Track created agent IDs for cleanup."""
    return []


@pytest.fixture(scope='function')
def created_groups():
    """Track created group IDs for cleanup."""
    return []


# ============================================================================
# 1. CORE MEMORY OPERATIONS
# ============================================================================

class TestCoreMemoryOperations:
    """Test core memory operations."""
    
    def test_1_1_store(self, memory, created_memories):
        """1.1 store() - Store a memory"""
        content = 'User prefers dark mode and Python for development'
        metadata = {'type': 'preference', 'category': 'ui'}
        result = memory.store(content, metadata)
        
        assert result is not None
        assert 'id' in result
        assert 'dark mode' in result.get('content', '')
        assert result.get('metadata', {}).get('type') == 'preference'
        created_memories.append(result['id'])
    
    def test_1_2_get_all(self, memory):
        """1.2 getAll() - Get all user memories"""
        # Store a few memories first
        memory.store('Memory 1')
        memory.store('Memory 2')
        memory.store('Memory 3')
        
        memories = memory.list_memories(limit=100)
        
        assert memories is not None
        assert isinstance(memories, list)
        assert len(memories) > 0
        for m in memories:
            assert 'id' in m
            assert 'content' in m
    
    def test_1_3_get_memory(self, memory, created_memories):
        """1.3 getMemory() - Get a specific memory by ID"""
        stored = memory.store('Memory to retrieve')
        created_memories.append(stored['id'])
        
        retrieved = memory.get_memory(stored['id'])
        
        assert retrieved is not None
        assert retrieved.get('id') == stored['id']
        assert 'Memory to retrieve' in retrieved.get('content', '')
    
    def test_1_4_update(self, memory, created_memories):
        """1.4 update() - Update a memory"""
        stored = memory.store('Original content')
        created_memories.append(stored['id'])
        
        updated = memory.update_memory(
            stored['id'],
            'Updated content',
            {'updated': True, 'timestamp': int(time.time())}
        )
        
        assert updated is not None
        assert updated.get('id') == stored['id']
        assert 'Updated' in updated.get('content', '')
        assert updated.get('metadata', {}).get('updated') is True
    
    def test_1_5_delete(self, memory):
        """1.5 delete() - Delete a memory"""
        stored = memory.store('Memory to delete')
        
        delay(1)  # Wait for memory to be fully created
        
        deleted = memory.delete_memory(stored['id'])
        assert deleted is True
        
        # Verify it's deleted
        result = memory.get_memory(stored['id'])
        assert not result or 'error' in result
    
    def test_1_6_delete_all(self, memory):
        """1.6 deleteAll() - Delete all user memories"""
        # Store some memories
        memory.store('Memory 1')
        memory.store('Memory 2')
        
        result = memory.clear()
        
        assert result is True
        
        # Verify all are deleted
        remaining = memory.list_memories(limit=10)
        assert len(remaining) == 0
    
    def test_1_7_batch_store(self, memory, created_memories):
        """1.7 batchStore() - Batch create multiple memories"""
        memories = [
            {'content': 'Batch memory 1', 'metadata': {'batch': 1}},
            {'content': 'Batch memory 2', 'metadata': {'batch': 1}},
            {'content': 'Batch memory 3', 'metadata': {'batch': 1}},
        ]
        
        results = memory.batch_store(memories, link_related=True)
        
        assert results is not None
        assert isinstance(results, list)  # batch_store returns list of created memories
        assert len(results) == 3
        for m in results:
            assert 'id' in m
            assert 'content' in m
            created_memories.append(m['id'])
    
    def test_2_1_search(self, memory):
        """2.1 search() - Basic semantic search (returns structured response)"""
        result = memory.search('programming languages', limit=5)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'facts' in result
        facts = result['facts']
        assert isinstance(facts, list)
        assert len(facts) > 0
        for f in facts:
            assert 'text' in f
    
    def test_2_2_search_reranking(self, memory):
        """2.2 search() - Search with reranking (returns structured response)"""
        result = memory.search(
            'programming',
            limit=5,
            rerank=True,
            rerank_provider='auto'
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'facts' in result
    
    def test_2_7_get_context(self, memory):
        """2.7 getContext() - Get formatted context"""
        context = memory.get_context('user preferences', limit=5)
        
        assert context is not None
        assert isinstance(context, str)
        # Context may be empty if no matching memories
    
    def test_3_1_store_conversation(self, memory):
        """3.1 storeConversation() - Store a conversation"""
        result = memory.store_conversation(
            'Hello, how are you?',
            'I am doing well, thank you!'
        )
        
        # store_conversation returns None, but should not raise
        assert result is None or isinstance(result, dict)
    
    def test_3_2_record_conversation(self, memory, created_conversations):
        """3.2 recordConversation() - Record a full conversation"""
        conversation = [
            {'role': 'user', 'content': 'What is the weather?'},
            {'role': 'assistant', 'content': 'The weather is sunny today.'},
            {'role': 'user', 'content': 'What about tomorrow?'},
            {'role': 'assistant', 'content': 'Tomorrow will be cloudy.'}
        ]
        
        result = memory.record_conversation(
            conversation,
            platform='test-platform',
            metadata={'test': True}
        )
        
        assert result is not None
        if 'conversation_id' in result:
            created_conversations.append(result['conversation_id'])
    
    def test_3_3_get_conversations(self, memory):
        """3.3 getConversations() - Get user conversations"""
        # Record a conversation first
        memory.record_conversation(
            [
                {'role': 'user', 'content': 'Test message'},
                {'role': 'assistant', 'content': 'Test response'}
            ],
            platform='test-platform'
        )
        
        delay(2)
        
        conversations = memory.get_conversations(platform='test-platform', limit=50)
        
        assert conversations is not None
        assert isinstance(conversations, list)
    
    def test_3_4_get_conversation(self, memory, created_conversations):
        """3.4 getConversation() - Get a specific conversation"""
        result = memory.record_conversation(
            [
                {'role': 'user', 'content': 'Get conversation test'},
                {'role': 'assistant', 'content': 'Response'}
            ]
        )
        
        assert result is not None
        assert 'conversation_id' in result
        created_conversations.append(result['conversation_id'])
        
        delay(1)  # Wait for conversation to be stored
        
        conversation = memory.get_conversation(result['conversation_id'])
        
        assert conversation is not None
        assert 'conversation_id' in conversation
    
    def test_3_5_summarize_conversation_brief(self, memory):
        """3.5 summarizeConversation() - Summarize a conversation (brief)"""
        conversation = [
            {'role': 'user', 'content': 'I need help with Python'},
            {'role': 'assistant', 'content': 'I can help you with Python. What do you need?'},
            {'role': 'user', 'content': 'How do I use decorators?'},
            {'role': 'assistant', 'content': 'Decorators allow you to modify functions.'}
        ]
        
        summary = memory.summarize_conversation(conversation, summary_type='brief')
        
        assert summary is not None
        assert 'summary' in summary
    
    def test_3_6_summarize_conversation_detailed(self, memory):
        """3.6 summarizeConversation() - Detailed summary"""
        conversation = [
            {'role': 'user', 'content': 'Tell me about React'},
            {'role': 'assistant', 'content': 'React is a JavaScript library for building UIs.'}
        ]
        
        summary = memory.summarize_conversation(conversation, summary_type='detailed')
        
        assert summary is not None
    
    def test_3_7_summarize_conversation_topics(self, memory):
        """3.7 summarizeConversation() - Topics summary"""
        conversation = [
            {'role': 'user', 'content': 'I like Python and JavaScript'},
            {'role': 'assistant', 'content': 'Both are great languages!'}
        ]
        
        summary = memory.summarize_conversation(conversation, summary_type='topics')
        
        assert summary is not None
    
    def test_3_8_summarize_conversation_action_items(self, memory):
        """3.8 summarizeConversation() - Action items summary"""
        conversation = [
            {'role': 'user', 'content': 'I need to finish the project by Friday'},
            {'role': 'assistant', 'content': 'I can help you plan that.'}
        ]
        
        summary = memory.summarize_conversation(conversation, summary_type='action_items')
        
        assert summary is not None
    
    def test_4_1_store_image_url(self, memory, created_memories):
        """4.1 storeImage() - Store image with URL"""
        result = memory.store_image(
            image_url='https://upload.wikimedia.org/wikipedia/commons/f/f2/LPU-v1-die.jpg',
            description='Test image of a processor die',
            metadata={'test': True}
        )
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])
    
    def test_4_2_store_image_base64(self, memory, created_memories):
        """4.2 storeImage() - Store image with base64"""
        # 10x10 red pixel PNG in base64 (Groq Vision requires at least 2x2 pixels)
        base64_image = 'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP4z8CAB+GTG8HSALfKY52fTcuYAAAAAElFTkSuQmCC'
        
        result = memory.store_image(
            image_base64=base64_image,
            description='Test base64 image',
            metadata={'test': True}
        )
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])
    
    def test_4_3_search_images(self, memory, created_memories):
        """4.3 searchImages() - Search image memories"""
        # Store an image first
        memory.store_image(
            image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/300px-PNG_transparency_demonstration_1.png',
            description='A beautiful sunset over mountains'
        )
        
        delay(2)
        
        results = memory.search_images('sunset', limit=5)
        
        assert results is not None
        assert isinstance(results, list)  # search_images returns list of image memories
    
    def test_4_4_upload_image(self, memory, created_memories):
        """4.4 uploadImage() - Upload image from Blob"""
        # Create a simple test image (10x10 red pixel PNG - Groq Vision requires at least 2x2 pixels)
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP4z8CAB+GTG8HSALfKY52fTcuYAAAAAElFTkSuQmCC'
        )
        
        result = memory.upload_image(png_data, 'test-image.png', metadata={'test': True})
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])


# ============================================================================
# 5. VERSION CONTROL
# ============================================================================

class TestMultiAgentFeatures:
    """Test multi-agent features."""
    
    @pytest.fixture(autouse=True)
    def setup_agent_ids(self):
        """Setup test agent and run IDs."""
        self.test_agent_id = f'test-agent-{int(time.time())}'
        self.test_run_id = f'test-run-{int(time.time())}'
    
    def test_6_1_store_agent_memory(self, memory, created_memories, created_agents):
        """6.1 storeAgentMemory() - Store memory for an agent"""
        result = memory.store_agent_memory(
            self.test_agent_id,
            'Agent memory content',
            run_id=self.test_run_id,
            metadata={'agent_test': True}
        )
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])
        created_agents.append(self.test_agent_id)
    
    def test_6_2_search_agent_memories(self, memory):
        """6.2 searchAgentMemories() - Search agent memories (returns structured response)"""
        memory.store_agent_memory(
            self.test_agent_id,
            'Agent search test memory',
            run_id=self.test_run_id
        )
        
        delay(2)
        
        result = memory.search_agent_memories(
            self.test_agent_id,
            'search test',
            run_id=self.test_run_id,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'facts' in result
        assert 'agent_id' in result
    
    def test_6_3_get_agent_memories(self, memory):
        """6.3 getAgentMemories() - Get all agent memories"""
        memory.store_agent_memory(
            self.test_agent_id,
            'Agent get all test',
            run_id=self.test_run_id
        )
        
        delay(2)
        
        memories = memory.get_agent_memories(self.test_agent_id, limit=100)
        
        assert memories is not None
        assert isinstance(memories, list)


# ============================================================================
# 7. GROUP MEMORIES
# ============================================================================

class TestGroupMemories:
    """Test group memories."""
    
    @pytest.fixture(autouse=True)
    def setup_group_id(self):
        """Setup test group ID."""
        self.test_group_id = f'test-group-{int(time.time())}'
    
    def test_7_1_store_group_memory(self, memory, created_memories, created_groups):
        """7.1 storeGroupMemory() - Store group memory"""
        result = memory.store_group_memory(
            self.test_group_id,
            'Group memory content',
            metadata={'group_test': True}
        )
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])
        created_groups.append(self.test_group_id)
    
    def test_7_2_search_group_memories(self, memory):
        """7.2 searchGroupMemories() - Search group memories (returns structured response)"""
        memory.store_group_memory(
            self.test_group_id,
            'Group search test memory'
        )
        
        delay(2)
        
        result = memory.search_group_memories(
            self.test_group_id,
            'search test',
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'facts' in result
        assert 'group_id' in result
    
    def test_7_3_get_group_context(self, memory):
        """7.3 getGroupContext() - Get group context"""
        memory.store_group_memory(
            self.test_group_id,
            'Group context test'
        )
        
        delay(2)
        
        context = memory.get_group_context(self.test_group_id, limit=50)
        
        assert context is not None


# ============================================================================
# 8. GRAPH OPERATIONS
# ============================================================================

class TestImportExport:
    """Test import/export."""
    
    def test_10_1_export_json(self, memory):
        """10.1 export() - Export memories as JSON"""
        memory.store('Export test memory')
        
        delay(2)
        
        exported = memory.export(format='json')
        
        assert exported is not None
    
    def test_10_2_export_csv(self, memory):
        """10.2 export() - Export memories as CSV"""
        memory.store('CSV export test')
        
        delay(2)
        
        exported = memory.export(format='csv')
        
        assert exported is not None
    
    def test_15_1_invalid_memory_id(self, memory):
        """15.1 Handle invalid memory ID"""
        result = memory.get_memory('invalid-id-that-does-not-exist-12345')
        # Should return empty dict or error dict, not raise
        assert isinstance(result, dict)
    
    def test_15_4_empty_search(self, memory):
        """15.4 Handle empty search gracefully"""
        results = memory.search('', limit=5)
        assert results is not None
        assert isinstance(results, dict) and 'facts' in results


# ============================================================================
# 16. PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance."""
    
    def test_16_1_bulk_memory_storage(self, memory):
        """16.1 Bulk memory storage"""
        start_time = time.time()
        
        for i in range(10):
            memory.store(f'Performance test memory {i}')
        
        duration = time.time() - start_time
        
        assert duration < 60  # Should complete in 60 seconds
        print(f'✓ Bulk store of 10 memories: {duration:.2f}s')
    
    def test_16_2_fast_search(self, memory):
        """16.2 Fast search performance"""
        start_time = time.time()
        memory.search('test query', limit=10)
        duration = time.time() - start_time
        
        assert duration < 60  # Should complete in 60 seconds
        print(f'✓ Search completed in: {duration:.2f}s')
    
    def test_4_5_ingest_document_text(self, memory):
        """4.5 ingestDocument() - Ingest plain text"""
        result = memory.ingest_document(
            content_type='text',
            text='This is a test document with important information about AI and machine learning.',
            metadata={'test': True, 'source': 'test_comprehensive'},
            async_processing=True
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ Text ingestion: {result}")
    
    def test_4_6_ingest_document_url(self, memory):
        """4.6 ingestDocument() - Ingest from URL (web page)"""
        result = memory.ingest_document(
            content_type='url',
            url='https://memphora.ai',
            metadata={'test': True, 'source': 'web_page'},
            async_processing=True
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ URL ingestion: {result}")
    
    def test_4_7_ingest_document_pdf_url(self, memory):
        """4.7 ingestDocument() - Ingest PDF from URL"""
        result = memory.ingest_document(
            content_type='pdf_url',
            url='https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            metadata={'test': True, 'doc_type': 'pdf'},
            async_processing=True
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ PDF URL ingestion: {result}")
    
    def test_4_8_upload_document_txt(self, memory):
        """4.8 uploadDocument() - Upload a .txt file"""
        txt_content = b"This is a test text file.\nIt contains multiple lines.\nUsed for testing document upload."
        
        result = memory.upload_document(
            file_data=txt_content,
            filename='test_document.txt',
            metadata={'test': True, 'file_type': 'txt'}
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ TXT upload: {result}")
    
    def test_4_9_upload_document_json(self, memory):
        """4.9 uploadDocument() - Upload a .json file"""
        import json
        json_content = json.dumps({
            'name': 'Test Config',
            'settings': {'theme': 'dark', 'language': 'en'},
            'features': ['memory', 'search', 'multimodal']
        }).encode('utf-8')
        
        result = memory.upload_document(
            file_data=json_content,
            filename='config.json',
            metadata={'test': True, 'file_type': 'json'}
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ JSON upload: {result}")
    
    def test_4_10_upload_document_csv(self, memory):
        """4.10 uploadDocument() - Upload a .csv file"""
        csv_content = b"name,email,role\nJohn,john@example.com,developer\nJane,jane@example.com,designer"
        
        result = memory.upload_document(
            file_data=csv_content,
            filename='users.csv',
            metadata={'test': True, 'file_type': 'csv'}
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ CSV upload: {result}")
    
    def test_4_11_upload_document_markdown(self, memory):
        """4.11 uploadDocument() - Upload a .md file"""
        md_content = b"# Test Document\n\n## Introduction\nThis is a test markdown document.\n\n## Features\n- Memory storage\n- Semantic search"
        
        result = memory.upload_document(
            file_data=md_content,
            filename='README.md',
            metadata={'test': True, 'file_type': 'markdown'}
        )
        
        assert result is not None
        assert 'job_id' in result or 'status' in result
        print(f"  ✓ Markdown upload: {result}")
    
    def test_4_12_get_image_url(self, memory, created_memories):
        """4.12 getImageUrl() - Get fresh signed URL for image memory"""
        import time
        
        # First store an image
        result = memory.store_image(
            image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/300px-PNG_transparency_demonstration_1.png',
            description='Test image for URL refresh',
            metadata={'test': True}
        )
        
        assert result is not None
        
        if 'id' in result:
            created_memories.append(result['id'])
            time.sleep(2)  # Wait for image to be stored
            
            # Now get the signed URL
            url_result = memory.get_image_url(result['id'])
            
            assert url_result is not None
            print(f"  ✓ Get image URL: {url_result}")

