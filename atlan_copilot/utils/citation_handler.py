import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import uuid

@dataclass
class CitationSource:
    """
    Represents a single citation source with all relevant information.
    """
    id: str
    title: str
    url: str
    source: str
    content_snippet: str
    relevance_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "content_snippet": self.content_snippet,
            "relevance_score": self.relevance_score
        }

@dataclass
class CitedText:
    """
    Represents text with embedded numbered citations.
    """
    text: str
    sources: List[CitationSource]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "text": self.text,
            "sources": [source.to_dict() for source in self.sources]
        }

class CitationHandler:
    """
    Handles the creation, processing, and formatting of citations.
    Inspired by LangExtract's approach to source grounding and traceability.
    """
    
    def __init__(self):
        self.citation_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.source_pattern = re.compile(r'\bSource\b', re.IGNORECASE)
        
    def extract_sources_from_context(self, context: str) -> List[CitationSource]:
        """
        Extract source information from RAG context.
        
        Args:
            context: The formatted context string from RAG agent
            
        Returns:
            List of CitationSource objects
        """
        sources = []
        
        # Split context by snippets
        snippet_pattern = re.compile(r'--- Context Snippet (\d+) ---\n(.*?)(?=--- Context Snippet \d+ ---|$)', re.DOTALL)
        matches = snippet_pattern.findall(context)
        
        for snippet_num, snippet_content in matches:
            # Extract source information
            source_info = self._parse_snippet_info(snippet_content)
            if source_info:
                citation_id = f"src_{uuid.uuid4().hex[:8]}"
                source = CitationSource(
                    id=citation_id,
                    title=source_info.get("title", "Unknown Title"),
                    url=source_info.get("url", ""),
                    source=source_info.get("source", "Atlan Documentation"),
                    content_snippet=source_info.get("content", "").strip(),  # FULL CONTENT - No truncation
                    relevance_score=None  # Could be added later
                )
                sources.append(source)
                
        return sources
    
    def _parse_snippet_info(self, snippet_content: str) -> Optional[Dict[str, str]]:
        """
        Parse individual snippet content to extract structured information.
        
        Args:
            snippet_content: Raw snippet content
            
        Returns:
            Dictionary with parsed information or None
        """
        info = {}
        
        lines = snippet_content.strip().split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('Source:'):
                info['source'] = line[7:].strip()
            elif line.startswith('URL:'):
                url = line[4:].strip()
                # Filter out localhost and invalid URLs
                if not url.startswith('http://localhost') and not url.startswith('http://127.0.0.1') and url.startswith('http'):
                    info['url'] = url
            elif line.startswith('Title:'):
                info['title'] = line[6:].strip()
            elif line.startswith('Content:'):
                info['content'] = line[8:].strip()
                in_content = True
            elif in_content:
                content_lines.append(line)
        
        # Join remaining content lines
        if content_lines:
            content_addition = ' ' + ' '.join(content_lines)
            info['content'] = info.get('content', '') + content_addition
        
        # Only return info if we have essential fields and valid URL
        if info.get('url') and info.get('title') and info.get('content'):
            return info
        return None
    
    def process_response_with_citations(self, response_text: str, sources: List[CitationSource]) -> CitedText:
        """
        Process response text to replace markdown citations with numbered citations.
        
        Args:
            response_text: The generated response text
            sources: List of available citation sources
            
        Returns:
            CitedText object with numbered citations
        """
        if not sources:
            return CitedText(text=response_text, sources=[])
        
        # Create a mapping of URLs to citation numbers
        url_to_citation = {}
        used_sources = []
        citation_counter = 1
        
        # First pass: identify all URLs mentioned in the text
        markdown_links = self.citation_pattern.findall(response_text)
        source_mentions = self.source_pattern.findall(response_text)
        
        processed_text = response_text
        
        # Handle markdown-style citations [text](url)
        for link_text, url in markdown_links:
            if url not in url_to_citation:
                # Find matching source
                matching_source = self._find_matching_source(url, sources)
                if matching_source:
                    url_to_citation[url] = citation_counter
                    used_sources.append(matching_source)
                    citation_counter += 1
            
            # Replace markdown link with numbered citation
            citation_num = url_to_citation.get(url)
            if citation_num:
                old_pattern = f"[{re.escape(link_text)}]({re.escape(url)})"
                new_pattern = f"[{citation_num}]"
                processed_text = re.sub(old_pattern, new_pattern, processed_text, count=1)
        
        # Handle generic "Source" mentions
        # This is more complex as we need to infer which source is being referenced
        if source_mentions and not markdown_links:
            # If we have sources but no specific URLs, assign them in order
            for i, source in enumerate(sources[:3]):  # Limit to first 3 sources
                if i + 1 not in [src.id for src in used_sources]:
                    used_sources.append(source)
        
        # Replace remaining "Source" mentions with numbered citations
        source_counter = 1
        def replace_source(match):
            nonlocal source_counter
            if source_counter <= len(used_sources):
                replacement = f"[{source_counter}]"
                source_counter += 1
                return replacement
            return match.group(0)
        
        processed_text = self.source_pattern.sub(replace_source, processed_text)
        
        return CitedText(text=processed_text, sources=used_sources)
    
    def _find_matching_source(self, url: str, sources: List[CitationSource]) -> Optional[CitationSource]:
        """
        Find a source that matches the given URL.
        
        Args:
            url: URL to match
            sources: List of available sources
            
        Returns:
            Matching CitationSource or None
        """
        for source in sources:
            if source.url == url or url in source.url:
                return source
        return None
    
    def format_sources_for_display(self, sources: List[CitationSource]) -> List[Dict[str, Any]]:
        """
        Format sources for display in the UI.
        
        Args:
            sources: List of CitationSource objects
            
        Returns:
            List of dictionaries formatted for UI display
        """
        formatted_sources = []
        
        for i, source in enumerate(sources, 1):
            formatted_source = {
                "number": i,
                "title": source.title,
                "url": source.url,
                "source": source.source,
                "content_snippet": source.content_snippet,
                "relevance_score": source.relevance_score
            }
            formatted_sources.append(formatted_source)
            
        return formatted_sources
    
    def create_sources_dropdown_html(self, sources: List[CitationSource]) -> str:
        """
        Create HTML for a sources dropdown component.
        
        Args:
            sources: List of CitationSource objects
            
        Returns:
            HTML string for the dropdown
        """
        if not sources:
            return ""
        
        html_parts = []
        html_parts.append('<div class="sources-dropdown">')
        html_parts.append('  <div class="sources-header">📚 Sources</div>')
        html_parts.append('  <div class="sources-content">')
        
        for i, source in enumerate(sources, 1):
            html_parts.append(f'    <div class="source-item">')
            html_parts.append(f'      <div class="source-number">[{i}]</div>')
            html_parts.append(f'      <div class="source-details">')
            html_parts.append(f'        <div class="source-title">{source.title}</div>')
            html_parts.append(f'        <div class="source-url"><a href="{source.url}" target="_blank">{source.url}</a></div>')
            html_parts.append(f'        <div class="source-snippet">"{source.content_snippet}"</div>')
            html_parts.append(f'      </div>')
            html_parts.append(f'    </div>')
        
        html_parts.append('  </div>')
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def extract_and_process_citations(self, response_text: str, context: str) -> CitedText:
        """
        Main method to extract sources from context and process citations in response.
        
        Args:
            response_text: The generated response text
            context: The RAG context string
            
        Returns:
            CitedText object with processed citations
        """
        # Extract sources from context
        sources = self.extract_sources_from_context(context)
        
        # Check if response already has numbered citations or needs processing
        numbered_citation_pattern = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
        existing_citations = numbered_citation_pattern.findall(response_text)
        
        if existing_citations:
            # Response already has numbered citations, just map them to sources
            cited_text = self._map_existing_citations_to_sources(response_text, sources)
        else:
            # Response needs citation processing from "Source" references
            cited_text = self.process_response_with_citations(response_text, sources)
        
        return cited_text
    
    def _map_existing_citations_to_sources(self, response_text: str, sources: List[CitationSource]) -> CitedText:
        """
        Map existing numbered citations in response to available sources.
        
        Args:
            response_text: Response text with numbered citations like [1], [2], [1, 2]
            sources: Available citation sources
            
        Returns:
            CitedText object with mapped sources
        """
        # Find all citation numbers used in the response
        citation_pattern = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
        matches = citation_pattern.findall(response_text)
        
        # Extract all unique citation numbers
        used_numbers = set()
        for match in matches:
            # Handle both single numbers [1] and comma-separated [1, 2]
            numbers = [int(n.strip()) for n in match.split(',')]
            used_numbers.update(numbers)
        
        # Map citation numbers to available sources
        mapped_sources = []
        for num in sorted(used_numbers):
            if num <= len(sources):
                mapped_sources.append(sources[num - 1])  # Convert to 0-based index
        
        return CitedText(text=response_text, sources=mapped_sources)
