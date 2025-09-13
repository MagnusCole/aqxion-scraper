"""
Efficient Scraping Demo for Marketing Agencies Insights
Focused on fast, reliable scraping with Redis caching
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from efficient_scraper import EfficientScraper, scrape_urls, ScrapingResult
from redis_cache import redis_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("marketing_scraper")

class MarketingInsightsScraper:
    """Scraper focused on marketing agencies insights"""

    def __init__(self):
        self.agency_keywords = [
            "agencia de marketing",
            "marketing digital",
            "consultoria marketing",
            "marketing lima",
            "agencia publicidad",
            "marketing online",
            "digital marketing agency"
        ]

        self.target_urls = [
            "https://www.google.com/search?q=agencias+de+marketing+en+lima",
            "https://pe.linkedin.com/jobs/marketing-jobs-lima",
            "https://www.yelp.com/search?find_desc=Marketing+Agencies&find_loc=Lima%2C+Peru",
            "https://www.yellowpages.com/lima-pe/marketing-agencies",
            "https://www.dexigner.com/directory/cat/Marketing-Agencies/Lima-Peru",
        ]

    async def extract_agency_info(self, scraped_data) -> Dict[str, Any]:
        """Extract marketing agency information from scraped content"""
        content = scraped_data.content.lower()

        # Look for agency indicators
        agency_indicators = [
            "marketing", "publicidad", "digital", "agency", "consultoria",
            "estrategia", "branding", "social media", "seo", "sem",
            "google ads", "facebook ads", "pymes", "emprendedores"
        ]

        # Count relevant keywords
        keyword_matches = sum(1 for keyword in agency_indicators if keyword in content)

        # Extract potential contact info
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', scraped_data.content)
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', scraped_data.content)

        # Extract company names (simple heuristic)
        lines = scraped_data.content.split('\n')
        potential_companies = []
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if 3 < len(line) < 50 and not any(char in line for char in ['@', 'http', 'www']):
                # Look for title case or capitalized words
                if sum(1 for word in line.split() if word.istitle()) >= 2:
                    potential_companies.append(line)

        return {
            "url": scraped_data.url,
            "title": scraped_data.title,
            "agency_relevance_score": keyword_matches / len(agency_indicators),
            "keyword_matches": keyword_matches,
            "emails_found": list(set(emails)),
            "phones_found": list(set(phones)),
            "potential_companies": potential_companies[:5],  # Top 5
            "content_length": len(scraped_data.content),
            "scraped_at": scraped_data.scraped_at.isoformat(),
            "content_hash": scraped_data.content_hash
        }

    async def generate_insights(self, agency_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from scraped agency data"""
        if not agency_data:
            return {"error": "No agency data available"}

        # Filter high-relevance agencies
        high_relevance = [agency for agency in agency_data if agency["agency_relevance_score"] > 0.3]

        # Extract unique emails and phones
        all_emails = []
        all_phones = []
        all_companies = []

        for agency in high_relevance:
            all_emails.extend(agency["emails_found"])
            all_phones.extend(agency["phones_found"])
            all_companies.extend(agency["potential_companies"])

        # Remove duplicates
        unique_emails = list(set(all_emails))
        unique_phones = list(set(all_phones))
        unique_companies = list(set(all_companies))

        # Generate insights
        insights = {
            "summary": {
                "total_urls_scraped": len(agency_data),
                "high_relevance_agencies": len(high_relevance),
                "unique_emails_found": len(unique_emails),
                "unique_phones_found": len(unique_phones),
                "potential_companies_identified": len(unique_companies),
                "generated_at": datetime.now().isoformat()
            },
            "top_agencies": sorted(high_relevance,
                                 key=lambda x: x["agency_relevance_score"],
                                 reverse=True)[:10],
            "contact_info": {
                "emails": unique_emails,
                "phones": unique_phones
            },
            "market_opportunities": {
                "total_market_size_estimate": len(high_relevance) * 50000,  # Rough estimate
                "service_areas": ["SEO", "Social Media", "Google Ads", "Content Marketing", "Branding"],
                "target_segments": ["PYMEs", "E-commerce", "Profesionales", "Emprendedores"]
            },
            "recommendations": [
                f"Contact {len(unique_emails)} potential leads via email",
                f"Call {len(unique_phones)} agencies for partnerships",
                f"Analyze {len(unique_companies)} company names for market gaps",
                "Focus on underserved segments like local PYMEs",
                "Consider white-label partnerships with smaller agencies"
            ]
        }

        return insights

    async def run_marketing_scraping(self) -> Dict[str, Any]:
        """Run complete marketing agencies scraping and analysis"""
        log.info("🚀 Starting Marketing Agencies Scraping")
        log.info(f"📊 Target URLs: {len(self.target_urls)}")
        log.info(f"🔍 Keywords: {len(self.agency_keywords)}")

        # Scrape URLs
        log.info("🔄 Scraping URLs...")
        results = await scrape_urls(self.target_urls, batch_size=3)

        # Process successful results
        agency_data = []
        successful_scrapes = 0
        cached_results = 0

        for result in results:
            if result.success:
                successful_scrapes += 1
                if result.cached:
                    cached_results += 1

                # Extract agency information
                agency_info = await self.extract_agency_info(result.data)
                agency_data.append(agency_info)

                log.info(f"✅ Processed: {result.url} (Score: {agency_info['agency_relevance_score']:.2f})")
            else:
                log.warning(f"❌ Failed: {result.url} - {result.error}")

        log.info(f"📈 Scraping Complete: {successful_scrapes}/{len(results)} successful ({cached_results} from cache)")

        # Generate insights
        log.info("🧠 Generating Insights...")
        insights = await self.generate_insights(agency_data)

        # Cache insights
        insights_key = f"marketing_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await redis_cache.set(insights_key, insights, ttl=86400, namespace="insights")  # 24 hours

        # Get cache stats
        cache_stats = await redis_cache.get_stats()

        return {
            "scraping_results": {
                "total_urls": len(results),
                "successful": successful_scrapes,
                "cached": cached_results,
                "failed": len(results) - successful_scrapes
            },
            "agency_data": agency_data,
            "insights": insights,
            "cache_stats": cache_stats,
            "performance": {
                "avg_response_time": sum(r.response_time for r in results if r.success) / max(successful_scrapes, 1),
                "cache_hit_rate": cached_results / max(successful_scrapes, 1) if successful_scrapes > 0 else 0
            }
        }

async def main():
    """Main function to run marketing insights scraping"""
    print("🎯 AQXION MARKETING INSIGHTS SCRAPER")
    print("=" * MIN_BODY_LENGTH)

    scraper = MarketingInsightsScraper()

    try:
        results = await scraper.run_marketing_scraping()

        # Print summary
        print("\n📊 SCRAPING SUMMARY:")
        print(f"   URLs Processed: {results['scraping_results']['total_urls']}")
        print(f"   Successful: {results['scraping_results']['successful']}")
        print(f"   From Cache: {results['scraping_results']['cached']}")
        print(f"   Failed: {results['scraping_results']['failed']}")

        print("\n🧠 INSIGHTS GENERATED:")
        insights = results['insights']
        summary = insights['summary']
        print(f"   High-Relevance Agencies: {summary['high_relevance_agencies']}")
        print(f"   Unique Emails: {summary['unique_emails_found']}")
        print(f"   Unique Phones: {summary['unique_phones_found']}")
        print(f"   Potential Companies: {summary['potential_companies_identified']}")

        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"   {i}. {rec}")

        print("\n⚡ PERFORMANCE:")
        perf = results['performance']
        print(f"   Avg Response Time: {perf['avg_response_time']:.2f}s")
        print(f"   Cache Hit Rate: {perf['cache_hit_rate']:.1%}")

        print("\n🔴 CACHE STATUS:")
        cache = results['cache_stats']
        print(f"   Redis Connected: {cache['redis_connected']}")
        if cache['redis_connected']:
            print(f"   Memory Used: {cache.get('redis_memory_used', 'N/A')}")
            print(f"   Connected Clients: {cache.get('redis_connected_clients', 'N/A')}")

        # Save results to file
        output_file = f"marketing_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")
        print("\n✅ Marketing insights scraping completed successfully!")

    except Exception as e:
        log.error(f"❌ Error during scraping: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())