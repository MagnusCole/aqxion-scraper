#!/usr/bin/env python3
"""
Test local cache functionality
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_system import cache_manager

async def test_local_cache():
    print('🧪 Testing Local Cache Functionality')
    print('=' * 40)

    # Test basic cache operations
    test_key = 'test_intent_key'
    test_value = 'test_intent_value'

    # Clear any existing value
    await cache_manager.intent_cache.delete(test_key)

    # Test set
    success = await cache_manager.intent_cache.set(test_key, test_value, 300)
    print(f'💾 Set operation: {success}')

    # Test get
    result = await cache_manager.intent_cache.get(test_key)
    print(f'🔍 Get operation: {result}')

    # Test cache stats
    stats = cache_manager.intent_cache.get_stats()
    print(f'📊 Intent cache stats: {stats}')

    # Test the high-level methods
    text = 'Test intent analysis text'
    tag = 'dolor'

    # Set via high-level method
    success = await cache_manager.set_cached_intent_analysis(text, tag)
    print(f'💾 High-level set: {success}')

    # Get via high-level method
    result = await cache_manager.get_cached_intent_analysis(text)
    print(f'🔍 High-level get: {result}')

if __name__ == "__main__":
    asyncio.run(test_local_cache())
