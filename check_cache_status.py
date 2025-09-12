#!/usr/bin/env python3
"""
Cache system status check
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_system import cache_manager

async def check_cache_status():
    print('🔍 Cache System Status Check')
    print('=' * 30)

    # Check if Redis is available
    try:
        import redis
        print('✅ Redis library available')
    except ImportError:
        print('❌ Redis library not available')
        return

    # Get cache stats
    stats = cache_manager.get_stats()
    print(f'📊 Cache Stats: {stats}')

    # Test intent cache specifically
    test_text = 'Test cache functionality'
    result = await cache_manager.get_cached_intent_analysis(test_text)
    print(f'🔍 Intent cache test (should be None): {result}')

    # Set a test value
    success = await cache_manager.set_cached_intent_analysis(test_text, 'test_tag')
    print(f'💾 Set test value: {success}')

    # Get it back
    result = await cache_manager.get_cached_intent_analysis(test_text)
    print(f'🔍 Get test value: {result}')

if __name__ == "__main__":
    asyncio.run(check_cache_status())
