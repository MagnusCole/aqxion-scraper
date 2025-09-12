#!/usr/bin/env python3
"""
AI-powered keyword generation for dynamic keyword discovery
"""
import asyncio
import sys
import os
from typing import List, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_service import ai_service
from config_v2 import get_settings

settings = get_settings()

async def generate_smart_keywords(industry: str = "marketing digital", count: int = 15) -> List[str]:
    """Generate AI-powered keywords for the specified industry"""
    print(f"🤖 Generating AI-powered keywords for: {industry}")
    print("=" * 50)

    # Try AI generation first
    ai_result = await ai_service.generate_keywords_ai(industry, count)
    if ai_result:
        print("✅ AI keyword generation successful!")
        print(f"📝 Reasoning: {ai_result.reasoning}")
        if ai_result.market_trends:
            print(f"📈 Market trends: {', '.join(ai_result.market_trends[:3])}")

        keywords = ai_result.keywords
    else:
        print("⚠️ AI generation failed, using fallback keywords")
        # Fallback to original keywords
        keywords = settings.scraping.keywords[:count]

    print(f"🎯 Generated {len(keywords)} keywords:")
    for i, keyword in enumerate(keywords, 1):
        print(f"   {i:2d}. {keyword}")

    return keywords

async def update_config_with_ai_keywords():
    """Update configuration with AI-generated keywords"""
    print("🔄 Updating configuration with AI-generated keywords...")

    # Generate new keywords
    new_keywords = await generate_smart_keywords()

    if new_keywords:
        # Here you could update the configuration file or database
        print("💾 New keywords generated successfully!")
        print("📝 To use these keywords, update your configuration or pass them to the scraper")
        return new_keywords
    else:
        print("❌ Failed to generate new keywords")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        industry = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        keywords = asyncio.run(generate_smart_keywords(industry, count))
    else:
        print("Usage: python ai_keywords.py [industry] [count]")
        print("Example: python ai_keywords.py 'marketing digital' 20")
        keywords = asyncio.run(update_config_with_ai_keywords())
