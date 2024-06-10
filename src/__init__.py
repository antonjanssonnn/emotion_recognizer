# src/__init__.py

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .emotion_analyzer import EmotionAnalyzer
from .frame_processor import FrameProcessor
from .database_manager import DatabaseManager
