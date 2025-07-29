"""
Lead Generation System

A sophisticated lead generation system that converts natural language queries 
into targeted company searches using the CoreSignal API.
"""

__version__ = "1.0.0"
__author__ = "Lead Generation Team"

from ai_agents.core_sdr.src.parsers.dsl_query_processor import (
    SimpleDSLProcessor,
    DSLQuery,
)

__all__ = [
    "SimpleDSLProcessor",
    "DSLQuery",
]