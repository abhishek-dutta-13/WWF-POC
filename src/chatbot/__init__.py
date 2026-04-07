"""
WWF Chatbot Module

This module contains the agentic RAG chatbot implementation.
"""

from .database import init_db, get_db, get_database_info

__all__ = ["init_db", "get_db", "get_database_info"]
