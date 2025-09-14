"""
LangExtract-based Citation Handler for Precise Source Grounding

This module integrates Google's LangExtract library to provide precise, 
character-level citation positioning and improved source grounding.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, asdict
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class PreciseSourceCitation:
    """Enhanced citation source with character-level positioning"""
    id: str
    title: str
    url: str
    source: str
    content_snippet: str
    extracted_text: str  # The exact text that supports the claim
    start_position: Optional[int] = None  # Character position in source
    end_position: Optional[int] = None
    relevance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PreciseCitedText:
    """Text with precise citations using LangExtract methodology"""
    text: str
    citations: List[PreciseSourceCitation]
    extraction_confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'citations': [citation.to_dict() for citation in self.citations],
            'extraction_confidence': self.extraction_confidence
        }


class LangExtractCitationHandler:
    """
    Advanced citation handler inspired by Google's LangExtract library
    for precise source grounding and citation positioning.
    
    Note: This is a simplified implementation that captures the core concepts
    of LangExtract without requiring the full library dependencies.
    """
    
    def __init__(self, gemini_api_key: str):
        """Initialize with Gemini API key for future LangExtract integration"""
        self.gemini_api_key = gemini_api_key
        self.citation_pattern = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
        
    async def extract_precise_citations(
        self, 
        response_text: str, 
        context_sources: List[Dict[str, str]]
    ) -> PreciseCitedText:
        """
        Use LangExtract-inspired approach for precise citations with source grounding
        
        Args:
            response_text: The generated response text with numbered citations
            context_sources: List of source documents with content
            
        Returns:
            PreciseCitedText with enhanced citation information
        """
        try:
            # Extract numbered citations from response
            citation_matches = self.citation_pattern.findall(response_text)
            
            if not citation_matches:
                logger.warning("No numbered citations found in response")
                return PreciseCitedText(
                    text=response_text,
                    citations=self._create_fallback_citations(context_sources)
                )
            
            # Process each claim in the response with LangExtract-inspired approach
            precise_citations = await self._process_claims_with_precision(
                response_text, 
                context_sources,
                citation_matches
            )
            
            return PreciseCitedText(
                text=response_text,
                citations=precise_citations,
                extraction_confidence=self._calculate_overall_confidence(precise_citations)
            )
            
        except Exception as e:
            logger.error(f"Error in LangExtract citation processing: {e}")
            return PreciseCitedText(
                text=response_text,
                citations=self._create_fallback_citations(context_sources)
            )
    
    async def _process_claims_with_precision(
        self,
        response_text: str,
        context_sources: List[Dict[str, str]],
        citation_matches: List[str]
    ) -> List[PreciseSourceCitation]:
        """Process individual claims with precise source grounding"""
        precise_citations = []
        
        # Split response into sentences for claim-level processing
        sentences = self._split_into_sentences(response_text)
        
        for sentence in sentences:
            # Check if sentence contains citations
            sentence_citations = self.citation_pattern.findall(sentence)
            
            if sentence_citations:
                # Extract the claim without citation numbers for processing
                clean_sentence = re.sub(self.citation_pattern, '', sentence).strip()
                
                if clean_sentence:
                    # Map results to citation numbers
                    for citation_nums_str in sentence_citations:
                        citation_nums = [int(n.strip()) for n in citation_nums_str.split(',')]
                        
                        for citation_num in citation_nums:
                            if citation_num <= len(context_sources):
                                source_info = context_sources[citation_num - 1]  # 0-indexed
                                
                                # Find precise evidence in the source
                                extracted_evidence = self._extract_precise_evidence(
                                    clean_sentence, 
                                    source_info.get('content', '')
                                )
                                
                                citation = PreciseSourceCitation(
                                    id=str(citation_num),
                                    title=source_info.get('title', f'Source {citation_num}'),
                                    url=source_info.get('url', ''),
                                    source=source_info.get('source', ''),
                                    content_snippet=source_info.get('content', '')[:200] + '...' if source_info.get('content') else '',
                                    extracted_text=extracted_evidence.get('text', clean_sentence),
                                    start_position=extracted_evidence.get('start'),
                                    end_position=extracted_evidence.get('end'),
                                    relevance_score=extracted_evidence.get('relevance', 0.8),
                                    confidence_score=extracted_evidence.get('confidence', 0.75)
                                )
                                
                                precise_citations.append(citation)
        
        # Remove duplicates based on ID
        unique_citations = {}
        for citation in precise_citations:
            if citation.id not in unique_citations:
                unique_citations[citation.id] = citation
        
        return list(unique_citations.values())
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for processing"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_precise_evidence(self, claim: str, source_content: str) -> Dict[str, Any]:
        """
        Extract precise evidence from source content that supports the claim.
        This implements core LangExtract concepts for source grounding.
        """
        if not source_content:
            return {
                'text': claim,
                'start': None,
                'end': None,
                'relevance': 0.5,
                'confidence': 0.5
            }
        
        claim_lower = claim.lower()
        source_lower = source_content.lower()
        
        # Find the best matching window using sliding window approach
        best_match = None
        best_score = 0
        
        # Try different window sizes for optimal evidence extraction
        for window_size in [50, 100, 150, 200]:
            if window_size > len(source_content):
                continue
                
            for start_pos in range(0, len(source_content) - window_size + 1, 25):
                window = source_content[start_pos:start_pos + window_size]
                window_lower = window.lower()
                
                # Calculate semantic relevance score
                relevance_score = self._calculate_semantic_relevance(claim_lower, window_lower)
                
                if relevance_score > best_score:
                    best_score = relevance_score
                    best_match = {
                        'text': window.strip(),
                        'start': start_pos,
                        'end': start_pos + window_size,
                        'relevance': relevance_score,
                        'confidence': min(relevance_score * 1.2, 0.95)  # Boost confidence slightly
                    }
        
        # If no good match found, return the beginning of the source
        if not best_match or best_score < 0.3:
            excerpt_length = min(150, len(source_content))
            return {
                'text': source_content[:excerpt_length].strip() + '...' if excerpt_length < len(source_content) else source_content.strip(),
                'start': 0,
                'end': excerpt_length,
                'relevance': 0.6,
                'confidence': 0.6
            }
        
        return best_match
    
    def _calculate_semantic_relevance(self, claim: str, window: str) -> float:
        """
        Calculate semantic relevance between claim and text window.
        Uses keyword overlap and phrase matching for relevance scoring.
        """
        claim_words = set(claim.split())
        window_words = set(window.split())
        
        if not claim_words:
            return 0.0
        
        # Basic keyword overlap
        intersection = claim_words.intersection(window_words)
        keyword_score = len(intersection) / len(claim_words)
        
        # Phrase matching bonus
        phrase_bonus = 0.0
        claim_phrases = self._extract_phrases(claim)
        
        for phrase in claim_phrases:
            if phrase.lower() in window.lower():
                phrase_bonus += 0.2
        
        # Combine scores
        final_score = min(keyword_score + phrase_bonus, 1.0)
        return final_score
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text"""
        # Simple n-gram extraction for 2-3 word phrases
        words = text.split()
        phrases = []
        
        # Extract 2-word phrases
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")
        
        # Extract 3-word phrases
        for i in range(len(words) - 2):
            phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases
    
    def _calculate_overall_confidence(self, citations: List[PreciseSourceCitation]) -> float:
        """Calculate overall confidence score for all citations"""
        if not citations:
            return 0.0
        
        confidence_scores = [c.confidence_score for c in citations if c.confidence_score]
        if not confidence_scores:
            return 0.0
        
        return sum(confidence_scores) / len(confidence_scores)
    
    def _create_fallback_citations(self, context_sources: List[Dict[str, str]]) -> List[PreciseSourceCitation]:
        """Create fallback citations when processing fails"""
        citations = []
        
        for i, source in enumerate(context_sources, 1):
            citation = PreciseSourceCitation(
                id=str(i),
                title=source.get('title', f'Source {i}'),
                url=source.get('url', ''),
                source=source.get('source', ''),
                content_snippet=source.get('content', '')[:200] + '...' if source.get('content') else '',
                extracted_text=source.get('content', '')[:150] + '...' if source.get('content') else '',
                relevance_score=0.7,
                confidence_score=0.6
            )
            citations.append(citation)
        
        return citations
    
    def format_sources_for_display(self, citations: List[PreciseSourceCitation]) -> List[Dict[str, Any]]:
        """Format citations for UI display with URL filtering"""
        formatted_sources = []

        # List of URL patterns to filter out
        invalid_url_patterns = [
            'http://localhost',
            'http://127.0.0.1',
            'https://localhost',
            'https://127.0.0.1',
            'localhost',
            '127.0.0.1'
        ]

        for citation in citations:
            # Use extracted text for better snippets
            snippet = citation.extracted_text or citation.content_snippet

            # Filter out invalid URLs
            url = citation.url
            if url:
                url_lower = url.lower()
                if any(pattern in url_lower for pattern in invalid_url_patterns):
                    url = ''  # Remove invalid URL

            formatted_source = {
                'id': citation.id,
                'title': citation.title,
                'url': url,  # Filtered URL
                'source': citation.source,
                'content_snippet': snippet,
                'relevance_score': citation.relevance_score,
                'confidence_score': citation.confidence_score
            }
            formatted_sources.append(formatted_source)

        return formatted_sources