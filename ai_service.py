"""
AI Service Module for Aqxion Scraper
Provides AI-powered content classification, keyword generation, and relevance scoring
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

from config_v2 import get_settings
from simple_cache import cache_manager

settings = get_settings()


@dataclass
class ClassificationResult:
    """Result of AI-powered content classification"""
    tag: str
    confidence: float
    reasoning: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class KeywordGenerationResult:
    """Result of AI-powered keyword generation"""
    keywords: List[str]
    reasoning: str
    market_trends: Optional[List[str]] = None


class AIService:
    """AI service for content analysis and keyword generation"""

    def __init__(self):
        self.client = None
        self._rate_limiter = {}
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client if available"""
        if not OPENAI_AVAILABLE:
            print("⚠️ OpenAI library not available. Install with: pip install openai")
            return

        if not settings.openai.api_key:
            print("⚠️ OpenAI API key not configured. Set OPENAI_API_KEY environment variable")
            return

        try:
            self.client = AsyncOpenAI(
                api_key=settings.openai.api_key.get_secret_value(),
                base_url=settings.openai.base_url
            )
            print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")

    async def _rate_limit_check(self) -> bool:
        """Check if we can make another API call within rate limits"""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        self._rate_limiter = {
            req_time: count for req_time, count in self._rate_limiter.items()
            if req_time > window_start
        }

        # Check current request count
        current_requests = sum(self._rate_limiter.values())

        if current_requests >= settings.openai.requests_per_minute:
            return False

        # Add current request
        self._rate_limiter[now] = self._rate_limiter.get(now, 0) + 1
        return True

    async def classify_content_ai(self, title: str, body: Optional[str] = None) -> Optional[ClassificationResult]:
        """Classify content using AI with caching"""
        if not self.client or not settings.openai.enable_content_classification:
            return None

        content = f"{title} {body or ''}".strip()
        if not content:
            return None

        # Check cache first
        cache_key = f"ai_classification:{hash(content[:500])}"
        cached_result = await cache_manager.get(cache_key, 'intent')
        if cached_result:
            try:
                data = json.loads(cached_result)
                return ClassificationResult(**data)
            except:
                pass

        # Rate limit check
        if not await self._rate_limit_check():
            print("⚠️ Rate limit reached, skipping AI classification")
            return None

        try:
            prompt = f"""
            Analiza el siguiente contenido y clasifícalo en una de estas categorías:

            - dolor: El usuario expresa un problema urgente, necesidad inmediata, o está buscando solución a un issue
            - busqueda: El usuario está investigando opciones, comparando servicios, o buscando información general
            - objecion: El usuario expresa dudas, preocupaciones, o está evaluando si necesita el servicio
            - ruido: Contenido irrelevante, spam, o no relacionado con necesidades de negocio

            Contenido a analizar:
            Título: {title}
            Texto: {body or 'Sin contenido adicional'}

            IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido en este formato exacto:
            {{"tag": "dolor|busqueda|objecion|ruido", "confidence": 0.0-1.0, "reasoning": "explicación breve"}}

            No incluyas ningún texto adicional, solo el JSON puro.
            """

            # Prepare request parameters based on model
            request_params = {
                "model": settings.openai.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            
            # GPT-5 Nano only supports default temperature (1), no other values
            if "gpt-5-nano" not in settings.openai.model:
                request_params["temperature"] = 0.1
            
            # Add reasoning_effort for GPT-5 models
            if "gpt-5" in settings.openai.model:
                request_params["reasoning_effort"] = "low"
            
            # GPT-5 Nano uses max_completion_tokens instead of max_tokens
            if "gpt-5-nano" in settings.openai.model:
                request_params["max_completion_tokens"] = min(settings.openai.max_tokens_per_request, 500)
            else:
                request_params["max_tokens"] = min(settings.openai.max_tokens_per_request, 500)

            response = await self.client.chat.completions.create(**request_params)

            result_text = response.choices[0].message.content
            if not result_text:
                print("❌ Empty response from OpenAI API")
                return None

            result_text = result_text.strip()

            # Parse JSON response
            try:
                result_data = json.loads(result_text)
                result = ClassificationResult(
                    tag=result_data.get('tag', 'ruido'),
                    confidence=float(result_data.get('confidence', 0.5)),
                    reasoning=result_data.get('reasoning', 'AI classification'),
                    metadata={'ai_model': settings.openai.model, 'timestamp': datetime.now().isoformat()}
                )

                # Cache the result
                await cache_manager.set(cache_key, json.dumps({
                    'tag': result.tag,
                    'confidence': result.confidence,
                    'reasoning': result.reasoning,
                    'metadata': result.metadata
                }), ttl=settings.openai.cache_ttl, cache_type='intent')

                return result

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse AI response: {e}")
                return None

        except Exception as e:
            print(f"❌ AI classification error: {e}")
            return None

    async def generate_keywords_ai(self, industry: str = "marketing digital", count: int = 10) -> Optional[KeywordGenerationResult]:
        """Generate relevant keywords using AI"""
        if not self.client or not settings.openai.enable_keyword_generation:
            return None

        # Check cache first
        cache_key = f"ai_keywords:{industry}:{count}"
        cached_result = await cache_manager.get(cache_key, 'url')
        if cached_result:
            try:
                data = json.loads(cached_result)
                return KeywordGenerationResult(**data)
            except:
                pass

        # Rate limit check
        if not await self._rate_limit_check():
            print("⚠️ Rate limit reached, skipping AI keyword generation")
            return None

        try:
            prompt = f"""Genera {min(count, 5)} keywords para marketing digital en Perú.

Responde solo con JSON:
{{"keywords": ["keyword1", "keyword2", "keyword3"], "reasoning": "explicación"}}"""

            # Prepare request parameters based on model
            request_params = {
                "model": settings.openai.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            
            # GPT-5 Nano only supports default temperature (1), no other values
            if "gpt-5-nano" not in settings.openai.model:
                request_params["temperature"] = 0.7
            
            # Add reasoning_effort for GPT-5 models
            if "gpt-5" in settings.openai.model:
                request_params["reasoning_effort"] = "low"
            
            # GPT-5 Nano uses max_completion_tokens instead of max_tokens
            if "gpt-5-nano" in settings.openai.model:
                request_params["max_completion_tokens"] = min(settings.openai.max_tokens_per_request, 1000)
            else:
                request_params["max_tokens"] = min(settings.openai.max_tokens_per_request, 1000)

            response = await self.client.chat.completions.create(**request_params)

            result_text = response.choices[0].message.content
            if not result_text:
                print("❌ Empty response from OpenAI API")
                return None

            result_text = result_text.strip()

            # Parse JSON response
            try:
                result_data = json.loads(result_text)
                result = KeywordGenerationResult(
                    keywords=result_data.get('keywords', []),
                    reasoning=result_data.get('reasoning', 'AI generated keywords'),
                    market_trends=result_data.get('market_trends', [])
                )

                # Cache the result
                await cache_manager.set(cache_key, json.dumps({
                    'keywords': result.keywords,
                    'reasoning': result.reasoning,
                    'market_trends': result.market_trends
                }), ttl=settings.openai.cache_ttl, cache_type='url')

                return result

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse AI keyword response: {e}")
                print(f"🔍 Debug - Raw response was: '{result_text}'")
                return None

        except Exception as e:
            print(f"❌ AI keyword generation error: {e}")
            return None

    async def score_relevance_ai(self, title: str, body: Optional[str] = None) -> Optional[int]:
        """Calculate relevance score using AI (experimental)"""
        if not self.client or not settings.openai.enable_relevance_scoring:
            return None

        content = f"{title} {body or ''}".strip()
        if not content:
            return None

        # Check cache first
        cache_key = f"ai_relevance:{hash(content[:500])}"
        cached_score = await cache_manager.get(cache_key, 'intent')
        if cached_score:
            try:
                return int(cached_score)
            except:
                pass

        # Rate limit check
        if not await self._rate_limit_check():
            print("⚠️ Rate limit reached, skipping AI relevance scoring")
            return None

        try:
            prompt = f"""
            Evalúa la relevancia de este contenido para identificar oportunidades de negocio en marketing digital.

            Contenido:
            Título: {title}
            Texto: {body or 'Sin contenido adicional'}

            Califica del 0-150 dónde:
            - 0-30: Completamente irrelevante
            - 31-70: Poco relevante
            - 71-110: Moderadamente relevante
            - 111-150: Altamente relevante (oportunidad clara)

            Factores a considerar:
            - Claridad de la necesidad/problema
            - Urgencia expresada
            - Potencial de conversión
            - Calidad del contenido

            Responde SOLO con un número entero entre 0-150.
            """

            # Prepare request parameters based on model
            request_params = {
                "model": settings.openai.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            
            # GPT-5 Nano only supports default temperature (1), no other values
            if "gpt-5-nano" not in settings.openai.model:
                request_params["temperature"] = 0.1
            
            # GPT-5 Nano uses max_completion_tokens instead of max_tokens
            if "gpt-5-nano" in settings.openai.model:
                request_params["max_completion_tokens"] = 10
            else:
                request_params["max_tokens"] = 10

            response = await self.client.chat.completions.create(**request_params)

            result_text = response.choices[0].message.content
            if not result_text:
                print("❌ Empty response from OpenAI API")
                return None

            result_text = result_text.strip()

            # Parse numeric response
            try:
                score = int(result_text)
                score = max(0, min(150, score))  # Clamp to valid range

                # Cache the result
                await cache_manager.set(cache_key, str(score), ttl=settings.openai.cache_ttl, cache_type='intent')

                return score

            except ValueError as e:
                print(f"❌ Failed to parse AI relevance score: {e}")
                return None

        except Exception as e:
            print(f"❌ AI relevance scoring error: {e}")
            return None


# Global AI service instance
ai_service = AIService()
