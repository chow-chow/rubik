"""
HTML parsers for extracting data from web pages.
"""

from .base import BaseParser
from .programs import ProgramsParser
from .study_plans import StudyPlansParser
from .courses import CoursesParser
from .groups import GroupsParser
from .labs import LabsParser
from .professors import ProfessorRatingsParser

__all__ = [
    'BaseParser',
    'ProgramsParser',
    'StudyPlansParser',
    'CoursesParser',
    'GroupsParser',
    'LabsParser',
    'ProfessorRatingsParser',
]
