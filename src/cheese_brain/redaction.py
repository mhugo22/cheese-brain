"""
Sensitive field redaction for CLI output.
"""

import re
from typing import Any, Dict

# Patterns for sensitive field keys
SENSITIVE_PATTERNS = [
    r"password",
    r"passwd",
    r"secret",
    r"api[_-]?key",
    r"token",
    r"private[_-]?key",
    r"auth",
    r"credential",
    r"bearer",
    r"jwt",
]

# Compile patterns for performance
SENSITIVE_REGEX = re.compile(
    "|".join(f"({pattern})" for pattern in SENSITIVE_PATTERNS),
    re.IGNORECASE,
)

REDACTED_VALUE = "●●●●●●●●"


def is_sensitive_key(key: str) -> bool:
    """Check if a key name indicates sensitive data.
    
    Args:
        key: Field name to check
        
    Returns:
        True if key matches sensitive patterns
    """
    return bool(SENSITIVE_REGEX.search(key))


def redact_dict(data: Dict[str, Any], reveal: bool = False) -> Dict[str, Any]:
    """Recursively redact sensitive values in a dictionary.
    
    Args:
        data: Dictionary to redact
        reveal: If True, don't redact (show real values)
        
    Returns:
        Dictionary with sensitive values redacted
    """
    if reveal:
        return data
    
    if not isinstance(data, dict):
        return data
    
    redacted = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            redacted[key] = REDACTED_VALUE
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value, reveal)
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item, reveal) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted
