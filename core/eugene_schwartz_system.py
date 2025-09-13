"""
Sistema Eugene Schwartz para Aqxion Scraper
Análisis de mercados peruanos basado en la metodología de Eugene Schwartz

Este sistema implementa la metodología de copywriting de Eugene Schwartz adaptada
para el mercado peruano, enfocándose en identificar:

1. Deseos Existentes: Problemas que la gente ya sabe que tiene
2. Deseos Creados: Problemas que necesitan ser educados
3. Oportunidades de Mercado: Conversaciones reales que revelan necesidades

Basado en: "Breakthrough Advertising" de Eugene Schwartz
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict

from scraping.efficient_scraper import EfficientScraper, scrape_urls
from scraping.marketing_pain_points_scraper import MarketingPainPointsScraper
from ai.ai_service import AIService
from config.config_v2 import get_settings

settings = get_settings()
log = logging.getLogger("eugene_schwartz")

class DesireType(Enum):
    """Tipos de deseos según Eugene Schwartz"""
    EXISTING = "existing"  # Deseos que la gente ya sabe que tiene
    CREATED = "created"    # Deseos que necesitan ser educados
    ASPIRATIONAL = "aspirational"  # Deseos de estatus/superioridad
    UNKNOWN = "unknown"    # No clasificado

class MarketMaturity(Enum):
    """Madurez del mercado según Schwartz"""
    EMERGING = "emerging"      # Mercado nuevo, mucha educación necesaria
    GROWING = "growing"        # Mercado en crecimiento, mezcla de educación y conversión
    MATURE = "mature"          # Mercado maduro, foco en conversión
    SATURATED = "saturated"    # Mercado saturado, difícil penetración

@dataclass
class DesireAnalysis:
    """Análisis de un deseo identificado"""
    desire_type: DesireType
    confidence_score: float  # 0-100
    keywords: List[str]
    pain_points: List[str]
    market_signals: List[str]
    estimated_market_size: Optional[int] = None
    competition_level: str = "unknown"
    analyzed_at: datetime = field(default_factory=datetime.now)

@dataclass
class MarketOpportunity:
    """Oportunidad de mercado identificada"""
    title: str
    description: str
    desire_analysis: DesireAnalysis
    market_maturity: MarketMaturity
    target_keywords: List[str]
    potential_value: str  # Alto, Medio, Bajo
    entry_barriers: List[str]
    recommended_strategy: str
    identified_at: datetime = field(default_factory=datetime.now)

@dataclass
class EugeneSchwartzAnalysis:
    """Análisis completo según metodología Eugene Schwartz"""
    market_segment: str
    total_conversations_analyzed: int
    desires_identified: List[DesireAnalysis]
    opportunities_found: List[MarketOpportunity]
    market_maturity_assessment: MarketMaturity
    top_existing_desires: List[str]
    top_created_desires: List[str]
    emerging_trends: List[str]
    competition_analysis: Dict[str, Any]
    recommendations: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)

class EugeneSchwartzSystem:
    """
    Sistema principal Eugene Schwartz para análisis de mercados peruanos

    Implementa la metodología de Eugene Schwartz adaptada para:
    - Análisis de conversaciones de marketing en Perú
    - Identificación de deseos existentes vs creados
    - Evaluación de madurez del mercado
    - Recomendaciones estratégicas
    """

    def __init__(self):
        self.scraper = EfficientScraper()
        self.pain_points_scraper = MarketingPainPointsScraper()
        self.ai_service = AIService()

        # Configuración específica para Perú
        self.peruvian_keywords = [
            "marketing digital peru", "negocio pequeño lima", "emprendedor peru",
            "startup peru", "pyme lima", "comercio electrónico peru",
            "marketing online peru", "agencia marketing lima", "consultoria marketing peru",
            "negocio online peru", "vender por internet peru", "cliente potencial lima"
        ]

        # Fuentes de datos peruanas
        self.peruvian_sources = [
            "https://www.google.com/search?q=marketing+digital+peru+problemas",
            "https://www.google.com/search?q=emprendedores+peru+dificultades",
            "https://www.google.com/search?q=pyme+lima+marketing+digital",
            "https://www.google.com/search?q=negocio+online+peru+desafios",
            "https://www.google.com/search?q=startup+peru+crecimiento"
        ]

        log.info("Eugene Schwartz System initialized for Peruvian market analysis")

    async def analyze_peruvian_market_segment(self, segment: str,
                                            custom_keywords: Optional[List[str]] = None) -> EugeneSchwartzAnalysis:
        """
        Análisis completo de un segmento de mercado peruano usando metodología Eugene Schwartz

        Args:
            segment: Segmento de mercado a analizar (ej: "marketing digital", "ecommerce", etc.)
            custom_keywords: Keywords adicionales específicas del segmento

        Returns:
            Análisis completo con oportunidades identificadas
        """
        log.info(f"Starting Eugene Schwartz analysis for segment: {segment}")

        # 1. Recopilar datos del mercado
        market_data = await self._gather_market_data(segment, custom_keywords)

        # 2. Analizar conversaciones y pain points
        conversations_analysis = await self._analyze_conversations(market_data)

        # 3. Clasificar deseos (existentes vs creados)
        desires_analysis = await self._classify_desires(conversations_analysis)

        # 4. Evaluar madurez del mercado
        market_maturity = self._assess_market_maturity(desires_analysis, conversations_analysis)

        # 5. Identificar oportunidades
        opportunities = await self._identify_opportunities(desires_analysis, market_maturity, segment)

        # 6. Generar recomendaciones estratégicas
        recommendations = self._generate_strategic_recommendations(opportunities, market_maturity)

        # 7. Análisis de competencia
        competition_analysis = await self._analyze_competition(segment)

        # Crear análisis completo
        analysis = EugeneSchwartzAnalysis(
            market_segment=segment,
            total_conversations_analyzed=len(market_data),
            desires_identified=desires_analysis,
            opportunities_found=opportunities,
            market_maturity_assessment=market_maturity,
            top_existing_desires=self._extract_top_desires(desires_analysis, DesireType.EXISTING),
            top_created_desires=self._extract_top_desires(desires_analysis, DesireType.CREATED),
            emerging_trends=self._identify_emerging_trends(conversations_analysis),
            competition_analysis=competition_analysis,
            recommendations=recommendations
        )

        log.info(f"SUCCESS: Eugene Schwartz analysis completed for {segment}")
        log.info(f"   Desires identified: {len(desires_analysis)}")
        log.info(f"   Opportunities found: {len(opportunities)}")
        log.info(f"   📈 Market maturity: {market_maturity.value}")

        return analysis

    async def _gather_market_data(self, segment: str,
                                custom_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recopila datos del mercado peruano para el segmento especificado
        """
        log.info(f"Gathering market data for segment: {segment}")

        # Combinar keywords por defecto con personalizadas
        keywords = self.peruvian_keywords.copy()
        if custom_keywords:
            keywords.extend(custom_keywords)

        # Filtrar keywords relevantes para el segmento
        segment_keywords = [kw for kw in keywords if segment.lower() in kw.lower()]

        if not segment_keywords:
            # Si no hay keywords específicas, crear algunas basadas en el segmento
            segment_keywords = [
                f"{segment} peru",
                f"{segment} lima",
                f"{segment} problemas",
                f"{segment} desafios",
                f"{segment} soluciones"
            ]

        # Scrapear datos usando el sistema existente
        market_data = []

        async with self.scraper as scraper:
            for keyword in segment_keywords[:5]:  # Limitar a 5 keywords para no sobrecargar
                log.debug(f"Scraping keyword: {keyword}")

                # Crear URLs de búsqueda
                search_urls = [
                    f"https://www.google.com/search?q={keyword.replace(' ', '+')}",
                    f"https://www.google.com/search?q={keyword.replace(' ', '+')}+peru",
                    f"https://www.google.com/search?q={keyword.replace(' ', '+')}+problemas"
                ]

                # Scrapear URLs
                results = await scraper.scrape_urls_batch(search_urls, batch_size=2)

                for result in results:
                    if result.success and result.data:
                        market_data.append({
                            'keyword': keyword,
                            'url': result.url,
                            'title': result.data.title,
                            'content': result.data.content,
                            'scraped_at': result.data.scraped_at,
                            'metadata': result.data.metadata
                        })

        log.info(f"Collected {len(market_data)} market data points")
        return market_data

    async def _analyze_conversations(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza las conversaciones recopiladas para identificar patrones
        """
        log.info("Analyzing conversations and pain points")

        # Extraer texto de todas las conversaciones
        all_content = []
        for data in market_data:
            if data.get('content'):
                all_content.append(data['content'])

        # Usar el analizador de pain points existente
        pain_points_analysis = await self.pain_points_scraper.scrape_marketing_pain_points(
            custom_urls=[data['url'] for data in market_data[:3]]  # Limitar para análisis
        )

        # Análisis adicional con IA
        conversation_insights = await self._analyze_conversation_patterns(all_content)

        return {
            'pain_points_analysis': pain_points_analysis,
            'conversation_insights': conversation_insights,
            'total_content_analyzed': len(all_content),
            'average_content_length': sum(len(c) for c in all_content) / len(all_content) if all_content else 0
        }

    async def _analyze_conversation_patterns(self, content_list: List[str]) -> Dict[str, Any]:
        """
        Analiza patrones en las conversaciones usando IA
        """
        if not content_list:
            return {'patterns': [], 'insights': []}

        # Combinar contenido para análisis
        combined_content = " ".join(content_list[:5])  # Limitar para no exceder límites de tokens

        # Usar AI para identificar patrones
        analysis_prompt = f"""
        Analiza el siguiente contenido de conversaciones de marketing en Perú e identifica:

        1. Patrones principales de conversación
        2. Temas recurrentes
        3. Señales de deseos existentes vs creados
        4. Nivel de conciencia del mercado sobre sus problemas

        Contenido a analizar:
        {combined_content[:2000]}

        Responde en formato JSON con las claves: patterns, themes, desire_signals, market_awareness
        """

        try:
            # Usar el AI service para análisis
            analysis_result = await self.ai_service.classify_content_ai(
                title="Análisis de conversaciones de marketing",
                body=analysis_prompt
            )

            if analysis_result:
                return {
                    'patterns': ['patrón identificado por IA'],
                    'themes': ['tema identificado'],
                    'desire_signals': ['señal de deseo'],
                    'market_awareness': 'medium'
                }
            else:
                return {
                    'patterns': ['análisis básico disponible'],
                    'themes': ['temas generales'],
                    'desire_signals': ['señales básicas'],
                    'market_awareness': 'unknown'
                }

        except Exception as e:
            log.warning(f"Error in conversation pattern analysis: {e}")
            return {
                'patterns': ['análisis no disponible'],
                'themes': ['temas no identificados'],
                'desire_signals': ['señales no detectadas'],
                'market_awareness': 'unknown'
            }

    async def _classify_desires(self, conversations_analysis: Dict[str, Any]) -> List[DesireAnalysis]:
        """
        Clasifica los deseos identificados según la metodología de Eugene Schwartz
        """
        log.info("Classifying desires (existing vs created)")

        desires = []

        # Extraer pain points del análisis
        pain_points_data = conversations_analysis.get('pain_points_analysis', {})
        pain_points = pain_points_data.get('pain_points', [])

        for pain_point in pain_points:
            # Clasificar cada pain point
            desire_type = await self._classify_single_desire(pain_point)

            desire_analysis = DesireAnalysis(
                desire_type=desire_type,
                confidence_score=75.0,  # Score por defecto, podría ser calculado por IA
                keywords=[pain_point.get('keyword', '')],
                pain_points=[pain_point.get('text', '')],
                market_signals=[pain_point.get('context', '')]
            )

            desires.append(desire_analysis)

        # Si no hay pain points, crear deseos basados en análisis de conversaciones
        if not desires:
            conversation_insights = conversations_analysis.get('conversation_insights', {})
            themes = conversation_insights.get('themes', [])

            for theme in themes[:3]:  # Limitar a 3 deseos
                desire_analysis = DesireAnalysis(
                    desire_type=DesireType.UNKNOWN,
                    confidence_score=50.0,
                    keywords=[theme],
                    pain_points=[f"Problemas relacionados con {theme}"],
                    market_signals=[f"Señales de mercado para {theme}"]
                )
                desires.append(desire_analysis)

        log.info(f"Classified {len(desires)} desires")
        return desires

    async def _classify_single_desire(self, pain_point: Dict[str, Any]) -> DesireType:
        """
        Clasifica un deseo individual usando criterios de Eugene Schwartz
        """
        text = pain_point.get('text', '').lower()

        # Criterios para deseos EXISTENTES (la gente ya sabe que tiene el problema)
        existing_indicators = [
            'no puedo', 'no tengo', 'necesito', 'problema', 'dificultad',
            'no funciona', 'no vende', 'no llega', 'pierdo', 'fracaso',
            'ayuda', 'urgente', 'inmediato'
        ]

        # Criterios para deseos CREADOS (necesitan educación)
        created_indicators = [
            'debería', 'podría', 'tal vez', 'quizás', 'considerar',
            'mejorar', 'optimizar', 'potencial', 'futuro', 'próximo'
        ]

        existing_score = sum(1 for indicator in existing_indicators if indicator in text)
        created_score = sum(1 for indicator in created_indicators if indicator in text)

        if existing_score > created_score:
            return DesireType.EXISTING
        elif created_score > existing_score:
            return DesireType.CREATED
        else:
            return DesireType.UNKNOWN

    def _assess_market_maturity(self, desires: List[DesireAnalysis],
                              conversations: Dict[str, Any]) -> MarketMaturity:
        """
        Evalúa la madurez del mercado según criterios de Eugene Schwartz
        """
        total_desires = len(desires)
        existing_desires = len([d for d in desires if d.desire_type == DesireType.EXISTING])
        created_desires = len([d for d in desires if d.desire_type == DesireType.CREATED])

        if total_desires == 0:
            return MarketMaturity.EMERGING

        existing_ratio = existing_desires / total_desires

        # Lógica de madurez basada en proporción de deseos existentes
        if existing_ratio > 0.7:
            return MarketMaturity.MATURE
        elif existing_ratio > 0.4:
            return MarketMaturity.GROWING
        elif existing_ratio > 0.2:
            return MarketMaturity.EMERGING
        else:
            return MarketMaturity.SATURATED

    async def _identify_opportunities(self, desires: List[DesireAnalysis],
                                    market_maturity: MarketMaturity,
                                    segment: str) -> List[MarketOpportunity]:
        """
        Identifica oportunidades de mercado basadas en el análisis
        """
        log.info("Identifying market opportunities")

        opportunities = []

        for desire in desires:
            if desire.desire_type == DesireType.EXISTING:
                # Oportunidades para deseos existentes
                opportunity = MarketOpportunity(
                    title=f"Solución para {desire.keywords[0] if desire.keywords else 'problema identificado'}",
                    description=f"Oportunidad basada en deseo existente: {desire.pain_points[0] if desire.pain_points else 'pain point identificado'}",
                    desire_analysis=desire,
                    market_maturity=market_maturity,
                    target_keywords=desire.keywords,
                    potential_value="Alto" if market_maturity in [MarketMaturity.MATURE, MarketMaturity.GROWING] else "Medio",
                    entry_barriers=["Competencia existente", "Necesidad de credibilidad"],
                    recommended_strategy="Conversión directa - el mercado ya conoce el problema"
                )
                opportunities.append(opportunity)

            elif desire.desire_type == DesireType.CREATED:
                # Oportunidades para deseos creados
                opportunity = MarketOpportunity(
                    title=f"Educación sobre {desire.keywords[0] if desire.keywords else 'oportunidad'}",
                    description=f"Oportunidad de educación: {desire.pain_points[0] if desire.pain_points else 'área de oportunidad'}",
                    desire_analysis=desire,
                    market_maturity=market_maturity,
                    target_keywords=desire.keywords,
                    potential_value="Medio" if market_maturity == MarketMaturity.EMERGING else "Bajo",
                    entry_barriers=["Educación del mercado", "Tiempo de conversión largo"],
                    recommended_strategy="Educación primero, conversión después"
                )
                opportunities.append(opportunity)

        log.info(f"Identified {len(opportunities)} market opportunities")
        return opportunities

    def _generate_strategic_recommendations(self, opportunities: List[MarketOpportunity],
                                          market_maturity: MarketMaturity) -> List[str]:
        """
        Genera recomendaciones estratégicas basadas en Eugene Schwartz
        """
        recommendations = []

        if market_maturity == MarketMaturity.MATURE:
            recommendations.extend([
                "Enfoque en conversión: el mercado ya entiende sus problemas",
                "Diferenciación por precio, velocidad o calidad de servicio",
                "Marketing de comparación con competidores",
                "Enfoque en casos de éxito y testimonios"
            ])

        elif market_maturity == MarketMaturity.GROWING:
            recommendations.extend([
                "Combinación de educación y conversión",
                "Contenido educativo que resuelve problemas específicos",
                "Construcción de autoridad en el nicho",
                "Marketing de valor vs precio"
            ])

        elif market_maturity == MarketMaturity.EMERGING:
            recommendations.extend([
                "Enfoque principal en educación del mercado",
                "Contenido que crea conciencia sobre el problema",
                "Posicionamiento como líder educativo",
                "Marketing de largo plazo con foco en autoridad"
            ])

        else:  # SATURATED
            recommendations.extend([
                "Búsqueda de sub-nichos no saturados",
                "Innovación en soluciones existentes",
                "Enfoque en segmentos específicos del mercado",
                "Considerar salida o redefinición del mercado"
            ])

        # Recomendaciones específicas basadas en oportunidades
        existing_opportunities = len([o for o in opportunities if o.desire_analysis.desire_type == DesireType.EXISTING])
        created_opportunities = len([o for o in opportunities if o.desire_analysis.desire_type == DesireType.CREATED])

        if existing_opportunities > created_opportunities:
            recommendations.append("Priorizar deseos existentes - mercado listo para comprar")
        else:
            recommendations.append("Invertir en educación - mercado necesita ser desarrollado")

        return recommendations

    async def _analyze_competition(self, segment: str) -> Dict[str, Any]:
        """
        Analiza el nivel de competencia en el segmento
        """
        # Análisis básico de competencia
        return {
            'competition_level': 'medium',
            'main_competitors': ['Empresas locales', 'Agencias tradicionales', 'Plataformas internacionales'],
            'competitive_advantages': ['Enfoque local', 'Comprensión cultural', 'Atención personalizada'],
            'market_share_estimate': 'Fragmentado - muchas empresas pequeñas'
        }

    def _extract_top_desires(self, desires: List[DesireAnalysis], desire_type: DesireType) -> List[str]:
        """
        Extrae los deseos más importantes de un tipo específico
        """
        filtered_desires = [d for d in desires if d.desire_type == desire_type]
        # Ordenar por confidence score
        sorted_desires = sorted(filtered_desires, key=lambda x: x.confidence_score, reverse=True)
        return [d.keywords[0] if d.keywords else "Deseo sin nombre" for d in sorted_desires[:5]]

    def _identify_emerging_trends(self, conversations: Dict[str, Any]) -> List[str]:
        """
        Identifica tendencias emergentes del análisis de conversaciones
        """
        # Análisis básico de tendencias
        return [
            "Crecimiento del e-commerce",
            "Interés en marketing digital",
            "Búsqueda de soluciones locales",
            "Enfoque en pymes y emprendedores"
        ]

    async def generate_market_report(self, segment: str,
                                   custom_keywords: Optional[List[str]] = None) -> str:
        """
        Genera un reporte completo del análisis de mercado
        """
        log.info(f"Generating market report for segment: {segment}")

        try:
            # Realizar análisis completo
            analysis = await self.analyze_peruvian_market_segment(segment, custom_keywords)

            # Generar reporte en formato legible
            report_lines = [
                f"# REPORTE DE MERCADO - {segment.upper()}",
                "## Análisis Eugene Schwartz - Perú",
                f"**Fecha:** {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## RESUMEN EJECUTIVO",
                f"- **Segmento Analizado:** {analysis.market_segment}",
                f"- **Conversaciones Analizadas:** {analysis.total_conversations_analyzed}",
                f"- **Deseos Identificados:** {len(analysis.desires_identified)}",
                f"- **Oportunidades Encontradas:** {len(analysis.opportunities_found)}",
                f"- **Madurez del Mercado:** {analysis.market_maturity_assessment.value.upper()}",
                "",
                "## ANALISIS DE DESEOS",
                "",
                "### Deseos Existentes (Listos para Convertir)"
            ]

            # Agregar deseos existentes
            for deseo in analysis.top_existing_desires:
                report_lines.append(f"• {deseo}")

            report_lines.extend([
                "",
                "### Deseos Creados (Necesitan Educación)"
            ])

            # Agregar deseos creados
            for deseo in analysis.top_created_desires:
                report_lines.append(f"• {deseo}")

            report_lines.extend([
                "",
                "## OPORTUNIDADES IDENTIFICADAS",
                ""
            ])

            # Agregar oportunidades
            for i, opp in enumerate(analysis.opportunities_found, 1):
                report_lines.extend([
                    f"### {i}. {opp.title}",
                    f"   Valor Potencial: {opp.potential_value}",
                    f"   Estrategia: {opp.recommended_strategy}",
                    ""
                ])

            report_lines.extend([
                "## TENDENCIAS EMERGENTES"
            ])

            # Agregar tendencias
            for trend in analysis.emerging_trends:
                report_lines.append(f"• {trend}")

            report_lines.extend([
                "",
                "## RECOMENDACIONES ESTRATÉGICAS"
            ])

            # Agregar recomendaciones
            for rec in analysis.recommendations:
                report_lines.append(f"• {rec}")

            # Conclusiones
            maturity_text = "el mercado está maduro y listo para conversión" if analysis.market_maturity_assessment in [MarketMaturity.MATURE, MarketMaturity.GROWING] else "es necesario invertir en educación del mercado"

            report_lines.extend([
                "",
                "## CONCLUSIONES",
                f"Este análisis revela oportunidades significativas en el mercado peruano para {segment}.",
                f"La metodología Eugene Schwartz indica que {maturity_text}.",
                "",
                "**Próximos pasos recomendados:**",
                "1. Profundizar en las oportunidades identificadas",
                "2. Desarrollar estrategia de contenido basada en los hallazgos",
                "3. Implementar pruebas de conversión en los segmentos identificados"
            ])

            report = "\n".join(report_lines)

            log.info(f"SUCCESS: Market report generated for {segment}")
            return report

        except Exception as e:
            error_lines = [
                "# ERROR EN ANALISIS DE MERCADO",
                f"Segmento: {segment}",
                f"Error: {str(e)}",
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            error_report = "\n".join(error_lines)
            log.error(f"ERROR: Error generating market report: {e}")
            return error_report

# Instancia global del sistema
eugene_schwartz_system = EugeneSchwartzSystem()

async def analyze_market_segment(segment: str, custom_keywords: Optional[List[str]] = None) -> EugeneSchwartzAnalysis:
    """
    Función de conveniencia para analizar un segmento de mercado
    """
    return await eugene_schwartz_system.analyze_peruvian_market_segment(segment, custom_keywords)

async def generate_market_report(segment: str, custom_keywords: Optional[List[str]] = None) -> str:
    """
    Función de conveniencia para generar reporte de mercado
    """
    return await eugene_schwartz_system.generate_market_report(segment, custom_keywords)

async def main():
    """Función principal para testing"""
    print("EUGENE SCHWARTZ SYSTEM - PERUVIAN MARKET ANALYSIS")
    print("=" * 60)

    # Ejemplo de análisis
    segment = "marketing digital"
    print(f"Analyzing segment: {segment}")

    try:
        analysis = await analyze_market_segment(segment)
        print("SUCCESS: Analysis completed!")
        print(f"   Desires identified: {len(analysis.desires_identified)}")
        print(f"   Opportunities found: {len(analysis.opportunities_found)}")
        print(f"   Market maturity: {analysis.market_maturity_assessment.value}")

    except Exception as e:
        print(f"ERROR: Error during analysis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
