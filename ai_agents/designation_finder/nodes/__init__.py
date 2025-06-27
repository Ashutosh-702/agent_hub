"""
Workflow nodes for designation finder
"""
from .csv_logger import csv_logger
from .linkedin_designation_finder import linkedin_designation_finder

__all__ = ['csv_logger', 'linkedin_designation_finder']