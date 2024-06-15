import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database_manager import DatabaseManager
from .frame_processor import FrameProcessor

__all__ = [
    "DatabaseManager",
    "FrameProcessor",
]
