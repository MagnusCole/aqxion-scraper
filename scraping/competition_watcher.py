"""
Competition Watcher - Análisis de Competencia para Mercado Peruano
Módulo especializado para analizar la competencia en "limpieza de piscina lima"
"""

import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse, urljoin
from pathlib import Path

from config.config_v2 import get_settings
from scraping.simple_scrapling import scrapling_scraper
from ai.ai_service import ai_service
from database.db import (
    init_competition_tables, save_competitor, load_competitors,
    save_competition_analysis, load_competition_analysis,
    start_competition_run, update_competition_run, get_competition_runs
)

# Configuración
settings = get_settings()

@dataclass
class CompetitorData:
    """Datos de un competidor identificado"""
    name: str
    website: str
    services: List[str]
    location: str
    pricing_info: Optional[str] = None
    contact_info: Optional[str] = None
    social_media: Optional[List[str]] = None
    description: Optional[str] = None
    scraped_at: Optional[datetime] = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
        if self.social_media is None:
            self.social_media = []

@dataclass
class MarketAnalysis:
    """Análisis de mercado basado en competencia"""
    keyword: str
    total_competitors: int
    service_categories: Dict[str, int]
    price_ranges: Dict[str, int]
    locations: Dict[str, int]
    common_services: List[str]
    market_gaps: List[str]
    opportunities: List[str]
    analyzed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()

class CompetitionWatcher:
    """
    Watcher especializado para analizar competencia en limpieza de piscinas en Lima
    """

    def __init__(self):
        self.keyword = "limpieza de piscina lima"
        self.competitors: List[CompetitorData] = []
        self.market_analysis: Optional[MarketAnalysis] = None
        self.logger = logging.getLogger("competition_watcher")
        self.current_run_id: Optional[str] = None

        # Configurar logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Inicializar tablas de base de datos
        try:
            init_competition_tables()
        except Exception as e:
            self.logger.warning(f"No se pudieron inicializar tablas de BD: {e}")

    async def collect_competitor_data(self, max_competitors: int = 15) -> int:
        """
        Fase 1: Recolectar datos de competidores y almacenarlos en BD
        Retorna el número de competidores encontrados
        """
        self.logger.info(f"🔍 Iniciando recolección de datos para: {self.keyword}")

        # Iniciar tracking de la ejecución
        self.current_run_id = start_competition_run(self.keyword, "collection")

        try:
            # 1. Buscar URLs de competencia
            competitor_urls = await self.search_competition_urls(max_competitors * 2)

            if not competitor_urls:
                self.logger.warning("⚠️ No se encontraron URLs de competencia")
                update_competition_run(self.current_run_id, "completed", 0, False)
                return 0

            # 2. Analizar cada competidor y guardar en BD
            competitors_found = 0
            for url in competitor_urls[:max_competitors]:
                competitor = await self.analyze_competitor(url)
                if competitor:
                    # Convertir a dict para guardar
                    competitor_dict = asdict(competitor)
                    save_competitor(competitor_dict, self.keyword)
                    competitors_found += 1

                    self.logger.info(f"💾 Competidor guardado: {competitor.name}")

                # Pequeña pausa para no sobrecargar
                await asyncio.sleep(1)

            # Actualizar estado de la ejecución
            update_competition_run(self.current_run_id, "completed", competitors_found, False)

            self.logger.info(f"✅ Recolección completada. {competitors_found} competidores guardados")
            return competitors_found

        except Exception as e:
            self.logger.error(f"❌ Error en recolección: {e}")
            update_competition_run(self.current_run_id, "failed", 0, False, str(e))
            raise

    def load_competitor_data(self, limit: Optional[int] = None) -> List[CompetitorData]:
        """
        Cargar datos de competidores desde la base de datos
        """
        self.logger.info(f"📂 Cargando datos de competidores para: {self.keyword}")

        try:
            # Cargar desde BD
            competitor_dicts = load_competitors(self.keyword, limit)

            # Convertir a objetos CompetitorData
            self.competitors = []
            for comp_dict in competitor_dicts:
                try:
                    competitor = CompetitorData(
                        name=comp_dict['name'],
                        website=comp_dict['website'],
                        services=comp_dict['services'],
                        location=comp_dict['location'],
                        pricing_info=comp_dict['pricing_info'],
                        contact_info=comp_dict['contact_info'],
                        social_media=comp_dict['social_media'],
                        description=comp_dict['description'],
                        scraped_at=datetime.fromisoformat(comp_dict['scraped_at']) if comp_dict['scraped_at'] else None
                    )
                    self.competitors.append(competitor)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error convirtiendo competidor {comp_dict.get('name', 'unknown')}: {e}")

            self.logger.info(f"✅ Cargados {len(self.competitors)} competidores desde BD")
            return self.competitors

        except Exception as e:
            self.logger.error(f"❌ Error cargando datos: {e}")
            return []

    async def analyze_competitor_data(self) -> MarketAnalysis:
        """
        Fase 2: Analizar datos de competidores ya recolectados
        """
        if not self.competitors:
            self.logger.warning("⚠️ No hay datos de competidores para analizar. Carga datos primero.")
            # Intentar cargar automáticamente
            self.load_competitor_data()

            if not self.competitors:
                raise ValueError("No hay datos de competidores disponibles para análisis")

        self.logger.info(f"🔬 Iniciando análisis de {len(self.competitors)} competidores")

        # Iniciar tracking de análisis
        analysis_run_id = start_competition_run(self.keyword, "analysis")

        try:
            # Generar análisis
            self.market_analysis = await self._generate_market_analysis()

            # Guardar análisis en BD
            analysis_dict = {
                'keyword': self.market_analysis.keyword,
                'total_competitors': self.market_analysis.total_competitors,
                'service_categories': self.market_analysis.service_categories,
                'price_ranges': self.market_analysis.price_ranges,
                'locations': self.market_analysis.locations,
                'common_services': self.market_analysis.common_services,
                'market_gaps': self.market_analysis.market_gaps,
                'opportunities': self.market_analysis.opportunities,
                'analyzed_at': self.market_analysis.analyzed_at.isoformat() if self.market_analysis.analyzed_at else datetime.now().isoformat()
            }

            analysis_id = save_competition_analysis(analysis_dict)

            # Actualizar estado
            update_competition_run(analysis_run_id, "completed", len(self.competitors), True)

            self.logger.info(f"✅ Análisis completado y guardado (ID: {analysis_id})")
            return self.market_analysis

        except Exception as e:
            self.logger.error(f"❌ Error en análisis: {e}")
            update_competition_run(analysis_run_id, "failed", len(self.competitors), False, str(e))
            raise

    async def run_full_analysis(self, max_competitors: int = 15) -> MarketAnalysis:
        """
        Ejecutar análisis completo: recolección + análisis
        """
        self.logger.info("🚀 Iniciando análisis completo de competencia...")

        # Iniciar tracking completo
        full_run_id = start_competition_run(self.keyword, "full")

        try:
            # Fase 1: Recolección
            competitors_found = await self.collect_competitor_data(max_competitors)

            if competitors_found == 0:
                update_competition_run(full_run_id, "completed", 0, False, "No se encontraron competidores")
                return MarketAnalysis(
                    keyword=self.keyword,
                    total_competitors=0,
                    service_categories={},
                    price_ranges={},
                    locations={},
                    common_services=[],
                    market_gaps=["No se encontraron competidores para analizar"],
                    opportunities=[]
                )

            # Fase 2: Análisis
            analysis = await self.analyze_competitor_data()

            # Actualizar estado final
            update_competition_run(full_run_id, "completed", competitors_found, True)

            self.logger.info("✅ Análisis completo finalizado")
            return analysis

        except Exception as e:
            self.logger.error(f"❌ Error en análisis completo: {e}")
            update_competition_run(full_run_id, "failed", 0, False, str(e))
            raise

    def get_analysis_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtener historial de análisis realizados
        """
        try:
            return load_competition_analysis(self.keyword, limit)
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo historial: {e}")
            return []

    def get_run_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener historial de ejecuciones
        """
        try:
            return get_competition_runs(self.keyword, limit)
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo historial de ejecuciones: {e}")
            return []

    async def initialize_database(self):
        """Inicializar las tablas de la base de datos"""
        try:
            init_competition_tables()
            self.logger.info("✅ Tablas de Competition Watcher inicializadas")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando tablas: {e}")
            raise

    async def search_competition_urls(self, max_results: int = 20) -> List[str]:
        """
        Buscar URLs de competencia en Google
        """
        self.logger.info(f"🔍 Buscando competencia para: {self.keyword}")

        try:
            # Usar el sistema de búsqueda existente
            from config.sources import search_urls_for
            urls = await search_urls_for(self.keyword, max_results)

            # Filtrar URLs relevantes (empresas locales, servicios)
            filtered_urls = []
            for url in urls:
                if self._is_relevant_competitor_url(url):
                    filtered_urls.append(url)

            self.logger.info(f"📊 Encontradas {len(filtered_urls)} URLs de competencia relevantes")
            return filtered_urls[:max_results]

        except Exception as e:
            self.logger.error(f"❌ Error buscando URLs: {e}")
            return []

    def _is_relevant_competitor_url(self, url: str) -> bool:
        """
        Determinar si una URL es relevante para análisis de competencia
        """
        url_lower = url.lower()

        # Patrones de URLs relevantes
        relevant_patterns = [
            # Empresas locales
            'empresa', 'servicio', 'limpieza', 'mantenimiento', 'piscina',
            # Plataformas de servicios
            'serviciosperu', 'yape', 'mercado', 'olx',
            # Directorios locales
            'paginasamarillas', 'yelp', 'google', 'facebook',
            # Sitios de empresas
            '.com.pe', '.pe', 'lima'
        ]

        # Excluir patrones irrelevantes
        irrelevant_patterns = [
            'wikipedia', 'youtube', 'facebook.com/groups',
            'instagram', 'twitter', 'linkedin'
        ]

        # Verificar relevancia
        has_relevant = any(pattern in url_lower for pattern in relevant_patterns)
        has_irrelevant = any(pattern in url_lower for pattern in irrelevant_patterns)

        return has_relevant and not has_irrelevant

    async def analyze_competitor(self, url: str) -> Optional[CompetitorData]:
        """
        Analizar una URL de competidor y extraer información
        """
        try:
            self.logger.info(f"🔬 Analizando competidor: {url}")

            # Scrape la página
            result = await scrapling_scraper.scrape_url(url)
            if not result or not result.get('success'):
                return None

            content = result.get('content', '')

            # Extraer información usando IA
            competitor_data = await self._extract_competitor_info_with_ai(url, content)

            if competitor_data:
                self.logger.info(f"✅ Competidor identificado: {competitor_data.name}")
                return competitor_data

        except Exception as e:
            self.logger.error(f"❌ Error analizando {url}: {e}")

        return None

    async def _extract_competitor_info_with_ai(self, url: str, content: str) -> Optional[CompetitorData]:
        """
        Extraer información del competidor usando análisis de texto básico
        """
        try:
            # Análisis básico sin IA por ahora
            name = self._extract_business_name(content, url)
            if not name:
                return None

            services = self._extract_services(content)
            location = self._extract_location(content)
            pricing_info = self._extract_pricing(content)
            contact_info = self._extract_contact(content)

            return CompetitorData(
                name=name,
                website=url,
                services=services,
                location=location,
                pricing_info=pricing_info,
                contact_info=contact_info,
                description=self._extract_description(content)
            )

        except Exception as e:
            self.logger.error(f"❌ Error en extracción: {e}")

        return None

    async def run_competition_analysis(self, max_competitors: int = 15) -> MarketAnalysis:
        """
        Método legacy - usar run_full_analysis en su lugar
        """
        self.logger.warning("⚠️ run_competition_analysis está deprecated. Usa run_full_analysis()")
        return await self.run_full_analysis(max_competitors)
        """
        Ejecutar análisis completo de competencia
        """
        self.logger.info("🚀 Iniciando análisis de competencia...")

        # 1. Buscar URLs de competencia
        competitor_urls = await self.search_competition_urls(max_competitors * 2)

        # 2. Analizar cada competidor
        for url in competitor_urls[:max_competitors]:
            competitor = await self.analyze_competitor(url)
            if competitor:
                self.competitors.append(competitor)

            # Pequeña pausa para no sobrecargar
            await asyncio.sleep(1)

        # 3. Generar análisis de mercado
        self.market_analysis = await self._generate_market_analysis()

        self.logger.info(f"✅ Análisis completado. {len(self.competitors)} competidores identificados")

        return self.market_analysis

    async def _generate_market_analysis(self) -> MarketAnalysis:
        """
        Generar análisis de mercado basado en competidores encontrados
        """
        if not self.competitors:
            return MarketAnalysis(
                keyword=self.keyword,
                total_competitors=0,
                service_categories={},
                price_ranges={},
                locations={},
                common_services=[],
                market_gaps=[],
                opportunities=[]
            )

        # Análisis de servicios
        service_categories = {}
        locations = {}
        price_ranges = {}
        all_services = []

        for competitor in self.competitors:
            # Categorizar servicios
            for service in competitor.services:
                service_lower = service.lower()
                if 'limpieza' in service_lower or 'mantenimiento' in service_lower:
                    category = 'Limpieza/Mantenimiento'
                elif 'reparacion' in service_lower or 'reparar' in service_lower:
                    category = 'Reparaciones'
                elif 'instalacion' in service_lower or 'montaje' in service_lower:
                    category = 'Instalación'
                elif 'cloracion' in service_lower or 'quimico' in service_lower:
                    category = 'Tratamiento Químico'
                else:
                    category = 'Otros Servicios'

                service_categories[category] = service_categories.get(category, 0) + 1
                all_services.append(service)

            # Análisis de ubicación
            location = competitor.location
            if 'lima' in location.lower():
                locations['Lima'] = locations.get('Lima', 0) + 1
            else:
                locations[location] = locations.get(location, 0) + 1

            # Análisis de precios (si disponible)
            if competitor.pricing_info:
                if 's/' in competitor.pricing_info.lower() or 'sol' in competitor.pricing_info.lower():
                    price_ranges['Soles'] = price_ranges.get('Soles', 0) + 1
                elif '$' in competitor.pricing_info:
                    price_ranges['Dólares'] = price_ranges.get('Dólares', 0) + 1
                else:
                    price_ranges['No especificado'] = price_ranges.get('No especificado', 0) + 1

        # Identificar servicios más comunes
        common_services = list(set(all_services))[:10]  # Top 10 servicios únicos

        # Generar insights usando IA
        market_gaps, opportunities = await self._identify_market_gaps_and_opportunities()

        return MarketAnalysis(
            keyword=self.keyword,
            total_competitors=len(self.competitors),
            service_categories=service_categories,
            price_ranges=price_ranges,
            locations=locations,
            common_services=common_services,
            market_gaps=market_gaps,
            opportunities=opportunities
        )

    async def _identify_market_gaps_and_opportunities(self) -> Tuple[List[str], List[str]]:
        """
        Identificar gaps de mercado y oportunidades usando lógica básica
        """
        try:
            # Análisis básico basado en competidores encontrados
            gaps = []
            opportunities = []

            # Analizar servicios más comunes
            if self.competitors:
                all_services = []
                for comp in self.competitors:
                    all_services.extend(comp.services)

                service_counts = {}
                for service in all_services:
                    service_counts[service] = service_counts.get(service, 0) + 1

                # Gaps: servicios poco ofrecidos
                if len(self.competitors) > 0:
                    avg_services_per_competitor = len(all_services) / len(self.competitors)
                    if avg_services_per_competitor < 2:
                        gaps.append("Especialización limitada - muchos competidores ofrecen pocos servicios")

                # Oportunidades basadas en análisis
                opportunities.append("Ofrecer paquetes de servicios integrales (limpieza + mantenimiento + tratamiento)")
                opportunities.append("Implementar sistema de reservas online y pagos digitales")
                opportunities.append("Crear programa de mantenimiento preventivo mensual")

            return gaps, opportunities

        except Exception as e:
            self.logger.error(f"❌ Error identificando gaps de mercado: {e}")
            return [], []

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generar reporte completo de análisis de competencia
        """
        if not self.market_analysis:
            return "No hay análisis disponible. Ejecuta run_competition_analysis() primero."

        report = f"""
# 📊 REPORTE DE ANÁLISIS DE COMPETENCIA
## Mercado: {self.keyword}

**Fecha de Análisis:** {self.market_analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S') if self.market_analysis.analyzed_at else 'No disponible'}
**Competidores Analizados:** {self.market_analysis.total_competitors}

## 🎯 RESUMEN EJECUTIVO

### Servicios Más Ofrecidos
{chr(10).join(f"- **{cat}**: {count} competidores" for cat, count in self.market_analysis.service_categories.items())}

### Distribución Geográfica
{chr(10).join(f"- **{loc}**: {count} competidores" for loc, count in self.market_analysis.locations.items())}

### Información de Precios
{chr(10).join(f"- **{price}**: {count} competidores" for price, count in self.market_analysis.price_ranges.items())}

## 🏢 COMPETIDORES IDENTIFICADOS

"""

        for i, competitor in enumerate(self.competitors, 1):
            report += f"""
### {i}. {competitor.name}
- **Website:** {competitor.website}
- **Ubicación:** {competitor.location}
- **Servicios:** {', '.join(competitor.services) if competitor.services else 'No especificados'}
"""

            if competitor.pricing_info:
                report += f"- **Precios:** {competitor.pricing_info}\n"
            if competitor.contact_info:
                report += f"- **Contacto:** {competitor.contact_info}\n"
            if competitor.description:
                report += f"- **Descripción:** {competitor.description}\n"

        report += f"""

## 💡 GAPS DE MERCADO IDENTIFICADOS

{chr(10).join(f"- {gap}" for gap in self.market_analysis.market_gaps)}

## 🚀 OPORTUNIDADES DE NEGOCIO

{chr(10).join(f"- {opp}" for opp in self.market_analysis.opportunities)}

## 📈 CONCLUSIONES

Este análisis proporciona una visión clara del mercado de limpieza de piscinas en Lima,
identificando tanto la competencia actual como oportunidades para diferenciarse.

---
*Reporte generado automáticamente por Competition Watcher*
"""

        # Guardar reporte si se especifica ruta
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"💾 Reporte guardado en: {output_path}")

        return report

    def _extract_business_name(self, content: str, url: str) -> Optional[str]:
        """Extraer nombre de empresa del contenido"""
        # Patrones comunes para nombres de empresa
        patterns = [
            r'<title[^>]*>([^<]+)</title>',  # Título de la página
            r'<h1[^>]*>([^<]+)</h1>',       # Encabezado principal
            r'class="[^"]*business[^"]*"[^>]*>([^<]+)</',
            r'class="[^"]*company[^"]*"[^>]*>([^<]+)</',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if len(name) > 3 and not any(word in name.lower() for word in ['http', 'www', 'com', 'facebook', 'instagram']):
                    return name

        # Fallback: usar dominio como nombre
        try:
            domain = urlparse(url).netloc.replace('www.', '')
            return f"Servicio {domain.split('.')[0].title()}"
        except:
            return "Servicio Local"

    def _extract_services(self, content: str) -> List[str]:
        """Extraer servicios ofrecidos"""
        services = []
        service_keywords = [
            'limpieza', 'mantenimiento', 'reparación', 'instalación',
            'cloración', 'filtrado', 'desinfección', 'tratamiento',
            'revestimiento', 'pintura', 'reparar', 'montaje'
        ]

        content_lower = content.lower()
        for keyword in service_keywords:
            if keyword in content_lower:
                services.append(keyword.title())

        return list(set(services))  # Eliminar duplicados

    def _extract_location(self, content: str) -> str:
        """Extraer ubicación"""
        location_patterns = [
            r'lima[^a-zA-Z]*perú',
            r'lima[^a-zA-Z]*peru',
            r'distrito[^a-zA-Z]*lima',
            r'provincia[^a-zA-Z]*lima'
        ]

        content_lower = content.lower()
        for pattern in location_patterns:
            if re.search(pattern, content_lower):
                return "Lima, Perú"

        # Buscar menciones de Lima
        if 'lima' in content_lower:
            return "Lima, Perú"

        return "Lima, Perú"  # Default

    def _extract_pricing(self, content: str) -> Optional[str]:
        """Extraer información de precios"""
        # Patrones de precios comunes en Perú
        price_patterns = [
            r'S/\s*\d+[\.,]?\d*',  # S/ 100.00
            r'soles?\s*\d+[\.,]?\d*',  # soles 100
            r'\$\s*\d+[\.,]?\d*',  # $ 100
            r'precio[^a-zA-Z]*\d+[\.,]?\d*',  # precio 100
        ]

        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            prices.extend(matches)

        if prices:
            return ', '.join(list(set(prices)))

        return None

    def _extract_contact(self, content: str) -> Optional[str]:
        """Extraer información de contacto"""
        # Patrones de teléfono y email
        phone_patterns = [
            r'\b9\d{2}[\s\-\.]?\d{3}[\s\-\.]?\d{3}\b',  # Celular peruano
            r'\b\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b',   # Teléfono fijo
        ]

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        contacts = []

        # Extraer teléfonos
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            contacts.extend([f"Tel: {match}" for match in matches])

        # Extraer emails
        email_matches = re.findall(email_pattern, content)
        contacts.extend([f"Email: {match}" for match in email_matches])

        if contacts:
            return ', '.join(list(set(contacts)))

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extraer descripción del negocio"""
        # Buscar meta description
        meta_desc = re.search(r'<meta[^>]*description[^>]*content="([^"]+)"', content, re.IGNORECASE)
        if meta_desc:
            return meta_desc.group(1)[:200] + "..." if len(meta_desc.group(1)) > 200 else meta_desc.group(1)

        # Buscar párrafos descriptivos
        paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', content, re.IGNORECASE)
        for p in paragraphs:
            p_clean = re.sub(r'<[^>]+>', '', p).strip()
            if len(p_clean) > 50 and any(word in p_clean.lower() for word in ['servicio', 'empresa', 'limpieza', 'mantenimiento']):
                return p_clean[:200] + "..." if len(p_clean) > 200 else p_clean

        return None

# Instancia global
competition_watcher = CompetitionWatcher()
