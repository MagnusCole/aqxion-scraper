"""
Context Optimization System for GPT-5 Nano
Based on Devin AI context management techniques
"""

import asyncio
import hashlib
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ai_service import ai_service
from simple_cache import cache_manager

@dataclass
class ContextChunk:
    """Represents a chunk of context for processing"""
    id: str
    content: str
    token_count: int
    summary: Optional[str] = None
    relevance_score: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContextWindow:
    """Manages the context window for GPT-5 Nano"""
    max_tokens: int = 400000  # GPT-5 Nano context window
    reserved_tokens: int = 50000  # Reserve for response
    available_tokens: int = 350000

    current_chunks: List[ContextChunk] = field(default_factory=list)
    total_tokens: int = 0

    def __post_init__(self):
        if self.current_chunks is None:
            self.current_chunks = []

    def can_add_chunk(self, chunk: ContextChunk) -> bool:
        """Check if a chunk can be added to the context window"""
        return self.total_tokens + chunk.token_count <= self.available_tokens

    def add_chunk(self, chunk: ContextChunk) -> bool:
        """Add a chunk to the context window"""
        if not self.can_add_chunk(chunk):
            return False

        self.current_chunks.append(chunk)
        self.total_tokens += chunk.token_count
        return True

    def remove_chunk(self, chunk_id: str) -> bool:
        """Remove a chunk from the context window"""
        for i, chunk in enumerate(self.current_chunks):
            if chunk.id == chunk_id:
                self.total_tokens -= chunk.token_count
                self.current_chunks.pop(i)
                return True
        return False

    def get_context_string(self, max_tokens: Optional[int] = None) -> str:
        """Get the current context as a formatted string"""
        if max_tokens:
            # Sort by relevance and take top chunks that fit
            sorted_chunks = sorted(self.current_chunks,
                                 key=lambda x: x.relevance_score,
                                 reverse=True)

            context_parts = []
            total_tokens = 0

            for chunk in sorted_chunks:
                if total_tokens + chunk.token_count <= max_tokens:
                    context_parts.append(chunk.content)
                    total_tokens += chunk.token_count
                else:
                    break

            return "\n\n".join(context_parts)

        # Return all chunks
        return "\n\n".join([chunk.content for chunk in self.current_chunks])

    def clear(self):
        """Clear all chunks from context window"""
        self.current_chunks = []
        self.total_tokens = 0

class ContextOptimizer:
    """Optimizes context management for GPT-5 Nano"""

    def __init__(self):
        self.context_window = ContextWindow()
        self.chunk_cache: Dict[str, ContextChunk] = {}

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text (rough approximation)"""
        # GPT models: ~4 characters per token on average
        return len(text) // 4

    def create_chunk(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ContextChunk:
        """Create a context chunk from content"""
        chunk_id = hashlib.md5(content.encode()).hexdigest()[:8]
        token_count = self.estimate_tokens(content)

        chunk = ContextChunk(
            id=chunk_id,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )

        # Cache the chunk
        self.chunk_cache[chunk_id] = chunk
        return chunk

    async def generate_summary(self, content: str, max_length: int = 200) -> Optional[str]:
        """Generate a summary of content using GPT-5 Nano"""
        if not ai_service.client:
            return None

        prompt = f"""
        Resume el siguiente contenido en máximo {max_length} caracteres.
        Mantén la información más importante y relevante.

        Contenido:
        {content}

        Resumen conciso:"""

        try:
            response = await ai_service.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                reasoning_effort="low",
                max_completion_tokens=100
            )

            summary = response.choices[0].message.content
            return summary.strip() if summary else None

        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return None

    def split_into_chunks(self, content: str, max_chunk_tokens: int = 50000) -> List[ContextChunk]:
        """Split large content into manageable chunks"""
        if self.estimate_tokens(content) <= max_chunk_tokens:
            return [self.create_chunk(content)]

        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', content)

        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)

            if current_tokens + sentence_tokens > max_chunk_tokens and current_chunk:
                # Create chunk from current content
                chunks.append(self.create_chunk(current_chunk.strip()))
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += " " + sentence
                current_tokens += sentence_tokens

        # Add remaining content
        if current_chunk.strip():
            chunks.append(self.create_chunk(current_chunk.strip()))

        return chunks

    async def optimize_context(self, content: str, query: str) -> str:
        """Optimize context for a specific query"""
        print(f"🔄 Optimizing context for query: {query[:50]}...")

        # Split content into chunks
        chunks = self.split_into_chunks(content)

        # Generate summaries for large chunks
        optimized_chunks = []
        for chunk in chunks:
            if chunk.token_count > 10000:  # Summarize large chunks
                summary = await self.generate_summary(chunk.content)
                if summary:
                    chunk.summary = summary
                    # Create summarized version
                    summarized_chunk = ContextChunk(
                        id=f"{chunk.id}_summary",
                        content=summary,
                        token_count=self.estimate_tokens(summary),
                        metadata={"original_chunk": chunk.id, "is_summary": True}
                    )
                    optimized_chunks.append(summarized_chunk)
                else:
                    optimized_chunks.append(chunk)
            else:
                optimized_chunks.append(chunk)

        # Score relevance to query
        for chunk in optimized_chunks:
            relevance = self._calculate_relevance(chunk.content, query)
            chunk.relevance_score = relevance

        # Add to context window (most relevant first)
        self.context_window.clear()
        optimized_chunks.sort(key=lambda x: x.relevance_score, reverse=True)

        for chunk in optimized_chunks:
            if self.context_window.can_add_chunk(chunk):
                self.context_window.add_chunk(chunk)
            else:
                break  # No more space

        return self.context_window.get_context_string()

    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score between content and query"""
        content_lower = content.lower()
        query_lower = query.lower()

        # Exact matches get highest score
        if query_lower in content_lower:
            return 1.0

        # Count query terms in content
        query_terms = set(query_lower.split())
        content_terms = set(content_lower.split())

        matching_terms = query_terms.intersection(content_terms)
        relevance = len(matching_terms) / len(query_terms) if query_terms else 0

        # Boost score for important keywords
        important_keywords = ["marketing", "digital", "pymes", "limpieza", "piscina", "agencia"]
        boost = sum(1 for keyword in important_keywords if keyword in content_lower) * 0.1

        return min(1.0, relevance + boost)

    async def query_with_context(self, query: str, context: str) -> Optional[str]:
        """Execute a query with optimized context"""
        if not ai_service.client:
            return None

        # Optimize context for this query
        optimized_context = await self.optimize_context(context, query)

        prompt = f"""
        Basándote en el siguiente contexto, responde a la consulta del usuario.

        CONTEXTO:
        {optimized_context}

        CONSULTA:
        {query}

        Respuesta:"""

        try:
            response = await ai_service.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                reasoning_effort="low",
                max_completion_tokens=1000
            )

            content = response.choices[0].message.content
            return content.strip() if content else None

        except Exception as e:
            print(f"❌ Error in context query: {e}")
            return None

    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about current context"""
        return {
            "total_chunks": len(self.context_window.current_chunks),
            "total_tokens": self.context_window.total_tokens,
            "available_tokens": self.context_window.available_tokens - self.context_window.total_tokens,
            "max_tokens": self.context_window.max_tokens,
            "utilization_percent": (self.context_window.total_tokens / self.context_window.available_tokens) * 100,
            "cached_chunks": len(self.chunk_cache)
        }

# Global context optimizer instance
context_optimizer = ContextOptimizer()

# Example usage
async def demo_context_optimization():
    """Demonstrate context optimization"""
    print("🧠 Demo: Context Optimization for GPT-5 Nano")
    print("=" * 50)

    # Sample large content
    large_content = """
    En el mundo del marketing digital en Perú, las empresas están adoptando cada vez más
    estrategias digitales para llegar a sus clientes. Las agencias de marketing en Lima
    ofrecen servicios como SEO, SEM, redes sociales, email marketing y creación de contenido.

    La limpieza de piscinas en Lima es un servicio esencial para mantener las propiedades
    en óptimas condiciones. Los servicios profesionales incluyen limpieza profunda,
    mantenimiento preventivo, tratamiento químico del agua y reparaciones.

    Los dashboards para pymes en Perú permiten a las pequeñas y medianas empresas
    monitorear su rendimiento en tiempo real. Estos sistemas incluyen métricas de ventas,
    análisis de clientes, reportes financieros y KPIs operativos.

    El marketing digital ha revolucionado la forma en que las empresas peruanas
    se conectan con sus clientes. Las estrategias incluyen posicionamiento en buscadores,
    publicidad pagada, marketing de contenidos y automatización de marketing.

    Los servicios de limpieza especializados ofrecen soluciones integrales que van
    desde la limpieza básica hasta tratamientos avanzados del agua, mantenimiento
    de equipos de filtración y reparación de sistemas de piscina.
    """ * 10  # Make it larger

    query = "¿Qué servicios ofrecen las agencias de marketing en Lima?"

    print(f"📊 Content length: {len(large_content)} characters")
    print(f"📊 Estimated tokens: {context_optimizer.estimate_tokens(large_content)}")

    # Optimize context
    optimized = await context_optimizer.optimize_context(large_content, query)

    print("\n📈 Context optimization results:")
    stats = context_optimizer.get_context_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")

    # Query with optimized context
    print("\n🤖 Querying with optimized context...")
    response = await context_optimizer.query_with_context(query, large_content)

    if response:
        print(f"✅ Response: {response[:200]}...")
    else:
        print("❌ No response generated")

if __name__ == "__main__":
    asyncio.run(demo_context_optimization())
