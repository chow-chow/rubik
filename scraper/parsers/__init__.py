"""
HTML parsers for extracting data from web pages.
"""

from .base import BaseParser
from .programs import ProgramsParser
from .study_plans import StudyPlansParser
from .study_plan_courses import StudyPlanCoursesParser
from .courses import CoursesParser
from .groups import GroupsParser
from .labs import LabsParser
from .professors import ProfessorRatingsParser

__all__ = [
    'BaseParser',
    'ProgramsParser',
    'StudyPlansParser',
    'StudyPlanCoursesParser',
    'CoursesParser',
    'GroupsParser',
    'LabsParser',
    'ProfessorRatingsParser',
]
