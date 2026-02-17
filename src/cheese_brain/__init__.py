"""
🧀 Cheese Brain - DuckDB-powered knowledge management system

A fast, flexible, git-friendly knowledge base designed for AI agents and humans
who want instant recall of projects, contacts, decisions, and more.
"""

__version__ = "0.1.0"
__author__ = "Matt H & Cheese"

from cheese_brain.core import CheeseBrain
from cheese_brain.models import Entity, EntityCategory
from cheese_brain.cli import main

__all__ = ["CheeseBrain", "Entity", "EntityCategory", "main"]
