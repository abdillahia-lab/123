"""
TerraJinki RAG+ Module

Retrieval-Augmented Generation with Application-Aware Reasoning
for intelligent ordinance analysis and document understanding.

Based on SOTA research from arXiv on RAG++ and Application-Aware systems.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from uuid import uuid4
import asyncio
import json
import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DOCUMENT TYPES
# =============================================================================

class DocumentType(str, Enum):
    """Types of documents in the knowledge base."""
    ZONING_ORDINANCE = "zoning_ordinance"
    SOLAR_ORDINANCE = "solar_ordinance"
    COMPREHENSIVE_PLAN = "comprehensive_plan"
    SUBDIVISION_REGS = "subdivision_regulations"
    ENVIRONMENTAL_REGS = "environmental_regulations"
    BUILDING_CODE = "building_code"
    UTILITY_TARIFF = "utility_tariff"
    INTERCONNECTION_GUIDE = "interconnection_guide"
    PERMIT_APPLICATION = "permit_application"
    MEETING_MINUTES = "meeting_minutes"


@dataclass
class Document:
    """Document in the knowledge base."""
    id: str = field(default_factory=lambda: str(uuid4()))
    doc_type: DocumentType = DocumentType.ZONING_ORDINANCE

    # Identification
    title: str = ""
    jurisdiction: str = ""  # County or municipality name
    state: str = ""
    fips_code: str = ""

    # Content
    content: str = ""
    sections: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    source_url: str = ""
    effective_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    version: str = ""

    # Processing
    processed_at: Optional[datetime] = None
    chunk_ids: List[str] = field(default_factory=list)

    # Vector embeddings (stored separately)
    embedding_model: str = ""


@dataclass
class DocumentChunk:
    """Chunk of document for embedding and retrieval."""
    id: str = field(default_factory=lambda: str(uuid4()))
    document_id: str = ""

    # Content
    content: str = ""
    section_path: str = ""  # e.g., "Article 5 > Section 5.2 > Paragraph b"

    # Position
    start_char: int = 0
    end_char: int = 0
    chunk_index: int = 0

    # Semantic
    summary: str = ""
    keywords: List[str] = field(default_factory=list)

    # Embedding
    embedding: Optional[List[float]] = None


@dataclass
class RetrievalResult:
    """Result from semantic retrieval."""
    chunk: DocumentChunk
    score: float
    document: Optional[Document] = None
    highlights: List[str] = field(default_factory=list)


# =============================================================================
# QUERY UNDERSTANDING
# =============================================================================

@dataclass
class ParsedQuery:
    """Parsed and enriched user query."""
    original: str
    intent: str  # what_is, how_to, compare, analyze
    entities: Dict[str, List[str]] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    expanded_terms: List[str] = field(default_factory=list)
    jurisdiction_filter: Optional[str] = None
    doc_type_filter: Optional[DocumentType] = None


class QueryUnderstandingEngine:
    """
    Understands and expands user queries for better retrieval.

    Features:
    - Intent classification
    - Entity extraction (jurisdictions, project types, setbacks)
    - Query expansion with domain synonyms
    - Context-aware filtering
    """

    # Domain-specific synonyms for expansion
    SYNONYMS = {
        "solar": ["photovoltaic", "pv", "solar energy", "solar power", "solar farm", "solar array"],
        "setback": ["buffer", "offset", "distance requirement", "separation"],
        "height": ["vertical", "elevation", "tall", "maximum height"],
        "screening": ["buffering", "landscaping", "visual buffer", "vegetation"],
        "permit": ["approval", "authorization", "permission", "application"],
        "conditional use": ["cup", "special use permit", "sup", "special exception"],
        "utility scale": ["large scale", "commercial scale", "grid scale", "utility solar"],
        "community solar": ["shared solar", "solar garden", "subscriber solar"],
        "decommissioning": ["removal", "end of life", "abandonment", "dismantling"],
        "glare": ["reflection", "reflectivity", "glint"],
        "interconnection": ["grid connection", "utility connection", "point of interconnection"],
    }

    # Entity patterns
    ENTITY_PATTERNS = {
        "setback_distance": r'(\d+)\s*(feet|ft|foot|meters|m|yards)',
        "height_limit": r'(\d+)\s*(feet|ft|foot|meters|m)\s*(height|tall|maximum)',
        "acreage": r'(\d+(?:\.\d+)?)\s*(acres?|ac)',
        "capacity": r'(\d+(?:\.\d+)?)\s*(MW|kW|megawatts?|kilowatts?)',
        "percentage": r'(\d+(?:\.\d+)?)\s*(%|percent)',
    }

    def parse(self, query: str, context: Optional[Dict] = None) -> ParsedQuery:
        """Parse and understand user query."""
        parsed = ParsedQuery(original=query)

        # Classify intent
        parsed.intent = self._classify_intent(query)

        # Extract entities
        parsed.entities = self._extract_entities(query)

        # Extract constraints from context
        if context:
            if "jurisdiction" in context:
                parsed.jurisdiction_filter = context["jurisdiction"]
            if "state" in context:
                parsed.constraints["state"] = context["state"]

        # Expand query with synonyms
        parsed.expanded_terms = self._expand_query(query)

        return parsed

    def _classify_intent(self, query: str) -> str:
        """Classify query intent."""
        query_lower = query.lower()

        if any(w in query_lower for w in ["what is", "what are", "define", "meaning of"]):
            return "what_is"
        elif any(w in query_lower for w in ["how to", "how do", "process", "steps"]):
            return "how_to"
        elif any(w in query_lower for w in ["compare", "difference", "versus", "vs"]):
            return "compare"
        elif any(w in query_lower for w in ["allowed", "permitted", "can i", "legal"]):
            return "check_permission"
        elif any(w in query_lower for w in ["requirement", "need", "must", "shall"]):
            return "find_requirement"
        else:
            return "analyze"

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract domain entities from query."""
        entities = {}

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = [m[0] if isinstance(m, tuple) else m for m in matches]

        return entities

    def _expand_query(self, query: str) -> List[str]:
        """Expand query with domain synonyms."""
        expanded = [query]
        query_lower = query.lower()

        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                for syn in synonyms[:3]:  # Limit expansion
                    expanded.append(query_lower.replace(term, syn))

        return expanded


# =============================================================================
# RETRIEVAL ENGINE
# =============================================================================

class SemanticRetriever:
    """
    Semantic retrieval engine with hybrid search.

    Combines:
    - Dense retrieval (embeddings)
    - Sparse retrieval (BM25)
    - Metadata filtering
    - Re-ranking
    """

    def __init__(self, embedding_dim: int = 1024):
        self.embedding_dim = embedding_dim
        self._documents: Dict[str, Document] = {}
        self._chunks: Dict[str, DocumentChunk] = {}
        self._index_built = False

    def add_document(self, document: Document, chunks: List[DocumentChunk]):
        """Add document and its chunks to the index."""
        self._documents[document.id] = document
        for chunk in chunks:
            chunk.document_id = document.id
            self._chunks[chunk.id] = chunk
            document.chunk_ids.append(chunk.id)
        self._index_built = False

    async def retrieve(
        self,
        query: ParsedQuery,
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant document chunks.

        Args:
            query: Parsed query with expansion
            top_k: Maximum results to return
            min_score: Minimum similarity score

        Returns:
            Ranked list of retrieval results
        """
        results = []

        # In production, this would use a vector database
        # For now, use simple keyword matching as placeholder
        for chunk_id, chunk in self._chunks.items():
            score = self._compute_score(query, chunk)
            if score >= min_score:
                doc = self._documents.get(chunk.document_id)

                # Apply filters
                if query.jurisdiction_filter:
                    if doc and query.jurisdiction_filter.lower() not in doc.jurisdiction.lower():
                        continue

                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    document=doc,
                    highlights=self._extract_highlights(query.original, chunk.content),
                ))

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _compute_score(self, query: ParsedQuery, chunk: DocumentChunk) -> float:
        """Compute relevance score between query and chunk."""
        # Simple keyword matching (placeholder for embedding similarity)
        query_terms = set(query.original.lower().split())
        query_terms.update(term.lower() for term in query.expanded_terms)

        chunk_terms = set(chunk.content.lower().split())
        chunk_terms.update(kw.lower() for kw in chunk.keywords)

        overlap = len(query_terms & chunk_terms)
        if not query_terms:
            return 0.0

        return overlap / len(query_terms)

    def _extract_highlights(self, query: str, content: str, context_chars: int = 100) -> List[str]:
        """Extract highlighted snippets containing query terms."""
        highlights = []
        terms = query.lower().split()
        content_lower = content.lower()

        for term in terms:
            idx = content_lower.find(term)
            if idx >= 0:
                start = max(0, idx - context_chars)
                end = min(len(content), idx + len(term) + context_chars)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                highlights.append(snippet)

        return highlights[:3]


# =============================================================================
# APPLICATION-AWARE REASONING
# =============================================================================

@dataclass
class ReasoningContext:
    """Context for application-aware reasoning."""
    parcel_state: str = ""
    parcel_county: str = ""
    project_type: str = ""
    project_size_mw: float = 0.0
    project_size_acres: float = 0.0
    current_zoning: str = ""
    question: str = ""


@dataclass
class ReasoningResult:
    """Result from RAG+ reasoning."""
    answer: str = ""
    confidence: float = 0.0
    sources: List[RetrievalResult] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    applicable_requirements: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RAGPlusEngine:
    """
    RAG+ Engine: Retrieval-Augmented Generation with Application-Aware Reasoning.

    Features:
    - Multi-step reasoning over retrieved documents
    - Application-specific context injection
    - Requirement extraction and validation
    - Confidence scoring with source attribution
    """

    def __init__(
        self,
        retriever: SemanticRetriever,
        llm_client: Any = None,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.query_engine = QueryUnderstandingEngine()

    async def reason(
        self,
        question: str,
        context: ReasoningContext,
        max_sources: int = 5,
    ) -> ReasoningResult:
        """
        Perform application-aware reasoning.

        Args:
            question: User question
            context: Application context (parcel, project info)
            max_sources: Maximum sources to consider

        Returns:
            Reasoning result with answer and sources
        """
        result = ReasoningResult()

        # Step 1: Parse and understand query
        parsed_query = self.query_engine.parse(
            question,
            context={"jurisdiction": context.parcel_county, "state": context.parcel_state}
        )
        result.reasoning_chain.append(f"Query intent: {parsed_query.intent}")

        # Step 2: Retrieve relevant documents
        sources = await self.retriever.retrieve(parsed_query, top_k=max_sources)
        result.sources = sources
        result.reasoning_chain.append(f"Retrieved {len(sources)} relevant sources")

        if not sources:
            result.answer = "No relevant ordinance information found for this jurisdiction."
            result.confidence = 0.0
            return result

        # Step 3: Extract applicable requirements
        for source in sources:
            reqs = self._extract_requirements(source.chunk.content, context)
            result.applicable_requirements.extend(reqs)

        result.reasoning_chain.append(
            f"Extracted {len(result.applicable_requirements)} applicable requirements"
        )

        # Step 4: Generate answer with LLM (or use rule-based fallback)
        if self.llm_client:
            result.answer = await self._generate_answer_with_llm(
                question, sources, context
            )
        else:
            result.answer = self._generate_answer_rule_based(
                question, sources, context
            )

        # Step 5: Calculate confidence
        result.confidence = self._calculate_confidence(sources, context)

        # Step 6: Add warnings for potential issues
        result.warnings = self._check_for_warnings(sources, context)

        return result

    def _extract_requirements(
        self,
        content: str,
        context: ReasoningContext,
    ) -> List[Dict[str, Any]]:
        """Extract specific requirements from content."""
        requirements = []

        # Setback patterns
        setback_pattern = r'(?:setback|buffer|offset).*?(\d+)\s*(feet|ft|foot)'
        for match in re.finditer(setback_pattern, content, re.IGNORECASE):
            requirements.append({
                "type": "setback",
                "value": int(match.group(1)),
                "unit": "feet",
                "full_text": match.group(0),
            })

        # Height patterns
        height_pattern = r'(?:height|tall|maximum height).*?(\d+)\s*(feet|ft|foot)'
        for match in re.finditer(height_pattern, content, re.IGNORECASE):
            requirements.append({
                "type": "height_limit",
                "value": int(match.group(1)),
                "unit": "feet",
                "full_text": match.group(0),
            })

        # Lot coverage patterns
        coverage_pattern = r'(?:lot coverage|ground coverage|impervious).*?(\d+)\s*%'
        for match in re.finditer(coverage_pattern, content, re.IGNORECASE):
            requirements.append({
                "type": "lot_coverage",
                "value": int(match.group(1)),
                "unit": "percent",
                "full_text": match.group(0),
            })

        return requirements

    def _generate_answer_rule_based(
        self,
        question: str,
        sources: List[RetrievalResult],
        context: ReasoningContext,
    ) -> str:
        """Generate answer using rule-based approach."""
        question_lower = question.lower()

        # Combine relevant source content
        combined_content = "\n\n".join([
            f"[Source: {s.document.title if s.document else 'Unknown'}]\n{s.chunk.content}"
            for s in sources[:3]
        ])

        if "setback" in question_lower:
            return f"Based on {context.parcel_county} ordinances:\n\n{combined_content}"
        elif "permitted" in question_lower or "allowed" in question_lower:
            return f"Regarding solar development in {context.parcel_county}:\n\n{combined_content}"
        else:
            return f"Relevant ordinance information:\n\n{combined_content}"

    async def _generate_answer_with_llm(
        self,
        question: str,
        sources: List[RetrievalResult],
        context: ReasoningContext,
    ) -> str:
        """Generate answer using LLM."""
        # Build context for LLM
        source_text = "\n\n---\n\n".join([
            f"Source: {s.document.title if s.document else 'Unknown'}\n\n{s.chunk.content}"
            for s in sources[:5]
        ])

        prompt = f"""You are analyzing zoning and solar ordinances for renewable energy development.

PROJECT CONTEXT:
- Location: {context.parcel_county}, {context.parcel_state}
- Project Type: {context.project_type}
- Project Size: {context.project_size_mw} MW / {context.project_size_acres} acres
- Current Zoning: {context.current_zoning}

RELEVANT ORDINANCES:
{source_text}

QUESTION:
{question}

Provide a clear, specific answer based on the ordinances above. Include specific requirements
(setbacks, height limits, etc.) when relevant. If information is unclear or missing, say so.

ANSWER:"""

        response = await self.llm_client.complete(
            messages=[{"role": "user", "content": prompt}],
            json_mode=False,
        )
        return response.get("content", "Unable to generate answer.")

    def _calculate_confidence(
        self,
        sources: List[RetrievalResult],
        context: ReasoningContext,
    ) -> float:
        """Calculate confidence score for the answer."""
        if not sources:
            return 0.0

        # Base confidence from retrieval scores
        avg_score = sum(s.score for s in sources) / len(sources)

        # Boost for jurisdiction match
        jurisdiction_match = any(
            s.document and context.parcel_county.lower() in s.document.jurisdiction.lower()
            for s in sources
        )
        if jurisdiction_match:
            avg_score = min(1.0, avg_score * 1.2)

        # Boost for recent documents
        recent_sources = sum(
            1 for s in sources
            if s.document and s.document.last_updated
            and (datetime.utcnow() - s.document.last_updated).days < 365
        )
        if recent_sources > 0:
            avg_score = min(1.0, avg_score * 1.1)

        return round(avg_score, 2)

    def _check_for_warnings(
        self,
        sources: List[RetrievalResult],
        context: ReasoningContext,
    ) -> List[str]:
        """Check for potential issues that warrant warnings."""
        warnings = []

        # Check for outdated sources
        for source in sources:
            if source.document and source.document.last_updated:
                age_days = (datetime.utcnow() - source.document.last_updated).days
                if age_days > 730:  # > 2 years
                    warnings.append(
                        f"Source '{source.document.title}' may be outdated "
                        f"(last updated {age_days // 365} years ago)"
                    )

        # Check for moratorium mentions
        for source in sources:
            if "moratorium" in source.chunk.content.lower():
                warnings.append("A moratorium on solar development may be in effect")

        # Check for prohibitions
        for source in sources:
            if "prohibited" in source.chunk.content.lower():
                warnings.append("Solar development may be prohibited in this zone")

        return warnings


# =============================================================================
# DOCUMENT PROCESSOR
# =============================================================================

class DocumentProcessor:
    """
    Process documents into chunks for indexing.

    Features:
    - Intelligent chunking by section
    - Metadata extraction
    - Keyword extraction
    - Embedding generation (placeholder)
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process(self, document: Document) -> List[DocumentChunk]:
        """Process document into chunks."""
        chunks = []
        content = document.content

        # Try to split by sections first
        sections = self._split_by_sections(content)

        if sections:
            for section_path, section_content in sections:
                section_chunks = self._chunk_text(section_content, section_path)
                chunks.extend(section_chunks)
        else:
            # Fall back to simple chunking
            chunks = self._chunk_text(content, "")

        # Extract keywords for each chunk
        for chunk in chunks:
            chunk.keywords = self._extract_keywords(chunk.content)

        return chunks

    def _split_by_sections(self, content: str) -> List[Tuple[str, str]]:
        """Split content by section headers."""
        sections = []

        # Common section patterns
        patterns = [
            r'^(Article\s+\d+[:\.]?\s+.+?)$',
            r'^(Section\s+\d+(?:\.\d+)*[:\.]?\s+.+?)$',
            r'^(\d+\.\d+(?:\.\d+)*\.?\s+.+?)$',
        ]

        current_path = ""
        current_content = []

        for line in content.split('\n'):
            is_header = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous section
                    if current_content:
                        sections.append((current_path, '\n'.join(current_content)))

                    current_path = match.group(1).strip()
                    current_content = []
                    is_header = True
                    break

            if not is_header:
                current_content.append(line)

        # Save last section
        if current_content:
            sections.append((current_path, '\n'.join(current_content)))

        return sections

    def _chunk_text(self, text: str, section_path: str) -> List[DocumentChunk]:
        """Chunk text into smaller pieces."""
        chunks = []
        words = text.split()

        current_chunk = []
        current_length = 0
        chunk_index = 0
        start_char = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1

            if current_length >= self.chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    section_path=section_path,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    chunk_index=chunk_index,
                ))

                # Keep overlap
                overlap_words = current_chunk[-self.chunk_overlap // 10:]
                current_chunk = overlap_words
                current_length = sum(len(w) + 1 for w in overlap_words)
                start_char += len(chunk_text) - sum(len(w) + 1 for w in overlap_words)
                chunk_index += 1

        # Add remaining
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(DocumentChunk(
                content=chunk_text,
                section_path=section_path,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                chunk_index=chunk_index,
            ))

        return chunks

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction (would use TF-IDF or similar in production)
        keywords = []

        # Domain-specific terms to look for
        domain_terms = [
            "solar", "setback", "height", "screening", "permit", "conditional use",
            "variance", "buffer", "decommissioning", "glare", "noise", "acreage",
            "utility", "commercial", "agricultural", "residential", "prohibited",
            "allowed", "required", "shall", "must", "may",
        ]

        text_lower = text.lower()
        for term in domain_terms:
            if term in text_lower:
                keywords.append(term)

        return keywords[:max_keywords]
