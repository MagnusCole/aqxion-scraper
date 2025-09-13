"""
Integration Tests for Aqxion Scraper
Tests end-to-end functionality of the scraping system
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

from scraping.efficient_scraper import EfficientScraper
from scraping.marketing_pain_points_scraper import MarketingPainPointsScraper
from ai.ai_service import AIService
from config.config_v2 import get_settings

settings = get_settings()

class IntegrationTester:
    """Integration test suite for Aqxion Scraper"""

    def __init__(self):
        self.scraper = None
        self.pain_points_scraper = None
        self.ai_service = None
        self.test_results = []

    async def setup(self):
        """Initialize all services"""
        print("🔧 Setting up integration test environment...")

        try:
            self.scraper = EfficientScraper()
            print("✅ EfficientScraper initialized")
        except Exception as e:
            print(f"❌ Failed to initialize EfficientScraper: {e}")
            return False

        try:
            self.pain_points_scraper = MarketingPainPointsScraper()
            print("✅ MarketingPainPointsScraper initialized")
        except Exception as e:
            print(f"❌ Failed to initialize MarketingPainPointsScraper: {e}")
            return False

        try:
            self.ai_service = AIService()
            print("✅ AIService initialized")
        except Exception as e:
            print(f"❌ Failed to initialize AIService: {e}")
            return False

        return True

    async def test_basic_scraping(self) -> Dict[str, Any]:
        """Test basic scraping functionality"""
        print("\n🧪 TEST 1: Basic Scraping Functionality")
        print("-" * 40)

        test_result = {
            "test_name": "basic_scraping",
            "passed": False,
            "duration": 0,
            "details": {}
        }

        start_time = time.time()

        try:
            # Test with a simple URL
            test_url = "https://www.google.com/search?q=marketing+digital+lima"
            print(f"🌐 Testing scraping URL: {test_url}")

            # Use context manager to ensure proper initialization
            async with self.scraper as scraper:
                scraped_result = await scraper.scrape_single_url(test_url)
                test_result["details"]["scraped_success"] = scraped_result.success

                if scraped_result.success and scraped_result.data:
                    print("✅ Successfully scraped data")
                    print(f"   📄 Title: {scraped_result.data.title[:50]}...")
                    print(f"   📝 Content length: {len(scraped_result.data.content)}")
                    test_result["passed"] = True
                else:
                    test_result["details"]["error"] = scraped_result.error or "Failed to scrape data"
                    print("❌ Failed to scrape data")

        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"❌ Test failed with error: {e}")

        test_result["duration"] = time.time() - start_time
        return test_result

    async def test_pain_points_analysis(self) -> Dict[str, Any]:
        """Test pain points analysis functionality"""
        print("\n🧪 TEST 2: Pain Points Analysis")
        print("-" * 40)

        test_result = {
            "test_name": "pain_points_analysis",
            "passed": False,
            "duration": 0,
            "details": {}
        }

        start_time = time.time()

        try:
            # Test with sample URLs
            test_urls = [
                "https://www.google.com/search?q=pain+points+marketing+digital+lima"
            ]

            print("🔍 Testing pain points analysis...")

            analysis_result = await self.pain_points_scraper.scrape_marketing_pain_points(test_urls)

            if analysis_result:
                test_result["details"]["analysis_result"] = True
                test_result["details"]["total_analyzed"] = analysis_result.get("total_analyzed", 0)
                print("✅ Pain points analysis completed")
                print(f"   🎯 Total analyzed: {analysis_result.get('total_analyzed', 0)}")
                test_result["passed"] = True
            else:
                test_result["details"]["error"] = "Analysis returned None"
                print("❌ Pain points analysis failed")

        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"❌ Test failed with error: {e}")

        test_result["duration"] = time.time() - start_time
        return test_result

    async def test_ai_service(self) -> Dict[str, Any]:
        """Test AI service functionality"""
        print("\n🧪 TEST 3: AI Service")
        print("-" * 40)

        test_result = {
            "test_name": "ai_service",
            "passed": False,
            "duration": 0,
            "details": {}
        }

        start_time = time.time()

        try:
            # Test keyword generation
            print("🤖 Testing AI keyword generation...")

            keywords_result = await self.ai_service.generate_keywords_ai("marketing digital en Lima", count=5)
            test_result["details"]["keywords_generated"] = len(keywords_result.keywords) if keywords_result and keywords_result.keywords else 0

            if keywords_result and keywords_result.keywords and len(keywords_result.keywords) > 0:
                print("✅ Keywords generated successfully")
                print(f"   🔑 Keywords: {keywords_result.keywords[:3]}...")
                test_result["passed"] = True
            else:
                test_result["details"]["error"] = "No keywords generated"
                print("❌ Failed to generate keywords")

        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"❌ Test failed with error: {e}")

        test_result["duration"] = time.time() - start_time
        return test_result

    async def test_configuration(self) -> Dict[str, Any]:
        """Test configuration loading"""
        print("\n🧪 TEST 4: Configuration Validation")
        print("-" * 40)

        test_result = {
            "test_name": "configuration",
            "passed": True,
            "duration": 0,
            "details": {}
        }

        try:
            # Test settings loading
            print("⚙️ Testing configuration loading...")

            test_result["details"]["app_name"] = settings.app_name
            test_result["details"]["version"] = settings.version
            test_result["details"]["debug"] = settings.debug
            test_result["details"]["keywords_count"] = len(settings.scraping.keywords)
            test_result["details"]["max_concurrent"] = settings.scraping.max_concurrent_requests

            print("✅ Configuration loaded successfully")
            print(f"   📋 App: {settings.app_name} v{settings.version}")
            print(f"   🔑 Keywords configured: {len(settings.scraping.keywords)}")
            print(f"   ⚡ Max concurrent requests: {settings.scraping.max_concurrent_requests}")

        except Exception as e:
            test_result["passed"] = False
            test_result["details"]["error"] = str(e)
            print(f"❌ Configuration test failed: {e}")

        return test_result

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 AQXION SCRAPER - INTEGRATION TEST SUITE")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Setup
        if not await self.setup():
            print("❌ Setup failed. Aborting tests.")
            return

        # Run tests
        tests = [
            self.test_configuration,
            self.test_basic_scraping,
            self.test_pain_points_analysis,
            self.test_ai_service
        ]

        all_passed = True
        total_duration = 0

        for test_func in tests:
            try:
                result = await test_func()
                self.test_results.append(result)
                total_duration += result["duration"]

                if not result["passed"]:
                    all_passed = False

            except Exception as e:
                print(f"❌ Test execution failed: {e}")
                all_passed = False

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        passed_tests = sum(1 for r in self.test_results if r["passed"])
        total_tests = len(self.test_results)

        print(f"✅ Tests passed: {passed_tests}/{total_tests}")
        print(".2f")
        print(f"🎯 Overall result: {'PASS' if all_passed else 'FAIL'}")

        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            duration = ".2f"
            print(f"   {status} {result['test_name']} ({duration}s)")

            if not result["passed"] and "error" in result["details"]:
                print(f"      Error: {result['details']['error']}")

        return all_passed

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()

    if success:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Aqxion Scraper is ready for production use.")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED!")
        print("❌ Please review the errors above and fix issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
