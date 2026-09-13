"""Thin coursework presentation layer over the accepted RAG services."""

from cu_intelligence.ui.service import (
    CourseworkDemoResult,
    CourseworkDemoService,
    build_live_coursework_demo_service,
)

__all__ = [
    "CourseworkDemoResult",
    "CourseworkDemoService",
    "build_live_coursework_demo_service",
]
