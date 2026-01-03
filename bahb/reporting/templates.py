"""Report template definitions."""

from enum import Enum


class ReportTemplate(Enum):
    """Available report templates."""
    STANDARD = "standard"
    DETAILED = "detailed"
    SUMMARY = "summary"
    EXECUTIVE = "executive"
    MAINTENANCE = "maintenance"
