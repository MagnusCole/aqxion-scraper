#!/usr/bin/env python3
"""
Test script to verify intent analysis caching integration
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_async import AsyncScraper
from cache_system import cache_manager

async def test_intent_caching():
    """Test that intent analysis caching works correctly"""
    print("🧪 Testing Intent Analysis Caching Integration")
    print("=" * 50)

    # Test text
    test_text = "Necesito ayuda urgente con mi sitio web que no funciona"

    async with AsyncScraper() as scraper:
        print(f"📝 Test Text: {test_text}")
        print()

        # First call - should cache the result
        print("🔄 First call (should execute analysis and cache):")
        tag1 = await scraper.get_cached_intent_tag(test_text)
        print(f"   Result: {tag1}")

        # Second call - should use cache
        print("🔄 Second call (should use cache):")
        tag2 = await scraper.get_cached_intent_tag(test_text)
        print(f"   Result: {tag2}")

        # Verify results are the same
        if tag1 == tag2:
            print("✅ Cache working correctly - results match")
        else:
            print("❌ Cache issue - results don't match")
            return False

        # Check cache stats
        print()
        print("📊 Cache Statistics:")
        stats = cache_manager.get_stats()
        intent_stats = stats.get('intent', {})
        print(f"   Intent Cache Hits: {intent_stats.get('hits', 0)}")
        print(f"   Intent Cache Misses: {intent_stats.get('misses', 0)}")
        print(f"   Intent Cache Size: {intent_stats.get('size', 0)}")

        return True

if __name__ == "__main__":
    success = asyncio.run(test_intent_caching())
    if success:
        print()
        print("🎉 Intent caching integration test PASSED")
    else:
        print()
        print("💥 Intent caching integration test FAILED")
        sys.exit(1)
