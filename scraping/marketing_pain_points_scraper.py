"""
Pain Points Scraper for Marketing in Lima, Peru
Focused on identifying marketing challenges and opportunities
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from collections import Counter
from efficient_scraper import EfficientScraper, scrape_urls, ScrapingResult
from cache.redis_cache import redis_cache
from config.config_v2 import MIN_TITLE_LENGTH

class MarketingPainPointsScraper:
    """Scraper specialized in finding marketing pain points in Lima"""

    def __init__(self):
        # Keywords for pain points in Spanish
        self.pain_keywords = [
            "problema", "dificultad", "frustración", "queja", "insatisfacción",
            "necesito ayuda", "no funciona", "no sirve", "mal servicio",
            "caro", "costoso", "poco efectivo", "no veo resultados",
            "desesperado", "urgente", "necesidad", "falta", "deficiente",
            "malo", "terrible", "horrible", "decepcionado", "arrepentido"
        ]

        # Marketing-specific pain points
        self.marketing_pain_indicators = [
            "marketing no funciona", "clientes no llegan", "poca visibilidad",
            "competencia me gana", "no tengo presupuesto", "no sé marketing",
            "redes sociales no venden", "google ads caro", "seo lento",
            "contenido no interesa", "branding confuso", "sin identidad",
            "pymes marketing", "emprendedor marketing", "negocio local",
            "marketing lima", "perú marketing", "difícil vender online"
        ]

        # Sources for pain points
        self.pain_sources = [
            # Foros y comunidades
            "https://www.reddit.com/r/peru/comments/search/?q=marketing+problemas",
            "https://www.reddit.com/r/emprendedores/comments/search/?q=marketing+digital",
            "https://www.reddit.com/r/PYMEs/comments/search/?q=marketing",

            # Reviews and complaints
            "https://www.google.com/search?q=problemas+con+agencias+de+marketing+en+lima",
            "https://www.yelp.com/search?find_desc=marketing+agencies+complaints&find_loc=Lima",

            # Social media and blogs
            "https://www.linkedin.com/search/results/content/?keywords=marketing%20problems%20lima",
            "https://medium.com/search?q=marketing+challenges+in+peru",

            # Local business forums
            "https://www.facebook.com/groups/emprendedoresperu/search/?query=marketing",
            "https://www.meetup.com/cities/pe/lima/?keywords=marketing+problems",

            # Peruvian business sites
            "https://gestion.pe/empresas/marketing-digital-problemas-peru",
            "https://elcomercio.pe/tecnologia/marketing-digital-problemas-empresas"
        ]

    def _extract_pain_points(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Extract pain points from content"""
        content_lower = content.lower()
        pain_points = []

        # Find sentences containing pain keywords
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if len(sentence_lower) < 10:  # Skip very short sentences
                continue

            # Check for pain keywords
            pain_matches = [kw for kw in self.pain_keywords if kw in sentence_lower]
            marketing_matches = [kw for kw in self.marketing_pain_indicators if kw in sentence_lower]

            if pain_matches or marketing_matches:
                # Calculate relevance score
                relevance_score = (len(pain_matches) * 2) + len(marketing_matches)

                # Extract context (surrounding sentences)
                context_sentences = self._get_context_sentences(sentences, sentence)

                pain_point = {
                    "text": sentence.strip(),
                    "pain_keywords": pain_matches,
                    "marketing_indicators": marketing_matches,
                    "relevance_score": relevance_score,
                    "context": context_sentences,
                    "source_url": url,
                    "extracted_at": datetime.now().isoformat(),
                    "word_count": len(sentence.split())
                }

                pain_points.append(pain_point)

        return pain_points

    def _get_context_sentences(self, all_sentences: List[str], target_sentence: str, context_window: int = 2) -> List[str]:
        """Get context sentences around the target sentence"""
        try:
            target_idx = all_sentences.index(target_sentence)
            start_idx = max(0, target_idx - context_window)
            end_idx = min(len(all_sentences), target_idx + context_window + 1)

            context = []
            for i in range(start_idx, end_idx):
                if i != target_idx and all_sentences[i].strip():
                    context.append(all_sentences[i].strip())

            return context[:4]  # Limit context to 4 sentences
        except ValueError:
            return []

    def _categorize_pain_point(self, pain_point: Dict[str, Any]) -> str:
        """Categorize pain point by type"""
        text = pain_point["text"].lower()

        categories = {
            "budget": ["caro", "costoso", "presupuesto", "dinero", "inversión"],
            "results": ["resultados", "no funciona", "poco efectivo", "no veo", "fracaso"],
            "knowledge": ["no sé", "desconozco", "falta conocimiento", "difícil", "complicado"],
            "competition": ["competencia", "me gana", "pierdo", "ventaja"],
            "time": ["lento", "tarda", "urgente", "rápido", "tiempo"],
            "quality": ["mal servicio", "decepcionado", "calidad", "profesional"],
            "visibility": ["visibilidad", "clientes no llegan", "poca presencia"],
            "technical": ["técnico", "tecnología", "herramientas", "plataforma"]
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "general"

    def _analyze_pain_points(self, all_pain_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collected pain points for insights"""
        if not all_pain_points:
            return {"error": "No pain points found"}

        # Categorize pain points
        categorized = {}
        for pain_point in all_pain_points:
            category = self._categorize_pain_point(pain_point)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(pain_point)

        # Calculate statistics
        total_pain_points = len(all_pain_points)
        avg_relevance = sum(pp["relevance_score"] for pp in all_pain_points) / total_pain_points

        # Most common pain keywords
        all_keywords = []
        for pp in all_pain_points:
            all_keywords.extend(pp["pain_keywords"])
            all_keywords.extend(pp["marketing_indicators"])

        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)

        # Most relevant pain points
        top_pain_points = sorted(all_pain_points,
                               key=lambda x: x["relevance_score"],
                               reverse=True)[:20]

        # Category distribution
        category_distribution = {cat: len(points) for cat, points in categorized.items()}

        return {
            "summary": {
                "total_pain_points": total_pain_points,
                "categories_found": len(categorized),
                "avg_relevance_score": round(avg_relevance, 2),
                "sources_analyzed": len(set(pp["source_url"] for pp in all_pain_points)),
                "generated_at": datetime.now().isoformat()
            },
            "top_keywords": [{"keyword": kw, "count": count} for kw, count in top_keywords],
            "category_distribution": category_distribution,
            "top_pain_points": top_pain_points,
            "category_breakdown": categorized,
            "market_opportunities": self._generate_opportunities(categorized, top_keywords),
            "recommendations": self._generate_recommendations(categorized)
        }

    def _generate_opportunities(self, categorized: Dict[str, List], top_keywords: List) -> List[str]:
        """Generate business opportunities based on pain points"""
        opportunities = []

        # Budget-related opportunities
        if "budget" in categorized and len(categorized["budget"]) > 2:
            opportunities.append("Servicio de marketing accesible para PYMEs con presupuestos limitados")

        # Results-related opportunities
        if "results" in categorized and len(categorized["results"]) > 3:
            opportunities.append("Consultoría especializada en optimización de resultados de marketing")

        # Knowledge-related opportunities
        if "knowledge" in categorized and len(categorized["knowledge"]) > 2:
            opportunities.append("Cursos y talleres de marketing digital para emprendedores")

        # Competition-related opportunities
        if "competition" in categorized and len(categorized["competition"]) > 1:
            opportunities.append("Estrategias de diferenciación competitiva en marketing local")

        # Technical opportunities
        if "technical" in categorized and len(categorized["technical"]) > 1:
            opportunities.append("Implementación de herramientas de marketing automatizadas")

        # Visibility opportunities
        if "visibility" in categorized and len(categorized["visibility"]) > 2:
            opportunities.append("Servicios de visibilidad online para negocios locales")

        return opportunities[:5]  # Top 5 opportunities

    def _generate_recommendations(self, categorized: Dict[str, List]) -> List[str]:
        """Generate recommendations based on pain points analysis"""
        recommendations = []

        if "budget" in categorized:
            recommendations.append("Ofrecer paquetes de marketing escalables según presupuesto del cliente")

        if "results" in categorized:
            recommendations.append("Implementar seguimiento detallado de KPIs y reportes transparentes")

        if "knowledge" in categorized:
            recommendations.append("Crear contenido educativo gratuito para atraer clientes potenciales")

        if "time" in categorized:
            recommendations.append("Desarrollar servicios express de marketing para necesidades urgentes")

        if "quality" in categorized:
            recommendations.append("Establecer procesos de calidad y garantías de servicio")

        return recommendations[:5]

    async def scrape_marketing_pain_points(self, custom_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Main function to scrape marketing pain points"""
        print("🎯 MARKETING PAIN POINTS SCRAPER - LIMA, PERÚ")
        print("=" * 60)

        # Use custom URLs or default sources
        target_urls = custom_urls or self.pain_sources
        print(f"📊 Analizando {len(target_urls)} fuentes de pain points")

        # Scrape URLs
        print("🔄 Scraping fuentes...")
        results = await scrape_urls(target_urls, batch_size=3)

        # Process results and extract pain points
        all_pain_points = []
        successful_scrapes = 0
        cached_results = 0

        for result in results:
            if result.success and result.data:
                successful_scrapes += 1
                if result.cached:
                    cached_results += 1

                # Extract pain points from content
                pain_points = self._extract_pain_points(result.data.content, result.data.url)
                all_pain_points.extend(pain_points)

                print(f"✅ Procesado: {result.data.url}")
                print(f"   Pain points encontrados: {len(pain_points)}")
                print(f"   Contenido: {len(result.data.content)} caracteres")

        print(f"\n📈 Scraping completado: {successful_scrapes}/{len(results)} exitosos")
        print(f"🔄 Resultados en caché: {cached_results}")
        print(f"🎯 Total pain points encontrados: {len(all_pain_points)}")

        # Analyze pain points
        print("\n🧠 Analizando pain points...")
        analysis = self._analyze_pain_points(all_pain_points)

        # Cache analysis results
        analysis_key = f"marketing_pain_points_lima_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await redis_cache.set(analysis_key, analysis, ttl=86400, namespace="pain_points")

        return {
            "scraping_results": {
                "total_urls": len(results),
                "successful": successful_scrapes,
                "cached": cached_results,
                "failed": len(results) - successful_scrapes
            },
            "pain_points_found": len(all_pain_points),
            "analysis": analysis,
            "raw_pain_points": all_pain_points,
            "performance": {
                "avg_response_time": sum(r.response_time for r in results if r.success) / max(successful_scrapes, 1),
                "cache_hit_rate": cached_results / max(successful_scrapes, 1) if successful_scrapes > 0 else 0
            }
        }

async def main():
    """Main function to run marketing pain points scraping"""
    scraper = MarketingPainPointsScraper()

    try:
        results = await scraper.scrape_marketing_pain_points()

        # Print summary
        print("\n📊 RESUMEN DE PAIN POINTS:")
        analysis = results["analysis"]
        summary = analysis["summary"]
        print(f"   Pain points totales: {summary['total_pain_points']}")
        print(f"   Categorías identificadas: {summary['categories_found']}")
        print(f"   Fuentes analizadas: {summary['sources_analyzed']}")
        print(".2f")

        print("\n🔥 TOP KEYWORDS DE PAIN:")
        for i, kw_data in enumerate(analysis["top_keywords"][:5], 1):
            print(f"   {i}. '{kw_data['keyword']}' ({kw_data['count']} menciones)")

        print("\n📈 DISTRIBUCIÓN POR CATEGORÍA:")
        for category, count in analysis["category_distribution"].items():
            print(f"   {category.title()}: {count} pain points")

        print("\n💡 OPORTUNIDADES DE NEGOCIO:")
        for i, opp in enumerate(analysis["market_opportunities"], 1):
            print(f"   {i}. {opp}")

        print("\n🎯 RECOMENDACIONES:")
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"   {i}. {rec}")

        print("\n💾 Resultados guardados en caché con key: marketing_pain_points_lima_*")
        print("\n✅ Análisis de pain points completado exitosamente!")

    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")

if __name__ == "__main__":
    asyncio.run(main())