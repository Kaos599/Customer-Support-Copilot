# LangExtract General Implementation Guide

## Overview

This guide provides a comprehensive blueprint for implementing LangExtract in applications that process documentation and text content. Unlike the SkyClad-specific guide, this focuses purely on text extraction and grounding without RAG systems, embeddings, or table processing.

LangExtract enables structured information extraction from unstructured text using Large Language Models, perfect for enhancing documentation understanding, content analysis, and information grounding.

## 🔑 Core Implementation Pattern

### Basic Architecture

```python
import langextract as lx
import os
from typing import List, Dict, Any, Optional
import logging

class LangExtractProcessor:
    def __init__(self, api_key: str, enable_extraction: bool = True):
        self.api_key = api_key
        self.enable_extraction = enable_extraction
        # Set API key for LangExtract
        os.environ['LANGEXTRACT_API_KEY'] = api_key
        self.logger = logging.getLogger(__name__)

    def extract_from_text(self, text: str, extraction_type: str) -> Optional[lx.data.Document]:
        """Extract structured information from text content"""
        # Implementation details below
```

## 🚀 Quick Start

### 1. Install LangExtract
```bash
pip install langextract>=1.0.8
```

### 2. Basic Text Extraction
```python
import langextract as lx

# Define what you want to extract
prompt = "Extract key concepts and their explanations from this technical documentation"

examples = [
    lx.data.ExampleData(
        text="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
        extractions=[
            lx.data.Extraction(
                extraction_class="concept",
                extraction_text="Machine Learning",
                attributes={
                    "definition": "subset of artificial intelligence that enables computers to learn without being explicitly programmed",
                    "category": "AI",
                    "difficulty": "intermediate"
                }
            )
        ]
    )
]

# Perform extraction
result = lx.extract(
    text_or_documents=your_document_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-1.5-flash",
    api_key="your-api-key"
)
```

## 📋 Common Text Extraction Patterns

### 1. Concept Extraction

```python
def extract_concepts(self, text: str) -> lx.data.Document:
    """Extract key concepts from documentation"""

    prompt_description = """
    Extract key concepts, terms, and their definitions from technical documentation.
    Focus on:
    1. Technical terms and their meanings
    2. Important concepts and principles
    3. Key methodologies or approaches
    4. Domain-specific terminology

    Provide clear, concise definitions and categorize appropriately.
    """

    examples = [
        lx.data.ExampleData(
            text="REST APIs use HTTP methods like GET, POST, PUT, and DELETE to perform operations on resources identified by URIs.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="concept",
                    extraction_text="REST API",
                    attributes={
                        "definition": "uses HTTP methods to perform operations on resources identified by URIs",
                        "category": "web_development",
                        "difficulty": "beginner"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="method",
                    extraction_text="HTTP Methods",
                    attributes={
                        "examples": ["GET", "POST", "PUT", "DELETE"],
                        "purpose": "perform operations on resources"
                    }
                )
            ]
        )
    ]

    return lx.extract(
        text_or_documents=text,
        prompt_description=prompt_description,
        examples=examples,
        model_id="gemini-1.5-flash",
        api_key=self.api_key,
        extraction_passes=1,
        max_workers=2,
        max_char_buffer=4000
    )
```

### 2. Information Architecture Extraction

```python
def extract_information_structure(self, text: str) -> lx.data.Document:
    """Extract document structure and organization"""

    prompt_description = """
    Analyze the document structure and extract:
    1. Main topics and subtopics
    2. Key sections and their purposes
    3. Document organization patterns
    4. Information hierarchy

    Focus on how information is organized and presented.
    """

    examples = [
        lx.data.ExampleData(
            text="# Introduction\n\nThis guide covers...\n\n## Getting Started\n\nFirst, install...\n\n### Prerequisites\n\nYou need...\n\n## Advanced Topics\n\nOnce familiar...",
            extractions=[
                lx.data.Extraction(
                    extraction_class="section",
                    extraction_text="Introduction",
                    attributes={
                        "level": "main",
                        "purpose": "overview",
                        "content_type": "explanatory"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="section",
                    extraction_text="Getting Started",
                    attributes={
                        "level": "main",
                        "purpose": "tutorial",
                        "prerequisites": ["Prerequisites"]
                    }
                )
            ]
        )
    ]

    return lx.extract(
        text_or_documents=text,
        prompt_description=prompt_description,
        examples=examples,
        model_id="gemini-1.5-flash",
        api_key=self.api_key
    )
```

### 3. Requirement Extraction

```python
def extract_requirements(self, text: str) -> lx.data.Document:
    """Extract requirements, constraints, and specifications"""

    prompt_description = """
    Extract requirements and specifications from documentation:
    1. Functional requirements
    2. Technical constraints
    3. Business rules
    4. Quality requirements
    5. Performance requirements

    Distinguish between mandatory and optional requirements.
    """

    examples = [
        lx.data.ExampleData(
            text="The system must process 1000 requests per second. Response time should be under 200ms. Users need to authenticate via OAuth2.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="performance_requirement",
                    extraction_text="Process 1000 requests per second",
                    attributes={
                        "type": "mandatory",
                        "metric": "throughput",
                        "value": "1000 req/s"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="functional_requirement",
                    extraction_text="Users need to authenticate via OAuth2",
                    attributes={
                        "type": "mandatory",
                        "component": "authentication",
                        "method": "OAuth2"
                    }
                )
            ]
        )
    ]

    return lx.extract(
        text_or_documents=text,
        prompt_description=prompt_description,
        examples=examples,
        model_id="gemini-1.5-flash",
        api_key=self.api_key
    )
```

### 4. Best Practice Extraction

```python
def extract_best_practices(self, text: str) -> lx.data.Document:
    """Extract best practices and recommendations"""

    prompt_description = """
    Extract best practices, recommendations, and guidelines from documentation:
    1. Recommended approaches
    2. Common pitfalls to avoid
    3. Proven patterns and solutions
    4. Quality standards and conventions

    Focus on actionable advice and practical guidance.
    """

    examples = [
        lx.data.ExampleData(
            text="Always validate user input on both client and server side. Never trust client-side validation alone. Use parameterized queries to prevent SQL injection.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="security_practice",
                    extraction_text="Validate input on client and server",
                    attributes={
                        "reason": "prevent malicious input",
                        "importance": "critical",
                        "implementation": "dual_validation"
                    }
                ),
                lx.data.Extraction(
                    extraction_class="security_practice",
                    extraction_text="Use parameterized queries",
                    attributes={
                        "threat": "SQL injection",
                        "solution_type": "defensive_coding"
                    }
                )
            ]
        )
    ]

    return lx.extract(
        text_or_documents=text,
        prompt_description=prompt_description,
        examples=examples,
        model_id="gemini-1.5-flash",
        api_key=self.api_key
    )
```

## 🔧 Configuration and Optimization

### Performance Profiles

```python
EXTRACTION_PROFILES = {
    "fast_analysis": {
        "extraction_passes": 1,
        "max_workers": 1,
        "max_char_buffer": 2000,
        "model_id": "gemini-1.5-flash"
    },
    "comprehensive": {
        "extraction_passes": 2,
        "max_workers": 3,
        "max_char_buffer": 6000,
        "model_id": "gemini-1.5-pro"
    },
    "detailed_research": {
        "extraction_passes": 3,
        "max_workers": 2,
        "max_char_buffer": 8000,
        "model_id": "gemini-1.5-pro"
    }
}

def extract_with_profile(self, text: str, extraction_type: str, profile: str = "fast_analysis"):
    """Extract using predefined performance profile"""

    config = EXTRACTION_PROFILES[profile]
    method = getattr(self, f"extract_{extraction_type}")

    return lx.extract(
        text_or_documents=text,
        **method().__dict__,  # Get the method's extraction config
        **config
    )
```

### Error Handling

```python
def safe_extract(self, text: str, extraction_type: str) -> Optional[lx.data.Document]:
    """Safe extraction with comprehensive error handling"""

    if not text or len(text.strip()) < 50:
        self.logger.warning("Text too short for meaningful extraction")
        return None

    try:
        method = getattr(self, f"extract_{extraction_type}")
        return method(text)

    except UnicodeEncodeError:
        self.logger.warning("Unicode encoding error - attempting safe extraction")
        # Try with ASCII-safe text
        safe_text = self._make_ascii_safe(text)
        return method(safe_text)

    except Exception as e:
        self.logger.error(f"LangExtract error for {extraction_type}: {e}")
        return None

def _make_ascii_safe(self, text: str) -> str:
    """Convert text to ASCII-safe version"""
    return text.encode('ascii', errors='replace').decode('ascii')
```

## 📁 Text Processing Utilities

### Text Preprocessing

```python
def preprocess_text(self, text: str) -> str:
    """Prepare text for extraction"""

    # Remove excessive whitespace
    text = ' '.join(text.split())

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

    # Limit length for performance
    if len(text) > 50000:  # ~10k tokens
        text = text[:50000] + "...[truncated]"

    return text

def chunk_large_text(self, text: str, chunk_size: int = 10000) -> List[str]:
    """Split large text into manageable chunks"""

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    words = text.split()
    current_chunk = []

    for word in words:
        if len(' '.join(current_chunk + [word])) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
```

### Result Processing

```python
def process_extraction_results(self, result: lx.data.Document) -> Dict[str, Any]:
    """Process and organize extraction results"""

    if not result or not hasattr(result, 'extractions'):
        return {"extractions": [], "summary": {}}

    processed = {
        "extractions": [],
        "summary": {
            "total_extractions": len(result.extractions),
            "extraction_classes": {},
            "confidence_scores": []
        }
    }

    for extraction in result.extractions:
        processed_extraction = {
            "class": getattr(extraction, 'extraction_class', 'unknown'),
            "text": getattr(extraction, 'extraction_text', ''),
            "attributes": getattr(extraction, 'attributes', {}),
            "confidence": getattr(extraction, 'confidence', None)
        }

        processed["extractions"].append(processed_extraction)

        # Update summary
        ext_class = processed_extraction["class"]
        processed["summary"]["extraction_classes"][ext_class] = \
            processed["summary"]["extraction_classes"].get(ext_class, 0) + 1

        if processed_extraction["confidence"]:
            processed["summary"]["confidence_scores"].append(processed_extraction["confidence"])

    return processed
```

## 🔄 Integration Patterns

### Simple API Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
processor = LangExtractProcessor(api_key="your-key")

class ExtractionRequest(BaseModel):
    text: str
    extraction_type: str  # "concepts", "requirements", "best_practices", etc.

@app.post("/extract")
async def extract_information(request: ExtractionRequest):
    """Extract structured information from text"""

    try:
        result = processor.extract_from_text(request.text, request.extraction_type)

        if not result:
            raise HTTPException(status_code=400, detail="Extraction failed")

        processed_result = processor.process_extraction_results(result)

        return {
            "success": True,
            "extractions": processed_result["extractions"],
            "summary": processed_result["summary"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")
```

### Batch Processing

```python
def process_document_batch(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Process multiple documents"""

    results = []

    for doc in documents:
        doc_id = doc.get("id", "unknown")
        text = doc.get("text", "")

        try:
            # Preprocess
            processed_text = self.preprocess_text(text)

            # Extract different types
            extractions = {}
            for ext_type in ["concepts", "requirements", "best_practices"]:
                result = self.extract_from_text(processed_text, ext_type)
                if result:
                    extractions[ext_type] = self.process_extraction_results(result)

            results.append({
                "document_id": doc_id,
                "extractions": extractions,
                "status": "success"
            })

        except Exception as e:
            results.append({
                "document_id": doc_id,
                "error": str(e),
                "status": "failed"
            })

    return results
```

## 📊 Quality Assessment

### Extraction Validation

```python
def validate_extractions(self, result: lx.data.Document, expected_classes: List[str]) -> Dict[str, Any]:
    """Validate extraction quality"""

    if not result or not hasattr(result, 'extractions'):
        return {"valid": False, "reason": "No extractions found"}

    validation = {
        "valid": True,
        "total_extractions": len(result.extractions),
        "class_coverage": 0,
        "issues": []
    }

    found_classes = set()
    for extraction in result.extractions:
        ext_class = getattr(extraction, 'extraction_class', '')
        found_classes.add(ext_class)

        # Check for empty or very short extractions
        text = getattr(extraction, 'extraction_text', '')
        if len(text.strip()) < 5:
            validation["issues"].append(f"Very short extraction: '{text}'")

    # Check class coverage
    expected_set = set(expected_classes)
    found_set = set(found_classes)
    coverage = len(expected_set.intersection(found_set)) / len(expected_set) if expected_set else 0
    validation["class_coverage"] = coverage

    if coverage < 0.5:
        validation["valid"] = False
        validation["issues"].append("Low class coverage - missing expected extraction types")

    return validation
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_concept_extraction():
    """Test concept extraction functionality"""

    with patch('langextract.extract') as mock_extract:
        # Mock successful extraction
        mock_result = Mock()
        mock_result.extractions = [
            Mock(
                extraction_class="concept",
                extraction_text="Machine Learning",
                attributes={"definition": "AI subset for learning"}
            )
        ]
        mock_extract.return_value = mock_result

        processor = LangExtractProcessor(api_key="test-key")
        result = processor.extract_concepts("Sample ML text")

        assert result is not None
        assert len(result.extractions) == 1
        assert result.extractions[0].extraction_class == "concept"

@pytest.mark.parametrize("extraction_type", ["concepts", "requirements", "best_practices"])
def test_extraction_types(extraction_type):
    """Test all extraction types"""

    processor = LangExtractProcessor(api_key="test-key")

    # Ensure method exists
    assert hasattr(processor, f"extract_{extraction_type}")

    # Test with mock
    with patch('langextract.extract') as mock_extract:
        mock_result = Mock()
        mock_result.extractions = []
        mock_extract.return_value = mock_result

        method = getattr(processor, f"extract_{extraction_type}")
        result = method("sample text")

        mock_extract.assert_called_once()
```

## 🚀 Production Considerations

### Configuration Management

```python
import os
from typing import Dict, Any

class ProductionConfig:
    def __init__(self):
        self.api_key = os.getenv('LANGEXTRACT_API_KEY')
        self.enable_extraction = os.getenv('ENABLE_LANGEXTRACT', 'true').lower() == 'true'
        self.max_text_length = int(os.getenv('MAX_TEXT_LENGTH', '50000'))
        self.default_model = os.getenv('DEFAULT_MODEL', 'gemini-1.5-flash')

    def get_extraction_config(self, profile: str) -> Dict[str, Any]:
        """Get configuration for extraction profile"""
        return EXTRACTION_PROFILES.get(profile, EXTRACTION_PROFILES['fast_analysis'])
```

### Monitoring

```python
class ExtractionMetrics:
    def __init__(self):
        self.extractions_performed = 0
        self.average_processing_time = 0.0
        self.error_count = 0
        self.extraction_types_used = {}

    def record_extraction(self, extraction_type: str, processing_time: float, success: bool):
        """Record extraction metrics"""
        self.extractions_performed += 1

        # Update average processing time
        current_avg = self.average_processing_time
        count = self.extractions_performed
        self.average_processing_time = (current_avg * (count - 1) + processing_time) / count

        # Track extraction types
        self.extraction_types_used[extraction_type] = \
            self.extraction_types_used.get(extraction_type, 0) + 1

        if not success:
            self.error_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            "total_extractions": self.extractions_performed,
            "average_time": round(self.average_processing_time, 2),
            "error_rate": self.error_count / max(self.extractions_performed, 1),
            "popular_types": sorted(self.extraction_types_used.items(), key=lambda x: x[1], reverse=True)
        }
```

## 🎯 Use Cases

### Documentation Analysis
- Extract key concepts from technical docs
- Identify requirements and specifications
- Find best practices and guidelines

### Content Grounding
- Provide context for user queries
- Enhance search results with structured information
- Improve content understanding

### Knowledge Management
- Build knowledge bases from documents
- Create structured summaries
- Generate training materials

### Quality Assurance
- Validate documentation completeness
- Check for consistency
- Identify missing information

## 📚 Best Practices

### 1. **Start with Clear Examples**
```python
# Good examples are specific and realistic
examples = [
    lx.data.ExampleData(
        text="REST APIs provide programmatic access to web services using standard HTTP methods.",
        extractions=[
            lx.data.Extraction(
                extraction_class="concept",
                extraction_text="REST API",
                attributes={"definition": "provides programmatic access using HTTP methods"}
            )
        ]
    )
]
```

### 2. **Use Appropriate Granularity**
- Extract meaningful units, not everything
- Focus on information that adds value
- Balance completeness with performance

### 3. **Handle Edge Cases**
- Empty or very short text
- Unicode encoding issues
- Network timeouts
- API rate limits

### 4. **Monitor and Optimize**
- Track extraction performance
- Monitor API usage and costs
- Adjust configurations based on usage patterns

This guide provides a solid foundation for implementing LangExtract in documentation processing applications, focusing on practical patterns that work well in production environments.
