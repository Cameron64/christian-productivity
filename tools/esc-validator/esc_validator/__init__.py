"""
ESC Sheet Validation System

Automated validation for Erosion and Sediment Control (ESC) sheets
in civil engineering drawing sets.
"""

__version__ = "0.1.0"
__author__ = "Christian's Productivity Tools"

from .extractor import extract_esc_sheet
from .text_detector import detect_required_labels, verify_minimum_quantities
from .validator import validate_esc_sheet

__all__ = [
    "extract_esc_sheet",
    "detect_required_labels",
    "verify_minimum_quantities",
    "validate_esc_sheet",
]
