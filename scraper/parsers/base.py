"""
Base parser with common utility methods.
"""

import logging

logger = logging.getLogger(__name__)


class BaseParser:
    """Base parser with common utility methods."""
    
    def __init__(self):
        self.logger = logger
    
    def safe_find(self, element, *args, **kwargs):
        """Safely find an element."""
        try:
            return element.find(*args, **kwargs)
        except Exception:
            return None
    
    def safe_find_all(self, element, *args, **kwargs):
        """Safely find all elements."""
        try:
            return element.find_all(*args, **kwargs)
        except Exception:
            return []
    
    def safe_get_text(self, element):
        """Safely get text from element."""
        try:
            return element.get_text(strip=True) if element else ""
        except Exception:
            return ""
