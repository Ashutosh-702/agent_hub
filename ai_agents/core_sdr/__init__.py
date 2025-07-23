"""
Lead Generation System

A sophisticated lead generation system that converts natural language queries 
into targeted company searches using the CoreSignal API.
"""

__version__ = "1.0.0"
__author__ = "Lead Generation Team"

from .src.core import (
    LeadGenerationOrchestrator,
    LeadGenerationError,
    SearchRequest,
    SearchResponse,
    Company
)

__all__ = [
    'LeadGenerationOrchestrator',
    'LeadGenerationError', 
    'SearchRequest',
    'SearchResponse',
    'Company'
]