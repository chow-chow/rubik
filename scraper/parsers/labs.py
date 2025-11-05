"""
Parser for laboratory courses.
"""

import re
import logging
from typing import List, Dict
from bs4 import BeautifulSoup

from .base import BaseParser

logger = logging.getLogger(__name__)


class LabsParser(BaseParser):
    """Parser for lab courses."""
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract lab courses from JavaScript file."""
        try:
            js_content = str(soup)
            matches = re.findall(r"asignatura\['(\d+)'\]\s*=\s*'([^']+)'", js_content)
            
            labs = [
                {'code': c[0].zfill(4), 'name': c[1]} 
                for c in matches if int(c[0]) > 5000
            ]
            
            logger.info(f"Found {len(labs)} lab courses")
            return labs
            
        except Exception as e:
            logger.error(f"Error parsing labs: {e}")
            return []
