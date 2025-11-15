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
    'api_key': os.getenv('MEMPHORA_API_KEY', 'memphora_live_sk_a4effdDKP4V2aa2smWrq1rSsB_YxxNhOSkA9DWcK48A'),
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
        assert isinstance(results, list)
        assert len(results) == 3
        for m in results:
            assert 'id' in m
            assert 'content' in m
            created_memories.append(m['id'])
    
    def test_1_8_merge(self, memory, created_memories):
        """1.8 merge() - Merge multiple memories"""
        mem1 = memory.store('User likes coffee')
        mem2 = memory.store('User prefers espresso')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        merged = memory.merge([mem1['id'], mem2['id']], 'combine')
        
        assert merged is not None
        assert 'id' in merged
        assert 'content' in merged
    
    def test_1_9_merge_keep_latest(self, memory, created_memories):
        """1.9 merge() - Merge with keep_latest strategy"""
        mem1 = memory.store('Old information')
        mem2 = memory.store('New information')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        merged = memory.merge([mem1['id'], mem2['id']], 'keep_latest')
        
        assert merged is not None
        assert 'id' in merged
    
    def test_1_10_merge_keep_most_relevant(self, memory, created_memories):
        """1.10 merge() - Merge with keep_most_relevant strategy"""
        mem1 = memory.store('Relevant information about Python')
        mem2 = memory.store('Less relevant information')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        merged = memory.merge([mem1['id'], mem2['id']], 'keep_most_relevant')
        
        assert merged is not None
        assert 'id' in merged


# ============================================================================
# 2. SEARCH OPERATIONS
# ============================================================================

class TestSearchOperations:
    """Test search operations."""
    
    @pytest.fixture(autouse=True)
    def setup_search_data(self, memory):
        """Setup test data for search tests."""
        memory.store('User loves Python programming')
        memory.store('User prefers React for frontend development')
        memory.store('User uses VS Code as editor')
        memory.store('Machine learning models need training data')
        memory.store('Neural networks use backpropagation')
        
        # Wait for indexing
        delay(3)
    
    def test_2_1_search(self, memory):
        """2.1 search() - Basic semantic search"""
        results = memory.search('programming languages', limit=5)
        
        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert 'id' in r
            assert 'content' in r
            assert 'similarity' in r or 'score' in r
    
    def test_2_2_search_reranking(self, memory):
        """2.2 search() - Search with reranking"""
        results = memory.search(
            'programming',
            limit=5,
            rerank=True,
            rerank_provider='auto'
        )
        
        assert results is not None
        assert isinstance(results, list)
    
    def test_2_3_search_advanced(self, memory):
        """2.3 searchAdvanced() - Advanced search with filters"""
        memory.store('Important project deadline', metadata={
            'priority': 'high',
            'type': 'task'
        })
        
        delay(2)
        
        results = memory.search_advanced(
            'deadline',
            limit=5,
            min_score=0.3,
            sort_by='relevance'
        )
        
        assert results is not None
        assert isinstance(results, list)
    
    def test_2_4_search_advanced_related(self, memory):
        """2.4 searchAdvanced() - Search with include_related"""
        results = memory.search_advanced(
            'programming',
            limit=5,
            include_related=True
        )
        
        assert results is not None
        assert isinstance(results, list)
    
    def test_2_5_search_optimized(self, memory):
        """2.5 searchOptimized() - Optimized search"""
        result = memory.search_optimized(
            'programming',
            max_tokens=1000,
            max_memories=10,
            use_compression=True,
            use_cache=True
        )
        
        assert result is not None
        assert 'context' in result
        assert isinstance(result['context'], str)
    
    def test_2_6_search_enhanced(self, memory):
        """2.6 searchEnhanced() - Enhanced search"""
        result = memory.search_enhanced(
            'programming',
            max_tokens=1500,
            max_memories=15,
            use_compression=True
        )
        
        assert result is not None
        assert 'context' in result
        assert isinstance(result['context'], str)
    
    def test_2_7_get_context(self, memory):
        """2.7 getContext() - Get formatted context"""
        context = memory.get_context('user preferences', limit=5)
        
        assert context is not None
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_2_8_get_optimized_context(self, memory):
        """2.8 getOptimizedContext() - Get optimized context"""
        context = memory.get_optimized_context(
            'programming languages',
            max_tokens=2000,
            max_memories=20,
            use_compression=True,
            use_cache=True
        )
        
        assert context is not None
        assert isinstance(context, str)
    
    def test_2_9_get_enhanced_context(self, memory):
        """2.9 getEnhancedContext() - Get enhanced context"""
        context = memory.get_enhanced_context(
            'programming languages',
            max_tokens=1500,
            max_memories=15,
            use_compression=True
        )
        
        assert context is not None
        assert isinstance(context, str)
    
    def test_2_10_find_contradictions(self, memory, created_memories):
        """2.10 findContradictions() - Find contradictory memories"""
        mem1 = memory.store('User prefers light theme')
        created_memories.append(mem1['id'])
        
        delay(2)
        
        contradictions = memory.find_contradictions(mem1['id'], threshold=0.7)
        
        assert contradictions is not None
        assert isinstance(contradictions, list)
    
    def test_2_11_get_related_memories(self, memory, created_memories):
        """2.11 getRelatedMemories() - Get related memories"""
        mem1 = memory.store('User likes Python')
        created_memories.append(mem1['id'])
        
        delay(2)
        
        related = memory.get_related_memories(mem1['id'], limit=10)
        
        assert related is not None
        assert isinstance(related, list)
    
    def test_2_12_get_context_for_memory(self, memory, created_memories):
        """2.12 getContextForMemory() - Get context for a memory"""
        mem1 = memory.store('Context test memory')
        created_memories.append(mem1['id'])
        
        delay(2)
        
        context = memory.get_context_for_memory(mem1['id'], depth=2)
        
        assert context is not None


# ============================================================================
# 3. CONVERSATION MANAGEMENT
# ============================================================================

class TestConversationManagement:
    """Test conversation management."""
    
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
    
    def test_3_9_get_summary(self, memory):
        """3.9 getSummary() - Get rolling summary"""
        # Record some conversations first
        memory.record_conversation([
            {'role': 'user', 'content': 'Summary test 1'},
            {'role': 'assistant', 'content': 'Response 1'}
        ])
        
        delay(2)
        
        summary = memory.get_summary()
        
        assert summary is not None


# ============================================================================
# 4. MULTIMODAL FEATURES
# ============================================================================

class TestMultimodalFeatures:
    """Test multimodal features."""
    
    def test_4_1_store_image_url(self, memory, created_memories):
        """4.1 storeImage() - Store image with URL"""
        result = memory.store_image(
            image_url='https://via.placeholder.com/150',
            description='Test placeholder image',
            metadata={'test': True}
        )
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])
    
    def test_4_2_store_image_base64(self, memory, created_memories):
        """4.2 storeImage() - Store image with base64"""
        # Small 1x1 blue pixel PNG in base64
        base64_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        
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
            image_url='https://via.placeholder.com/150',
            description='A beautiful sunset over mountains'
        )
        
        delay(2)
        
        results = memory.search_images('sunset', limit=5)
        
        assert results is not None
        assert isinstance(results, list)
    
    def test_4_4_upload_image(self, memory, created_memories):
        """4.4 uploadImage() - Upload image from Blob"""
        # Create a simple test image (1x1 blue pixel PNG)
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        
        result = memory.upload_image(png_data, 'test-image.png', metadata={'test': True})
        
        assert result is not None
        if 'id' in result:
            created_memories.append(result['id'])


# ============================================================================
# 5. VERSION CONTROL
# ============================================================================

class TestVersionControl:
    """Test version control."""
    
    def test_5_1_get_versions(self, memory, created_memories):
        """5.1 getVersions() - Get memory versions"""
        stored = memory.store('Version test memory')
        created_memories.append(stored['id'])
        
        # Update it to create a version
        memory.update_memory(stored['id'], 'Updated version')
        
        delay(2)
        
        versions = memory.get_versions(stored['id'], limit=50)
        
        assert versions is not None
        assert isinstance(versions, list)
    
    def test_5_2_rollback(self, memory, created_memories):
        """5.2 rollback() - Rollback memory to a version"""
        stored = memory.store('Original version')
        created_memories.append(stored['id'])
        
        # Update it
        memory.update_memory(stored['id'], 'Updated version')
        
        delay(2)
        
        # Get versions and rollback to first version
        versions = memory.get_versions(stored['id'], limit=10)
        if versions and len(versions) > 0 and 'version' in versions[0]:
            result = memory.rollback(stored['id'], versions[0]['version'])
            assert result is not None
    
    def test_5_3_compare_versions(self, memory, created_memories):
        """5.3 compareVersions() - Compare two versions"""
        stored = memory.store('Version comparison test')
        created_memories.append(stored['id'])
        
        memory.update_memory(stored['id'], 'Updated for comparison')
        
        delay(2)
        
        versions = memory.get_versions(stored['id'], limit=10)
        assert versions is not None
        assert len(versions) >= 2
        
        comparison = memory.compare_versions(
            versions[0].get('id') or versions[0].get('version_id'),
            versions[1].get('id') or versions[1].get('version_id')
        )
        
        assert comparison is not None


# ============================================================================
# 6. MULTI-AGENT FEATURES
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
        """6.2 searchAgentMemories() - Search agent memories"""
        memory.store_agent_memory(
            self.test_agent_id,
            'Agent search test memory',
            run_id=self.test_run_id
        )
        
        delay(2)
        
        results = memory.search_agent_memories(
            self.test_agent_id,
            'search test',
            run_id=self.test_run_id,
            limit=10
        )
        
        assert results is not None
        assert isinstance(results, list)
    
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
        """7.2 searchGroupMemories() - Search group memories"""
        memory.store_group_memory(
            self.test_group_id,
            'Group search test memory'
        )
        
        delay(2)
        
        results = memory.search_group_memories(
            self.test_group_id,
            'search test',
            limit=10
        )
        
        assert results is not None
        assert isinstance(results, list)
    
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

class TestGraphOperations:
    """Test graph operations."""
    
    def test_8_1_link(self, memory, created_memories):
        """8.1 link() - Link two memories"""
        mem1 = memory.store('Memory 1 for linking')
        mem2 = memory.store('Memory 2 for linking')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        delay(2)
        
        result = memory.link(mem1['id'], mem2['id'], 'related')
        
        assert result is not None
    
    def test_8_2_link_different_relationship(self, memory, created_memories):
        """8.2 link() - Link with different relationship types"""
        mem1 = memory.store('Supports memory')
        mem2 = memory.store('Supported memory')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        delay(2)
        
        result = memory.link(mem1['id'], mem2['id'], 'supports')
        assert result is not None
    
    def test_8_3_find_path(self, memory, created_memories):
        """8.3 findPath() - Find path between memories"""
        mem1 = memory.store('Path start memory')
        mem2 = memory.store('Path end memory')
        created_memories.append(mem1['id'])
        created_memories.append(mem2['id'])
        
        delay(2)
        
        # Link them first
        memory.link(mem1['id'], mem2['id'], 'related')
        
        delay(2)
        
        path = memory.find_path(mem1['id'], mem2['id'])
        
        assert path is not None


# ============================================================================
# 9. ANALYTICS & STATISTICS
# ============================================================================

class TestAnalyticsStatistics:
    """Test analytics and statistics."""
    
    def test_9_1_get_statistics(self, memory):
        """9.1 getStatistics() - Get user statistics"""
        # Store some memories first
        memory.store('Stats test memory 1')
        memory.store('Stats test memory 2')
        
        delay(2)
        
        stats = memory.get_statistics()
        
        assert stats is not None
        assert 'total_memories' in stats
        assert isinstance(stats['total_memories'], (int, float))
    
    def test_9_2_get_user_analytics(self, memory):
        """9.2 getUserAnalytics() - Get user analytics"""
        analytics = memory.get_user_analytics()
        
        assert analytics is not None
    
    def test_9_3_get_memory_growth(self, memory):
        """9.3 getMemoryGrowth() - Get memory growth over time"""
        growth = memory.get_memory_growth(days=30)
        
        assert growth is not None


# ============================================================================
# 10. IMPORT/EXPORT
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
    
    def test_10_3_import_memories(self, memory):
        """10.3 import() - Import memories from JSON"""
        import_data = json.dumps([
            {'content': 'Imported memory 1', 'metadata': {'imported': True}},
            {'content': 'Imported memory 2', 'metadata': {'imported': True}}
        ])
        
        result = memory.import_memories(import_data, format='json')
        
        assert result is not None


# ============================================================================
# 11. WEBHOOKS
# ============================================================================

class TestWebhooks:
    """Test webhooks."""
    
    def test_11_1_create_webhook(self, memory, created_webhooks):
        """11.1 createWebhook() - Create a webhook"""
        result = memory.create_webhook(
            url='https://example.com/webhook',
            events=['memory.created', 'memory.updated'],
            secret='test-secret'
        )
        
        assert result is not None
        if 'id' in result:
            created_webhooks.append(result['id'])
    
    def test_11_2_list_webhooks(self, memory):
        """11.2 listWebhooks() - List all webhooks"""
        webhooks = memory.list_webhooks()
        
        assert webhooks is not None
        assert isinstance(webhooks, list)
    
    def test_11_3_get_webhook(self, memory, created_webhooks):
        """11.3 getWebhook() - Get a specific webhook"""
        created = memory.create_webhook(
            url='https://example.com/webhook-get',
            events=['memory.created']
        )
        
        if created and 'id' in created:
            created_webhooks.append(created['id'])
            
            webhook = memory.get_webhook(created['id'])
            
            assert webhook is not None
            assert webhook.get('id') == created['id']
    
    def test_11_4_update_webhook(self, memory, created_webhooks):
        """11.4 updateWebhook() - Update a webhook"""
        created = memory.create_webhook(
            url='https://example.com/webhook-update',
            events=['memory.created']
        )
        
        if created and 'id' in created:
            created_webhooks.append(created['id'])
            
            updated = memory.update_webhook(created['id'], url='https://example.com/webhook-updated', active=True)
            
            assert updated is not None
    
    def test_11_5_test_webhook(self, memory, created_webhooks):
        """11.5 testWebhook() - Test a webhook"""
        created = memory.create_webhook(
            url='https://example.com/webhook-test',
            events=['memory.created']
        )
        
        if created and 'id' in created:
            created_webhooks.append(created['id'])
            
            result = memory.test_webhook(created['id'])
            
            assert result is not None
    
    def test_11_6_delete_webhook(self, memory):
        """11.6 deleteWebhook() - Delete a webhook"""
        created = memory.create_webhook(
            url='https://example.com/webhook-delete',
            events=['memory.created']
        )
        
        if created and 'id' in created:
            deleted = memory.delete_webhook(created['id'])
            
            assert deleted is not None


# ============================================================================
# 12. SECURITY & COMPLIANCE
# ============================================================================

class TestSecurityCompliance:
    """Test security and compliance."""
    
    def test_12_1_export_gdpr(self, memory):
        """12.1 exportGdpr() - Export GDPR data"""
        result = memory.export_gdpr()
        
        assert result is not None
    
    def test_12_2_set_retention_policy(self, memory):
        """12.2 setRetentionPolicy() - Set retention policy"""
        result = memory.set_retention_policy(
            data_type='memories',
            retention_days=90,
            auto_delete=True
        )
        
        assert result is not None
    
    def test_12_3_apply_retention_policies(self, memory):
        """12.3 applyRetentionPolicies() - Apply retention policies"""
        result = memory.apply_retention_policies()
        
        assert result is not None
    
    def test_12_4_get_compliance_report(self, memory):
        """12.4 getComplianceReport() - Get compliance report"""
        result = memory.get_compliance_report(organization_id='test-org-id')
        assert result is not None
    
    def test_12_5_record_compliance_event(self, memory):
        """12.5 recordComplianceEvent() - Record compliance event"""
        result = memory.record_compliance_event(
            compliance_type='GDPR',
            event_type='data_access',
            details={'test': True, 'description': 'Test compliance event'}
        )
        
        assert result is not None
    
    def test_12_6_encrypt_data(self, memory):
        """12.6 encryptData() - Encrypt data"""
        result = memory.encrypt_data(data='sensitive data to encrypt')
        
        assert result is not None
        assert 'encrypted_data' in result or 'encrypted' in result
    
    def test_12_7_decrypt_data(self, memory):
        """12.7 decryptData() - Decrypt data"""
        # First encrypt
        encrypted = memory.encrypt_data(data='data to decrypt')
        
        assert encrypted is not None
        assert 'encrypted_data' in encrypted or 'encrypted' in encrypted
        
        encrypted_value = encrypted.get('encrypted_data') or encrypted.get('encrypted')
        decrypted = memory.decrypt_data(encrypted_data=encrypted_value)
        
        assert decrypted is not None
        assert 'decrypted_data' in decrypted or 'decrypted' in decrypted


# ============================================================================
# 13. OBSERVABILITY
# ============================================================================

class TestObservability:
    """Test observability."""
    
    def test_13_1_get_metrics(self, memory):
        """13.1 getMetrics() - Get metrics"""
        metrics = memory.get_metrics()
        
        assert metrics is not None
    
    def test_13_2_get_metrics_summary(self, memory):
        """13.2 getMetricsSummary() - Get metrics summary"""
        summary = memory.get_metrics_summary()
        
        assert summary is not None
    
    def test_13_3_get_audit_logs(self, memory):
        """13.3 getAuditLogs() - Get audit logs"""
        logs = memory.get_audit_logs(limit=50)
        
        assert logs is not None
        assert isinstance(logs, list)


# ============================================================================
# 14. UTILITY METHODS
# ============================================================================

class TestUtilityMethods:
    """Test utility methods."""
    
    def test_14_1_concise(self, memory):
        """14.1 concise() - Make text concise"""
        long_text = 'This is a very long text that needs to be made more concise and shorter for better readability and understanding.'
        
        result = memory.concise(long_text)
        
        assert result is not None
        assert 'concise' in result
        assert isinstance(result['concise'], str)
        assert 'original' in result
        assert 'original_length' in result
        assert 'concise_length' in result
    
    def test_14_2_health(self, memory):
        """14.2 health() - Check API health"""
        health = memory.health()
        
        assert health is not None
        assert 'status' in health
    
    def test_14_3_remember_decorator(self, memory):
        """14.3 remember() - Remember decorator"""
        @memory.remember
        def test_function(message: str, **kwargs) -> str:
            # kwargs may contain 'memory_context' from the decorator
            return f'Response to: {message}'
        
        result = test_function('Hello')
        
        assert result is not None
        assert 'Hello' in result


# ============================================================================
# 15. ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_15_1_invalid_memory_id(self, memory):
        """15.1 Handle invalid memory ID"""
        result = memory.get_memory('invalid-id-that-does-not-exist-12345')
        # Should return empty dict or error dict, not raise
        assert isinstance(result, dict)
    
    def test_15_2_invalid_conversation_id(self, memory):
        """15.2 Handle invalid conversation ID"""
        result = memory.get_conversation('invalid-conversation-id-12345')
        # Should return empty dict or error dict, not raise
        assert isinstance(result, dict)
    
    def test_15_3_invalid_webhook_id(self, memory):
        """15.3 Handle invalid webhook ID"""
        result = memory.get_webhook('invalid-webhook-id-12345')
        # Should return empty dict or error dict, not raise
        assert isinstance(result, dict)
    
    def test_15_4_empty_search(self, memory):
        """15.4 Handle empty search gracefully"""
        results = memory.search('', limit=5)
        assert results is not None
        assert isinstance(results, list)


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
    
    def test_16_3_concurrent_operations(self, memory):
        """16.3 Concurrent operations"""
        import concurrent.futures
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(memory.store, 'Concurrent 1'),
                executor.submit(memory.store, 'Concurrent 2'),
                executor.submit(memory.store, 'Concurrent 3'),
                executor.submit(memory.search, 'concurrent', limit=5),
                executor.submit(memory.get_statistics)
            ]
            
            concurrent.futures.wait(futures)
        
        duration = time.time() - start_time
        
        assert duration < 60  # Should complete in 60 seconds
        print(f'✓ Concurrent operations completed in: {duration:.2f}s')


if __name__ == '__main__':
    print('\n🧪 Running Memphora Python SDK Comprehensive Test Suite\n')
    print('Configuration:')
    print(f"  API URL: {TEST_CONFIG['api_url']}")
    print(f"  User ID: {TEST_CONFIG['user_id']}")
    print(f"  Timeout: {TEST_CONFIG['timeout']}s")
    print(f"  Total Test Classes: 16")
    print(f"  Estimated Test Cases: 100+\n")
    
    pytest.main([__file__, '-v', '--tb=short'])
