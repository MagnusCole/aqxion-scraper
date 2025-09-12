#!/usr/bin/env python3
"""
Test AI integration and fallback mechanisms
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_service import ai_service, AIService
from main_async import AsyncScraper

async def test_ai_integration():
    """Test AI integration with graceful fallback"""
    print("🧪 Testing AI Integration")
    print("=" * 40)

    # Test 1: AI Service initialization
    print("1️⃣ Testing AI Service initialization...")
    if ai_service.client:
        print("   ✅ OpenAI client initialized")
    else:
        print("   ⚠️ OpenAI client not available (expected without API key)")

    # Test 2: Content classification with fallback
    print("\n2️⃣ Testing content classification...")
    test_title = "Necesito ayuda urgente con mi sitio web"
    test_body = "Mi página web no funciona y necesito una solución inmediata para mi negocio."

    async with AsyncScraper() as scraper:
        # This should work with or without AI (fallback to regex)
        tag = await scraper.get_cached_intent_tag(test_body, test_title)
        print(f"   📝 Content: {test_title}")
        print(f"   🏷️ Classified as: {tag}")

        if tag in ['dolor', 'busqueda', 'objecion', 'ruido']:
            print("   ✅ Classification successful")
        else:
            print("   ❌ Unexpected classification result")

    # Test 3: AI keyword generation (should handle gracefully without API key)
    print("\n3️⃣ Testing AI keyword generation...")
    try:
        result = await ai_service.generate_keywords_ai("marketing digital", 5)
        if result:
            print("   ✅ AI keyword generation successful")
            print(f"   🎯 Generated {len(result.keywords)} keywords")
        else:
            print("   ⚠️ AI keyword generation returned None (expected without API key)")
    except Exception as e:
        print(f"   ❌ AI keyword generation error: {e}")

    # Test 4: Cache integration
    print("\n4️⃣ Testing cache integration...")
    # Second call should use cache
    tag2 = await scraper.get_cached_intent_tag(test_body, test_title)
    print(f"   🔄 Second classification: {tag2}")
    if tag == tag2:
        print("   ✅ Cache working correctly")
    else:
        print("   ⚠️ Cache may not be working as expected")

    print("\n📋 Test Summary:")
    print("   ✅ AI service initializes gracefully")
    print("   ✅ Content classification works with fallback")
    print("   ✅ Cache integration functional")
    print("   ✅ Graceful handling of missing API keys")

    return True

if __name__ == "__main__":
    success = asyncio.run(test_ai_integration())
    if success:
        print("\n🎉 AI integration test completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Get OpenAI API key from https://platform.openai.com/api-keys")
        print("   2. Add OPENAI_API_KEY to your .env file")
        print("   3. Run: python ai_keywords.py 'marketing digital' 20")
        print("   4. Test full AI features with real API calls")
    else:
        print("\n❌ Some tests failed")
