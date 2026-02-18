"""
Auto-capture entities from daily notes and markdown files.

Extracts structured entities from text using pattern matching.
"""

import re
from typing import Optional
from cheese_brain.models import EntityCategory


class EntityExtractor:
    """Extract entities from markdown text using pattern matching."""
    
    # Pattern: **Tool:** Tool Name - description
    TOOL_PATTERN = r'\*\*Tool:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Pattern: **Workflow:** Workflow Name - description
    WORKFLOW_PATTERN = r'\*\*Workflow:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Pattern: **Decision:** Decision Name - reason
    DECISION_PATTERN = r'\*\*Decision:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Pattern: **Project:** Project Name - description
    PROJECT_PATTERN = r'\*\*Project:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Pattern: **API:** API Name - description
    API_PATTERN = r'\*\*API:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Pattern: **Infrastructure:** Name - description
    INFRASTRUCTURE_PATTERN = r'\*\*Infrastructure:\*\*\s+([^-\n]+?)(?:\s+-\s+(.+))?$'
    
    # Generic pattern: - Category: Title (tags) - description
    GENERIC_PATTERN = r'-\s+(\w+):\s+([^(\n]+?)(?:\s+\(([^)]+)\))?(?:\s+-\s+(.+))?$'
    
    def __init__(self):
        """Initialize extractor."""
        self.patterns = {
            EntityCategory.TOOL: re.compile(self.TOOL_PATTERN, re.MULTILINE | re.IGNORECASE),
            EntityCategory.WORKFLOW: re.compile(self.WORKFLOW_PATTERN, re.MULTILINE | re.IGNORECASE),
            EntityCategory.DECISION: re.compile(self.DECISION_PATTERN, re.MULTILINE | re.IGNORECASE),
            EntityCategory.PROJECT: re.compile(self.PROJECT_PATTERN, re.MULTILINE | re.IGNORECASE),
            EntityCategory.API: re.compile(self.API_PATTERN, re.MULTILINE | re.IGNORECASE),
            EntityCategory.INFRASTRUCTURE: re.compile(self.INFRASTRUCTURE_PATTERN, re.MULTILINE | re.IGNORECASE),
        }
    
    def extract_from_text(self, text: str, confidence_threshold: float = 0.7) -> list[dict]:
        """Extract entities from markdown text.
        
        Args:
            text: Markdown text to parse
            confidence_threshold: Minimum confidence (0.0-1.0) to include
            
        Returns:
            List of entity dicts: [{category, title, description, confidence, tags}, ...]
        """
        entities = []
        
        # Try specific patterns first
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    title = match[0].strip()
                    description = match[1].strip() if len(match) > 1 and match[1] else ""
                else:
                    title = match.strip()
                    description = ""
                
                if title:
                    entities.append({
                        "category": category.value,
                        "title": title,
                        "data": {"description": description} if description else {},
                        "confidence": 0.9,  # High confidence for explicit patterns
                        "tags": [],
                        "source": "explicit_pattern"
                    })
        
        # Try generic pattern (lower confidence)
        generic_pattern = re.compile(self.GENERIC_PATTERN, re.MULTILINE | re.IGNORECASE)
        matches = generic_pattern.findall(text)
        
        for match in matches:
            category_str, title, tags_str, description = match
            
            # Try to map category string to EntityCategory
            try:
                category = EntityCategory(category_str.lower())
                confidence = 0.8  # Medium confidence for generic pattern
            except ValueError:
                # Unknown category, skip
                continue
            
            title = title.strip()
            tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
            description = description.strip() if description else ""
            
            # Check if already extracted
            if not any(e["title"] == title and e["category"] == category.value for e in entities):
                entities.append({
                    "category": category.value,
                    "title": title,
                    "data": {"description": description} if description else {},
                    "confidence": confidence,
                    "tags": tags,
                    "source": "generic_pattern"
                })
        
        # Filter by confidence
        return [e for e in entities if e["confidence"] >= confidence_threshold]
    
    def extract_from_cheese_digest(self, text: str) -> list[dict]:
        """Extract entities from ## 🧀 Cheese Digest sections.
        
        Args:
            text: Markdown text containing Cheese Digest section
            
        Returns:
            List of entity dicts
        """
        # Find Cheese Digest section
        digest_pattern = r'##\s+🧀\s+Cheese\s+Digest\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(digest_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return []
        
        digest_text = match.group(1)
        return self.extract_from_text(digest_text, confidence_threshold=0.85)


def scan_file(file_path: str, confidence_threshold: float = 0.7) -> dict:
    """Scan a markdown file for entities.
    
    Args:
        file_path: Path to markdown file
        confidence_threshold: Minimum confidence (0.0-1.0)
        
    Returns:
        Dict with scan results: {
            "file": str,
            "entities": list[dict],
            "digest_entities": list[dict],
            "total": int
        }
    """
    extractor = EntityExtractor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extract from whole file
    entities = extractor.extract_from_text(text, confidence_threshold)
    
    # Extract from Cheese Digest section specifically
    digest_entities = extractor.extract_from_cheese_digest(text)
    
    # Combine and deduplicate
    all_entities = []
    seen = set()
    
    for entity in digest_entities + entities:
        key = (entity["category"], entity["title"])
        if key not in seen:
            seen.add(key)
            all_entities.append(entity)
    
    return {
        "file": file_path,
        "entities": all_entities,
        "digest_entities": digest_entities,
        "total": len(all_entities)
    }
